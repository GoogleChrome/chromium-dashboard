# -*- coding: utf-8 -*-
# Copyright 2026 Google Inc.
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

"""REST API handlers for AI-assisted release notes summary reviews.

This module provides endpoints for generating, fetching, applying, and bypassing
the AI-generated feature summaries and documentation link suggestions.
"""

import datetime
from typing import Any

from google.cloud import ndb  # type: ignore

from framework import basehandlers, cloud_tasks_helpers, permissions
from internals import core_enums
from internals.core_models import FeatureEntry, FeatureSummarySuggestion
from api import converters
from internals.review_models import Activity


class SummarySuggestionAPI(basehandlers.EntitiesAPIHandler):
    """API handler to retrieve the draft AI summary suggestion."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch the current AI summary suggestion and baseline details for a feature."""
        feature_id = kwargs.get('feature_id')
        if not feature_id:
            self.abort(400, msg='Feature ID is required.')

        feature = FeatureEntry.get_by_id(feature_id)
        if not feature:
            self.abort(404, msg='Feature not found.')

        user = self.get_current_user()
        if not permissions.can_view_feature(user, feature):
            self.abort(403, msg='Unauthorized to view feature.')

        suggestion = FeatureSummarySuggestion.get_by_id(feature_id)
        if not suggestion:
            # Return a default none state response conforming to the schema
            return {
                'status': core_enums.SummarySuggestionStatus.NONE.value,
                'suggested_summary': None,
                'suggested_doc_links': [],
                'baseline_status': None,
                'baseline_newly_date': None,
                'baseline_widely_date': None,
                'original_baseline_status': 'none',
                'original_baseline_newly_date': None,
                'original_baseline_widely_date': None,
                'status_timestamp': None,
                'last_generation_attempt': None,
                'version_token': 1,
                'summary_provenance': None,
                'doc_links_provenance': None,
                'suggested_format': 'markdown',
                'original_summary_format': None,
            }

        return {
            'suggested_summary': suggestion.suggested_summary,
            'suggested_doc_links': suggestion.suggested_doc_links or [],
            'baseline_status': suggestion.baseline_status,
            'baseline_newly_date': (
                suggestion.baseline_newly_date.isoformat()
                if suggestion.baseline_newly_date
                else None
            ),
            'baseline_widely_date': (
                suggestion.baseline_widely_date.isoformat()
                if suggestion.baseline_widely_date
                else None
            ),
            'original_baseline_status': suggestion.original_baseline_status or 'none',
            'original_baseline_newly_date': (
                suggestion.original_baseline_newly_date.isoformat()
                if suggestion.original_baseline_newly_date
                else None
            ),
            'original_baseline_widely_date': (
                suggestion.original_baseline_widely_date.isoformat()
                if suggestion.original_baseline_widely_date
                else None
            ),
            'status': suggestion.status,
            'status_timestamp': (
                suggestion.status_timestamp.isoformat()
                if suggestion.status_timestamp
                else None
            ),
            'last_generation_attempt': (
                suggestion.last_generation_attempt.isoformat()
                if suggestion.last_generation_attempt
                else None
            ),
            'version_token': suggestion.version_token or 1,
            'summary_provenance': suggestion.summary_provenance,
            'doc_links_provenance': suggestion.doc_links_provenance,
            'suggested_format': suggestion.suggested_format or 'markdown',
            'original_summary_format': suggestion.original_summary_format,
        }

    def do_patch(self, **kwargs: Any) -> dict[str, Any]:
        """RESTful state update for AI release notes suggestion.

        Handles:
        - COMPLETE -> APPLIED (accepts/tweaks summary text and selects links).
        - COMPLETE -> DISCARDED (discard suggestion tombstone).
        - DISCARDED -> COMPLETE (restore suggestion).
        Enforces Optimistic Concurrency Control using version_token.
        """
        feature_id = kwargs.get('feature_id')
        if not feature_id:
            self.abort(400, msg='Feature ID is required.')

        user = self.get_current_user()
        if not user:
            self.abort(401, msg='Sign in required.')
        if not (
            permissions.can_edit_feature(user, feature_id)
            or permissions.can_review_release_notes(user)
        ):
            self.abort(403, msg='Unauthorized.')

        # Read JSON body params
        params = self.get_json_param_dict()
        new_status_str = params.get('status')
        version_token = params.get('version_token')

        if not new_status_str:
            self.abort(400, msg='New status is required.')
        if version_token is None:
            self.abort(400, msg='version_token is required.')

        try:
            target_status = core_enums.SummarySuggestionStatus(new_status_str)
        except ValueError:
            self.abort(400, msg=f'Invalid target status: {new_status_str}')

        @ndb.transactional()
        def patch_suggestion_tx() -> tuple[
            bool, str | None, dict[str, Any] | None
        ]:
            feature = FeatureEntry.get_by_id(feature_id)
            suggestion = FeatureSummarySuggestion.get_by_id(feature_id)
            if not feature or not suggestion:
                return False, 'Feature or AI suggestion not found.', None

            # Concurrency check (stale write prevention)
            if suggestion.version_token != version_token:
                return (
                    False,
                    'Conflict: The suggestion has been modified by another request.',
                    None,
                )

            # Check if request is a DevRel bypass during the 7-day grace period
            is_owner = user.email() in (feature.owner_emails or [])
            is_editor = user.email() in (feature.editor_emails or [])
            is_creator = user.email() == feature.creator_email
            is_privileged_owner = is_owner or is_editor or is_creator

            is_within_grace = False
            if current_status := suggestion.status:
                if (
                    current_status
                    == core_enums.SummarySuggestionStatus.COMPLETE.value
                    and suggestion.status_timestamp
                ):
                    grace_limit = (
                        suggestion.status_timestamp + datetime.timedelta(days=7)
                    )
                    is_within_grace = datetime.datetime.utcnow() < grace_limit

            is_bypass = is_within_grace and not is_privileged_owner
            bypass_justification = params.get('bypass_justification')

            if is_bypass and not bypass_justification:
                return (
                    False,
                    'Bypass justification is required during the 7-day grace period.',
                    None,
                )

            # Validate State Transitions
            current_status = suggestion.status
            if target_status == core_enums.SummarySuggestionStatus.APPLIED:
                if (
                    current_status
                    != core_enums.SummarySuggestionStatus.COMPLETE.value
                ):
                    return (
                        False,
                        f'Cannot transition from {current_status} to applied.',
                        None,
                    )

                # Apply: read approved values from payload
                approved_summary = params.get('suggested_summary')
                approved_links = params.get('suggested_doc_links')

                if not approved_summary:
                    return (
                        False,
                        'suggested_summary is required when status is applied.',
                        None,
                    )
                if approved_links is None:
                    return (
                        False,
                        'suggested_doc_links list is required when status is applied.',
                        None,
                    )

                # Save backup values of FeatureEntry before overwriting
                if suggestion.original_summary is None:
                    suggestion.original_summary = feature.summary
                    suggestion.original_doc_links = feature.doc_links or []
                    # Backup original markdown format
                    original_had_md = 'summary' in (
                        feature.markdown_fields or []
                    )
                    suggestion.original_summary_format = (
                        'markdown' if original_had_md else 'plain'
                    )

                # Write-back to FeatureEntry
                feature.summary = approved_summary
                feature.doc_links = list(set(approved_links))

                # Apply suggestion format (default to markdown)
                sug_format = suggestion.suggested_format or 'markdown'
                if sug_format == 'markdown':
                    if 'summary' not in (feature.markdown_fields or []):
                        if feature.markdown_fields is None:
                            feature.markdown_fields = []
                        feature.markdown_fields.append('summary')
                else:
                    if 'summary' in (feature.markdown_fields or []):
                        feature.markdown_fields.remove('summary')

                feature.put()

                # Update provenance records
                now_str = datetime.datetime.utcnow().isoformat()

                # Summary Provenance
                is_summary_modified = (
                    approved_summary != suggestion.suggested_summary
                )
                suggestion.summary_provenance = {
                    'original_author': 'SYSTEM',
                    'modified_by': user.email()
                    if is_summary_modified
                    else None,
                    'reviewed_by': user.email(),
                    'state': 'modified' if is_summary_modified else 'original',
                    'timestamp': now_str,
                }
                # Save the final text as the new suggested_summary
                suggestion.suggested_summary = approved_summary

                # Doc Links Provenance
                is_links_modified = set(approved_links) != set(
                    suggestion.suggested_doc_links or []
                )
                suggestion.doc_links_provenance = {
                    'original_author': 'SYSTEM',
                    'modified_by': user.email() if is_links_modified else None,
                    'reviewed_by': user.email(),
                    'state': 'modified' if is_links_modified else 'original',
                    'timestamp': now_str,
                }
                suggestion.suggested_doc_links = approved_links

                # Update approved baseline status and dates
                approved_baseline_status = params.get('baseline_status', suggestion.baseline_status)
                approved_baseline_newly = params.get('baseline_newly_date')
                approved_baseline_widely = params.get('baseline_widely_date')

                def parse_date(date_str):
                    if not date_str:
                        return None
                    try:
                        if isinstance(date_str, datetime.date):
                            return date_str
                        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        return None

                suggestion.baseline_status = approved_baseline_status
                if approved_baseline_newly is not None:
                    suggestion.baseline_newly_date = parse_date(approved_baseline_newly)
                if approved_baseline_widely is not None:
                    suggestion.baseline_widely_date = parse_date(approved_baseline_widely)

                # First-time apply: backup baseline status to none if no prior backup exists
                if suggestion.original_baseline_status is None:
                    suggestion.original_baseline_status = 'none'

            elif target_status == core_enums.SummarySuggestionStatus.DISCARDED:
                if current_status not in [
                    core_enums.SummarySuggestionStatus.COMPLETE.value,
                    core_enums.SummarySuggestionStatus.BYPASSED.value,
                ]:
                    return (
                        False,
                        f'Cannot transition from {current_status} to discarded.',
                        None,
                    )

                now_str = datetime.datetime.utcnow().isoformat()
                if suggestion.summary_provenance:
                    suggestion.summary_provenance['reviewed_by'] = user.email()
                    suggestion.summary_provenance['timestamp'] = now_str
                if suggestion.doc_links_provenance:
                    suggestion.doc_links_provenance['reviewed_by'] = (
                        user.email()
                    )
                    suggestion.doc_links_provenance['timestamp'] = now_str

            elif target_status == core_enums.SummarySuggestionStatus.COMPLETE:
                # Restore: transition back to COMPLETE from DISCARDED or BYPASSED
                if current_status not in [
                    core_enums.SummarySuggestionStatus.DISCARDED.value,
                    core_enums.SummarySuggestionStatus.BYPASSED.value,
                ]:
                    return (
                        False,
                        f'Cannot restore status to complete from {current_status}.',
                        None,
                    )

                # Revert: write back backup values to FeatureEntry
                if suggestion.original_summary is not None:
                    feature.summary = suggestion.original_summary
                    feature.doc_links = suggestion.original_doc_links or []

                    # Restore original markdown format
                    if suggestion.original_summary_format == 'markdown':
                        if 'summary' not in (feature.markdown_fields or []):
                            if feature.markdown_fields is None:
                                feature.markdown_fields = []
                            feature.markdown_fields.append('summary')
                    else:
                        if 'summary' in (feature.markdown_fields or []):
                            feature.markdown_fields.remove('summary')

                    feature.put()

                    # Clear backups
                    suggestion.original_summary = None
                    suggestion.original_doc_links = []
                    suggestion.original_summary_format = None

                # Revert baseline status and dates
                if suggestion.original_baseline_status is not None:
                    suggestion.baseline_status = suggestion.original_baseline_status
                    suggestion.baseline_newly_date = suggestion.original_baseline_newly_date
                    suggestion.baseline_widely_date = suggestion.original_baseline_widely_date

                    # Clear backups
                    suggestion.original_baseline_status = None
                    suggestion.original_baseline_newly_date = None
                    suggestion.original_baseline_widely_date = None

            else:
                return (
                    False,
                    f'Transitioning to {target_status.value} is not allowed via REST PATCH.',
                    None,
                )

            # Increment concurrency version token
            if is_bypass:
                suggestion.status = (
                    core_enums.SummarySuggestionStatus.BYPASSED.value
                )
            else:
                suggestion.status = target_status.value
            suggestion.version_token += 1
            suggestion.put()

            # Record Activity log (A)
            if is_bypass:
                log_type = Activity.BYPASS_APPLIED
                content = (
                    f'AI suggestion status transitioned to bypassed '
                    f'by DevRel bypass. Justification: {bypass_justification}'
                )
            else:
                log_type = Activity.USER_CHANGE
                content = f'AI suggestion status transitioned to {target_status.value}.'

            activity = Activity(
                feature_id=feature_id,
                log_type=log_type,
                author=user.email(),
                content=content,
            )
            activity.put()

            return (
                True,
                None,
                {
                    'message': 'AI suggestion status updated successfully.',
                    'version_token': suggestion.version_token,
                },
            )

        success, error_msg, response_data = patch_suggestion_tx()
        if not success:
            if 'Conflict' in error_msg:
                self.abort(409, msg=error_msg)
            if 'justification is required' in error_msg:
                self.abort(403, msg=error_msg)
            self.abort(400, msg=error_msg)

        return response_data


class SummarySuggestionGenerateAPI(basehandlers.EntitiesAPIHandler):
    """API handler to trigger asynchronous AI summary generation."""

    def do_post(self, **kwargs: Any) -> dict[str, Any]:
        """Enqueue a background task to generate the AI summary for a feature."""
        feature_id = kwargs.get('feature_id')
        if not feature_id:
            self.abort(400, msg='Feature ID is required.')

        user = self.get_current_user()
        if not user:
            self.abort(401, msg='Sign in required.')
        if not (
            permissions.can_edit_feature(user, feature_id)
            or permissions.can_review_release_notes(user)
        ):
            self.abort(403, msg='Unauthorized.')

        # NDB transactional block for safety, rate limiting, and status update
        @ndb.transactional()
        def start_generation_tx() -> tuple[FeatureEntry | None, str | None]:
            feature = FeatureEntry.get_by_id(feature_id)
            if not feature:
                return None, 'Feature not found'

            suggestion = FeatureSummarySuggestion.get_by_id(feature_id)
            now = datetime.datetime.utcnow()

            if suggestion:
                # If generation is already in progress, rate limit it (15 mins timeout)
                if (
                    suggestion.status
                    == core_enums.SummarySuggestionStatus.IN_PROGRESS
                ):
                    if suggestion.status_timestamp:
                        time_since = now - suggestion.status_timestamp
                        if time_since < datetime.timedelta(minutes=15):
                            return (
                                None,
                                'AI summary generation is already in progress.',
                            )

                # Cooldown limit to prevent abuse if complete (30 mins cooldown)
                if (
                    suggestion.status
                    == core_enums.SummarySuggestionStatus.COMPLETE
                ):
                    if suggestion.status_timestamp:
                        time_since = now - suggestion.status_timestamp
                        if time_since < datetime.timedelta(minutes=30):
                            return (
                                None,
                                'Cooldown in progress. Try again in a few minutes.',
                            )
            else:
                suggestion = FeatureSummarySuggestion(
                    id=feature_id,
                    status=core_enums.SummarySuggestionStatus.NONE.value,
                )

            suggestion.status = (
                core_enums.SummarySuggestionStatus.IN_PROGRESS.value
            )
            suggestion.status_timestamp = now
            suggestion.last_generation_attempt = now
            suggestion.put()
            return feature, None

        feature, error_msg = start_generation_tx()
        if error_msg:
            self.abort(400, msg=error_msg)

        # Enqueue the Cloud Task to do the work asynchronously
        task_params = {
            'feature_id': feature_id,
            'updated_time': (
                feature.updated.timestamp()
                if feature and feature.updated
                else 0
            ),
        }
        cloud_tasks_helpers.enqueue_task(
            '/tasks/generate-summary',
            task_params,
        )

        return {'message': 'AI summary generation task accepted and queued.'}


class PendingReviewsCountAPI(basehandlers.EntitiesAPIHandler):
    """API handler to fetch count of pending AI reviews."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieve the count of all AI suggestions in COMPLETE status."""
        user = self.get_current_user()
        if not user or not permissions.can_review_release_notes(user):
            self.abort(403, msg='Unauthorized.')

        count = FeatureSummarySuggestion.query(
            FeatureSummarySuggestion.status
            == core_enums.SummarySuggestionStatus.COMPLETE
        ).count()
        return {'count': count}


class PendingReviewsAPI(basehandlers.EntitiesAPIHandler):
    """API handler to fetch the list of features with pending AI reviews."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieve the list of features that have suggestions in COMPLETE status."""
        user = self.get_current_user()
        if not user or not permissions.can_review_release_notes(user):
            self.abort(403, msg='Unauthorized.')

        # 1. Query suggestions in COMPLETE status
        suggestions = FeatureSummarySuggestion.query(
            FeatureSummarySuggestion.status
            == core_enums.SummarySuggestionStatus.COMPLETE
        ).fetch()

        if not suggestions:
            return {'features': [], 'total_count': 0}

        # 2. Get the feature IDs
        feature_ids = [s.key.id() for s in suggestions]

        # 3. Load all feature entries in a batch get
        keys = [ndb.Key(FeatureEntry, fid) for fid in feature_ids]
        features = ndb.get_multi(keys)

        # 4. Serialize features to JSON verbose
        serialized_features = [
            converters.feature_entry_to_json_verbose(f)
            for f in features
            if f is not None
        ]

        return {
            'features': serialized_features,
            'total_count': len(serialized_features)
        }
