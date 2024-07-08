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
import difflib
import re
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
from internals.data_types import StageDict
from internals import stage_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.data_types import StageDict
from internals.review_models import Gate
from internals.user_models import (
    AppUser, BlinkComponent, FeatureOwner, UserPref)


OT_SUPPORT_EMAIL = 'origin-trials-support@google.com'
BLINK_DEV_EMAIL = 'blink-dev@chromium.org'


def _determine_milestone_string(ship_stages: list[Stage]) -> str:
  """Determine the shipping milestone string to display in the template."""
  # Get the earliest desktop and android milestones.
  first_desktop = min(
      (stage.milestones.desktop_first for stage in ship_stages
        if stage.milestones and stage.milestones.desktop_first),
    default=None)
  first_android = min(
      (stage.milestones.android_first for stage in ship_stages
        if stage.milestones and stage.milestones.android_first),
    default=None)

  # Use the desktop milestone by default if it's available.
  milestone_str = str(first_desktop)
  # Use the android milestone with the android suffix if there are no
  # desktop milestones.
  if not first_desktop and first_android:
    milestone_str = f'{first_android} (android)'
  return milestone_str

def highlight_diff(old_text, new_text, highlight_type):
  differ = difflib.ndiff(
      re.split(r'(\W)', old_text), re.split(r'(\W)', new_text))
  highlighted_text = []
  for item in differ:
    text = escape(item[2:])
    if not text: continue
    if item.startswith('-') and highlight_type == 'deletion':
      highlighted_text.append(
          f'<span style="background:#FDD">{text}</span>')
    elif item.startswith('+') and highlight_type == 'addition':
      highlighted_text.append(
          f'<span style="background:#DFD">{text}</span>')
    elif item.startswith(' '):
      highlighted_text.append(text)
  return ''.join(highlighted_text)

def format_email_body(
    template_path, fe: FeatureEntry, changes: list[dict[str, Any]],
    updater_email: Optional[str] = None,
    additional_template_data: dict[str, Any] | None = None) -> str:
  """Return an HTML string for a notification email body."""

  stage_info = stage_helpers.get_stage_info_for_templates(fe)
  milestone_str = _determine_milestone_string(stage_info['ship_stages'])

  formatted_changes = ''
  for prop in changes:
    prop_name = escape(prop['prop_name'])  # Ensure to escape
    new_val = prop['new_val']
    old_val = prop['old_val']

    # Escaping values before passing to highlight_diff
    highlighted_old_val = highlight_diff(old_val, new_val, 'deletion')
    highlighted_new_val = highlight_diff(old_val, new_val, 'addition')

    # Using f-strings for clear formatting
    formatted_changes += (
        f'<li><b>{prop_name}:</b><br/>'
        f'<b>old:</b> {highlighted_old_val}<br/>'
        f'<b>new:</b> {highlighted_new_val}<br/></li><br/>')

  if not formatted_changes:
    formatted_changes = '<li>None</li>'

  body_data = {
      'feature': fe,
      'category': core_enums.FEATURE_CATEGORIES[fe.category],
      'feature_type': core_enums.FEATURE_TYPES[fe.feature_type],
      'stage_info': stage_info,
      'should_render_mstone_table': stage_info['should_render_mstone_table'],
      'creator_email': fe.creator_email,
      'updater_email': updater_email or fe.updater_email,
      'id': fe.key.integer_id(),
      'milestone': milestone_str,
      'status': core_enums.IMPLEMENTATION_STATUS[fe.impl_status_chrome],
      'formatted_changes': formatted_changes,
      'APP_TITLE': settings.APP_TITLE,
      'SITE_URL': settings.SITE_URL,
  }
  body_data.update(additional_template_data or {})
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
  if permissions.can_create_feature(recipient_user) and triggering_user_email:
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
IWA_RULE_REASON = (
    'You are subscribed to all IWA features')
IWA_RULE_ADDRS = ['iwa-dev@chromium.org']



def apply_subscription_rules(
    fe: FeatureEntry, changes: list) -> dict[str, list[str]]:
  """Return {"reason": [addrs]} for users who set up rules."""
  # Note: for now this is hard-coded, but it will eventually be
  # configurable through some kind of user preference.
  changed_field_names = {c['prop_name'] for c in changes}
  results: dict[str, list[str]] = {}

  # Rule 1: Check for IWA features
  if fe.category == core_enums.IWA:
    results[IWA_RULE_REASON] = IWA_RULE_ADDRS

  # Find an existing shipping stage with milestone info.
  fe_stages = stage_helpers.get_feature_stages(fe.key.integer_id())
  stage_type = core_enums.STAGE_TYPES_SHIPPING[fe.feature_type] or 0
  ship_stages: list[Stage] = fe_stages.get(stage_type, [])
  ship_milestones: MilestoneSet | None = (
      ship_stages[0].milestones if len(ship_stages) > 0 else None)

  # Rule 2: Check if feature has some other milestone set, but not webview.
  if (ship_milestones is not None and
      ship_milestones.android_first and
      not ship_milestones.webview_first):
    milestone_fields = ['shipped_android_milestone']
    if not changed_field_names.isdisjoint(milestone_fields):
      results[WEBVIEW_RULE_REASON] = WEBVIEW_RULE_ADDRS

  return results


def add_core_receivers(fe: FeatureEntry, addr_reasons: dict[str, list[str]]):
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


def make_feature_changes_email(
    fe: FeatureEntry, is_update: bool=False, changes: Optional[list]=None,
    triggering_user_email: Optional[str]=None):
  """Return a list of task dicts to notify users of feature changes."""
  if changes is None:
    changes = []
  watchers: list[FeatureOwner] = FeatureOwner.query(
      FeatureOwner.watching_all_features == True).fetch(None)
  watcher_emails: list[str] = [watcher.email for watcher in watchers]

  if is_update:
    subject = 'updated feature: %s' % fe.name
    triggering_user_email = triggering_user_email or fe.updater_email
    template_path = 'update-feature-email.html'
  else:
    subject = 'new feature: %s' % fe.name
    triggering_user_email = fe.creator_email
    template_path = 'new-feature-email.html'

  email_html = format_email_body(
      template_path, fe, changes, updater_email=triggering_user_email)

  addr_reasons: dict[str, list[str]] = collections.defaultdict(list)

  add_core_receivers(fe, addr_reasons)
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

  rule_results = apply_subscription_rules(fe, changes)
  for reason, sub_addrs in rule_results.items():
    accumulate_reasons(addr_reasons, sub_addrs, reason)

  all_tasks = [convert_reasons_to_task(
                   addr, reasons, email_html, subject, triggering_user_email)
               for addr, reasons in sorted(addr_reasons.items())]
  return all_tasks


def add_reviewers(
    fe: FeatureEntry, gate_type: int, addr_reasons: dict[str, list[str]]):
  """Add addresses of people who will do the review."""
  gate = approval_defs.get_gate_by_type(fe.key.integer_id(), gate_type)
  if gate and gate.assignee_emails:
    recipients = gate.assignee_emails
    reasons = 'This review is assigned to you'
  else:
    recipients = approval_defs.get_approvers(gate_type)
    reasons = 'You are a reviewer for this type of gate'

  accumulate_reasons(addr_reasons, recipients, reasons)


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
    users: list[AppUser] = q.fetch()
    inactive_users = []
    inactive_cutoff = now - timedelta(days=self.INACTIVE_WARN_DAYS)

    for user in users:
      # Site admins and editors aren't warned due to inactivity.
      # Also, users that have been previously notified are not notified again.
      if user.is_admin or user.is_site_editor or user.notified_inactive:
        continue

      # If the user does not have a last visit, it is assumed the last visit
      # is either the account's creation date or the date the last_visit
      # field was created on the model - whatever is latest.
      last_visit = user.last_visit or self.DEFAULT_LAST_VISIT
      if user.created > last_visit:
        last_visit = user.created
      # Notify the user of inactivity if they haven't already been notified.
      if (last_visit < inactive_cutoff):
        inactive_users.append(user.email)
        user.notified_inactive = True
        user.put()
    return inactive_users

  def _build_email_tasks(self, users_to_notify):
    email_tasks = []
    for email in users_to_notify:
      body_data = {'SITE_URL': settings.SITE_URL}
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
    triggering_user_email = self.get_param(
        'triggering_user_email', required=False)

    logging.info('Starting to notify subscribers for feature %s',
                 repr(feature)[:settings.MAX_LOG_LINE])

    # Email feature subscribers if the feature exists and there were
    # actually changes to it.
    # Load feature directly from NDB so as to never get a stale cached copy.
    fe = FeatureEntry.get_by_id(feature['id'])
    if fe and (is_update and len(changes) or not is_update):
      email_tasks = make_feature_changes_email(
          fe, is_update=is_update, changes=changes,
          triggering_user_email=triggering_user_email)
      send_emails(email_tasks)

    return {'message': 'Done'}


class FeatureReviewHandler(basehandlers.FlaskHandler):
  """This task handles feature review requests by making email tasks."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'review-request-email.html'

  def process_post_data(self, **kwargs):
    self.require_task_header()

    feature = self.get_param('feature')
    gate_type = self.get_param('gate_type')
    gate_url = self.get_param('gate_url', required=False)
    new_val = self.get_param('new_val', required=False)
    updater_email = self.get_param('updater_email', required=False)
    team_name = None
    appr_def = approval_defs.APPROVAL_FIELDS_BY_ID.get(gate_type)
    if appr_def:
      team_name = appr_def.team_name

    # TODO(jrobbins): Remove this backward compatibility code
    # after next deployment.
    changes = self.get_param('changes', required=False) or []
    if changes and not gate_url:
      prop_name = changes[0]['prop_name']
      gate_url = prop_name.split()[-1]
    if changes and not new_val:
      new_val = changes[0]['new_val']

    logging.info('Starting to notify reviewers for feature %s',
                 repr(feature)[:settings.MAX_LOG_LINE])
    logging.info('gate type is %r', gate_type)
    logging.info('team_name is %r', team_name)

    fe = FeatureEntry.get_by_id(feature['id'])
    if fe:
      additional_template_data = {
          'gate_url': gate_url,
          'new_val': new_val,
          'updater_email': updater_email,
          'team_name': team_name,
      }
      email_tasks = self.make_review_requests_email(
          fe, gate_type, additional_template_data)
      send_emails(email_tasks)

    return {'message': 'Done'}

  def make_review_requests_email(
      self, fe: FeatureEntry, gate_type: int,
      additional_template_data: dict[str, str]):
    """Return a list of task dicts to notify approvers of review requests."""
    email_html = format_email_body(
        self.EMAIL_TEMPLATE_PATH, fe, [],
        additional_template_data=additional_template_data)

    subject = 'Review Request for feature: %s' % fe.name

    addr_reasons: dict[str, list[str]] = collections.defaultdict(list)
    add_reviewers(fe, gate_type, addr_reasons)

    all_tasks = [
        convert_reasons_to_task(
            addr, reasons, email_html, subject, None)
        for addr, reasons in sorted(addr_reasons.items())]
    return all_tasks


class ReviewAssignmentHandler(basehandlers.FlaskHandler):
  """This task handles feature review assignments by making email tasks."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'review-assigned-email.html'

  def process_post_data(self, **kwargs):
    self.require_task_header()

    feature = self.get_param('feature')
    gate_type = self.get_param('gate_type')
    gate_url = self.get_param('gate_url')
    triggering_user_email = self.get_param('triggering_user_email')
    old_assignees = self.get_param('old_assignees')
    new_assignees = self.get_param('new_assignees')

    team_name = None
    appr_def = approval_defs.APPROVAL_FIELDS_BY_ID.get(gate_type)
    if appr_def:
      team_name = appr_def.team_name

    logging.info('Starting to notify assignees for feature %s',
                 repr(feature)[:settings.MAX_LOG_LINE])

    fe = FeatureEntry.get_by_id(feature['id'])
    if fe:
      additional_template_data = {
          'gate_url': gate_url,
          'updater_email': triggering_user_email,
          'team_name': team_name,
      }
      email_tasks = self.make_review_assignment_email(
          fe, triggering_user_email, old_assignees, new_assignees,
          additional_template_data)
      send_emails(email_tasks)

    return {'message': 'Done'}

  def make_review_assignment_email(
      self, fe: FeatureEntry, triggering_user_email: str,
      old_assignees: list[str], new_assignees: list[str],
      additional_template_data: dict[str, str]):
    """Return a list of task dicts to notify assigned reviewers."""
    changed_prop = {
        'prop_name': 'Assigned reviewer',
        'old_val': ', '.join(old_assignees or ['None']),
        'new_val': ', '.join(new_assignees or ['None']),
    }
    email_html = format_email_body(
        self.EMAIL_TEMPLATE_PATH, fe, [changed_prop],
        additional_template_data=additional_template_data)

    subject = 'Review assigned for feature: %s' % fe.name

    addr_reasons: dict[str, list[str]] = collections.defaultdict(list)
    accumulate_reasons(
        addr_reasons, old_assignees,
        'The review was previously assigned to you')
    accumulate_reasons(
        addr_reasons, new_assignees, 'The review is now assigned to you')

    all_tasks = [
        convert_reasons_to_task(
            addr, reasons, email_html, subject, triggering_user_email)
        for addr, reasons in sorted(addr_reasons.items())]
    return all_tasks


class FeatureCommentHandler(basehandlers.FlaskHandler):
  """This task handles feature comment notifications by making email tasks."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'review-comment-notification-email.html'

  def process_post_data(self, **kwargs):
    self.require_task_header()

    feature = self.get_param('feature')
    gate_type = self.get_param('gate_type')
    gate_url = self.get_param('gate_url')
    triggering_user_email = self.get_param('triggering_user_email')
    content = self.get_param('content')

    logging.info('Starting to notify of comments for feature %s',
                 repr(feature)[:settings.MAX_LOG_LINE])

    fe = FeatureEntry.get_by_id(feature['id'])
    if fe:
      additional_template_data = {
          'gate_url': gate_url,
          'triggering_user_email': triggering_user_email,
          'content': content,
      }
      email_tasks = self.make_new_comments_email(
          fe, gate_type, triggering_user_email, additional_template_data)
      send_emails(email_tasks)

    return {'message': 'Done'}

  def make_new_comments_email(
      self, fe: FeatureEntry, gate_type: int, triggering_user_email: str,
      additional_template_data: dict[str, str]):
    """Return a list of task dicts to notify of new comments."""
    email_html = format_email_body(
        self.EMAIL_TEMPLATE_PATH, fe, [],
        additional_template_data=additional_template_data)

    subject = 'New comments for feature: %s' % fe.name

    addr_reasons: dict[str, list[str]] = collections.defaultdict(list)
    add_core_receivers(fe, addr_reasons)
    add_reviewers(fe, gate_type, addr_reasons)

    all_tasks = [convert_reasons_to_task(
        addr, reasons, email_html, subject, triggering_user_email)
                 for addr, reasons in sorted(addr_reasons.items())]
    return all_tasks


class OTActivatedHandler(basehandlers.FlaskHandler):
  """Notify about an origin trial being activated."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-activated-email.html'

  def process_post_data(self, **kwargs):
    stage = self.get_param('stage', required=True)
    contacts = stage['ot_emails'] or []
    contacts.append('ot_owner_email')
    send_emails([self.build_email(stage, contacts)])
    return {'message': 'OK'}

  def build_email(self, stage: StageDict, contacts: list[str]) -> dict:
    body_data = {
      'stage': stage,
      'ot_url': f'{settings.OT_URL}#/view_trial/{stage["origin_trial_id"]}',
      'chromestatus_url': ('https://chromestatus.com/feature/'
                           f'{stage["feature_id"]}')
    }
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': contacts,
      'subject': f'{stage["ot_display_name"]} origin trial is now available',
      'reply_to': None,
      'html': body,
    }

class OTCreationProcessedHandler(basehandlers.FlaskHandler):
  """Notify about an origin trial creation request being processed,
  but activation is at a later date.
  """

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-creation-processed-email.html'

  def process_post_data(self, **kwargs):
    stage = self.get_param('stage', required=True)
    contacts = stage['ot_emails'] or []
    contacts.append('ot_owner_email')
    send_emails([self.build_email(stage, contacts)])
    return {'message': 'OK'}

  def build_email(self, stage: dict[str, Any], contacts: list[str]) -> dict:
    body_data = {
      'stage': stage,
      'ot_url': settings.OT_URL,
      'chromestatus_url': ('https://chromestatus.com/feature/'
                           f'{stage["feature_id"]}')
    }
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': contacts,
      'subject': (f'{stage["ot_display_name"]} origin trial has been created '
                  f'and will begin {stage["ot_activation_date"]}'),
      'reply_to': None,
      'html': body,
    }


class OTCreationRequestFailedHandler(basehandlers.FlaskHandler):
  """Notify about an origin trial creation request failing automated request."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-creation-request-failed-email.html'

  def process_post_data(self, **kwargs):
    stage = self.get_param('stage', required=True)
    send_emails([self.build_email(stage)])
    return {'message': 'OK'}

  def build_email(self, stage: StageDict) -> dict:
    body_data = {
      'stage': stage,
      'chromestatus_url': ('https://chromestatus.com/feature/'
                           f'{stage["feature_id"]}')
    }
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': OT_SUPPORT_EMAIL,
      'subject': ('Automated trial creation request failed for '
                  f'{stage["ot_display_name"]}'),
      'reply_to': None,
      'html': body,
    }


class OTActivationFailedHandler(basehandlers.FlaskHandler):
  """Notify about an origin trial activation automated request failing."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-activation-failed-email.html'

  def process_post_data(self, **kwargs):
    stage = self.get_param('stage', required=True)
    send_emails([self.build_email(stage)])
    return {'message': 'OK'}

  def build_email(self, stage: StageDict) -> dict:
    body_data = {
      'stage': stage,
      'chromestatus_url': ('https://chromestatus.com/feature/'
                           f'{stage["feature_id"]}')
    }
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': OT_SUPPORT_EMAIL,
      'subject': ('Automated trial activation request failed for '
                  f'{stage["ot_display_name"]}'),
      'reply_to': None,
      'html': body,
    }


class OTCreationRequestHandler(basehandlers.FlaskHandler):
  """Notify about an origin trial creation request."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self, **kwargs):
    stage = self.get_param('stage')
    logging.info('Starting to notify about origin trial creation request.')
    send_emails([self.make_creation_request_email(stage)])

    return {'message': 'OK'}

  def _yes_or_no(self, value: bool):
    return 'Yes' if value else 'No'

  def make_creation_request_email(self, stage):
    chromestatus_url = ('https://chromestatus.com/feature/'
                         f'{stage["feature_id"]}')
    email_body = f"""
<p>
  Requested by: {stage["ot_owner_email"]}
  <br>
  Additional contacts for your team?: {",".join(stage["ot_emails"])}
  <br>
  Feature name: {stage["ot_display_name"]}
  <br>
  Feature description: {stage["ot_description"]}
  <br>
  Start Chrome milestone: {stage["desktop_first"]}
  <br>
  End Chrome milestone: {stage["desktop_last"]}
  <br>
  Chromium trial name: {stage["ot_chromium_trial_name"]}
  <br>
  Is this a deprecation trial?: {self._yes_or_no(stage["ot_is_deprecation_trial"])}
  <br>
  Third party origin support: {self._yes_or_no(stage["ot_has_third_party_support"])}
  <br>
  WebFeature UseCounter value: {stage["ot_webfeature_use_counter"]}
  <br>
  Documentation link: {stage["ot_documentation_url"]}
  <br>
  Chromestatus link: {chromestatus_url}
  <br>
  Feature feedback link: {stage["ot_feedback_submission_url"]}
  <br>
  Intent to Experiment link: {stage["intent_thread_url"]}
  <br>
  Is this a critical trial?: {self._yes_or_no(stage["ot_is_critical_trial"])}
  <br>
  Anything else?: {stage["ot_request_note"]}
  <br>
  <br>
  Instructions for handling this request can be found at: https://g3doc.corp.google.com/chrome/origin_trials/g3doc/trial_admin.md?cl=head#setup-a-new-trial
</p>
"""

    return {
      'to': OT_SUPPORT_EMAIL,
      'subject': f'New Trial Creation Request for {stage["ot_display_name"]}',
      'reply_to': None,
      'html': email_body,
    }


class OTExtensionApprovedHandler(basehandlers.FlaskHandler):
  """Notify about an origin trial extension that is approved and needs
  finalized.
  """
  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-extension-approved-email.html'

  def process_post_data(self, **kwargs):
    feature = self.get_param('feature')
    if feature is None:
      self.abort(400, 'No feature provided.')
    gate_id = self.get_param('gate_id')
    if gate_id is None:
      self.abort(400, 'Extension gate ID not provided.')
    requester_email = self.get_param('requester_email')
    if not requester_email:
      self.abort(400, 'Extension requester\'s email address not provided.')
    logging.info('Starting to notify about successful origin trial extension.')
    send_emails([self.build_email(feature, requester_email, gate_id)])

    return {'message': 'OK'}

  def build_email(
      self, feature: FeatureEntry, requester_email: str, gate_id: int):
    body_data = {
      'feature': feature,
      'id': feature['id'],
      'gate_id': gate_id,
      'SITE_URL': settings.SITE_URL,
    }
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)

    return {
      'to': requester_email,
      'cc': [OT_SUPPORT_EMAIL],
      'subject': ('Origin trial approved and ready to be initiated: '
                  f'{feature["name"]}'),
      'reply_to': None,
      'html': body,
    }


class IntentToBlinkDevHandler(basehandlers.FlaskHandler):
  """Submit an intent email directly to blink-dev."""
  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'templates/blink/intent_to_implement.html'

  def process_post_data(self, **kwargs):
    self.require_task_header()
    send_emails([self.build_email()])
    return {'message': 'OK'}

  def build_email(self):
    json_data = self.get_json_param_dict()
    template_data = {
      'feature': json_data['feature'],
      'stage_info': json_data['stage_info'],
      'should_render_mston_table': json_data['should_render_mston_table'],
      'should_render_intents': json_data['should_render_intents'],
      'intent_stage': json_data['intent_stage'],
      'default_url': json_data['default_url'],
    }
    body = render_template(self.EMAIL_TEMPLATE_PATH, **template_data)

    return {
      'to': BLINK_DEV_EMAIL,
      'cc': json_data['intent_cc_emails'],
      'subject': json_data['subject'],
      'reply_to': None,
      'html': body,
    }


GLOBAL_OT_PROCESS_REMINDER_CC_LIST = [
  OT_SUPPORT_EMAIL,
  'origin-trials-timeline-updates@google.com'
  ]

class OTEndingNextReleaseReminderHandler(basehandlers.FlaskHandler):
  """Send origin trial ending next release reminder email to OT contacts."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-ending-next-release-email.html'

  def process_post_data(self, **kwargs):
    contacts = self.get_param('contacts')
    body_data = {
      'name': self.get_param('name'),
      'release_milestone': self.get_param('release_milestone'),
      'after_end_release': self.get_param('after_end_release'),
      'after_end_date': self.get_param('after_end_date'),
    }
    send_emails([self.build_email(body_data, contacts)])
    return {'message': 'OK'}

  def build_email(self, body_data: dict[str, Any], contacts: list[str]):
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': contacts,
      'cc': GLOBAL_OT_PROCESS_REMINDER_CC_LIST,
      'subject': f'{body_data["name"]} origin trial ship decision approaching',
      'reply_to': None,
      'html': body,
    }


class OTEndingThisReleaseReminderHandler(basehandlers.FlaskHandler):
  """Send origin trial ending this release reminder email to OT contacts."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-ending-this-release-email.html'

  def process_post_data(self, **kwargs):
    name = self.get_param('name')
    release_milestone = self.get_param('release_milestone')
    next_release = self.get_param('next_release')
    contacts = self.get_param('contacts')
    body_data = {
      'name': name,
      'release_milestone': release_milestone,
      'next_release': next_release,
    }
    send_emails([self.build_email(body_data, contacts)])
    return {'message': 'OK'}

  def build_email(self, body_data: dict[str, Any], contacts: list[str]):
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': contacts,
      'cc': GLOBAL_OT_PROCESS_REMINDER_CC_LIST,
      'subject': f'{body_data["name"]} origin trial needs blink-dev update',
      'reply_to': None,
      'html': body,
    }


class OTBetaAvailabilityReminderHandler(basehandlers.FlaskHandler):
  """Send origin trial beta availability reminder email to OT contacts."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-beta-availability-email.html'

  def process_post_data(self, **kwargs):
    contacts = self.get_param('contacts')
    body_data = {
      'name': self.get_param('name'),
      'release_milestone': self.get_param('release_milestone'),
    }
    send_emails([self.build_email(body_data, contacts)])
    return {'message': 'OK'}

  def build_email(self, body_data: dict[str, Any], contacts: list[str]):
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': contacts,
      'cc': GLOBAL_OT_PROCESS_REMINDER_CC_LIST,
      'subject': f'{body_data["name"]} origin trial is entering beta',
      'reply_to': None,
      'html': body,
    }


class OTFirstBranchReminderHandler(basehandlers.FlaskHandler):
  """Send origin trial first branch reminder email to OT contacts."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-first-branch-email.html'

  def process_post_data(self, **kwargs):
    contacts = self.get_param('contacts')
    body_data = {
      'name': self.get_param('name'),
      'release_milestone': self.get_param('release_milestone'),
      'branch_date': self.get_param('branch_date')
    }
    send_emails([self.build_email(body_data, contacts)])
    return {'message': 'OK'}

  def build_email(self, body_data: dict[str, Any], contacts: list[str]):
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': contacts,
      'cc': GLOBAL_OT_PROCESS_REMINDER_CC_LIST,
      'subject': f'{body_data["name"]} origin trial is branching',
      'reply_to': None,
      'html': body,
    }


class OTLastBranchReminderHandler(basehandlers.FlaskHandler):
  """Send origin trial last branch reminder email to OT contacts."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-last-branch-email.html'

  def process_post_data(self, **kwargs):
    contacts = self.get_param('contacts')
    body_data = {
      'name': self.get_param('name'),
      'release_milestone': self.get_param('release_milestone'),
      'branch_date': self.get_param('branch_date')
    }
    send_emails([self.build_email(body_data, contacts)])
    return {'message': 'OK'}

  def build_email(self, body_data: dict[str, Any], contacts: list[str]):
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': contacts,
      'cc': GLOBAL_OT_PROCESS_REMINDER_CC_LIST,
      'subject': (f'{body_data["name"]} '
                  'origin trial has branched for its last release'),
      'reply_to': None,
      'html': body,
    }


class OTAutomatedProcessEmailHandler(basehandlers.FlaskHandler):
  """Send a final notification to OT support with automated reminder info."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-automated-process-email.html'

  def process_post_data(self, **kwargs):
    now_date = datetime.now().strftime('%d %B, %Y')
    body_data = {
      'email_date': now_date,
      'send_count': self.get_param('send_count'),
      'next_branch_milestone': self.get_param('next_branch_milestone'),
      'next_branch_date': self.get_param('next_branch_date'),
      'stable_milestone': self.get_param('stable_milestone'),
      'stable_date': self.get_param('stable_date'),
    }
    send_emails([self.build_email(body_data)])
    return {'message': 'OK'}

  def build_email(self, body_data: dict[str, Any]):
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)
    return {
      'to': OT_SUPPORT_EMAIL,
      'subject': 'Origin trials automated process reminder just ran',
      'reply_to': None,
      'html': body,
    }


class OTExtendedHandler(basehandlers.FlaskHandler):
  """Notify about an origin trial extension being completed."""

  IS_INTERNAL_HANDLER = True
  EMAIL_TEMPLATE_PATH = 'origintrials/ot-extended-email.html'

  def process_post_data(self, **kwargs):
    extension_stage = self.get_param('stage')
    ot_stage = self.get_param('ot_stage')
    logging.info('Starting to notify about successful origin trial extension.')
    send_emails([self.build_email(extension_stage, ot_stage)])

    return {'message': 'OK'}

  def build_email(self, extension_stage, ot_stage):
    body_data = {
      'extension_stage': extension_stage,
      'ot_stage': ot_stage
    }
    body = render_template(self.EMAIL_TEMPLATE_PATH, **body_data)

    return {
      'to': OT_SUPPORT_EMAIL,
      'subject': ('Origin trial extension processed: '
                  f'{ot_stage["ot_display_name"]}'),
      'reply_to': None,
      'html': body,
    }


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
    logging.info(
        'Working on the following email:\n'
        'To: %s\n'
        'Cc: %s\n'
        'From: %s\n'
        'References: %s\n'
        'Reply-To: %s\n'
        'Subject: %s\n'
        'Body:\n%s',
        task.get('to', None),
        task.get('cc', None),
        task.get('from_user', None),
        task.get('references', None),
        task.get('reply_to', None),
        task.get('subject', None),
        task.get('html', "")[:settings.MAX_LOG_LINE])
    if settings.SEND_EMAIL:
      try:
        cloud_tasks_helpers.enqueue_task(
            '/tasks/outbound-email', task)
      except e:
        logging.exception('could not enqueue.')
    else:
      logging.info('Not enqueued because of settings.SEND_EMAIL')


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
