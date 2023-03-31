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
from internals import stage_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate
from internals import processes
from internals import search_fulltext
import settings


# Internal DevRel mailing list for ChromeStatus.
DEVREL_EMAIL = 'devrel-chromestatus-all@google.com'


class FeatureCreateHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'spa.html'

  def get_template_data(self, **defaults):
    return basehandlers.get_spa_template_data(self, defaults)

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
        creator_email=signed_in_user.email(),
        updater_email=signed_in_user.email(),
        accurate_as_of=datetime.now(),
        unlisted=self.form.get('unlisted') == 'on',
        breaking_change=self.form.get('breaking_change') == 'on',
        blink_components=blink_components,
        tag_review_status=processes.initial_tag_review_status(feature_type))
    key: ndb.Key = feature_entry.put()
    search_fulltext.index_feature(feature_entry)

    # Write each Stage and Gate entity for the given feature.
    self.write_gates_and_stages_for_feature(key.integer_id(), feature_type)

    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(FeatureEntry.feature_cache_prefix())

    # TODO(jrobbins): Make this be /feature/ID after ability to edit
    # from the feature detail page is complete.
    redirect_url = '/guide/edit/' + str(key.integer_id())
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
    owners = self.split_emails('owner')
    editors = self.split_emails('editors')

    signed_in_user = ndb.User(
        email=self.get_current_user().email(),
        _auth_domain='gmail.com')
    feature_type = core_enums.FEATURE_TYPE_ENTERPRISE_ID

    # Write for new FeatureEntry entity.
    feature_entry = FeatureEntry(
        category=int(core_enums.MISC),
        enterprise_feature_categories=self.split_input(
            'enterprise_feature_categories'),
        name=self.form.get('name'),
        feature_type=feature_type,
        summary=self.form.get('summary'),
        owner_emails=owners,
        editor_emails=editors,
        launch_bug_url=self.form.get('launch_bug_url'),
        breaking_change=self.form.get('breaking_change') == 'on',
        creator_email=signed_in_user.email(),
        updater_email=signed_in_user.email(),
        accurate_as_of=datetime.now(),
        blink_components=[settings.DEFAULT_ENTERPRISE_COMPONENT],
        tag_review_status=core_enums.REVIEW_NA)
    key: ndb.Key = feature_entry.put()
    search_fulltext.index_feature(feature_entry)

    # Write each Stage and Gate entity for the given feature.
    self.write_gates_and_stages_for_feature(key.integer_id(), feature_type)

    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(FeatureEntry.feature_cache_prefix())

    # TODO(jrobbins): Make this be /feature/ID after ability to edit
    # from the feature detail page is complete.
    redirect_url = '/guide/editall/' + str(key.integer_id()) + '#rollout1'
    return self.redirect(redirect_url)


class FeatureEditHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'spa.html'

  def get_template_data(self, **defaults):
    return basehandlers.get_spa_template_data(self, defaults)

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
      ('unlisted', 'bool'),
      ('doc_links', 'links'),
      ('measurement', 'str'),
      ('availability_expectation', 'str'),
      ('adoption_expectation', 'str'),
      ('adoption_plan', 'str'),
      ('sample_links', 'links'),
      ('search_tags', 'split_str'),
      ('blink_components', 'split_str'),
      ('devrel', 'emails'),
      ('category', 'int'),
      ('enterprise_feature_categories', 'split_str'),
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
      ('breaking_change', 'bool'),
      ('ongoing_constraints', 'str')]

  # Old field name, new field name
  RENAMED_FIELD_MAPPING: dict[str, str] = {
      'owner': 'owner_emails',
      'editors': 'editor_emails',
      'cc_recipients': 'cc_emails',
      'devrel': 'devrel_emails',
      'spec_mentors': 'spec_mentor_emails',
      'comments': 'feature_notes',
      'intent_to_implement_url': 'intent_thread_url',
      'intent_to_ship_url': 'intent_thread_url',
      'intent_to_experiment_url': 'intent_thread_url',
      'intent_to_extend_experiment_url': 'intent_thread_url'}

  # Field name, data type
  STAGE_FIELDS: list[tuple[str, str]] = [
      ('announcement_url', 'link'),
      ('origin_trial_feedback_url', 'link'),
      ('experiment_extension_reason', 'str'),
      ('finch_url', 'link'),
      ('experiment_goals', 'str'),
      ('experiment_risks', 'str'),
      ('rollout_impact', 'int'),
      ('rollout_milestone', 'int'),
      ('rollout_platforms', 'split_str'),
      ('rollout_details', 'str'),
      ('enterprise_policies', 'split_str'),
      ('intent_thread_url', 'str'),
      ('display_name', 'str'),
  ]

  INTENT_FIELDS: list[str] = [
      'intent_to_implement_url',
      'intent_to_experiment_url',
      'intent_to_ship_url'
  ]

  DEV_TRIAL_MILESTONE_FIELDS: list[tuple[str, str]] = [
      ('dt_milestone_desktop_start', 'desktop_first'),
      ('dt_milestone_android_start', 'android_first'),
      ('dt_milestone_ios_start', 'ios_first'),
      ('dt_milestone_webview_start', 'webview_first')
  ]

  OT_MILESTONE_FIELDS: list[tuple[str, str]] = [
      ('ot_milestone_desktop_start', 'desktop_first'),
      ('ot_milestone_desktop_end', 'desktop_last'),
      ('ot_milestone_android_start', 'android_first'),
      ('ot_milestone_android_end', 'android_last'),
      ('ot_milestone_ios_start', 'ios_first'),
      ('ot_milestone_ios_end', 'ios_last'),
      ('ot_milestone_webview_start', 'webview_first'),
      ('ot_milestone_webview_end', 'webview_last'),
  ]

  OT_EXTENSION_MILESTONE_FIELDS: list[tuple[str, str]] = [
    ('extension_desktop_last', 'desktop_last'),
    ('extension_android_last', 'android_last'),
    ('extension_webview_last', 'webview_last'),
  ]

  SHIPPING_MILESTONE_FIELDS: list[tuple[str, str]] = [
      ('shipped_milestone', 'desktop_first'),
      ('shipped_android_milestone', 'android_first'),
      ('shipped_ios_milestone', 'ios_first'),
      ('shipped_webview_milestone', 'webview_first'),
  ]

  CHECKBOX_FIELDS: frozenset[str] = frozenset([
      'accurate_as_of', 'unlisted', 'api_spec', 'all_platforms',
      'wpt', 'requires_embedder_support', 'prefixed', 'breaking_change'])

  SELECT_FIELDS: frozenset[str] = frozenset([
      'category', 'intent_stage', 'standard_maturity', 'security_review_status',
      'privacy_review_status', 'tag_review_status', 'safari_views', 'ff_views',
      'web_dev_views', 'blink_components', 'impl_status_chrome'])

  MULTI_SELECT_FIELDS: frozenset[str] = frozenset(['rollout_platforms', 'enterprise_feature_categories'])

  def touched(self, param_name: str, form_fields: list[str]) -> bool:
    """Return True if the user edited the specified field."""
    # TODO(jrobbins): for now we just consider everything on the current form
    # to have been touched.  Later we will add javascript to populate a
    # hidden form field named "touched" that lists the names of all fields
    # actually touched by the user.

    # For now, checkboxes and multi-selects are always considered "touched",
    # if they are present on the form.
    if (param_name in self.CHECKBOX_FIELDS or
        param_name in self.MULTI_SELECT_FIELDS):
      return param_name in form_fields if len(form_fields) > 0 else True

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
      if field == 'rollout_platforms' or field == 'enterprise_feature_categories':
        val = self.form.getlist(field)
        # Occasionally, input will give an empty string as the first element.
        # It needs to be removed.
        if val and val[0] == '':
          val = val[1:]
        return val
      elif field == 'blink_components' and len(val) == 0:
        return [settings.DEFAULT_COMPONENT]
      return val
    raise ValueError(f'Unknown field data type: {field_type}')

  def _add_changed_field(self, fe: FeatureEntry, field: str, new_val: Any,
      changed_fields: list[tuple[str, Any, Any]]) -> None:
    """Add values to the list of changed fields if the values differ."""
    old_val = getattr(fe, field)
    if new_val != old_val:
      changed_fields.append((field, old_val, new_val))

  # TODO(danielrsmith): This method's logic is way too complicated to easily
  # maintain. This needs to be scrapped and submission of edits should be
  # handled using features_api and stages_api.
  def process_post_data(self, **kwargs) -> requests.Response:
    feature_id = kwargs.get('feature_id', None)
    stage_id = kwargs.get('stage_id', None)
    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    if feature_id:
      # Load feature directly from NDB so as to never get a stale cached copy.
      fe: FeatureEntry = FeatureEntry.get_by_id(feature_id)
      if fe is None:
        self.abort(404, msg='Feature not found')

    logging.info('POST is %r', self.form)

    stage_update_items: list[tuple[str, Any]] = []
    changed_fields: list[tuple[str, Any, Any]] = []

    form_fields_str = self.form.get('form_fields')
    form_fields: list[str] = []
    if form_fields_str:
      form_fields = [
          field_name.strip() for field_name in form_fields_str.split(',')]

    for field, field_type in self.EXISTING_FIELDS:
      if self.touched(field, form_fields):
        field_val = self._get_field_val(field, field_type)
        new_field = self.RENAMED_FIELD_MAPPING.get(field, field)
        self._add_changed_field(fe, new_field, field_val, changed_fields)
        setattr(fe, new_field, field_val)

    # impl_status_chrome and intent_stage
    # can be be set either by <select> or a checkbox.
    impl_status_val: Optional[int] = None
    if self.touched('impl_status_chrome', form_fields):
      impl_status_val = self._get_field_val('impl_status_chrome', 'int')
    elif self._get_field_val('set_impl_status', 'bool'):
      impl_status_val = self._get_field_val('impl_status_offered', 'int')
    if impl_status_val:
      self._add_changed_field(
          fe, 'impl_status_chrome', impl_status_val, changed_fields)
      setattr(fe, 'impl_status_chrome', impl_status_val)

    active_stage_id = -1
    intent_stage_val: int | None = None
    if self.form.get('set_stage') == 'on':
      active_stage_id = kwargs.get('stage_id', 0)
      intent_stage_val = kwargs.get('intent_stage', core_enums.INTENT_NONE)
    if intent_stage_val is not None:
      self._add_changed_field(
          fe, 'active_stage_id', active_stage_id, changed_fields)
      self._add_changed_field(
          fe, 'intent_stage', intent_stage_val, changed_fields)
      setattr(fe, 'active_stage_id', active_stage_id)
      setattr(fe, 'intent_stage', intent_stage_val)

    # List of stage IDs will be present if the request comes from edit_all page.
    stage_ids = self.form.get('stages')
    if stage_ids:
      stage_ids_list = [int(id) for id in stage_ids.split(',')]
      self.update_stages_editall(
          fe.feature_type, stage_ids_list, changed_fields, form_fields)
    # If a stage_id is supplied, we make changes to only that specific stage.
    elif stage_id:
      for field, field_type in self.STAGE_FIELDS:
        if self.touched(field, form_fields):
          field_val = self._get_field_val(field, field_type)
          stage_update_items.append((field, field_val))

      for field in MilestoneSet.MILESTONE_FIELD_MAPPING.keys():
        if self.touched(field, form_fields):
          # TODO(jrobbins): Consider supporting milestones that are not ints.
          field_val = self._get_field_val(field, 'int')
          stage_update_items.append((field, field_val))
      self.update_single_stage(
          stage_id, fe.feature_type, stage_update_items, changed_fields)

    extension_stage_ids = self.form.get('extension_stage_ids')
    if extension_stage_ids:
      stage_ids_list = [int(id) for id in extension_stage_ids.split(',')]
      self.update_stages_editall(fe.feature_type, stage_ids_list, changed_fields, form_fields)
    # Update metadata fields.
    now = datetime.now()
    if self.form.get('accurate_as_of'):
      fe.accurate_as_of = now
      fe.outstanding_notifications = 0
    user_email = self.get_current_user().email()
    fe.updater_email = user_email
    fe.updated = now

    key: ndb.Key = fe.put()

    notifier_helpers.notify_subscribers_and_save_amendments(
        fe, changed_fields, notify=True)
    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(FeatureEntry.feature_cache_prefix())

    # Update full-text index.
    if fe:
      search_fulltext.index_feature(fe)

    # Navigate back to the page that the user was on before editing, iff
    # it is the URL of a feature detail page on our site.
    nextPage = self.form.get('nextPage')
    if nextPage and nextPage.startswith('/feature/'):
      redirect_url = nextPage
    else:
      redirect_url = '/guide/edit/' + str(key.integer_id())
    return self.redirect(redirect_url)

  def update_multiple_stages(self, feature_id: int, feature_type: int,
      update_items: list[tuple[str, Any]],
      changed_fields: list[tuple[str, Any, Any]]) -> None:
    """Handle updating stages when IDs have not been specified."""
    # Get all existing stages associated with the feature.
    stages = stage_helpers.get_feature_stages(feature_id)

    for field, new_val in update_items:
      field = self.RENAMED_FIELD_MAPPING.get(field, field)
      # Determine the stage type that the field should change on.
      stage_type = core_enums.STAGE_TYPES_BY_FIELD_MAPPING[field][feature_type]
      # If this feature type does not have this field, skip it
      # (e.g. developer-facing code changes cannot have origin trial fields).
      if stage_type is None:
        continue
      stages_list: list[Stage] = stages.get(stage_type, [])
      stage: Stage | None = stages_list[0] if stages_list else None
      # If a stage of this type does not exist for this feature, create it.
      if stage is None:
        stage = Stage(feature_id=feature_id, stage_type=stage_type)
        stage.put()
        stages[stage_type].append(stage)

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
    for stages_by_type in stages.values():
      for stage in stages_by_type:
        stage.put()

  def update_single_stage(self, stage_id: int, feature_type: int,
      update_items: list[tuple[str, Any]],
      changed_fields: list[tuple[str, Any, Any]]) -> None:
    """Update the fields of the stage of a given ID."""
    stage_to_update = Stage.get_by_id(stage_id)
    if stage_to_update is None:
      self.abort(404, msg=f'Stage {stage_id} not found.')

    # Determine if 'intent_thread_url' field needs to be changed.
    intent_thread_val = None
    changed_field = None
    for field in self.INTENT_FIELDS:
      field_val = self._get_field_val(field, 'link')
      if field_val is not None:
        intent_thread_val = field_val
        changed_field = field
        break
    if changed_field is not None:
      changed_fields.append(
          (changed_field, stage_to_update.intent_thread_url, intent_thread_val))
    setattr(stage_to_update, 'intent_thread_url', intent_thread_val)

    for field, new_val in update_items:
      # Update the field's name if it has been renamed.
      old_field_name = field
      field = self.RENAMED_FIELD_MAPPING.get(field, field)

      old_val = None
      if field in MilestoneSet.MILESTONE_FIELD_MAPPING:
        milestone_field = MilestoneSet.MILESTONE_FIELD_MAPPING[field]
        if stage_to_update.milestones is None:
          stage_to_update.milestones = MilestoneSet()
        old_val = getattr(stage_to_update.milestones, milestone_field)
        setattr(stage_to_update.milestones, milestone_field, new_val)
      else:
        old_val = getattr(stage_to_update, field)
        setattr(stage_to_update, field, new_val)
      if old_val != new_val:
        changed_fields.append((old_field_name, old_val, new_val))
    stage_to_update.put()

  def update_stages_editall(
      self,
      feature_type: int,
      stage_ids: list[int],
      changed_fields: list[tuple[str, Any, Any]],
      form_fields: list[str]) -> None:
    """Handle the updates for stages on the edit-all page."""
    for id in stage_ids:
      stage = Stage.get_by_id(id)
      if not stage:
        self.abort(404, msg=f'No stage {id} found')
      # Update the stage-specific fields.
      for field, field_type in self.STAGE_FIELDS:
        # To differentiate stages that have the same fields, the stage ID
        # is appended to the field name with 2 underscores.
        field_with_id = f'{field}__{id}'
        if not self.touched(field_with_id, form_fields):
          continue
        new_field_name = self.RENAMED_FIELD_MAPPING.get(field, field)
        old_val = getattr(stage, new_field_name)
        new_val = self._get_field_val(field_with_id, field_type)
        setattr(stage, new_field_name, new_val)
        if old_val != new_val:
          changed_fields.append((field, old_val, new_val))

      intent_thread_field = None
      milestone_fields = []
      # Determine if the stage type is one with specific milestone fields.
      if stage.stage_type == core_enums.STAGE_TYPES_PROTOTYPE[feature_type]:
        intent_thread_field = 'intent_to_implement_url'
      if stage.stage_type == core_enums.STAGE_TYPES_DEV_TRIAL[feature_type]:
        milestone_fields = self.DEV_TRIAL_MILESTONE_FIELDS
      if stage.stage_type == core_enums.STAGE_TYPES_ORIGIN_TRIAL[feature_type]:
        intent_thread_field = 'intent_to_experiment_url'
        milestone_fields = self.OT_MILESTONE_FIELDS
      if (stage.stage_type ==
          core_enums.STAGE_TYPES_EXTEND_ORIGIN_TRIAL[feature_type]):
        intent_thread_field = 'intent_to_extend_experiment_url'
        milestone_fields = self.OT_EXTENSION_MILESTONE_FIELDS
      if stage.stage_type == core_enums.STAGE_TYPES_SHIPPING[feature_type]:
        intent_thread_field = 'intent_to_ship_url'
        milestone_fields = self.SHIPPING_MILESTONE_FIELDS

      # Determine if 'intent_thread_url' field needs to be changed.
      intent_field_with_id = f'{intent_thread_field}__{id}'
      if intent_thread_field and self.touched(intent_field_with_id, form_fields):
        old_val = stage.intent_thread_url
        new_val = self._get_field_val(intent_field_with_id, 'link')
        if old_val != new_val:
          changed_fields.append((intent_thread_field, old_val, new_val))
        setattr(stage, 'intent_thread_url', new_val)

      for field, milestone_field in milestone_fields:
        field_with_id = f'{field}__{id}'
        if not self.touched(field_with_id, form_fields):
          continue
        old_val = None
        new_val = self._get_field_val(field_with_id, 'int')
        milestoneset_entity = stage.milestones
        milestoneset_entity = getattr(stage, 'milestones')
        if milestoneset_entity is None:
          milestoneset_entity = MilestoneSet()
        else:
          old_val = getattr(milestoneset_entity, milestone_field)
        setattr(milestoneset_entity, milestone_field, new_val)
        stage.milestones = milestoneset_entity
        if old_val != new_val:
          changed_fields.append((field, old_val, new_val))
      stage.put()
