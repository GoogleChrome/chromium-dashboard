# Copyright 2025 Google Inc.
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

from datetime import datetime, timedelta
from framework import basehandlers
from framework import cloud_tasks_helpers
from framework import permissions
from internals import core_enums
from internals.core_models import FeatureEntry


class WPTCoverageAPI(basehandlers.EntitiesAPIHandler):
  """Accepts requests related to WPT AI coverage evaluations."""

  def do_post(self, **kwargs):
    """Enqueue a Cloud Task for generating a WPT coverage evaluation report."""
    feature_id = self.get_int_param('feature_id')
    feature = self.get_validated_entity(feature_id, FeatureEntry)

    # Validate the user has edit permissions.
    can_edit = permissions.can_edit_feature(
      self.get_current_user(), feature_id)
    if not can_edit:
      self.abort(403, f'User does not have dit access to feature {feature_id}')

    last_status_time = feature.ai_test_eval_status_timestamp
    one_hour = timedelta(hours=1)
    if (feature.ai_test_eval_run_status == core_enums.AITestEvaluationStatus.IN_PROGRESS
        and last_status_time
        # Assume that a request that is in progress for over an hour is hanging.
        and last_status_time + one_hour > datetime.now()):
      self.abort(
        409,
        'The WPT coverage evaluation pipeline is already running for this feature.')

    feature.ai_test_eval_run_status = core_enums.AITestEvaluationStatus.IN_PROGRESS.value
    feature.ai_test_eval_status_timestamp = datetime.now()
    feature.put()
    cloud_tasks_helpers.enqueue_task('/tasks/generate-wpt-coverage-evaluation',
                                     { 'feature_id': feature_id })

    return {'message': 'Task enqueued'}
