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

import flask
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
from internals import attachments
from internals.enterprise_helpers import *
from internals.core_enums import *
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.data_types import CHANGED_FIELDS_LIST_TYPE
from internals import feature_links
from internals import notifier, notifier_helpers
from internals.review_models import Gate, Activity
from internals.data_types import VerboseFeatureDict
from internals import feature_helpers
from internals import processes
from internals import search
from internals import search_fulltext
from internals import stage_helpers
from internals.user_models import AppUser
import settings


# See https://www.regextester.com/93901 for url regex
SCHEME_PATTERN = r'((?P<scheme>[a-z]+):(\/\/)?)?'
DOMAIN_PATTERN = r'([\w-]+(\.[\w-]+)+)'
PATH_PARAMS_ANCHOR_PATTERN = r'([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'
URL_RE = re.compile(r'\b%s%s%s\b' % (
    SCHEME_PATTERN, DOMAIN_PATTERN, PATH_PARAMS_ANCHOR_PATTERN))
ALLOWED_SCHEMES = [None, 'http', 'https']

# Internal DevRel mailing list for ChromeStatus.
DEVREL_EMAIL = 'devrel-chromestatus-all@google.com'

class FeaturesAPI(basehandlers.EntitiesAPIHandler):
  """Features are the the main records that we track."""

  def get_one_feature(self, feature_id: int) -> VerboseFeatureDict:
    feature = FeatureEntry.get_by_id(feature_id)
    if not feature:
      self.abort(404, msg='Feature %r not found' % feature_id)
    user = users.get_current_user()
    if feature.deleted and not permissions.can_edit_feature(user, feature_id):
      self.abort(404, msg='Feature %r not found' % feature_id)
    if not permissions.can_view_feature(user, feature):
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

  def _shared_update_special_fields(
      self,
      feature: FeatureEntry,
      feature_changes: dict[str, Any],
    ) -> bool:
    """Handle any special FeatureEntry fields common to creating or updating."""
    has_updated = False
    # Handle "Use Markdown" checkboxes.
    for field, field_type in api_specs.FEATURE_FIELD_DATA_TYPES:
      new_markdown = feature_changes.get(field + '_is_markdown')
      if new_markdown is None:
        continue
      if new_markdown and field not in feature.markdown_fields:
        feature.markdown_fields.append(field)
        has_updated = True
      elif not new_markdown and field in feature.markdown_fields:
        feature.markdown_fields = [mf for mf in feature.markdown_fields
                                   if mf != field]
        has_updated = True

    return has_updated

  def _post_update_special_fields(
      self,
      feature: FeatureEntry,
      feature_changes: dict[str, Any],
    ) -> None:
    """Handle any special FeatureEntry fields when creating."""
    self._shared_update_special_fields(feature, feature_changes)

    if ('first_enterprise_notification_milestone' in feature_changes):
      feature.first_enterprise_notification_milestone = int(feature_changes['first_enterprise_notification_milestone'])
      has_updated = True
    elif needs_default_first_notification_milestone(new_fields=feature_changes):
      feature.first_enterprise_notification_milestone = get_default_first_notice_milestone_for_feature()

    if feature.feature_type == FEATURE_TYPE_ENTERPRISE_ID:
      feature.blink_components = [settings.DEFAULT_ENTERPRISE_COMPONENT]
      feature.tag_review_status = REVIEW_NA
    else:
      feature.tag_review_status = processes.initial_tag_review_status(
          feature.feature_type)

    feature.creator_email = self.get_current_user().email()
    feature.updater_email = self.get_current_user().email()
    feature.accurate_as_of = datetime.now()

  @permissions.require_create_feature
  def do_post(self, **kwargs):
    """Handle POST requests to create a single feature."""
    feature_changes = self.get_json_param_dict()

    # A feature creation request should have all required fields.
    for field in FeatureEntry.REQUIRED_FIELDS:
      if field not in feature_changes:
        self.abort(400, msg=f'Required field "{field}" not provided.')

    fields_dict = {
        'owner_emails': [self.get_current_user().email()],
        'devrel_emails': [DEVREL_EMAIL],
        'category': int(MISC),
        'blink_components': [settings.DEFAULT_COMPONENT],
    }
    for field, field_type in api_specs.FEATURE_FIELD_DATA_TYPES:
      if field in feature_changes:
        fields_dict[field] = self.format_field_val(
            field, field_type, feature_changes[field])

    # Try to create the feature using the provided data.
    try:
      feature = FeatureEntry(**fields_dict)
      self._post_update_special_fields(feature, feature_changes)
      feature.put()
    except Exception as e:
      self.abort(400, msg=str(e))
    id = feature.key.integer_id()

    search_fulltext.index_feature(feature)
    self._write_stages_and_gates_for_feature(id, feature.feature_type)

    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(FeatureEntry.DEFAULT_CACHE_KEY)
    rediscache.delete_keys_with_prefix(FeatureEntry.SEARCH_CACHE_KEY)

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
    ) -> tuple[list[Stage], bool]:
    """Update stage fields with changes provided in the PATCH request."""
    # TODO(DanielRyanSmith): This method should be updated to use the logic
    # for basehandlers.update_stage(). This logic is mostly duplicated otherwise.
    stages_to_store: list[Stage] = []
    ship_milestones_were_updated = False
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
        # desktop_first will be the new default field for "start" milestone,
        # like rollout_milestone.

        # If this is the rollout milestone, also save it to the old field.
        # TODO(DanielRyanSmith): Remove this double-storage once the
        # rollout_milestone field is deprecated.
        if form_field_name == 'rollout_milestone':
          self.update_field_value(stage, 'rollout_milestone', 'int', new_value)

        # Track if any shipping milestones were updated so we know to reset
        # outstanding notifications if so.
        if (form_field_name == 'rollout_milestone' or
            form_field_name == 'shipped_milestone' or
            form_field_name == 'shipped_android_milestone' or
            form_field_name == 'shipped_ios_milestone' or
            form_field_name == 'shipped_webview_milestone'):
          ship_milestones_were_updated = True

        self.update_field_value(milestones, field, field_type, new_value)
        changed_fields.append((form_field_name, old_value, new_value))
        stage_was_updated = True
      stage.milestones = milestones

      # Changing other rollout details also counts.
      if ('rollout_platforms' in change_info or
          'rollout_details' in change_info):
        ship_milestones_were_updated = True

      if stage_was_updated:
        stages_to_store.append(stage)

    # Save all of the updates made.
    if stages_to_store:
      ndb.put_multi(stages_to_store)

    # Return the list of modified stages, and whether any shipping/rollout
    # milestones were updated.
    return stages_to_store, ship_milestones_were_updated

  def _maybe_reset_releasenotes_flags(
      self, feature: FeatureEntry,
      changed_fields: CHANGED_FIELDS_LIST_TYPE) -> None:
    if permissions.can_review_release_notes(self.get_current_user()):
      return
    notify_reviewers = False
    if feature.is_releasenotes_content_reviewed:
      feature.is_releasenotes_content_reviewed = False
      changed_fields.append(('is_releasenotes_content_reviewed', True, False))
      notify_reviewers = True
    if feature.is_releasenotes_publish_ready:
      feature.is_releasenotes_publish_ready = False
      changed_fields.append(('is_releasenotes_publish_ready', True, False))
      notify_reviewers = True
    if notify_reviewers:
      notifier.notify_releasenotes_reviewers(feature)

  def _patch_update_special_fields(
      self,
      feature: FeatureEntry,
      feature_changes: dict[str, Any],
      has_updated: bool,
      updated_stages: list[Stage],
      changed_fields: CHANGED_FIELDS_LIST_TYPE,
      stage_ids: list[int]
    ) -> None:
    """Handle any special FeatureEntry fields when updating."""
    now = datetime.now()
    feature_id = feature.key.integer_id()
    # Set accurate_as_of if this is an accuracy verification request.
    if 'accurate_as_of' in feature_changes:
      changed_fields.append(('accurate_as_of', feature.accurate_as_of, now))
      feature.accurate_as_of = now
      feature.outstanding_notifications = 0
      has_updated = True

    if 'screenshot_links' in feature_changes:
      attachments.delete_orphan_attachments(
          feature_id, feature_changes['screenshot_links'])

    has_updated |= self._shared_update_special_fields(feature, feature_changes)
    # Set enterprise first notification milestones.
    if is_update_first_notification_milestone(feature, feature_changes):
      feature.first_enterprise_notification_milestone = int(feature_changes['first_enterprise_notification_milestone'])
      has_updated = True
    elif needs_default_first_notification_milestone(feature, feature_changes):
      feature.first_enterprise_notification_milestone = get_default_first_notice_milestone_for_feature()
      has_updated = True
    if should_remove_first_notice_milestone(feature, feature_changes):
      feature.first_enterprise_notification_milestone = None

    # If a shipping stage was edited, set shipping_year based on milestones.
    updated_shipping_stages = [
        us for us in updated_stages
        if us.stage_type in STAGE_TYPES_SHIPPING.values()]
    if updated_shipping_stages:
      existing_shipping_stages = (
          stage_helpers.get_all_shipping_stages_with_milestones(
              feature_id=feature_id))
      shipping_stage_dict = {
          es.key.integer_id(): es
          for es in existing_shipping_stages
      }
      shipping_stage_dict.update({
          uss.key.integer_id(): uss
          for uss in updated_shipping_stages
      })
      earliest = stage_helpers.find_earliest_milestone(
          list(shipping_stage_dict.values()))
      if earliest:
          year = stage_helpers.look_up_year(earliest)
          if year != feature.shipping_year:
            changed_fields.append(('shipping_year', feature.shipping_year, year))
            feature.shipping_year = year
            has_updated = True

    # Release notes flags get reset if a non-reviewer makes a change.
    if 'name' in feature_changes or 'summary' in feature_changes:
      self._maybe_reset_releasenotes_flags(feature, changed_fields)

    # If any stages were mentioned, update active_stage_id.
    if stage_ids:
      stage_type_to_stage_ids = stage_helpers.get_feature_stage_ids(feature_id)
      stage_id_to_stage_type = {
          stage_id: stage_type
          for stage_type, stage_id_list in stage_type_to_stage_ids.items()
          for stage_id in stage_id_list}
      active_stage_type = stage_id_to_stage_type.get(feature.active_stage_id, 0)
      highest_edited_stage_id = max(
          stage_ids, key=lambda s: stage_id_to_stage_type[s])
      highest_edited_stage_type = stage_id_to_stage_type[highest_edited_stage_id]
      if highest_edited_stage_type > active_stage_type:
        feature.active_stage_id = highest_edited_stage_id

    # If changes were made, set the feature.updated timestamp.
    if has_updated:
      user_email = self.get_current_user().email()
      feature.updater_email = user_email
      feature.updated = now

  def _patch_update_feature(
      self,
      feature: FeatureEntry,
      feature_changes: dict[str, Any],
      updated_stages: list[Stage],
      changed_fields: CHANGED_FIELDS_LIST_TYPE,
      stage_ids: list[int]
    ) -> None:
    """Update feature fields with changes provided in the PATCH request."""
    has_updated = len(updated_stages) > 0
    for field, field_type in api_specs.FEATURE_FIELD_DATA_TYPES:
      if field not in feature_changes:
        continue
      old_value = getattr(feature, field)
      new_value = feature_changes[field]
      self.update_field_value(feature, field, field_type, new_value)
      changed_fields.append((field, old_value, new_value))
      has_updated = True

    self._patch_update_special_fields(
        feature, feature_changes, has_updated, updated_stages, changed_fields,
        stage_ids)
    feature.put()

  def do_patch(self, **kwargs) -> flask.Response | dict[str, str]:
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
    stage_ids = [s['id'] for s in body['stages'] if 'id' in s]
    updated_stages, ship_milestones_were_updated = self._patch_update_stages(
      body['stages'], changed_fields)
    # Reset outstanding notifications if the user updated any ship/rollout milestones.
    if ship_milestones_were_updated:
      feature.outstanding_notifications = 0
      self._maybe_reset_releasenotes_flags(feature, changed_fields)

    self._patch_update_feature(
        feature, body['feature_changes'], updated_stages, changed_fields,
        stage_ids)

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

  def do_delete(self, **kwargs) -> flask.Response | dict[str, str]:
    """Delete the specified feature."""
    # TODO(jrobbins): implement undelete UI.  For now, use cloud console.
    if 'feature_id' not in kwargs:
      self.abort(404, msg='Feature ID not specified')
    feature_id: int = kwargs['feature_id']
    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      self.abort(403, msg='User does not have permission to edit this feature.')

    feature: FeatureEntry = self.get_specified_feature(feature_id=feature_id)
    feature.deleted = True
    # Delete any AI-generated content during archival.
    feature.ai_test_eval_report = None
    feature.put()

    user = users.get_current_user()
    email = user.email() if user else None
    activity = Activity(
        feature_id=feature_id,
        author=email,
        content=f'Feature "{feature.name}" was archived.')
    activity.put()

    rediscache.delete_keys_with_prefix(FeatureEntry.DEFAULT_CACHE_KEY)
    rediscache.delete_keys_with_prefix(FeatureEntry.SEARCH_CACHE_KEY)

    return {'message': 'Done'}
