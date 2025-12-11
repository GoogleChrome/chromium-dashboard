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

import flask
from datetime import datetime, timedelta
from framework import basehandlers
from framework import cloud_tasks_helpers
from framework import permissions
from internals import core_enums
from internals.core_models import FeatureEntry

# 29 minute cooldown for regenerating the evaluation report.
# 29 minutes instead of 30 so we don't block the UI sending a request
# accidentally.
COOLDOWN_THRESHOLD = timedelta(minutes=29)

# 59 minute timeout to allow retrying if the process hangs.
HANGING_TIMEOUT_THRESHOLD = timedelta(minutes=59)

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

    request_in_progress = (
      feature.ai_test_eval_run_status == core_enums.AITestEvaluationStatus.IN_PROGRESS
      and last_status_time
      # Assume that a request that is in progress for over an hour is hanging.
      and last_status_time + HANGING_TIMEOUT_THRESHOLD > datetime.now())

    on_cooldown = (
      feature.ai_test_eval_run_status == core_enums.AITestEvaluationStatus.COMPLETE
      and last_status_time
      and last_status_time + COOLDOWN_THRESHOLD > datetime.now())

    if request_in_progress or on_cooldown:
      msg = (
        'The WPT coverage evaluation pipeline is already running for this feature.'
        if request_in_progress
        else 'Requests to the pipeline are on cooldown for this feature.')
      retry_after = ((last_status_time + HANGING_TIMEOUT_THRESHOLD) - datetime.now()
                     if request_in_progress
                     else (last_status_time + COOLDOWN_THRESHOLD) - datetime.now())
      # Safety check: Ensure we never send a negative Retry-After
      # (which can happen if the condition evaluated true milliseconds ago but time passed)
      retry_after_seconds = int(max(0, retry_after.total_seconds()))
      error_resp = {'error': msg}
      # TODO(#5688): Create a BaseHandler.abort_with_headers helper method
      # and refactor these lines to use that new method.
      resp = flask.make_response(flask.jsonify(error_resp), 409)
      resp.headers['Retry-After'] = retry_after_seconds
      flask.abort(resp)

    feature.ai_test_eval_run_status = core_enums.AITestEvaluationStatus.IN_PROGRESS.value
    feature.ai_test_eval_status_timestamp = datetime.now()
    feature.put()
    cloud_tasks_helpers.enqueue_task('/tasks/generate-wpt-coverage-evaluation',
                                     { 'feature_id': feature_id })

    return {'message': 'Task enqueued'}
