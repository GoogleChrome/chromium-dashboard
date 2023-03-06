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

from datetime import datetime, timedelta
import json
import logging
from typing import Optional
import requests

from flask import render_template

from framework import basehandlers
from internals.core_models import FeatureEntry, MilestoneSet
from internals.legacy_models import Feature
from internals import notifier
from internals import stage_helpers
from internals.core_enums import STAGE_TYPES_BY_FIELD_MAPPING
import settings


CHROME_RELEASE_SCHEDULE_URL = (
    'https://chromiumdash.appspot.com/fetch_milestone_schedule')


def get_current_milestone_info(anchor_channel: str):
  """Return a dict of info about the next milestone reaching anchor_channel."""
  try:
    resp = requests.get(f'{CHROME_RELEASE_SCHEDULE_URL}?mstone={anchor_channel}')
  except requests.RequestException as e:
    raise e
  mstone_info = json.loads(resp.text)
  return mstone_info['mstones'][0]


def build_email_tasks(
    features_to_notify, subject_format, body_template_path,
    current_milestone_info):
  email_tasks = []
  beta_date = datetime.fromisoformat(current_milestone_info['earliest_beta'])
  beta_date_str = beta_date.strftime('%Y-%m-%d')
  for fe, mstone in features_to_notify:
    # TODO(danielrsmith): the estimated-milestones-template.html is reliant
    # on old Feature entity milestone fields and will need to be refactored
    # to use Stage entity fields before removing this Feature use.
    feature = Feature.get_by_id(fe.key.integer_id())
    body_data = {
      'id': fe.key.integer_id(),
      'feature': feature,
      'site_url': settings.SITE_URL,
      'milestone': mstone,
      'beta_date_str': beta_date_str,
    }
    html = render_template(body_template_path, **body_data)
    subject = subject_format % fe.name
    for owner in fe.owner_emails:
      email_tasks.append({
        'to': owner,
        'subject': subject,
        'reply_to': None,
        'html': html
      })
  return email_tasks


class AbstractReminderHandler(basehandlers.FlaskHandler):
  JSONIFY = True
  SUBJECT_FORMAT: Optional[str] = '%s'
  EMAIL_TEMPLATE_PATH: Optional[str] = None  # Subclasses must override
  ANCHOR_CHANNEL = 'current'  # the stable channel
  FUTURE_MILESTONES_TO_CONSIDER = 0
  MILESTONE_FIELDS: Optional[tuple] = None  # Subclasses must override

  def get_template_data(self, **kwargs):
    """Sends notifications to users requesting feature updates for accuracy."""
    self.require_cron_header()
    current_milestone_info = get_current_milestone_info(self.ANCHOR_CHANNEL)
    features_to_notify = self.determine_features_to_notify(
        current_milestone_info)
    email_tasks = build_email_tasks(
        features_to_notify, self.SUBJECT_FORMAT, self.EMAIL_TEMPLATE_PATH,
        current_milestone_info)
    notifier.send_emails(email_tasks)

    message =  f'{len(email_tasks)} email(s) sent or logged.'
    logging.info(message)
    return {'message': message}

  def prefilter_features(self, current_milestone_info, features):
    """Return a list of features that fit class-specific criteria."""
    return features  # Defaults to no prefiltering.

  def filter_by_milestones(self, current_milestone_info, features):
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
        relevant_stages = stages[
            STAGE_TYPES_BY_FIELD_MAPPING[field][feature.feature_type]]
        for stage in relevant_stages:
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

  def determine_features_to_notify(self, current_milestone_info):
    """Get all features filter them by class-specific and milestone criteria."""
    features = FeatureEntry.query(
        FeatureEntry.deleted == False).fetch()
    prefiltered_features = self.prefilter_features(
        current_milestone_info, features)
    features_milestone_pairs = self.filter_by_milestones(
        current_milestone_info, prefiltered_features)
    return features_milestone_pairs


class FeatureAccuracyHandler(AbstractReminderHandler):
  """Periodically remind owners to verify the accuracy of their entries."""

  ACCURACY_GRACE_PERIOD = timedelta(weeks=4)
  SUBJECT_FORMAT = '[Action requested] Update %s'
  EMAIL_TEMPLATE_PATH = 'accuracy_notice_email.html'
  FUTURE_MILESTONES_TO_CONSIDER = 2
  MILESTONE_FIELDS = (
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
      'shipped_webview_milestone')

  def prefilter_features(self, current_milestone_info, features):
    now = datetime.now()
    prefiltered_features = [
        feature for feature in features
        # It needs review if never reviewed, or if grace period has passed.
        if (feature.accurate_as_of is None or
            feature.accurate_as_of + self.ACCURACY_GRACE_PERIOD < now)]
    return prefiltered_features


class PrepublicationHandler(AbstractReminderHandler):
  """Give feature owners a final preview just before publication."""

  SUBJECT_FORMAT = '[Action requested] Review %s'
  EMAIL_TEMPLATE_PATH = 'prepublication-notice-email.html'
  MILESTONE_FIELDS = (
      'shipped_android_milestone',
      'shipped_ios_milestone',
      'shipped_milestone',
      'shipped_webview_milestone')
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
