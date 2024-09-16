# Copyright 2022 Google Inc.
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

from collections import defaultdict
from datetime import datetime, timedelta
import json
import logging
from typing import Any, Callable
import requests

from google.cloud import ndb  # type: ignore
from flask import render_template

from framework import basehandlers
from internals import approval_defs
from internals.core_models import FeatureEntry, MilestoneSet
from internals.review_models import Gate
from internals import notifier
from internals import ot_process_reminders
from internals import stage_helpers
from internals import slo
from internals.core_enums import (
    STAGE_TYPES_BY_FIELD_MAPPING)
import settings


CHROME_RELEASE_SCHEDULE_URL = (
    'https://chromiumdash.appspot.com/fetch_milestone_schedule')
WEBSTATUS_EMAIL = 'webstatus@google.com'
CBE_ESCLATION_EMAIL = 'cbe-releasenotes@google.com'
STAGING_EMAIL = 'jrobbins-test@googlegroups.com'


def get_current_milestone_info(anchor_channel: str):
  """Return a dict of info about the next milestone reaching anchor_channel."""
  try:
    resp = requests.get(f'{CHROME_RELEASE_SCHEDULE_URL}?mstone={anchor_channel}')
  except requests.RequestException as e:
    raise e
  mstone_info = json.loads(resp.text)
  return mstone_info['mstones'][0]


def choose_email_recipients(
    feature: FeatureEntry, is_escalated: bool) -> list[str]:
  """Choose which recipients will receive the email notification."""
  # Only feature owners are notified for a non-escalated notification.
  if not is_escalated:
    return feature.owner_emails

  # Escalated notification. Add extended recipients.
  ws_group_emails = [STAGING_EMAIL]
  if settings.PROD:
    ws_group_emails = [WEBSTATUS_EMAIL, CBE_ESCLATION_EMAIL]
  all_notified_users = set(ws_group_emails)
  all_notified_users.add(feature.creator_email)
  all_notified_users.update(feature.owner_emails)
  all_notified_users.update(feature.editor_emails)
  all_notified_users.update(feature.spec_mentor_emails or [])
  return list(all_notified_users)


def build_email_tasks(
    features_to_notify: list[tuple[FeatureEntry, int]],
    subject_format: str,
    body_template_path: str,
    current_milestone_info: dict,
    escalation_check: Callable
    ) -> list[dict[str, Any]]:
  email_tasks: list[dict[str, Any]] = []
  beta_date = datetime.fromisoformat(current_milestone_info['earliest_beta'])
  beta_date_str = beta_date.strftime('%Y-%m-%d')
  for fe, mstone in features_to_notify:
    # Check if this notification should be escalated.
    is_escalated = escalation_check(fe)

    # Get stage information needed to display the template.
    stage_info = stage_helpers.get_stage_info_for_templates(fe)

    body_data = {
      'id': fe.key.integer_id(),
      'feature': fe,
      'stage_info': stage_info,
      'should_render_mstone_table': stage_info['should_render_mstone_table'],
      'SITE_URL': settings.SITE_URL,
      'milestone': mstone,
      'beta_date_str': beta_date_str,
      'is_escalated': is_escalated,
    }
    html = render_template(body_template_path, **body_data)
    subject = subject_format % fe.name
    if is_escalated:
      subject = f'ESCALATED: {subject}'
    recipients = choose_email_recipients(fe, is_escalated)
    for recipient in recipients:
      email_tasks.append({
        'to': recipient,
        'subject': subject,
        'reply_to': None,
        'html': html
      })
  return email_tasks


class AbstractReminderHandler(basehandlers.FlaskHandler):
  JSONIFY = True
  SUBJECT_FORMAT: str | None = '%s'
  EMAIL_TEMPLATE_PATH: str | None = None  # Subclasses must override
  ANCHOR_CHANNEL = 'current'  # the stable channel
  FUTURE_MILESTONES_TO_CONSIDER = 0
  MILESTONE_FIELDS: list[str] = list()  # Subclasses must override

  def get_template_data(self, **kwargs):
    """Sends notifications to users requesting feature updates for accuracy."""
    self.require_cron_header()
    current_milestone_info = get_current_milestone_info(self.ANCHOR_CHANNEL)
    features_to_notify = self.determine_features_to_notify(
        current_milestone_info)
    email_tasks = build_email_tasks(
        features_to_notify, self.SUBJECT_FORMAT,
        self.EMAIL_TEMPLATE_PATH, current_milestone_info,
        self.should_escalate_notification)
    notifier.send_emails(email_tasks)

    recipients_str = ''
    # Add an alphabetical list of unique recipients to the return message.
    if len(email_tasks):
      recipients = '\n'.join(
          sorted(list(set([task['to'] for task in email_tasks]))))
      recipients_str = f'\nRecipients:\n{recipients}'
    message =  f'{len(email_tasks)} email(s) sent or logged.{recipients_str}'
    logging.info(message)

    self.changes_after_sending_notifications(features_to_notify)
    return {'message': message}

  def prefilter_features(
      self,
      current_milestone_info: dict,
      features: list[FeatureEntry]
      ) -> list[FeatureEntry]:
    """Return a list of features that fit class-specific criteria."""
    return features  # Defaults to no prefiltering.

  def filter_by_milestones(
      self,
      current_milestone_info: dict,
      features: list[FeatureEntry]
      ) -> list[tuple[FeatureEntry, int]]:
    """Return [(feature, milestone)] for features with a milestone in range."""
    # 'current' milestone is the next stable milestone that hasn't landed.
    # We send notifications to any feature planned for beta or stable launch
    # in the next 4 * FUTURE_MILESTONES_TO_CONSIDER weeks.
    min_mstone = int(current_milestone_info['mstone'])
    max_mstone = min_mstone + self.FUTURE_MILESTONES_TO_CONSIDER

    result = []
    for feature in features:
      stages = stage_helpers.get_feature_stages(feature.key.integer_id())
      min_milestone = None
      for field in self.MILESTONE_FIELDS:
        # Get fields that are relevant to the milestones field specified
        # (e.g. 'shipped_milestone' implies shipping stages)
        relevant_stages = stages.get(
            STAGE_TYPES_BY_FIELD_MAPPING[field][feature.feature_type] or -1, [])
        for stage in relevant_stages:
          if field == 'rollout_milestone':
            m = getattr(stage, field)
          else:
            milestones = stage.milestones
            m = (None if milestones is None
                else getattr(milestones,
                    MilestoneSet.MILESTONE_FIELD_MAPPING[field]))
          if m is not None and m >= min_mstone and m <= max_mstone:
            if min_milestone is None:
              min_milestone = m
            else:
              min_milestone = min(min_milestone, m)
      # If a matching milestone was ever found, use it for the reminder.
      if min_milestone:
        result.append((feature, min_milestone))

    return result

  def determine_features_to_notify(
      self,
      current_milestone_info: dict
      ) -> list[tuple[FeatureEntry, int]]:
    """Get all features filter them by class-specific and milestone criteria."""
    features = FeatureEntry.query(
        FeatureEntry.deleted == False).fetch()
    prefiltered_features = self.prefilter_features(
        current_milestone_info, features)
    features_milestone_pairs = self.filter_by_milestones(
        current_milestone_info, prefiltered_features)
    return features_milestone_pairs

  # Subclasses should override if escalation is needed.
  def should_escalate_notification(self, feature: FeatureEntry) -> bool:
    """Determine if the notification should be escalated to more users."""
    return False

  # Subclasses should override if processing is needed after notifications sent.
  def changes_after_sending_notifications(
      self, features_notified: list[tuple[FeatureEntry, int]]) -> None:
    pass


class FeatureAccuracyHandler(AbstractReminderHandler):
  """Periodically remind owners to verify the accuracy of their entries."""

  ACCURACY_GRACE_PERIOD = timedelta(weeks=4)
  SUBJECT_FORMAT = '[Action requested] Update %s'
  EMAIL_TEMPLATE_PATH = 'accuracy_notice_email.html'
  FUTURE_MILESTONES_TO_CONSIDER = 2
  MILESTONE_FIELDS = [
      'dt_milestone_android_start',
      'dt_milestone_desktop_start',
      'dt_milestone_ios_start',
      'dt_milestone_webview_start',
      'ot_milestone_android_start',
      'ot_milestone_desktop_start',
      'ot_milestone_webview_start',
      'shipped_android_milestone',
      'shipped_ios_milestone',
      'shipped_milestone',
      'shipped_webview_milestone',
      'rollout_milestone']

  def prefilter_features(
      self,
      current_milestone_info: dict,
      features: list[FeatureEntry]
      ) -> list[FeatureEntry]:
    now = datetime.now()
    prefiltered_features = [
        feature for feature in features
        # It needs review if never reviewed, or if grace period has passed.
        if (feature.accurate_as_of is None or
            feature.accurate_as_of + self.ACCURACY_GRACE_PERIOD < now)]
    return prefiltered_features

  def should_escalate_notification(self, feature: FeatureEntry) -> bool:
    """Escalate notification if 2 previous emails have had no response."""
    return feature.outstanding_notifications >= 2

  def changes_after_sending_notifications(
      self, notified_features: list[tuple[FeatureEntry, int]]) -> None:
    """Updates the count of any outstanding notifications."""
    features_to_update = []
    for feature, _ in notified_features:
      feature.outstanding_notifications += 1
      features_to_update.append(feature)
    ndb.put_multi(features_to_update)


class PrepublicationHandler(AbstractReminderHandler):
  """Give feature owners a final preview just before publication."""

  SUBJECT_FORMAT = '[Action requested] Review %s'
  EMAIL_TEMPLATE_PATH = 'prepublication-notice-email.html'
  MILESTONE_FIELDS = [
      'shipped_android_milestone',
      'shipped_ios_milestone',
      'shipped_milestone',
      'shipped_webview_milestone']
  # Devrel copies summaries 1 week before the beta goes live.
  PUBLICATION_LEAD_TIME = timedelta(weeks=1)
  # We remind owners 1 week before that.
  REMINDER_WINDOW = timedelta(weeks=1)
  ANCHOR_CHANNEL = 'beta'

  def prefilter_features(self, current_milestone_info, features, now=None):
    earliest_beta = datetime.fromisoformat(
        current_milestone_info['earliest_beta'])

    now = now or datetime.now()
    window_end = earliest_beta - self.PUBLICATION_LEAD_TIME
    window_start = window_end - self.REMINDER_WINDOW
    logging.info('%r <= %r <= %r ?', window_start, now, window_end)
    if window_start <= now <= window_end:
      # If we are in the reminder window, process all releveant features.
      logging.info('On week')
      return features
    else:
      # If this cron is running on an off week, do nothing.
      logging.info('Off week')
      return []


class SLOReportHandler(basehandlers.FlaskHandler):
  JSONIFY = True
  # For now, this just returns a JSON report to help me evaluate if we
  # are ready to start sending SLO reminder emails without sending too
  # many.

  def get_template_data(self, **kwargs):
    """Returns a JSON report listing overdue review for each reviewer."""
    overdue_gates = slo.get_overdue_gates(
        approval_defs.APPROVAL_FIELDS_BY_ID, approval_defs.DEFAULT_SLO_LIMIT)
    gates_by_reviewer: dict[str, list[Gate]] = defaultdict(list)
    for og in overdue_gates:
      gate_info = [og.feature_id, og.stage_id, og.key.integer_id()]
      reviewers = approval_defs.get_approvers(og.gate_type)
      for r in reviewers:
        gates_by_reviewer[r].append(gate_info)

    return {'message': 'OK',
            'gates_by_reviewer': gates_by_reviewer}


class SLOOverdueHandler(basehandlers.FlaskHandler):
  JSONIFY = True
  SUBJECT_FORMAT = 'Review due for: %s'
  BODY_TEMPLATE_PATH = 'slo_overdue_email.html'

  def get_template_data(self, **kwargs):
    """Sends notifications to reviewers of newly overdue reviews."""
    self.require_cron_header()
    newly_overdue_gates, long_overdue_gates, relevant_features = (
        self.get_overdue_gates_and_features())
    newly_email_tasks = self.build_gate_email_tasks(
        newly_overdue_gates, relevant_features, False)
    long_email_tasks = self.build_gate_email_tasks(
        long_overdue_gates, relevant_features, True)
    email_tasks = newly_email_tasks + long_email_tasks
    notifier.send_emails(email_tasks)

    recipients_str = ''
    # Add an alphabetical list of unique recipients to the return message.
    if len(email_tasks):
      recipients = '\n'.join(
          sorted(list(set([task['to'] for task in email_tasks]))))
      recipients_str = f'\nRecipients:\n{recipients}'
    message =  f'{len(email_tasks)} email(s) sent or logged.{recipients_str}'
    logging.info(message)

    return {'message': message}

  def get_overdue_gates_and_features(self):
    """Return lists of newly and long overdue review gates, and their FEs."""
    overdue_gates: list[Gate] = slo.get_overdue_gates(
        approval_defs.APPROVAL_FIELDS_BY_ID, approval_defs.DEFAULT_SLO_LIMIT)
    newly_overdue_gates: list[Gate] = []
    long_overdue_gates: list[Gate] = []
    relevant_feature_ids: set[int] = set()
    for og in overdue_gates:
      appr_def = approval_defs.APPROVAL_FIELDS_BY_ID.get(og.gate_type)
      slo_limit = (appr_def.slo_initial_response
                   if appr_def else approval_defs.DEFAULT_SLO_LIMIT)
      remaining = slo.remaining_days(og.requested_on, slo_limit)
      if remaining == -1:
        newly_overdue_gates.append(og)
        relevant_feature_ids.add(og.feature_id)
      elif remaining == -slo_limit:
        long_overdue_gates.append(og)
        relevant_feature_ids.add(og.feature_id)

    relevant_features = {
        fe_id: FeatureEntry.get_by_id(fe_id)
        for fe_id in relevant_feature_ids}
    return newly_overdue_gates, long_overdue_gates, relevant_features

  def build_gate_email_tasks(
      self,
      gates_to_notify: list[Gate],
      relevant_features: dict[int, FeatureEntry],
      is_escalated: bool
  ) -> list[dict[str, Any]]:
    email_tasks: list[dict[str, Any]] = []
    for gate in gates_to_notify:
      gate_id = gate.key.integer_id()
      appr_def = approval_defs.APPROVAL_FIELDS_BY_ID[gate.gate_type]
      fe = relevant_features[gate.feature_id]
      feature_id = fe.key.integer_id()
      gate_url = settings.SITE_URL + f'feature/{feature_id}?gate={gate_id}'
      body_data = {
          'feature': fe,
          'appr_def': appr_def,
          'gate_url': gate_url,
          'is_escalated': is_escalated,
      }
      html = render_template(self.BODY_TEMPLATE_PATH, **body_data)
      subject = self.SUBJECT_FORMAT % fe.name
      if is_escalated:
        subject = f'ESCALATED: {subject}'
      recipients = self.choose_reviewers(gate, is_escalated)
      for recipient in recipients:
        email_tasks.append({
            'to': recipient,
            'subject': subject,
            'reply_to': None,
            'html': html
        })
    return email_tasks

  def choose_reviewers(self, gate: Gate, is_escalated: bool) -> list[str]:
    """Decide who to notify that a review is overdue."""
    if not is_escalated and gate.assignee_emails:
      return gate.assignee_emails

    review_team = approval_defs.get_approvers(gate.gate_type)
    assignees = gate.assignee_emails or []
    return list(set(assignees + review_team))


class SendOTReminderEmailsHandler(basehandlers.FlaskHandler):
  def get_template_data(self, **kwargs):
    """Send any time-based origin trials reminder emails."""
    self.require_cron_header()
    return ot_process_reminders.send_email_reminders()
