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

from typing import Any, Optional
from api import converters
from framework import cloud_tasks_helpers, rediscache, users
from internals import core_enums
from internals import review_models

def _get_changes_as_amendments(f) -> list[review_models.Amendment]:
  """Get all feature changes as Amendment entities."""
  # Diff values to see what properties have changed.
  amendments = []
  for prop_name in f._properties.keys():
    if prop_name in (
        'created_by', 'updated_by', 'updated', 'created'):
      continue
    new_val = getattr(f, prop_name, None)
    old_val = getattr(f, '_old_' + prop_name, None)
    if new_val != old_val:
      if (new_val == '' or new_val == False) and old_val is None:
        continue
      amendments.append(
          review_models.Amendment(field_name=prop_name,
          old_value=str(old_val), new_value=str(new_val)))
  return amendments

def notify_feature_subscribers_of_changes(feature,
    amendments: list[review_models.Amendment], is_update: bool) -> None:
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
    'is_update': is_update,
    # TODO(danielrsmith): Change converter function
    # after switch to using FeatureEntry here.
    'feature': converters.feature_to_legacy_json(feature)
  }

  # Create task to email subscribers.
  cloud_tasks_helpers.enqueue_task('/tasks/email-subscribers', params)

def notify_subscribers_and_save_amendments(fe, notify: bool=True) -> None:
  """Notify subscribers of changes to FeatureEntry and save amendments."""
  is_update = (fe.key is not None)
  amendments = _get_changes_as_amendments(fe)

  # Document changes as new Activity entity with amendments only if all true:
  # 1. This is an update to an existing feature.
  # 2. We used stash_values() to document what fields changed.
  # 3. One or more fields were changed.
  should_write_activity = (is_update and hasattr(fe, '_values_stashed')
      and len(amendments) > 0)

  if should_write_activity:
    user = users.get_current_user()
    email = user.email() if user else None
    activity = review_models.Activity(feature_id=fe.key.integer_id(),
        author=email, content='')
    activity.amendments = amendments
    activity.put()

  if notify:
    notify_feature_subscribers_of_changes(fe, amendments, is_update)
