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
from typing import Any
from google.cloud import ndb

from api import converters
from framework import basehandlers
from framework import permissions
from framework import rediscache
from framework import users
from internals.core_enums import *
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate
from internals.data_types import VerboseFeatureDict
from internals import feature_helpers
from internals import search
import settings


# Data type for lists defining field data type information.
FIELD_INFO_DATA_TYPE = list[tuple[str, str]]


class FeaturesAPI(basehandlers.APIHandler):
  """Features are the the main records that we track."""

  ############################
  ###### Mutable Fields ######
  ############################
  # Dictionary with fields that can be edited on feature creation
  # and their data types.
  # Field name, data type
  FEATURE_FIELD_DATA_TYPES: FIELD_INFO_DATA_TYPE = [
    ('activation_risks', 'str'),
    ('adoption_expectation', 'str'),
    ('adoption_plan', 'str'),
    ('all_platforms', 'bool'),
    ('all_platforms_descr', 'str'),
    ('anticipated_spec_changes', 'str'),
    ('api_spec', 'bool'),
    ('availability_expectation', 'str'),
    ('blink_components', 'list'),
    ('breaking_change', 'bool'),
    ('bug_url', 'str'),
    ('category', 'int'),
    ('cc_emails', 'list'),
    ('comments', 'str'),
    ('debuggability', 'str'),
    ('devrel', 'list'),
    ('devtrial_instructions', 'str'),
    ('doc_links', 'list'),
    ('editors_emails', 'list'),
    ('enterprise_feature_categories', 'list'),
    ('ergonomics_risks', 'str'),
    ('explainer_links', 'list'),
    ('feature_type', 'int'),
    ('ff_views', 'int'),
    ('ff_views_link', 'str'),
    ('ff_views_notes', 'str'),
    ('flag_name', 'str'),
    ('impl_status_chrome', 'int'),
    ('initial_public_proposal_url', 'str'),
    ('intent_stage', 'int'),
    ('interop_compat_risks', 'str'),
    ('launch_bug_url', 'str'),
    ('screenshot_links', 'list'),
    ('measurement', 'str'),
    ('motivation', 'str'),
    ('name', 'str'),
    ('non_oss_deps', 'str'),
    ('ongoing_constraints', 'str'),
    ('other_views_notes', 'str'),
    ('owner_emails', 'list'),
    ('prefixed', 'bool'),
    ('privacy_review_status', 'int'),
    ('requires_embedder_support', 'bool'),
    ('safari_views', 'int'),
    ('safari_views_link', 'str'),
    ('safari_views_notes', 'str'),
    ('sample_links', 'list'),
    ('search_tags', 'list'),
    ('security_review_status', 'int'),
    ('security_risks', 'str'),
    ('spec_link', 'str'),
    ('spec_mentors', 'list'),
    ('standard_maturity', 'int'),
    ('summary', 'str'),
    ('tag_review', 'str'),
    ('tag_review_status', 'int'),
    ('unlisted', 'bool'),
    ('web_dev_views', 'int'),
    ('web_dev_views_link', 'str'),
    ('web_dev_views_notes', 'str'),
    ('webview_risks', 'str'),
    ('wpt', 'bool'),
    ('wpt_descr', 'str'),
  ]

  STAGE_FIELD_DATA_TYPES: FIELD_INFO_DATA_TYPE = [
    ('display_name', 'str'),
    ('browser', 'str'),
    ('experiment_goals', 'str'),
    ('experiment_risks', 'str'),
    ('experiment_extension_reason', 'str'),
    ('intent_thread_url', 'str'),
    ('origin_trial_feedback_url', 'str'),
    ('announcement_url', 'str'),
    ('rollout_impact', 'int'),
    ('rollout_milestone', 'int'),
    ('rollout_platforms', 'list'),
    ('rollout_details', 'str'),
    ('enterprise_policies', 'str'),
  ]

  MILESTONESET_FIELD_DATA_TYPES: FIELD_INFO_DATA_TYPE = [
    ('desktop_first', 'int'),
    ('desktop_last', 'int'),
    ('android_first', 'int'),
    ('android_last', 'int'),
    ('ios_first', 'int'),
    ('ios_last', 'int'),
    ('webview_first', 'int'),
    ('webview_last', 'int'),
  ]


  def _abort_invalid_data_type(
      self, field: str, field_type: str, value: Any) -> None:
    """Abort the process if an invalid data type is given."""
    self.abort(400, msg=(
        f'Bad value for field {field} of type {field_type}: {value}'))

  def _format_field_val(
      self,
      field: str,
      field_type: str,
      value: Any,
    ) -> str | int | bool | list | None:
    """Format the given feature value based on the field type."""

    # If the field is empty, no need to format.
    if value is None:
      return None

    # TODO(DanielRyanSmith): Write checks to ensure enum values are valid.
    if (field_type == 'list'):
      if field == 'blink_components' and len(value) == 0:
        return [settings.DEFAULT_COMPONENT]
      return value
    elif field_type == 'int':
      try:
        return int(value)
      except ValueError:
        self._abort_invalid_data_type(field, field_type, value)
    elif field_type == 'bool':
      return bool(value)
    return str(value)

  ###########
  ### GET ###
  ###########

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

    user_query = self.request.args.get('q', '')
    sort_spec = self.request.args.get('sort')
    num = self.get_int_arg('num', search.DEFAULT_RESULTS_PER_PAGE)
    start = self.get_int_arg('start', 0)

    show_enterprise = 'feature_type' in user_query
    try:
      features_on_page, total_count = search.process_query(
          user_query, sort_spec=sort_spec, show_unlisted=show_unlisted_features,
          show_enterprise=show_enterprise, start=start, num=num)
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

  ############
  ### POST ###
  ############

  @permissions.require_create_feature
  def do_post(self, **kwargs):
    """Handle POST requests to create a single feature."""
    body = self.get_json_param_dict()

    # A feature creation request should have all required fields.
    for field in FeatureEntry.REQUIRED_FIELDS:
      if field not in body:
        self.abort(400, msg=f'Required field "{field}" not provided.')

    fields_dict = {}
    for field, field_type in self.FEATURE_FIELD_DATA_TYPES:
      if field in body:
        fields_dict[field] = self._format_field_val(
            field, field_type, body[field])

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

  #############
  ### PATCH ###
  #############

  def _update_field_value(
      self,
      entity: FeatureEntry | MilestoneSet | Stage,
      field: str,
      field_type: str,
      value: Any
    ) -> None:
    new_value = self._format_field_val(field, field_type, value)
    setattr(entity, field, new_value)

  def _patch_update_stages(
      self,
      stage_changes_list: list[dict[str, Any]]
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
      for field, field_type in self.STAGE_FIELD_DATA_TYPES:
        if field not in change_info:
          continue
        self._update_field_value(stage, field, field_type, change_info[field])
        stage_was_updated = True

      # Update milestone fields.
      milestones = stage.milestones
      for field, field_type in self.MILESTONESET_FIELD_DATA_TYPES:
        if field not in change_info:
          continue
        if milestones is None:
          milestones = MilestoneSet()
        self._update_field_value(
            milestones, field, field_type, change_info[field])
        stage_was_updated = True
      stage.milestones = milestones

      if stage_was_updated:
        stages.append(stage)

    # Save all of the updates made.
    # Return a boolean representing if any changes were made to any stages.
    if stages:
      ndb.put_multi(stages)
      return True
    return False

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
    
    if has_updated:
      user_email = self.get_current_user().email()
      feature.updater_email = user_email
      feature.updated = now

  def _patch_update_feature(
      self,
      feature: FeatureEntry,
      feature_changes: dict[str, Any],
      has_updated: bool
    ) -> None:
    """Update feature fields with changes provided in the PATCH request."""
    for field, field_type in self.FEATURE_FIELD_DATA_TYPES:
      if field not in feature_changes:
        continue
      self._update_field_value(
          feature, field, field_type, feature_changes[field])
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

    has_updated = self._patch_update_stages(body['stages'])
    self._patch_update_feature(feature, body['feature_changes'], has_updated)

    return {'message': f'Feature {feature_id} updated.'}

  ##############
  ### DELETE ###
  ##############

  @permissions.require_admin_site
  def do_delete(self, **kwargs) -> dict[str, str]:
    """Delete the specified feature."""
    # TODO(jrobbins): implement undelete UI.  For now, use cloud console.
    feature_id = kwargs.get('feature_id', None)
    feature = self.get_specified_feature(feature_id=feature_id)
    if feature is None:
      return {'message': 'ID does not match any feature.'}
    feature.deleted = True
    feature.put()
    rediscache.delete_keys_with_prefix(FeatureEntry.feature_cache_prefix())

    # Write for new FeatureEntry entity.
    feature_entry: FeatureEntry | None = (
        FeatureEntry.get_by_id(feature_id))
    if feature_entry:
      feature_entry.deleted = True
      feature_entry.put()

    return {'message': 'Done'}
