# -*- coding: utf-8 -*-
# Copyright 2020 Google Inc.
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

from datetime import datetime
import logging
from typing import Any, Optional
from google.cloud import ndb
import flask

# Appengine imports.
from framework import rediscache

from framework import basehandlers
from framework import permissions
from internals import core_enums, notifier_helpers
from internals import stage_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.data_types import CHANGED_FIELDS_LIST_TYPE
from internals.review_models import Gate
from internals import processes
from internals import search_fulltext
from internals import feature_links
from internals.enterprise_helpers import *
import settings


# Internal DevRel mailing list for ChromeStatus.
DEVREL_EMAIL = 'devrel-chromestatus-all@google.com'


class FeatureCreateHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'spa.html'

  def get_template_data(self, **defaults):
    return basehandlers.get_spa_template_data(self, defaults)

  @permissions.require_create_feature
  def process_post_data(self, **kwargs):
    owners = self.split_emails('owner_emails')
    editors = self.split_emails('editor_emails')
    cc_emails = self.split_emails('cc_emails')

    blink_components = (
        self.split_input('blink_components', delim=',') or
        [settings.DEFAULT_COMPONENT])

    # TODO(jrobbins): Validate input, even though it is done on client.

    feature_type = int(self.form.get('feature_type', 0))
    shipping_year = int(self.form.get('shipping_year', 0))

    has_enterprise_impact = int(self.form.get('enterprise_impact', '1')) > ENTERPRISE_IMPACT_NONE
    enterprise_notification_milestone = self.form.get('first_enterprise_notification_milestone')
    if enterprise_notification_milestone:
      enterprise_notification_milestone = int(enterprise_notification_milestone)
    if has_enterprise_impact and needs_default_first_notification_milestone(new_fields={
      'feature_type': feature_type,
      'enterprise_impact': int(self.form.get('enterprise_impact')),
      'first_enterprise_notification_milestone': enterprise_notification_milestone
      }):
      enterprise_notification_milestone = get_default_first_notice_milestone_for_feature()

    # Write for new FeatureEntry entity.
    feature_entry = FeatureEntry(
        category=int(self.form.get('category')),
        name=self.form.get('name'),
        feature_type=feature_type,
        summary=self.form.get('summary'),
        owner_emails=owners,
        editor_emails=editors,
        cc_emails=cc_emails,
        devrel_emails=[DEVREL_EMAIL],
        creator_email=self.get_current_user().email(),
        updater_email=self.get_current_user().email(),
        accurate_as_of=datetime.now(),
        unlisted=self.form.get('unlisted') == 'on',
        enterprise_impact=int(self.form.get('enterprise_impact', '1')),
        first_enterprise_notification_milestone=enterprise_notification_milestone,
        blink_components=blink_components,
        tag_review_status=processes.initial_tag_review_status(feature_type))
    if shipping_year:
      feature_entry.shipping_year = shipping_year
    key: ndb.Key = feature_entry.put()
    search_fulltext.index_feature(feature_entry)

    # Write each Stage and Gate entity for the given feature.
    self.write_gates_and_stages_for_feature(key.integer_id(), feature_type)

    notifier_helpers.notify_subscribers_and_save_amendments(
        feature_entry, [], is_update=False)

    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(FeatureEntry.DEFAULT_CACHE_KEY)
    rediscache.delete_keys_with_prefix(FeatureEntry.SEARCH_CACHE_KEY)

    redirect_url = '/feature/' + str(key.integer_id())
    return self.redirect(redirect_url)

  def write_gates_and_stages_for_feature(
      self, feature_id: int, feature_type: int) -> None:
    """Write each Stage and Gate entity for the given feature."""
    # Obtain a list of stages and gates for the given feature type.
    stages_gates = core_enums.STAGES_AND_GATES_BY_FEATURE_TYPE[feature_type]

    for stage_type, gate_types in stages_gates:
      # Don't create a trial extension stage pre-emptively.
      if stage_type == core_enums.STAGE_TYPES_EXTEND_ORIGIN_TRIAL[feature_type]:
        continue

      stage = Stage(feature_id=feature_id, stage_type=stage_type)
      stage.put()
      # Stages can have zero or more gates.
      for gate_type in gate_types:
        gate = Gate(feature_id=feature_id, stage_id=stage.key.integer_id(),
                    gate_type=gate_type, state=Gate.PREPARING)
        gate.put()


class EnterpriseFeatureCreateHandler(FeatureCreateHandler):

  TEMPLATE_PATH = 'spa.html'

  def get_template_data(self, **defaults):
    return basehandlers.get_spa_template_data(self, defaults)

  @permissions.require_create_feature
  def process_post_data(self, **kwargs):
    owners = self.split_emails('owner_emails')
    editors = self.split_emails('editor_emails')

    signed_in_user = ndb.User(
        email=self.get_current_user().email(),
        _auth_domain='gmail.com')
    feature_type = core_enums.FEATURE_TYPE_ENTERPRISE_ID

    enterprise_notification_milestone = self.form.get('first_enterprise_notification_milestone')
    if enterprise_notification_milestone:
      enterprise_notification_milestone = int(enterprise_notification_milestone)
    if needs_default_first_notification_milestone(new_fields={
      'feature_type': feature_type,
      'first_enterprise_notification_milestone': enterprise_notification_milestone}):
      enterprise_notification_milestone = get_default_first_notice_milestone_for_feature()

    # Write for new FeatureEntry entity.
    feature_entry = FeatureEntry(
        category=int(core_enums.MISC),
        enterprise_feature_categories=self.form.getlist(
            'enterprise_feature_categories'),
        name=self.form.get('name'),
        feature_type=feature_type,
        summary=self.form.get('summary'),
        owner_emails=owners,
        editor_emails=editors,
        creator_email=signed_in_user.email(),
        updater_email=signed_in_user.email(),
        accurate_as_of=datetime.now(),
        screenshot_links=self.parse_links('screenshot_links'),
        first_enterprise_notification_milestone=enterprise_notification_milestone,
        blink_components=[settings.DEFAULT_ENTERPRISE_COMPONENT],
        tag_review_status=core_enums.REVIEW_NA)
    key: ndb.Key = feature_entry.put()
    search_fulltext.index_feature(feature_entry)

    # Write each Stage and Gate entity for the given feature.
    self.write_gates_and_stages_for_feature(key.integer_id(), feature_type)

    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(FeatureEntry.DEFAULT_CACHE_KEY)

    redirect_url = '/guide/editall/' + str(key.integer_id()) + '#rollout1'
    return self.redirect(redirect_url)
