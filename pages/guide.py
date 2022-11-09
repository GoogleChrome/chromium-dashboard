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
import requests  # type: ignore

# Appengine imports.
from framework import rediscache

from framework import basehandlers
from framework import permissions
from internals import core_enums, notifier_helpers
from internals.core_models import Feature, FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote
from internals import processes
from internals import search_fulltext
import settings


class FeatureCreateHandler(basehandlers.FlaskHandler):

  @permissions.require_create_feature
  def process_post_data(self, **kwargs):
    owners = self.split_emails('owner')
    editors = self.split_emails('editors')
    cc_emails = self.split_emails('cc_recipients')

    blink_components = (
        self.split_input('blink_components', delim=',') or
        [settings.DEFAULT_COMPONENT])

    # TODO(jrobbins): Validate input, even though it is done on client.

    feature_type = int(self.form.get('feature_type', 0))
    signed_in_user = ndb.User(
        email=self.get_current_user().email(),
        _auth_domain='gmail.com')
    feature = Feature(
        category=int(self.form.get('category')),
        name=self.form.get('name'),
        feature_type=feature_type,
        summary=self.form.get('summary'),
        owner=owners,
        editors=editors,
        cc_recipients=cc_emails,
        creator=signed_in_user.email(),
        accurate_as_of=datetime.now(),
        unlisted=self.form.get('unlisted') == 'on',
        blink_components=blink_components,
        tag_review_status=processes.initial_tag_review_status(feature_type),
        created_by=signed_in_user,
        updated_by=signed_in_user)
    key = feature.put()

    # Write for new FeatureEntry entity.
    feature_entry = FeatureEntry(
        id=feature.key.integer_id(),
        category=int(self.form.get('category')),
        name=self.form.get('name'),
        feature_type=feature_type,
        summary=self.form.get('summary'),
        owner_emails=owners,
        editor_emails=editors,
        cc_emails=cc_emails,
        creator_email=signed_in_user.email(),
        updater_email=signed_in_user.email(),
        accurate_as_of=datetime.now(),
        unlisted=self.form.get('unlisted') == 'on',
        blink_components=blink_components,
        tag_review_status=processes.initial_tag_review_status(feature_type))
    feature_entry.put()
    search_fulltext.index_feature(feature_entry)

    # Write each Stage and Gate entity for the given feature.
    self.write_gates_and_stages_for_feature(
        feature_entry.key.integer_id(), feature_type)

    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(Feature.feature_cache_prefix())
    rediscache.delete_keys_with_prefix(FeatureEntry.feature_cache_prefix())

    redirect_url = '/guide/edit/' + str(key.integer_id())
    return self.redirect(redirect_url)

  def write_gates_and_stages_for_feature(
      self, feature_id: int, feature_type: int) -> None:
    """Write each Stage and Gate entity for the given feature."""
    # Obtain a list of stages and gates for the given feature type.
    stages_gates = core_enums.STAGES_AND_GATES_BY_FEATURE_TYPE[feature_type]

    ot_stage_id: Optional[int] = None
    for stage_type, gate_type in stages_gates:
      stage = Stage(feature_id=feature_id, stage_type=stage_type)
      stage.put()
      # Not all stages have gates. If a gate is specified, create it.
      if gate_type:
        # Keep track of the ID of the origin trial Stage entity
        # to use for the trial extension Stage entity.
        if gate_type == core_enums.GATE_ORIGIN_TRIAL:
          ot_stage_id = stage.key.integer_id()
        gate = Gate(feature_id=feature_id, stage_id=stage.key.integer_id(),
            gate_type=gate_type, state=Vote.NA)

        # If we are creating a trial extension gate,
        # then the trial extension stage was just created.
        # Associate the origin trial stage id with the extension stage.
        if gate_type == core_enums.GATE_EXTEND_ORIGIN_TRIAL:
          stage.ot_stage_id = ot_stage_id
        gate.put()


class FeatureEditHandler(basehandlers.FlaskHandler):

  # Field name, data type
  EXISTING_FIELDS: list[tuple[str, str]] = [
      # impl_status_chrome and intent_stage handled separately.
      ('spec_link', 'link'),
      ('standard_maturity', 'int'),
      ('api_spec', 'bool'),
      ('spec_mentors', 'emails'),
      ('security_review_status', 'int'),
      ('privacy_review_status', 'int'),
      ('initial_public_proposal_url', 'link'),
      ('explainer_links', 'links'),
      ('bug_url', 'link'),
      ('launch_bug_url', 'link'),
      ('anticipated_spec_changes', 'str'),
      ('requires_embedder_support', 'bool'),
      ('devtrial_instructions', 'link'),
      ('flag_name', 'str'),
      ('owner', 'emails'),
      ('editors', 'emails'),
      ('cc_recipients', 'emails'),
      ('doc_links', 'links'),
      ('measurement', 'str'),
      ('sample_links', 'links'),
      ('search_tags', 'split_str'),
      ('blink_components', 'split_str'),
      ('devrel', 'emails'),
      ('category', 'int'),
      ('name', 'str'),
      ('summary', 'str'),
      ('motivation', 'str'),
      ('interop_compat_risks', 'str'),
      ('ergonomics_risks', 'str'),
      ('activation_risks', 'str'),
      ('security_risks', 'str'),
      ('debuggability', 'str'),
      ('all_platforms', 'bool'),
      ('all_platforms_descr', 'str'),
      ('wpt', 'bool'),
      ('wpt_descr', 'str'),
      ('ff_views', 'int'),
      ('ff_views_link', 'link'),
      ('ff_views_notes', 'str'),
      ('safari_views', 'int'),
      ('safari_views_link', 'link'),
      ('safari_views_notes', 'str'),
      ('web_dev_views', 'int'),
      ('web_dev_views_link', 'link'),
      ('web_dev_views_notes', 'str'),
      ('other_views_notes', 'str'),
      ('prefixed', 'bool'),
      ('non_oss_deps', 'str'),
      ('tag_review', 'str'),
      ('tag_review_status', 'int'),
      ('webview_risks', 'str'),
      ('comments', 'str'),
      ('ongoing_constraints', 'str')]

  # Old field name, new field name
  RENAMED_FIELD_MAPPING: dict[str, str] = {
      'owner': 'owner_emails',
      'editors': 'editor_emails',
      'cc_recipients': 'cc_emails',
      'devrel': 'devrel_emails',
      'spec_mentors': 'spec_mentor_emails',
      'comments': 'feature_notes',
      'ready_for_trial_url': 'announcement_url'}

  # Field name, data type
  STAGE_FIELDS: list[tuple[str, str]] = [
      ('intent_to_implement_url', 'link'),
      ('intent_to_ship_url', 'link'),
      ('ready_for_trial_url', 'link'),
      ('intent_to_experiment_url', 'link'),
      ('intent_to_extend_experiment_url', 'link'),
      ('origin_trial_feedback_url', 'link'),
      ('finch_url', 'link'),
      ('experiment_goals', 'str'),
      ('experiment_risks', 'str'),
      ('experiment_extension_reason', 'str')]

  CHECKBOX_FIELDS: frozenset[str] = frozenset([
      'accurate_as_of', 'unlisted', 'api_spec', 'all_platforms',
      'wpt', 'requires_embedder_support', 'prefixed'])
  
  SELECT_FIELDS: frozenset[str] = frozenset([
      'category', 'intent_stage', 'standard_maturity', 'security_review_status',
      'privacy_review_status', 'tag_review_status', 'safari_views', 'ff_views',
      'web_dev_views', 'blink_components', 'impl_status_chrome'])

  def touched(self, param_name: str) -> bool:
    """Return True if the user edited the specified field."""
    # TODO(jrobbins): for now we just consider everything on the current form
    # to have been touched.  Later we will add javascript to populate a
    # hidden form field named "touched" that lists the names of all fields
    # actually touched by the user.

    # For now, checkboxes are always considered "touched", if they are
    # present on the form.
    if param_name in self.CHECKBOX_FIELDS:
      form_fields_str = self.form.get('form_fields')
      if form_fields_str:
        form_fields = [field_name.strip()
                       for field_name in form_fields_str.split(',')]
        return param_name in form_fields
      else:
        return True

    # For now, selects are considered "touched", if they are
    # present on the form and are not empty strings.
    if param_name in self.SELECT_FIELDS:
      return bool(self.form.get(param_name))

    # See TODO at top of this method.
    return param_name in self.form

  def _get_field_val(self, field: str, field_type: str) -> Any:
    """Get the form value of a given field name."""
    if field_type == 'int':
      return self.parse_int(field)
    elif field_type == 'bool':
      return self.form.get(field) == 'on'
    elif field_type == 'link':
      return self.parse_link(field)
    elif field_type == 'links':
      return self.parse_links(field)
    elif field_type == 'emails':
      return self.split_emails(field)
    elif field_type == 'str':
      return self.form.get(field)
    elif field_type == 'split_str':
      val = self.split_input(field, delim=',')
      if field == 'blink_components' and len(val) == 0:
        return [settings.DEFAULT_COMPONENT]
      return val
    raise ValueError(f'Unknown field data type: {field_type}')

  def _add_changed_field(self, fe: FeatureEntry, field: str, new_val: Any,
      changed_fields: list[tuple[str, Any, Any]]) -> None:
    """Add values to the list of changed fields if the values differ."""
    old_val = getattr(fe, field)
    if new_val != old_val:
      changed_fields.append((field, old_val, new_val))

  def process_post_data(self, **kwargs) -> requests.Response:
    feature_id = kwargs.get('feature_id', None)
    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    if feature_id:
      # Load feature directly from NDB so as to never get a stale cached copy.
      feature: Feature = Feature.get_by_id(feature_id)
      fe: FeatureEntry = FeatureEntry.get_by_id(feature_id)
      if fe is None:
        self.abort(404, msg='Feature not found')

    logging.info('POST is %r', self.form)

    stage_update_items: list[tuple[str, Any]] = []
    changed_fields: list[tuple[str, Any, Any]] = []

    for field, field_type in self.EXISTING_FIELDS:
      if self.touched(field):
        field_val = self._get_field_val(field, field_type)
        new_field = self.RENAMED_FIELD_MAPPING.get(field, field)
        self._add_changed_field(fe, new_field, field_val, changed_fields)
        setattr(feature, field, field_val)
        setattr(fe, new_field, field_val)

    # impl_status_chrome and intent_stage
    # can be be set either by <select> or a checkbox.
    impl_status_val: Optional[int] = None
    if self.touched('impl_status_chrome'):
      impl_status_val = self._get_field_val('impl_status_chrome', 'int')
    elif self._get_field_val('set_impl_status', 'bool'):
      impl_status_val = self._get_field_val('impl_status_offered', 'int')
    if impl_status_val:
      self._add_changed_field(
          fe, 'impl_status_chrome', impl_status_val, changed_fields)
      setattr(feature, 'impl_status_chrome', impl_status_val)
      setattr(fe, 'impl_status_chrome', impl_status_val)

    intent_stage_val: Optional[int] = None
    if self.touched('intent_stage'):
      intent_stage_val = self._get_field_val('intent_stage', 'int')
    elif self.form.get('set_stage') == 'on':
      intent_stage_val = kwargs.get('stage_id', 0)
    if intent_stage_val is not None:
      self._add_changed_field(
          fe, 'intent_stage', intent_stage_val, changed_fields)
      setattr(feature, 'intent_stage', impl_status_val)
      setattr(fe, 'intent_stage', impl_status_val)

    for field, field_type in self.STAGE_FIELDS:
      if self.touched(field):
        field_val = self._get_field_val(field, field_type)
        setattr(feature, field, field_val)
        stage_update_items.append((field, field_val))

    for field in MilestoneSet.MILESTONE_FIELD_MAPPING.keys():
      if self.touched(field):
        # TODO(jrobbins): Consider supporting milestones that are not ints.
        field_val = self._get_field_val(field, 'int')
        setattr(feature, field, field_val)
        stage_update_items.append((field, field_val))

    # Update metadata fields.
    now = datetime.now()
    if self.form.get('accurate_as_of'):
      feature.accurate_as_of = now
      fe.accurate_as_of = now
    user_email = self.get_current_user().email()
    feature.updated_by = ndb.User(
        email=user_email,
        _auth_domain='gmail.com')
    fe.updater_email = user_email
    fe.updated = now

    key: ndb.Key = fe.put()
    feature.put()

    # Write changes made to the corresponding stage type.
    if stage_update_items:
      self.update_stage_fields(feature_id, feature.feature_type,
          stage_update_items, changed_fields)

    notifier_helpers.notify_subscribers_and_save_amendments(
        fe, changed_fields, notify=True)
    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(Feature.feature_cache_prefix())
    rediscache.delete_keys_with_prefix(FeatureEntry.feature_cache_prefix())

    # Update full-text index.
    if fe:
      search_fulltext.index_feature(fe)

    redirect_url = '/guide/edit/' + str(key.integer_id())
    return self.redirect(redirect_url)

  def update_stage_fields(self, feature_id: int, feature_type: int,
      update_items: list[tuple[str, Any]],
      changed_fields: list[tuple[str, Any, Any]]) -> None:
    # Get all existing stages associated with the feature.
    stages = Stage.get_feature_stages(feature_id)

    for field, new_val in update_items:
      field = self.RENAMED_FIELD_MAPPING.get(field, field)
      # Determine the stage type that the field should change on.
      stage_type = core_enums.STAGE_TYPES_BY_FIELD_MAPPING[field][feature_type]
      # If this feature type does not have this field, skip it
      # (e.g. developer-facing code changes cannot have origin trial fields).
      if stage_type is None:
        continue
      stage = stages.get(stage_type, None)
      # If a stage of this type does not exist for this feature, create it.
      if stage is None:
        stage = Stage(feature_id=feature_id, stage_type=stage_type)
        stage.put()
        stages[stage_type] = stage

      # Change the field based on the field type.
      # If this field changing is a milestone, change it in the
      # MilestoneSet entity.
      if field in MilestoneSet.MILESTONE_FIELD_MAPPING:
        old_val = None
        milestone_field = (
            MilestoneSet.MILESTONE_FIELD_MAPPING[field])
        milestoneset_entity = getattr(stage, 'milestones')
        # If the MilestoneSet entity has not been initiated, create it.
        if milestoneset_entity is None:
          milestoneset_entity = MilestoneSet()
        old_val = getattr(milestoneset_entity, milestone_field)
        setattr(milestoneset_entity, milestone_field, new_val)
        stage.milestones = milestoneset_entity
      # If the field starts with "intent_", it should modify the
      # more general "intent_thread_url" field.
      elif field.startswith('intent_'):
        old_val = getattr(stage, 'intent_thread_url')
        setattr(stage, 'intent_thread_url', new_val)
      # Otherwise, replace field value with attribute of the same field name.
      else:
        old_val = getattr(stage, field)
        setattr(stage, field, new_val)
      
      if old_val != new_val:
        changed_fields.append((field, old_val, new_val))

    # Write to all the stages.
    for stage in stages.values():
      stage.put()
