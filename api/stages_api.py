# -*- coding: utf-8 -*-
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

from datetime import datetime
import logging
from typing import Any, Optional
from google.cloud import ndb  # type: ignore

# Appengine imports.
from framework import rediscache

from framework import basehandlers
from framework import permissions
from internals import core_enums, notifier_helpers
from internals import stage_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate
import settings




class StagesAPI(basehandlers.APIHandler):

  # Categorized field names of the Stage kind.
  GENERAL_FIELDS: tuple[str] = (
      'stage_type',
      'browser',
      'pm_emails',
      'tl_emails',
      'ux_emails',
      'te_emails',
      'intent_thread_url')

  MILESTONE_FIELDS: tuple[str] = (
      'desktop_first',
      'desktop_last',
      'android_first',
      'android_last',
      'ios_first',
      'ios_last',
      'webview_first',
      'webview_last')

  OT_FIELDS: tuple[str] = (
      'experiment_goals',
      'experiment_risks',
      'origin_trial_feedback_url')

  OT_EXTENSION_FIELDS: tuple[str] = (
      'experiment_extension_reason',
      'ot_stage_id')

  SHIPPING_FIELDS: tuple[str] = (
      'announcement_url',
      'finch_url')
  
  ENTERPRISE_FIELDS: tuple[str] = (
      'rollout_milestone',
      'rollout_platforms',
      'rollout_details',
      'enterprise_policies')

  # Fields that should default to an empty list if null.
  FIELDS_DEFAULT_TO_LIST: tuple[str] = (
      'pm_emails',
      'tl_emails',
      'ux_emails',
      'te_emails',
      'rollout_platforms',
      'enterprise_policies')

  def _stage_to_json_dict(self, stage: Stage) -> dict:
    """Create a JSON representation of a given stage."""
    stage_dict = {}
    # Get a list of every non-milestone field.
    all_fields = (self.GENERAL_FIELDS + self.OT_FIELDS +
        self.OT_EXTENSION_FIELDS + self.SHIPPING_FIELDS +
        self.ENTERPRISE_FIELDS)
    for field in all_fields:
      stage_dict[field] = getattr(stage, field)
    for field in self.MILESTONE_FIELDS:
      if stage.milestones is not None:
        stage_dict[field] = getattr(stage.milestones, field)
      else:
        stage_dict[field] = None

    # Set list fields as empty list if null.
    for field in self.FIELDS_DEFAULT_TO_LIST:
      if getattr(stage, field) is None:
        stage_dict[field] = []

    stage_dict['id'] = stage.key.integer_id()
    stage_dict['feature_id'] = stage.feature_id
    return stage_dict

  def _create_gate_for_stage(
      self, feature_id: int, stage_id: int, gate_type: int) -> None:
    """Create a Gate entity for the given stage type."""
    gate = Gate(feature_id=feature_id, stage_id=stage_id, gate_type=gate_type,
        state=Gate.PREPARING)
    gate.put()

  def _add_given_stage_vals(self,
      stage: Stage, kwargs: dict, fields: tuple[str]) -> None:
    """Add given fields of the stage entity."""
    for field in fields:
      if field in kwargs:
        setattr(stage, field, kwargs[field])

  def _update_stage_vals(self, stage: Stage, feature_type: int,
      kwargs: dict, create_gate: bool=False) -> None:
    """Check for relevant stage fields and update stage as needed."""
    if 'stage_type' in kwargs:
      stage.stage_type = kwargs['stage_type']
    s_type = stage.stage_type


    for field in self.GENERAL_FIELDS:
      if field in kwargs:
        setattr(stage, field, kwargs[field])

    # Update milestone fields.
    for field in self.MILESTONE_FIELDS:
      if field in kwargs:
        if stage.milestones is None:
          stage.milestones = MilestoneSet()
        setattr(stage.milestones, field, kwargs['field'])
    
    # Keep the gate type that might need to be created for the stage type.
    gate_type: int | None = None
    # Update type-specific fields.
    if s_type == core_enums.STAGE_TYPES_DEV_TRIAL[feature_type]:
      gate_type = core_enums.GATE_PROTOTYPE

    if s_type == core_enums.STAGE_TYPES_ORIGIN_TRIAL[feature_type]:
      self._add_given_stage_vals(stage, kwargs, self.OT_FIELDS)
      gate_type = core_enums.GATE_ORIGIN_TRIAL

    if s_type == core_enums.STAGE_TYPES_EXTEND_ORIGIN_TRIAL[feature_type]:
      self._add_given_stage_vals(stage, kwargs, self.OT_EXTENSION_FIELDS)
      gate_type = core_enums.GATE_EXTEND_ORIGIN_TRIAL

    if s_type == core_enums.STAGE_TYPES_SHIPPING[feature_type]:
      self._add_given_stage_vals(stage, kwargs, self.SHIPPING_FIELDS)
      gate_type = core_enums.GATE_SHIP

    stage.put()

    # If we should create a gate and this is a stage that requires a gate,
    # create it.
    if create_gate and gate_type is not None:
      self._create_gate_for_stage(
          stage.feature_id, stage.key.integer_id(), gate_type)


  def do_get(self, **kwargs):
    """Return a specified stage based on the given ID."""
    stage_id = kwargs.get('stage_id', None)

    if stage_id is None:
      self.abort(404, msg='No stage specified.')
    
    stage: Stage | None = Stage.get_by_id(stage_id)
    if stage is None:
      self.abort(404, msg=f'Stage {stage_id} not found')

    return self._stage_to_json_dict(stage)

  def do_post(self, **kwargs):
    """Create a new stage."""
    feature_id = kwargs.get('feature_id', None)
    if feature_id is None:
      self.abort(404, msg='No feature specified.')

    feature: FeatureEntry | None = FeatureEntry.get_by_id(feature_id)
    if feature is None:
      self.abort(404, msg=f'Feature {feature_id} not found')

    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    if 'stage_type' not in kwargs:
      self.abort(404, msg='Stage type not specified.')

    # Create the stage.
    stage = Stage(feature_id=feature_id)
    # Add the specified field values to the stage. Create a gate if needed.
    self._update_stage_vals(
        stage, feature.feature_type, kwargs, create_gate=True)

    # Return  the newly created stage ID.
    return {'message': 'Stage created.', 'stage_id': stage.key.integer_id()}
  
  def do_patch(self, **kwargs):
    """Update an existing stage based on the stage ID."""
    stage_id = kwargs.get('stage_id', None)

    if stage_id is None:
      self.abort(404, msg='No stage specified.')

    stage: Stage | None = Stage.get_by_id(stage_id)
    if stage is None:
      self.abort(404, msg=f'Stage {stage_id} not found')

    feature: FeatureEntry | None = FeatureEntry.get_by_id(stage.feature_id)
    if feature is None:
      self.abort(404, msg=(f'Feature {stage.feature_id} not found '
          f'associated with stage {stage_id}'))
    feature_id = feature.key.integer_id()
    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    # The stage_type field should not be able to change.
    if 'stage_type' in kwargs:
      self.abort(404, msg='stage_type field cannot be mutated.')

    # Update specified fields. No need to create a gate for existing stage.
    self._update_stage_vals(
        stage, feature.feature_type, kwargs, create_gate=False)

    return {'message': 'Stage values updated.'}

  def do_delete(self, **kwargs):
    """Delete an existing stage."""
    stage_id = kwargs.get('stage_id', None)
    if stage_id is None:
      self.abort(404, msg='No stage specified.')
    
    stage: Stage | None = Stage.get_by_id(stage_id)
    if stage is None:
      self.abort(404, msg=f'Stage {stage_id} not found.')
    
    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, stage.feature_id)
    if redirect_resp:
      return redirect_resp
    
    stage.deleted = True
    stage.put()

    return {'message': 'Stage deleted.'}
