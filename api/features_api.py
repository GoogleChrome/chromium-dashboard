# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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
import re
from typing import Any
from google.cloud import ndb

from api import api_specs
from api import converters
from framework import basehandlers
from framework import permissions
from framework import rediscache
from framework import users
from internals.enterprise_helpers import *
from internals.core_enums import *
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.data_types import CHANGED_FIELDS_LIST_TYPE
from internals import feature_links
from internals import notifier_helpers
from internals.review_models import Gate
from internals.data_types import VerboseFeatureDict
from internals import feature_helpers
from internals import search
from internals import search_fulltext
from internals.user_models import AppUser
import settings


# See https://www.regextester.com/93901 for url regex
SCHEME_PATTERN = r'((?P<scheme>[a-z]+):(\/\/)?)?'
DOMAIN_PATTERN = r'([\w-]+(\.[\w-]+)+)'
PATH_PARAMS_ANCHOR_PATTERN = r'([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'
URL_RE = re.compile(r'\b%s%s%s\b' % (
    SCHEME_PATTERN, DOMAIN_PATTERN, PATH_PARAMS_ANCHOR_PATTERN))
ALLOWED_SCHEMES = [None, 'http', 'https']


class FeaturesAPI(basehandlers.EntitiesAPIHandler):
  """Features are the the main records that we track."""

  def get_one_feature(self, feature_id: int) -> VerboseFeatureDict:
    feature = FeatureEntry.get_by_id(feature_id)
    if not feature:
      self.abort(404, msg='Feature %r not found' % feature_id)
    user = users.get_current_user()
    if feature.deleted and not permissions.can_edit_feature(user, feature_id):
      self.abort(404, msg='Feature %r not found' % feature_id)
    return converters.feature_entry_to_json_verbose(feature)

  def do_search(self):
    user = users.get_current_user()
    # Show unlisted features to site editors or admins.
    show_unlisted_features = permissions.can_edit_any_feature(user)
    features_on_page = None

    # Query-string parameter 'milestone' is provided
    milestone = self.get_int_arg('milestone')
    if milestone:
      features_by_type = feature_helpers.get_in_milestone(
        show_unlisted=show_unlisted_features, milestone=milestone)
      total_count = sum(len(features_by_type[t]) for t in features_by_type)
      return {
          'features_by_type': features_by_type,
          'total_count': total_count,
          }

    # Query-string parameter 'releaseNotesMilestone' is provided
    release_notes_milestone = self.get_int_arg('releaseNotesMilestone')
    if release_notes_milestone:
      features_in_release_notes = feature_helpers.get_features_in_release_notes(
        milestone=release_notes_milestone)
      return {
        'features': features_in_release_notes,
        'total_count': len(features_in_release_notes)
        }

    user_query = self.request.args.get('q', '')
    sort_spec = self.request.args.get('sort')
    num = self.get_int_arg('num', search.DEFAULT_RESULTS_PER_PAGE)
    start = self.get_int_arg('start', 0)
    name_only = self.get_bool_arg('name_only', False)

    show_enterprise = (
        'feature_type' in user_query or self.get_bool_arg('showEnterprise'))
    try:
      features_on_page, total_count = search.process_query_using_cache(
          user_query, sort_spec=sort_spec, show_unlisted=show_unlisted_features,
          show_enterprise=show_enterprise, start=start, num=num, name_only=name_only)
    except ValueError as err:
      self.abort(400, msg=str(err))

    return {
        'total_count': total_count,
        'features': features_on_page,
        }

  def do_get(self, **kwargs):
    """Handle GET requests for a single feature or a search."""
    # TODO(danielrsmith): This request gives two independent return types
    # based on whether a feature_id was specified. Determine the best
    # way to handle this in a strictly-typed manner and implement it.
    feature_id = kwargs.get('feature_id', None)
    if feature_id:
      return self.get_one_feature(feature_id)
    return self.do_search()

  @permissions.require_create_feature
  def do_post(self, **kwargs):
    """Handle POST requests to create a single feature."""
    body = self.get_json_param_dict()

    # A feature creation request should have all required fields.
    for field in FeatureEntry.REQUIRED_FIELDS:
      if field not in body:
        self.abort(400, msg=f'Required field "{field}" not provided.')

    fields_dict = {}
    for field, field_type in api_specs.FEATURE_FIELD_DATA_TYPES:
      if field in body:
        fields_dict[field] = self.format_field_val(
            field, field_type, body[field])

    # If no enterprise notification milestone was set, set one since it will be shown in the next
    # release notes by default. This is true for breaking changes and enterprise features only.
    if ('first_enterprise_notification_milestone' in body):
      fields_dict['first_enterprise_notification_milestone'] = body['first_enterprise_notification_milestone']
    elif needs_default_first_notification_milestone(new_fields=body):
      fields_dict['first_enterprise_notification_milestone'] = get_default_first_notice_milestone_for_feature()

    # Try to create the feature using the provided data.
    try:
      feature = FeatureEntry(**fields_dict,
                             creator_email=self.get_current_user().email())
      feature.put()
    except Exception as e:
      self.abort(400, msg=str(e))
    id = feature.key.integer_id()

    self._write_stages_and_gates_for_feature(id, feature.feature_type)
    return {'message': f'Feature {id} created.',
            'feature_id': id}

  def _write_stages_and_gates_for_feature(
      self, feature_id: int, feature_type: int) -> None:
    """Write each Stage and Gate entity for newly created feature."""
    # Obtain a list of stages and gates for the given feature type.
    stages_gates = STAGES_AND_GATES_BY_FEATURE_TYPE[feature_type]

    for stage_type, gate_types in stages_gates:
      # Don't create a trial extension stage pre-emptively.
      if stage_type == STAGE_TYPES_EXTEND_ORIGIN_TRIAL[feature_type]:
        continue

      stage = Stage(feature_id=feature_id, stage_type=stage_type)
      stage.put()
      new_gates: list[Gate] = []
      # Stages can have zero or more gates.
      for gate_type in gate_types:
        gate = Gate(feature_id=feature_id, stage_id=stage.key.integer_id(),
                    gate_type=gate_type, state=Gate.PREPARING)
        new_gates.append(gate)

      if new_gates:
        ndb.put_multi(new_gates)

  def _patch_update_stages(
      self,
      stage_changes_list: list[dict[str, Any]],
      changed_fields: CHANGED_FIELDS_LIST_TYPE
    ) -> bool:
    """Update stage fields with changes provided in the PATCH request."""
    stages: list[Stage] = []
    for change_info in stage_changes_list:
      stage_was_updated = False
      # Check if valid ID is provided and fetch stage if it exists.
      if 'id' not in change_info:
        self.abort(400, msg='Missing stage ID in stage updates')
      id = change_info['id']
      stage = Stage.get_by_id(id)
      if not stage:
        self.abort(400, msg=f'Stage not found for ID {id}')

      # Update stage fields.
      for field, field_type in api_specs.STAGE_FIELD_DATA_TYPES:
        if field not in change_info:
          continue
        form_field_name = change_info[field]['form_field_name']

        old_value = getattr(stage, field)
        new_value = change_info[field]['value']
        self.update_field_value(stage, field, field_type, new_value)
        # The OT additional details does not need to be sent to subscribers.
        if form_field_name != 'ot_request_note':
          changed_fields.append((form_field_name, old_value, new_value))
        stage_was_updated = True

      # Update milestone fields.
      milestones = stage.milestones
      for field, field_type in api_specs.MILESTONESET_FIELD_DATA_TYPES:
        if field not in change_info:
          continue
        if milestones is None:
          milestones = MilestoneSet()
        form_field_name = change_info[field]['form_field_name']
        old_value = getattr(milestones, field)
        new_value = change_info[field]['value']
        self.update_field_value(milestones, field, field_type, new_value)
        changed_fields.append((form_field_name, old_value, new_value))
        stage_was_updated = True
      stage.milestones = milestones

      if stage_was_updated:
        stages.append(stage)

    # Save all of the updates made.
    if stages:
      ndb.put_multi(stages)

    # Return a boolean representing if any changes were made to any stages.
    return len(stages) > 0

  def _patch_update_special_fields(
      self,
      feature: FeatureEntry,
      feature_changes: dict[str, Any],
      has_updated: bool
    ) -> None:
    """Handle any special FeatureEntry fields."""
    now = datetime.now()
    # Handle accuracy notifications if this is an accuracy verification request.
    if 'accurate_as_of' in feature_changes:
      feature.accurate_as_of = now
      feature.outstanding_notifications = 0
      has_updated = True

    if is_update_first_notification_milestone(feature, feature_changes):
      feature.first_enterprise_notification_milestone = int(feature_changes['first_enterprise_notification_milestone'])
      has_updated = True
    elif needs_default_first_notification_milestone(feature, feature_changes):
      feature.first_enterprise_notification_milestone = get_default_first_notice_milestone_for_feature()
      has_updated = True
    if should_remove_first_notice_milestone(feature, feature_changes):
      feature.first_enterprise_notification_milestone = None

    if has_updated:
      user_email = self.get_current_user().email()
      feature.updater_email = user_email
      feature.updated = now

  def _patch_update_feature(
      self,
      feature: FeatureEntry,
      feature_changes: dict[str, Any],
      has_updated: bool,
      changed_fields: CHANGED_FIELDS_LIST_TYPE
    ) -> None:
    """Update feature fields with changes provided in the PATCH request."""
    for field, field_type in api_specs.FEATURE_FIELD_DATA_TYPES:
      if field not in feature_changes:
        continue
      old_value = getattr(feature, field)
      new_value = feature_changes[field]
      self.update_field_value(feature, field, field_type, new_value)
      changed_fields.append((field, old_value, new_value))
      has_updated = True

    self._patch_update_special_fields(feature, feature_changes, has_updated)
    feature.put()

  def do_patch(self, **kwargs):
    """Handle PATCH requests to update fields in a single feature."""
    body = self.get_json_param_dict()

    # Check if valid ID is provided and fetch feature if it exists.
    if 'id' not in body['feature_changes']:
      self.abort(400, msg='Missing feature ID in feature updates')
    feature_id = body['feature_changes']['id']
    feature: FeatureEntry | None = FeatureEntry.get_by_id(feature_id)
    if not feature:
      self.abort(400, msg=f'Feature not found for ID {feature_id}')

    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    changed_fields: CHANGED_FIELDS_LIST_TYPE = []
    has_updated = self._patch_update_stages(body['stages'], changed_fields)
    self._patch_update_feature(
      feature, body['feature_changes'], has_updated, changed_fields)

    notifier_helpers.notify_subscribers_and_save_amendments(
        feature, changed_fields, notify=True)
    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(FeatureEntry.DEFAULT_CACHE_KEY)
    rediscache.delete_keys_with_prefix(FeatureEntry.SEARCH_CACHE_KEY)
    # Update full-text index.
    if feature:
      search_fulltext.index_feature(feature)
      feature_links.update_feature_links(feature, changed_fields)

    return {'message': f'Feature {feature_id} updated.'}

  @permissions.require_create_feature
  def do_delete(self, **kwargs) -> dict[str, str]:
    """Delete the specified feature."""
    # TODO(jrobbins): implement undelete UI.  For now, use cloud console.
    feature_id = kwargs.get('feature_id', None)
    feature = self.get_specified_feature(feature_id=feature_id)
    if feature is None:
      return {'message': 'ID does not match any feature.'}

    user = users.get_current_user()
    app_user = AppUser.get_app_user(user.email())
    if ((app_user is None or not app_user.is_admin)
         and user.email() != feature.creator_email):
      self.abort(403)
    feature.deleted = True
    feature.put()
    rediscache.delete_keys_with_prefix(FeatureEntry.DEFAULT_CACHE_KEY)
    rediscache.delete_keys_with_prefix(FeatureEntry.SEARCH_CACHE_KEY)

    # Write for new FeatureEntry entity.
    feature_entry: FeatureEntry | None = (
        FeatureEntry.get_by_id(feature_id))
    if feature_entry:
      feature_entry.deleted = True
      feature_entry.put()

    return {'message': 'Done'}
