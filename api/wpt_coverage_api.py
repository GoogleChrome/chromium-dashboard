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

"""API endpoints for triggering and managing AI-generated WPT coverage analysis reports."""

from datetime import datetime, timedelta

from framework import basehandlers, cloud_tasks_helpers, permissions
from internals import core_enums
from internals.core_models import FeatureEntry

# 29 minute cooldown for regenerating the analysis report.
# 29 minutes instead of 30 so we don't block the UI sending a request
# accidentally.
COOLDOWN_THRESHOLD = timedelta(minutes=29)

# 59 minute timeout to allow retrying if the process hangs.
HANGING_TIMEOUT_THRESHOLD = timedelta(minutes=59)


class WPTCoverageAPI(basehandlers.EntitiesAPIHandler):
    """Accepts requests related to WPT AI coverage analyses."""

    def do_post(self, **kwargs):
        """Enqueue a Cloud Task for generating a WPT coverage analysis report."""
        feature_id = kwargs.get('feature_id')
        feature = self.get_validated_entity(feature_id, FeatureEntry)

        # Validate the user has edit permissions.
        can_edit = permissions.can_edit_feature(
            self.get_current_user(), feature_id
        )
        if not can_edit:
            self.abort(
                403, f'User does not have edit access to feature {feature_id}'
            )

        if not permissions.is_google_or_chromium_account(
            self.get_current_user()
        ):
            self.abort(
                403,
                'This feature is currently only available to Google or Chromium accounts.',  # noqa: E501
            )

        if feature.confidential:
            self.abort(
                400,
                (
                    'Confidential feature information cannot be used to '
                    'generate WTP coverage reports.'
                ),
            )

        last_status_time = feature.ai_test_eval_status_timestamp

        request_in_progress = (
            feature.ai_test_eval_run_status
            == core_enums.AITestEvaluationStatus.IN_PROGRESS  # noqa: E501
            and last_status_time
            # Assume that a request that is in progress for over an hour is hanging.
            and last_status_time + HANGING_TIMEOUT_THRESHOLD > datetime.now()
        )

        on_cooldown = (
            (
                feature.ai_test_eval_run_status
                == core_enums.AITestEvaluationStatus.COMPLETE  # noqa: E501
                or feature.ai_test_eval_run_status
                == core_enums.AITestEvaluationStatus.DELETED  # noqa: E501
            )
            and last_status_time
            and last_status_time + COOLDOWN_THRESHOLD > datetime.now()
        )

        if request_in_progress or on_cooldown:
            msg = (
                'The WPT coverage pipeline is already running for this feature.'
                if request_in_progress
                else 'Requests to the pipeline are on cooldown for this feature.'
            )
            retry_after = (
                (last_status_time + HANGING_TIMEOUT_THRESHOLD) - datetime.now()  # noqa: E501
                if request_in_progress
                else (last_status_time + COOLDOWN_THRESHOLD) - datetime.now()
            )  # noqa: E501
            # Safety check: Ensure we never send a negative Retry-After
            # (which can happen if the condition evaluated true milliseconds ago but time passed)  # noqa: E501
            retry_after_seconds = int(max(0, retry_after.total_seconds()))
            self.abort(
                409, msg, headers={'Retry-After': str(retry_after_seconds)}
            )

        feature.ai_test_eval_run_status = (
            core_enums.AITestEvaluationStatus.IN_PROGRESS.value
        )  # noqa: E501
        feature.ai_test_eval_status_timestamp = datetime.now()
        feature.put()
        include_explainer = self.get_bool_param('include_explainer', False)
        cloud_tasks_helpers.enqueue_task(
            '/tasks/generate-wpt-coverage-analysis',
            {'feature_id': feature_id, 'include_explainer': include_explainer},
        )  # noqa: E501

        return {'message': 'Task enqueued'}

    def do_delete(self, **kwargs):
        """Delete the generated WPT coverage analysis report."""
        feature_id = kwargs.get('feature_id')
        feature = self.get_validated_entity(feature_id, FeatureEntry)

        # Validate the user has edit permissions.
        can_edit = permissions.can_edit_feature(
            self.get_current_user(), feature_id
        )
        if not can_edit:
            self.abort(
                403, f'User does not have edit access to feature {feature_id}'
            )

        feature.ai_test_eval_report = None
        feature.ai_test_eval_run_status = (
            core_enums.AITestEvaluationStatus.DELETED.value
        )  # noqa: E501
        feature.put()

        return {'message': 'WPT coverage analysis report deleted.'}
