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

import re
from datetime import datetime, timezone
from typing import Any

from chromestatus_openapi.models import (
    PendingSuggestionsCountResponse,
    SummarySuggestionListResponse,
    SummarySuggestionResponse,
)
from google.cloud import ndb

from api import converters
from framework import basehandlers, permissions
from internals import core_enums
from internals.core_models import (
    FeatureEntry,
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)


def strip_markdown_hover_snippet(text: str | None, max_len: int = 150) -> str:
    """Strips markdown formatting and collapses whitespace for plain-text hover previews."""
    if not text:
        return ''
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    cleaned = re.sub(r'[*_`#]', '', cleaned)
    cleaned = ' '.join(cleaned.split())
    if len(cleaned) > max_len:
        return cleaned[: max_len - 3] + '...'
    return cleaned


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


class PendingSuggestionsCountAPI(basehandlers.APIHandler):
    """API handler for fetching total count of pending summary suggestions (GET /api/v0/summary-suggestions/pending-count)."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Returns total count of pending AI summary suggestions in review queue."""
        user = self.get_current_user()
        if not user or not permissions.can_edit_any_feature(user):
            self.abort(
                403,
                msg='User does not have permission to view pending suggestions queue',
            )

        count = FeatureSummarySuggestion.query(
            FeatureSummarySuggestion.status
            == core_enums.SummarySuggestionStatus.PENDING.value
        ).count()

        return PendingSuggestionsCountResponse.from_dict(
            {'count': count}
        ).to_dict()


class PendingSuggestionsQueueAPI(basehandlers.APIHandler):
    """API handler for fetching paginated pending summary suggestions (GET /api/v0/summary-suggestions/pending)."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Returns cursor-paginated list of pending AI summary suggestions in review queue."""
        user = self.get_current_user()
        if not user or not permissions.can_edit_any_feature(user):
            self.abort(
                403,
                msg='User does not have permission to view pending suggestions queue',
            )

        # 1. Parse pagination query parameters.
        limit_param = self.request.args.get('limit', '25')
        try:
            limit = int(limit_param)
            if limit < 1 or limit > 100:
                self.abort(400, msg='Limit must be between 1 and 100')
        except (ValueError, TypeError):
            self.abort(400, msg='Limit must be an integer')

        cursor_str = self.request.args.get('cursor', None)
        start_cursor = None
        if cursor_str:
            try:
                start_cursor = ndb.Cursor(urlsafe=cursor_str.encode('utf-8'))
            except Exception:
                self.abort(400, msg='Invalid cursor parameter')

        # 2. Query pending summary suggestions with cursor pagination.
        query = FeatureSummarySuggestion.query(
            FeatureSummarySuggestion.status
            == core_enums.SummarySuggestionStatus.PENDING.value
        ).order(-FeatureSummarySuggestion.created)

        suggestions, next_cursor, more = query.fetch_page(
            limit, start_cursor=start_cursor
        )
        total_count = query.count()

        has_more = len(suggestions) == limit and more
        next_cursor_str = (
            next_cursor.urlsafe().decode('utf-8')
            if (has_more and next_cursor)
            else None
        )

        # 3. Batch lookup parent FeatureEntries to attach feature metadata.
        feature_keys = [ndb.Key(FeatureEntry, s.key.id()) for s in suggestions]
        features = ndb.get_multi(feature_keys)
        feature_map = {f.key.id(): f for f in features if f}

        # 4. Serialize suggestion dicts and attach hover snippets.
        suggestion_dicts = []
        for s in suggestions:
            feature_id = s.key.id()
            fe = feature_map.get(feature_id)
            d = converters.feature_summary_suggestion_to_dict(s)
            d['feature_id'] = feature_id
            d['feature_name'] = fe.name if fe else 'Unknown Feature'
            d['hover_snippet'] = strip_markdown_hover_snippet(
                s.suggested_summary
            )
            suggestion_dicts.append(d)

        payload = {
            'suggestions': suggestion_dicts,
            'next_cursor': next_cursor_str,
            'total_count': total_count,
        }
        return SummarySuggestionListResponse.from_dict(payload).to_dict()
