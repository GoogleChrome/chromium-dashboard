# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'ericbidelman@chromium.org (Eric Bidelman)'

from datetime import datetime, timedelta
import collections
import logging
import os
from typing import Any, Optional
import urllib

from framework import permissions
from google.cloud import ndb  # type: ignore

from flask import escape
from flask import render_template

from framework import basehandlers
from framework import cloud_tasks_helpers
from framework import users
import settings
from internals import approval_defs
from internals import core_enums
from internals import stage_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate
from internals.user_models import (
    AppUser, BlinkComponent, FeatureOwner, UserPref)


def format_email_body(
    is_update: bool, fe: FeatureEntry, fe_stages: dict[int, list[Stage]],
    changes: list[dict[str, Any]]) -> str:
  """Return an HTML string for a notification email body."""

  stage_type = core_enums.STAGE_TYPES_SHIPPING[fe.feature_type] or 0
  ship_stages: list[Stage] = fe_stages.get(stage_type, [])
  # TODO(danielrsmith): These notifications do not convey correct information
  # for features with multiple shipping stages. Implement a new way to
  # specify the shipping stage affected.
  ship_milestones: MilestoneSet | None = (
      ship_stages[0].milestones if len(ship_stages) > 0 else None)

  milestone_str = 'not yet assigned'
  if ship_milestones is not None:
    if ship_milestones.desktop_first:
      milestone_str = ship_milestones.desktop_first
    elif (ship_milestones.desktop_first is None and
        ship_milestones.android_first is not None):
      milestone_str = f'{ship_milestones.android_first} (android)'

  moz_link_urls = [
      link for link in fe.doc_links
      if urllib.parse.urlparse(link).hostname == 'developer.mozilla.org']

  formatted_changes = ''
  for prop in changes:
    prop_name = prop['prop_name']
    new_val = prop['new_val']
    old_val = prop['old_val']

    formatted_changes += ('<li><b>%s:</b> <br/><b>old:</b> %s <br/>'
                          '<b>new:</b> %s<br/></li><br/>' %
                          (prop_name, escape(old_val), escape(new_val)))
  if not formatted_changes:
    formatted_changes = '<li>None</li>'

  body_data = {
      'feature': fe,
      'creator_email': fe.creator_email,
      'updater_email': fe.updater_email,
      'id': fe.key.integer_id(),
      'milestone': milestone_str,
      'status': core_enums.IMPLEMENTATION_STATUS[fe.impl_status_chrome],
      'formatted_changes': formatted_changes,
      'moz_link_urls': moz_link_urls,
  }
  template_path = ('update-feature-email.html' if is_update
                   else 'new-feature-email.html')
  body = render_template(template_path, **body_data)
  return body


def accumulate_reasons(
      addr_reasons: dict[str, list], addr_list: list[str], reason: str) -> None:
  """Add a reason string for each user."""
  for email in addr_list:
    addr_reasons[email].append(reason)


def convert_reasons_to_task(
    addr, reasons, email_html, subject, triggering_user_email):
  """Add a task dict to task_list for each user who has not already got one."""
  assert reasons, 'We are emailing someone without any reason'
  footer_lines = ['<p>You are receiving this email because:</p>', '<ul>']
  for reason in sorted(set(reasons)):
    footer_lines.append('<li>%s</li>' % reason)
  footer_lines.append('</ul>')
  footer_lines.append('<p><a href="%ssettings">Unsubscribe</a></p>' %
                      settings.SITE_URL)
  email_html_with_footer = email_html + '\n\n' + '\n'.join(footer_lines)

  reply_to = None
  recipient_user = users.User(email=addr)
  if permissions.can_create_feature(recipient_user):
    reply_to = triggering_user_email

  one_email_task = {
      'to': addr,
      'subject': subject,
      'reply_to': reply_to,
      'html': email_html_with_footer
  }
  return one_email_task


WEBVIEW_RULE_REASON = (
    'This feature has an android milestone, but not a webview milestone')
WEBVIEW_RULE_ADDRS = ['webview-leads-external@google.com']


def apply_subscription_rules(
    fe: FeatureEntry, fe_stages: dict[int, list[Stage]],
    changes: list) -> dict[str, list[str]]:
  """Return {"reason": [addrs]} for users who set up rules."""
  # Note: for now this is hard-coded, but it will eventually be
  # configurable through some kind of user preference.
  changed_field_names = {c['prop_name'] for c in changes}
  results: dict[str, list[str]] = {}

  # Find an existing shipping stage with milestone info.
  stage_type = core_enums.STAGE_TYPES_SHIPPING[fe.feature_type] or 0
  ship_stages: list[Stage] = fe_stages.get(stage_type, [])
  # TODO(danielrsmith): These notifications do not convey correct information
  # for features with multiple shipping stages. Implement a new way to
  # specify the shipping stage affected.
  ship_milestones: MilestoneSet | None = (
      ship_stages[0].milestones if len(ship_stages) > 0 else None)

  # Check if feature has some other milestone set, but not webview.
  if (ship_milestones is not None and
      ship_milestones.android_first and
      not ship_milestones.webview_first):
    milestone_fields = ['shipped_android_milestone']
    if not changed_field_names.isdisjoint(milestone_fields):
      results[WEBVIEW_RULE_REASON] = WEBVIEW_RULE_ADDRS

  return results


def make_feature_changes_email(fe: FeatureEntry, is_update: bool=False,
    changes: Optional[list]=None):
  """Return a list of task dicts to notify users of feature changes."""
  if changes is None:
    changes = []
  watchers: list[FeatureOwner] = FeatureOwner.query(
      FeatureOwner.watching_all_features == True).fetch(None)
  watcher_emails: list[str] = [watcher.email for watcher in watchers]

  fe_stages = stage_helpers.get_feature_stages(fe.key.integer_id())

  email_html = format_email_body(is_update, fe, fe_stages, changes)
  if is_update:
    subject = 'updated feature: %s' % fe.name
    triggering_user_email = fe.updater_email
  else:
    subject = 'new feature: %s' % fe.name
    triggering_user_email = fe.creator_email

  addr_reasons: dict[str, list[str]] = collections.defaultdict(list)

  accumulate_reasons(
    addr_reasons, fe.owner_emails,
    'You are listed as an owner of this feature'
  )
  accumulate_reasons(
    addr_reasons, fe.editor_emails,
    'You are listed as an editor of this feature'
  )
  accumulate_reasons(
    addr_reasons, fe.cc_emails,
    'You are CC\'d on this feature'
  )
  accumulate_reasons(
    addr_reasons, fe.devrel_emails,
    'You are a devrel contact for this feature.'
  )
  accumulate_reasons(
    addr_reasons, watcher_emails,
    'You are watching all feature changes'
  )

  # There will always be at least one component.
  for component_name in fe.blink_components:
    component = BlinkComponent.get_by_name(component_name)
    if not component:
      logging.warning('Blink component "%s" not found.'
                      'Not sending email to subscribers' % component_name)
      continue
    owner_emails: list[str] = [owner.email for owner in component.owners]
    subscriber_emails: list[str] = [sub.email for sub in component.subscribers]
    accumulate_reasons(
        addr_reasons, owner_emails,
        'You are an owner of this feature\'s component')
    accumulate_reasons(
        addr_reasons, subscriber_emails,
        'You subscribe to this feature\'s component')
  starrers = FeatureStar.get_feature_starrers(fe.key.integer_id())
  starrer_emails: list[str] = [user.email for user in starrers]
  accumulate_reasons(addr_reasons, starrer_emails, 'You starred this feature')

  rule_results = apply_subscription_rules(fe, fe_stages, changes)
  for reason, sub_addrs in rule_results.items():
    accumulate_reasons(addr_reasons, sub_addrs, reason)

  all_tasks = [convert_reasons_to_task(
                   addr, reasons, email_html, subject, triggering_user_email)
               for addr, reasons in sorted(addr_reasons.items())]
  return all_tasks


def make_review_requests_email(fe: FeatureEntry, gate_type: int, changes: Optional[list]=None):
  """Return a list of task dicts to notify approvers of review requests."""
  if changes is None:
    changes = []
  fe_stages = stage_helpers.get_feature_stages(fe.key.integer_id())
  email_html = format_email_body(True, fe, fe_stages, changes)

  subject = 'Review Request for feature: %s' % fe.name
  triggering_user_email = fe.updater_email

  approvers = approval_defs.get_approvers(gate_type)
  reasons = 'You received a review request for this feature'

  addr_reasons: dict[str, list[str]] = collections.defaultdict(list)
  accumulate_reasons(addr_reasons, approvers, reasons)
  all_tasks = [convert_reasons_to_task(
                   addr, reasons, email_html, subject, triggering_user_email)
               for addr, reasons in sorted(addr_reasons.items())]
  return all_tasks


class FeatureStar(ndb.Model):
  """A FeatureStar represent one user's interest in one feature."""
  email = ndb.StringProperty(required=True)
  feature_id = ndb.IntegerProperty(required=True)
  # This is so that we do not sync a bell to a star that the user has removed.
  starred = ndb.BooleanProperty(default=True)

  @classmethod
  def get_star(self, email, feature_id):
    """If that user starred that feature, return the model or None."""
    q = FeatureStar.query()
    q = q.filter(FeatureStar.email == email)
    q = q.filter(FeatureStar.feature_id == feature_id)
    return q.get()

  @classmethod
  def set_star(self, email, feature_id, starred=True):
    """Set/clear a star for the specified user and feature."""
    feature_star = self.get_star(email, feature_id)
    if not feature_star and starred:
      feature_star = FeatureStar(email=email, feature_id=feature_id)
      feature_star.put()
    elif feature_star and feature_star.starred != starred:
      feature_star.starred = starred
      feature_star.put()
    else:
      return  # No need to update anything in datastore

    feature_entry = FeatureEntry.get_by_id(feature_id)
    feature_entry.star_count += 1 if starred else -1
    if feature_entry.star_count < 0:
      logging.error('count would be < 0: %r', (email, feature_id, starred))
      return
    feature_entry.put()

  @classmethod
  def get_user_stars(self, email):
    """Return a list of feature_ids of all features that the user starred."""
    q = FeatureStar.query()
    q = q.filter(FeatureStar.email == email)
    q = q.filter(FeatureStar.starred == True)
    feature_stars = q.fetch(None)
    logging.info('found %d stars for %r', len(feature_stars), email)
    feature_ids = [fs.feature_id for fs in feature_stars]
    logging.info('returning %r', feature_ids)
    return sorted(feature_ids, reverse=True)

  @classmethod
  def get_feature_starrers(self, feature_id: int) -> list[UserPref]:
    """Return list of UserPref objects for starrers that want notifications."""
    q = FeatureStar.query()
    q = q.filter(FeatureStar.feature_id == feature_id)
    q = q.filter(FeatureStar.starred == True)
    feature_stars: list[FeatureStar] = q.fetch(None)
    logging.info('found %d stars for %r', len(feature_stars), feature_id)
    emails: list[str] = [fs.email for fs in feature_stars]
    logging.info('looking up %r', repr(emails)[:settings.MAX_LOG_LINE])
    user_prefs = UserPref.get_prefs_for_emails(emails)
    user_prefs = [up for up in user_prefs
                  if up.notify_as_starrer and not up.bounced]
    return user_prefs


class NotifyInactiveUsersHandler(basehandlers.FlaskHandler):
  JSONIFY = True
  DEFAULT_LAST_VISIT = datetime(2022, 8, 1)  # 2022-08-01
  INACTIVE_WARN_DAYS = 180
  EMAIL_TEMPLATE_PATH = 'inactive_user_email.html'

  def get_template_data(self, **kwargs):
    """Notify any users that have been inactive for 6 months."""
    self.require_cron_header()
    now = kwargs.get('now', datetime.now())

    users_to_notify = self._determine_users_to_notify(now)
    email_tasks = self._build_email_tasks(users_to_notify)
    send_emails(email_tasks)

    message_parts = [f'{len(email_tasks)} users notified of inactivity.',
        'Notified users:']
    for task in email_tasks:
      message_parts.append(task['to'])

    message = '\n'.join(message_parts)
    logging.info(message)
    return {'message': message}

  def _determine_users_to_notify(self, now=None):
    # date var can be passed in for testing purposes.
    if now is None:
      now = datetime.now()

    q = AppUser.query()
    users = q.fetch()
    inactive_users = []
    inactive_cutoff = now - timedelta(days=self.INACTIVE_WARN_DAYS)

    for user in users:
      # Site admins and editors aren't warned due to inactivity.
      # Also, users that have been previously notified are not notified again.
      if user.is_admin or user.is_site_editor or user.notified_inactive:
        continue

      # If the user does not have a last visit, it is assumed the last visit
      # is roughly the date the last_visit field was added.
      last_visit = user.last_visit or self.DEFAULT_LAST_VISIT
      # Notify the user of inactivity if they haven't already been notified.
      if (last_visit < inactive_cutoff):
        inactive_users.append(user.email)
        user.notified_inactive = True
        user.put()
    return inactive_users

  def _build_email_tasks(self, users_to_notify):
    email_tasks = []
    for email in users_to_notify:
      body_data = {'site_url': settings.SITE_URL}
      html = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
      subject = f'Notice of WebStatus user inactivity for {email}'
      email_tasks.append({
        'to': email,
        'subject': subject,
        'reply_to': None,
        'html': html
      })
    return email_tasks


class FeatureChangeHandler(basehandlers.FlaskHandler):
  """This task handles a feature creation or update by making email tasks."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self, **kwargs):
    self.require_task_header()

    feature = self.get_param('feature')
    is_update = self.get_bool_param('is_update')
    changes = self.get_param('changes', required=False) or []

    logging.info('Starting to notify subscribers for feature %s',
                 repr(feature)[:settings.MAX_LOG_LINE])

    # Email feature subscribers if the feature exists and there were
    # actually changes to it.
    # Load feature directly from NDB so as to never get a stale cached copy.
    fe = FeatureEntry.get_by_id(feature['id'])
    if fe and (is_update and len(changes) or not is_update):
      email_tasks = make_feature_changes_email(fe, is_update=is_update, changes=changes)
      send_emails(email_tasks)

    return {'message': 'Done'}


class FeatureReviewHandler(basehandlers.FlaskHandler):
  """This task handles feature review requests by making email tasks."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self, **kwargs):
    self.require_task_header()

    feature = self.get_param('feature')
    gate_type = self.get_param('gate_type')
    changes = self.get_param('changes', required=False) or []

    logging.info('Starting to notify reviewers for feature %s',
                 repr(feature)[:settings.MAX_LOG_LINE])

    fe = FeatureEntry.get_by_id(feature['id'])
    if fe:
      email_tasks = make_review_requests_email(fe, gate_type, changes)
      send_emails(email_tasks)

    return {'message': 'Done'}


BLINK_DEV_ARCHIVE_URL_PREFIX = (
    'https://groups.google.com/a/chromium.org/d/msgid/blink-dev/')
TEST_ARCHIVE_URL_PREFIX = (
    'https://groups.google.com/d/msgid/jrobbins-test/')


def generate_thread_subject(feature, approval_field):
  """Use the expected subject based on the feature type and approval type."""
  intent_phrase = approval_field.name
  if feature.feature_type == core_enums.FEATURE_TYPE_DEPRECATION_ID:
    if approval_field == approval_defs.PrototypeApproval:
      intent_phrase = 'Intent to Deprecate and Remove'
    if approval_field == approval_defs.ExperimentApproval:
      intent_phrase = 'Request for Deprecation Trial'
    if approval_field == approval_defs.ExtendExperimentApproval:
      intent_phrase = 'Intent to Extend Deprecation Trial'

  return '%s: %s' % (intent_phrase, feature.name)


def get_thread_id(stage: Stage):
  """If we have the URL of the Google Groups thread, we can get its ID."""
  if stage.intent_thread_url is None:
    return None

  thread_url = stage.intent_thread_url
  thread_url = thread_url.split('#')[0]  # Chop off any anchor
  thread_url = thread_url.split('?')[0]  # Chop off any query string params
  thread_url = urllib.parse.unquote(thread_url)  # Convert %40 to @.

  thread_id = None
  if thread_url.startswith(BLINK_DEV_ARCHIVE_URL_PREFIX):
    thread_id = thread_url[len(BLINK_DEV_ARCHIVE_URL_PREFIX):]
  if thread_url.startswith(TEST_ARCHIVE_URL_PREFIX):
    thread_id = thread_url[len(TEST_ARCHIVE_URL_PREFIX):]

  return thread_id


def send_emails(email_tasks):
  """Process a list of email tasks (send or log)."""
  logging.info('Processing %d email tasks', len(email_tasks))
  for task in email_tasks:
    if settings.SEND_EMAIL:
      cloud_tasks_helpers.enqueue_task(
          '/tasks/outbound-email', task)
    else:
      logging.info(
          'Would send the following email:\n'
          'To: %s\n'
          'From: %s\n'
          'References: %s\n'
          'Reply-To: %s\n'
          'Subject: %s\n'
          'Body:\n%s',
          task.get('to', None),
          task.get('from_user', None),
          task.get('references', None),
          task.get('reply_to', None),
          task.get('subject', None),
          task.get('html', "")[:settings.MAX_LOG_LINE])


def post_comment_to_mailing_list(
    feature: FeatureEntry,
    gate_id: int,
    approval_field_id: int,
    author_addr: str,
    comment_content: str):
  """Post a message to the intent thread."""
  to_addr = settings.REVIEW_COMMENT_MAILING_LIST
  from_user = author_addr.split('@')[0]
  approval_field = approval_defs.APPROVAL_FIELDS_BY_ID[approval_field_id]

  # Use the Gate ID to find the Stage ID that has the thread URL and subject.
  gate: Gate | None = Gate.get_by_id(gate_id)
  stage: Stage | None = None if gate is None else Stage.get_by_id(gate.stage_id)
  # There should always be a matching stage for every gate.
  if stage is None:
    raise ValueError("No matching Stage entity found for given Gate ID.")

  # Set the subject line from the stage, or generate it if null.
  subject = None if stage is None else stage.intent_subject_line
  if subject is None:
    subject = generate_thread_subject(feature, approval_field)

  if not subject.startswith('Re: '):
    subject = 'Re: ' + subject
  thread_id = get_thread_id(stage)
  references = None
  if thread_id:
    references = '<%s>' % thread_id
  html = render_template(
      'review-comment-email.html', comment_content=comment_content)

  email_task = {
      'to': to_addr,
      'from_user': from_user,
      'references': references,
      'subject': subject,
      'html': html,
      }
  send_emails([email_task])
