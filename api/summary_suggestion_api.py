# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

"""API handler for AI summary suggestions (GET and PATCH /api/v0/summary-suggestions/<int:feature_id>)."""

from datetime import datetime, timezone
from typing import Any

from chromestatus_openapi.models import SummarySuggestionResponse
from google.cloud import ndb

from api import converters
from framework import basehandlers, permissions
from internals import core_enums
from internals.core_models import (
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)


class SummarySuggestionAPI(basehandlers.APIHandler):
    """API handler for AI summary suggestions (GET and PATCH /api/v0/summary-suggestions/<int:feature_id>)."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Fetches an AI summary suggestion, progress steps timeline, and access level.

        Returns:
            JSON response conforming to SummarySuggestionResponse schema.
        """
        # 1. Retrieve feature and check view permissions (handles feature_id extraction, 404 & 403 aborts).
        feature = self.get_specified_feature(**kwargs)
        if feature.deleted:
            self.abort(404, msg='Feature not found')
        feature_id = feature.key.id()

        # 2. Retrieve suggestion entity and execution progress steps.
        suggestion = FeatureSummarySuggestion.get_by_id(feature_id)
        if not suggestion:
            self.abort(404, msg='Summary suggestion not found')

        ancestor_key = ndb.Key(FeatureSummarySuggestion, feature_id)
        steps = (
            FeatureSummaryProgressStep.query(ancestor=ancestor_key)
            .order(-FeatureSummaryProgressStep.start_timestamp)
            .fetch()
        )

        # 3. Determine editorial access level for authenticated user.
        user = self.get_current_user()
        can_edit = permissions.can_edit_feature(user, feature)
        access_level = converters.SUMMARY_SUGGESTION_ACCESS_LEVEL_TO_API[
            can_edit
        ].value

        # 4. Build and return OpenAPI-compliant dictionary response.
        payload = {
            'suggestion': converters.feature_summary_suggestion_to_dict(
                suggestion
            ),
            'progress_steps': [
                converters.summary_progress_step_to_dict(s) for s in steps
            ],
            'access_level': access_level,
        }
        return SummarySuggestionResponse.from_dict(payload).to_dict()

    def do_patch(self, **kwargs: Any) -> dict[str, Any]:
        """Updates an AI summary suggestion with OCC version token enforcement.

        Returns:
            JSON response conforming to SummarySuggestionResponse schema.
        """
        # 1. Retrieve feature and check edit permissions (BOLA authorization).
        feature = self.get_specified_feature(**kwargs)
        if feature.deleted:
            self.abort(404, msg='Feature not found')

        user = self.get_current_user()
        if not permissions.can_edit_feature(user, feature):
            self.abort(
                403, msg='User does not have edit permissions for this feature'
            )
        feature_id = feature.key.id()

        # 3. Retrieve target summary suggestion entity.
        suggestion = FeatureSummarySuggestion.get_by_id(feature_id)
        if not suggestion:
            self.abort(404, msg='Summary suggestion not found')

        # 4. Validate OCC version token & request parameters using BaseHandler helpers.
        request_body = self.get_json_param_dict()
        request_version_token = self.get_int_param(
            'version_token', required=True
        )
        if request_version_token < 1:
            self.abort(400, msg='version_token must be a positive integer')

        if suggestion.version_token != request_version_token:
            self.abort(
                409,
                msg=(
                    'Conflict: Modified by another process. Please refresh'
                    ' and try again.'
                ),
            )

        # 5. Apply requested mutations (status enum, suggested summary text).
        if 'status' in request_body:
            raw_status = request_body['status']
            try:
                status_enum = core_enums.SummarySuggestionStatus(raw_status)
            except (ValueError, TypeError):
                self.abort(400, msg=f'Invalid status value: {raw_status}')
            suggestion.status = status_enum.value

        if 'suggested_summary' in request_body:
            suggestion.suggested_summary = request_body['suggested_summary']

        # 6. Increment OCC version token, update timestamp, and save entity.
        suggestion.version_token += 1
        suggestion.updated = datetime.now(timezone.utc)
        suggestion.put()

        # 7. Fetch progress steps timeline and return updated response.
        ancestor_key = ndb.Key(FeatureSummarySuggestion, feature_id)
        steps = (
            FeatureSummaryProgressStep.query(ancestor=ancestor_key)
            .order(-FeatureSummaryProgressStep.start_timestamp)
            .fetch()
        )

        payload = {
            'suggestion': converters.feature_summary_suggestion_to_dict(
                suggestion
            ),
            'progress_steps': [
                converters.summary_progress_step_to_dict(s) for s in steps
            ],
            'access_level': converters.SUMMARY_SUGGESTION_ACCESS_LEVEL_TO_API[
                True
            ].value,
        }
        return SummarySuggestionResponse.from_dict(payload).to_dict()
