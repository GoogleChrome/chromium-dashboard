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
from typing import Optional
import urllib

from framework import permissions
from google.cloud import ndb  # type: ignore

from django.utils.html import conditional_escape as escape

from flask import render_template

from framework import basehandlers
from framework import cloud_tasks_helpers
from framework import users
import settings
from internals import approval_defs
from internals import core_enums
from internals.core_models import Feature
from internals.user_models import (
    AppUser, BlinkComponent, FeatureOwner, UserPref)


def format_email_body(is_update, feature, changes):
  """Return an HTML string for a notification email body."""
  if feature.shipped_milestone:
    milestone_str = feature.shipped_milestone
  elif feature.shipped_milestone is None and feature.shipped_android_milestone:
    milestone_str = '%s (android)' % feature.shipped_android_milestone
  else:
    milestone_str = 'not yet assigned'

  moz_link_urls = [
      link for link in feature.doc_links
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
      'feature': feature,
      'creator_email': feature.created_by.email(),
      'updater_email': feature.updated_by.email(),
      'id': feature.key.integer_id(),
      'milestone': milestone_str,
      'status': core_enums.IMPLEMENTATION_STATUS[feature.impl_status_chrome],
      'formatted_changes': formatted_changes,
      'moz_link_urls': moz_link_urls,
  }
  template_path = ('update-feature-email.html' if is_update
                   else 'new-feature-email.html')
  # final_full_path = os.path.join(settings.TEMPLATES[0]['DIRS'][0], template_path)
  body = render_template(template_path, **body_data)
  return body


def accumulate_reasons(
      addr_reasons: dict[str, list], user_list: list[str], reason: str) -> None:
  """Add a reason string for each user."""
  for user in user_list:
    addr_reasons[user].append(reason)


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
    feature: Feature, changes: list) -> dict[str, list[str]]:
  """Return {"reason": [addrs]} for users who set up rules."""
  # Note: for now this is hard-coded, but it will eventually be
  # configurable through some kind of user preference.
  changed_field_names = {c['prop_name'] for c in changes}
  results: dict[str, list[str]] = {}

  # Check if feature has some other milestone set, but not webview.
  if (feature.shipped_android_milestone and
      not feature.shipped_webview_milestone):
    milestone_fields = ['shipped_android_milestone']
    if not changed_field_names.isdisjoint(milestone_fields):
      results[WEBVIEW_RULE_REASON] = WEBVIEW_RULE_ADDRS

  return results


def make_email_tasks(feature: Feature, is_update: bool=False,
    changes: Optional[list]=None):
  """Return a list of task dicts to notify users of feature changes."""
  if changes is None:
    changes = []

  watchers: list[FeatureOwner] = FeatureOwner.query(
      FeatureOwner.watching_all_features == True).fetch(None)
  watcher_emails: list[str] = [watcher.email for watcher in watchers]

  email_html = format_email_body(is_update, feature, changes)
  if is_update:
    subject = 'updated feature: %s' % feature.name
    triggering_user_email = feature.updated_by.email()
  else:
    subject = 'new feature: %s' % feature.name
    triggering_user_email = feature.created_by.email()

  # [{email_addr: [reason,...]}]
  addr_reasons: dict[str, list] = collections.defaultdict(list)

  accumulate_reasons(
    addr_reasons, feature.owner,
    'You are listed as an owner of this feature'
  )
  accumulate_reasons(
    addr_reasons, feature.editors,
    'You are listed as an editor of this feature'
  )
  accumulate_reasons(
    addr_reasons, feature.cc_recipients,
    'You are CC\'d on this feature'
  )
  accumulate_reasons(
      addr_reasons, watcher_emails,
      'You are watching all feature changes')

  # There will always be at least one component.
  for component_name in feature.blink_components:
    component = BlinkComponent.get_by_name(component_name)
    owner_emails: list[str] = [owner.email for owner in component.owners]
    subscriber_emails: list[str] = [sub.email for sub in component.subscribers]
    if not component:
      logging.warning('Blink component "%s" not found.'
                      'Not sending email to subscribers' % component_name)
      continue

    accumulate_reasons(
        addr_reasons, owner_emails,
        'You are an owner of this feature\'s component')
    accumulate_reasons(
        addr_reasons, subscriber_emails,
        'You subscribe to this feature\'s component')
  starrers = FeatureStar.get_feature_starrers(feature.key.integer_id())
  starrer_emails: list[str] = [user.email for user in starrers]
  accumulate_reasons(addr_reasons, starrer_emails, 'You starred this feature')

  rule_results = apply_subscription_rules(feature, changes)
  for reason, sub_addrs in rule_results.items():
    accumulate_reasons(addr_reasons, sub_addrs, reason)

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

    # Load feature directly from NDB so as to never get a stale cached copy.
    feature = Feature.get_by_id(feature_id)
    feature.star_count += 1 if starred else -1
    if feature.star_count < 0:
      logging.error('count would be < 0: %r', (email, feature_id, starred))
      return
    feature.put(notify=False)

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
    feature = Feature.get_by_id(feature['id'])
    if feature and (is_update and len(changes) or not is_update):
      email_tasks = make_email_tasks(
          feature, is_update=is_update, changes=changes)
      send_emails(email_tasks)

    return {'message': 'Done'}


BLINK_DEV_ARCHIVE_URL_PREFIX = (
    'https://groups.google.com/a/chromium.org/d/msgid/blink-dev/')
TEST_ARCHIVE_URL_PREFIX = (
    'https://groups.google.com/d/msgid/jrobbins-test/')


def get_existing_thread_subject(feature, approval_field):
  """If we have the subject line of the Google Groups thread, use it."""
  # This improves message threading in gmail.

  if approval_field == approval_defs.PrototypeApproval:
    return feature.intent_to_implement_subject_line
  # TODO(jrobbins): Ready-for-trial threads
  elif approval_field == approval_defs.ExperimentApproval:
    return feature.intent_to_experiment_subject_line
  elif approval_field == approval_defs.ExtendExperimentApproval:
    return feature.intent_to_extend_experiment_subject_line
  elif approval_field == approval_defs.ShipApproval:
    return feature.intent_to_ship_subject_line
  else:
    raise ValueError('Unexpected approval type')


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


def get_thread_id(feature, approval_field):
  """If we have the URL of the Google Groups thread, we can get its ID."""
  if approval_field == approval_defs.PrototypeApproval:
    thread_url = feature.intent_to_implement_url
  # TODO(jrobbins): Ready-for-trial threads
  if approval_field == approval_defs.ExperimentApproval:
    thread_url = feature.intent_to_experiment_url
  if approval_field == approval_defs.ExtendExperimentApproval:
    thread_url = feature.intent_to_extend_experiment_url
  if approval_field == approval_defs.ShipApproval:
    thread_url = feature.intent_to_ship_url

  if not thread_url:
    return None

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
    feature, approval_field_id, author_addr, comment_content):
  """Post a message to the intent thread."""
  to_addr = settings.REVIEW_COMMENT_MAILING_LIST
  from_user = author_addr.split('@')[0]
  approval_field = approval_defs.APPROVAL_FIELDS_BY_ID[approval_field_id]
  subject = (get_existing_thread_subject(feature, approval_field) or
             generate_thread_subject(feature, approval_field))
  if not subject.startswith('Re: '):
    subject = 'Re: ' + subject
  thread_id = get_thread_id(feature, approval_field)
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
