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

from typing import Any
from api import converters
from framework import cloud_tasks_helpers, users
from internals import core_enums
from internals import review_models

def _get_changes_as_amendments(
    changed_fields: list[tuple[str, Any, Any]]) -> list[review_models.Amendment]:
  """Convert list of field changes to Amendment entities."""
  # Diff values to see what properties have changed.
  amendments = []
  for field, old_val, new_val in changed_fields:
    if new_val != old_val:
      if (new_val == '' or new_val == False) and old_val is None:
        continue
      amendments.append(
          review_models.Amendment(field_name=field,
          old_value=str(old_val), new_value=str(new_val)))
  return amendments

def notify_feature_subscribers_of_changes(fe,
    amendments: list[review_models.Amendment]) -> None:
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

def notify_subscribers_and_save_amendments(fe,
    changed_fields: list[tuple[str, Any, Any]], notify: bool=True) -> None:
  """Notify subscribers of changes to FeatureEntry and save amendments."""
  amendments = _get_changes_as_amendments(changed_fields)

  if len(amendments) > 0:
    user = users.get_current_user()
    email = user.email() if user else None
    activity = review_models.Activity(feature_id=fe.key.integer_id(),
        author=email, content='')
    activity.amendments = amendments
    activity.put()

  if notify:
    notify_feature_subscribers_of_changes(fe, amendments)
