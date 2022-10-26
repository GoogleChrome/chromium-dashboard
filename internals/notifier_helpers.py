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

from framework import cloud_tasks_helpers
from internals import core_enums
from internals import feature_helpers
from internals import review_models

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
    'feature': feature_helpers.feature_to_legacy_json(feature)
  }

  # Create task to email subscribers.
  cloud_tasks_helpers.enqueue_task('/tasks/email-subscribers', params)
