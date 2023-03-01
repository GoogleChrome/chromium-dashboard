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

from typing import Any, TYPE_CHECKING
from api import converters
from framework import cloud_tasks_helpers, users
from internals import core_enums, approval_defs, core_models
from internals.review_models import Gate, Amendment, Activity, Vote

if TYPE_CHECKING:
  from internals.core_models import FeatureEntry

def _get_changes_as_amendments(
    changed_fields: list[tuple[str, Any, Any]]) -> list[Amendment]:
  """Convert list of field changes to Amendment entities."""
  # Diff values to see what properties have changed.
  amendments = []
  for field, old_val, new_val in changed_fields:
    if new_val != old_val:
      # Don't log if the old value was null and now it's falsey.
      if old_val is None and not bool(new_val):
        continue
      amendments.append(
          Amendment(field_name=field,
          old_value=str(old_val), new_value=str(new_val)))
  return amendments

def notify_feature_subscribers_of_changes(fe: 'FeatureEntry',
    amendments: list[Amendment]) -> None:
  """Async notifies subscribers of new features and property changes to
      features by posting to a task queue.
  """
  changed_props = [{
      'prop_name': a.field_name,
      'old_val': core_enums.convert_enum_int_to_string(
          a.field_name, a.old_value),
      'new_val': core_enums.convert_enum_int_to_string(
          a.field_name, a.new_value)
    } for a in amendments]

  params = {
    'changes': changed_props,
    # Subscribers are only notified on feature update.
    'is_update': True,
    'feature': converters.feature_entry_to_json_verbose(fe)
  }

  # Create task to email subscribers.
  cloud_tasks_helpers.enqueue_task('/tasks/email-subscribers', params)

def notify_subscribers_and_save_amendments(fe: 'FeatureEntry',
    changed_fields: list[tuple[str, Any, Any]], notify: bool=True) -> None:
  """Notify subscribers of changes to FeatureEntry and save amendments."""
  amendments = _get_changes_as_amendments(changed_fields)

  if len(amendments) > 0:
    user = users.get_current_user()
    email = user.email() if user else None
    activity = Activity(feature_id=fe.key.integer_id(),
        author=email, content='')
    activity.amendments = amendments
    activity.put()

  if notify:
    notify_feature_subscribers_of_changes(fe, amendments)


def notify_approvers_of_reviews(fe: 'FeatureEntry', gate: Gate) -> None:
  """Notify approvers of a review requested from a Gate."""
  gate_url = 'https://chromestatus.com/feature/%s?gate=%s' % (
    gate.feature_id, gate.key.integer_id())
  changed_props = {
      'prop_name': 'Review status change in %s' % (gate_url),
      'old_val': 'na',
      'new_val': 'review_requested',
  }

  params = {
    'changes': [changed_props],
    'gate_type': gate.gate_type,
    'feature': converters.feature_entry_to_json_verbose(fe)
  }

  # Create task to email subscribers.
  cloud_tasks_helpers.enqueue_task('/tasks/email-reviewers', params)


def notify_subscribers_of_vote_changes(fe: 'FeatureEntry', gate: Gate,
    email: str, new_state: int, old_state: int) -> None:
  """Notify subscribers of a vote change and save amendments."""
  stage = core_models.Stage.get_by_id(gate.stage_id)
  stage_enum = core_enums.INTENT_STAGES_BY_STAGE_TYPE.get(
    stage.stage_type, core_enums.INTENT_NONE)
  stage_name = core_enums.INTENT_STAGES[stage_enum]
  state_name = Vote.VOTE_VALUES[new_state]

  appr_def = approval_defs.APPROVAL_FIELDS_BY_ID[gate.gate_type]
  gate_name = appr_def.name

  acitivity_content = '%s set review status for stage: %s, gate: %s to %s.' % (
      email, stage_name, gate_name, state_name)
  gate_id = gate.key.integer_id()
  activity = Activity(feature_id=fe.key.integer_id(), gate_id=gate_id,
                      author=email, content=acitivity_content)
  activity.put()

  old_state_name = Vote.VOTE_VALUES.get(old_state, Vote.VOTE_VALUES[Vote.NA])
  gate_url = 'https://chromestatus.com/feature/%s?gate=%s' % (
    gate.feature_id, gate_id)
  changed_props = {
      'prop_name': '%s set review status in %s' % (email, gate_url),
      'old_val': old_state_name,
      'new_val': state_name,
  }

  params = {
    'changes': [changed_props],
    # Subscribers are only notified on feature update.
    'is_update': True,
    'feature': converters.feature_entry_to_json_verbose(fe)
  }

  # Create task to email subscribers.
  cloud_tasks_helpers.enqueue_task('/tasks/email-subscribers', params)
