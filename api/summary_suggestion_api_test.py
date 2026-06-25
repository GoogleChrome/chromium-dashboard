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

"""Unit tests for api/summary_suggestion_api.py."""

import datetime
from datetime import date
from unittest import mock

import flask
import werkzeug.exceptions
from google.cloud import ndb  # type: ignore

import testing_config
from api import summary_suggestion_api
from internals import core_enums
from internals.core_models import (
    FeatureEntry,
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)
from internals.review_models import Activity

test_app = flask.Flask(__name__)


class SummarySuggestionAPITest(testing_config.CustomTestCase):
    """Tests for GET /features/{feature_id}/summary_suggestion."""

    def setUp(self):
        """Set up test environment and mock data."""
        testing_config.sign_in('viewer@example.com', 111)
        self.handler = summary_suggestion_api.SummarySuggestionAPI()
        self.feature = FeatureEntry(
            id=12345,
            name='Test Feature',
            summary='Technical description.',
            category=1,
        )
        self.feature.put()

    def tearDown(self):
        """Clean up datastore entities."""
        self.feature.key.delete()
        suggestion = FeatureSummarySuggestion.get_by_id(12345)
        if suggestion:
            suggestion.key.delete()
        # Clean up progress steps parented under feature 12345 to prevent test pollution
        steps = FeatureSummaryProgressStep.query(
            ancestor=ndb.Key(FeatureSummarySuggestion, 12345)
        ).fetch(keys_only=True)
        ndb.delete_multi(steps)

    @mock.patch('framework.permissions.can_view_feature')
    def test_get__default_none(self, mock_can_view):
        """Ensure requesting a suggestion when none exists returns a default NONE status."""
        mock_can_view.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion'
        ):
            response = self.handler.do_get(feature_id=12345)

        self.assertEqual(
            response,
            {
                'status': 'none',
                'status_message': None,
                'model_used': None,
                'progress_steps': [],
                'suggested_summary': None,
                'generation_rationale': None,
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
            },
        )

    @mock.patch('framework.permissions.can_view_feature')
    def test_get__success(self, mock_can_view):
        """Ensure requesting a suggestion returns the draft details if COMPLETE."""
        mock_can_view.return_value = True
        suggestion = FeatureSummarySuggestion(
            id=12345,
            suggested_summary='Simplified summary.',
            suggested_doc_links=['https://example.com/doc'],
            baseline_status=core_enums.BaselineStatus.LIMITED,
            status=core_enums.SummarySuggestionStatus.COMPLETE,
            status_message='Generation complete!',
            model_used='gemini-3.5-flash',
            status_timestamp=datetime.datetime(2026, 6, 1, 12, 0, 0),
            last_generation_attempt=datetime.datetime(2026, 6, 1, 11, 58, 0),
        )
        suggestion.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion'
        ):
            response = self.handler.do_get(feature_id=12345)

        self.assertEqual(response['status'], 'complete')
        self.assertEqual(response['status_message'], 'Generation complete!')
        self.assertEqual(response['model_used'], 'gemini-3.5-flash')
        self.assertEqual(response['progress_steps'], [])
        self.assertEqual(response['suggested_summary'], 'Simplified summary.')
        self.assertEqual(
            response['suggested_doc_links'], ['https://example.com/doc']
        )
        self.assertEqual(response['baseline_status'], 'limited')
        self.assertEqual(
            response['last_generation_attempt'], '2026-06-01T11:58:00Z'
        )
        self.assertIsNotNone(response['status_timestamp'])

    @mock.patch('framework.permissions.can_view_feature')
    def test_get__success_with_progress(self, mock_can_view):
        """Ensure requesting a suggestion returns progress steps correctly serialized."""
        mock_can_view.return_value = True
        suggestion = FeatureSummarySuggestion(
            id=12345,
            status=core_enums.SummarySuggestionStatus.IN_PROGRESS,
            status_message='Executing AI generation loop...',
            status_timestamp=datetime.datetime(2026, 6, 1, 12, 0, 0),
        )
        suggestion.put()

        # Insert progress steps
        FeatureSummaryProgressStep.update_step(
            12345, 'start', 'Initializing...', 'SUCCESS'
        )
        FeatureSummaryProgressStep.update_step(
            12345, 'tool_1', 'Searching MDN...', 'IN_PROGRESS'
        )

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion'
        ):
            response = self.handler.do_get(feature_id=12345)

        self.assertEqual(response['status'], 'in_progress')
        self.assertEqual(response['status_message'], 'Executing AI generation loop...')
        
        steps = response['progress_steps']
        self.assertEqual(len(steps), 2)
        
        # Step 1: start
        self.assertEqual(steps[0]['step_id'], 'start')
        self.assertEqual(steps[0]['message'], 'Initializing...')
        self.assertEqual(steps[0]['status'], 'success')
        self.assertIsNotNone(steps[0]['start_timestamp'])
        
        # Step 2: tool_1
        self.assertEqual(steps[1]['step_id'], 'tool_1')
        self.assertEqual(steps[1]['message'], 'Searching MDN...')
        self.assertEqual(steps[1]['status'], 'in_progress')
        self.assertIsNotNone(steps[1]['start_timestamp'])
        self.assertIsNone(steps[1]['end_timestamp'])  # In progress step has no end timestamp

    @mock.patch('framework.permissions.can_view_feature')
    def test_get__unauthorized(self, mock_can_view):
        """Ensure unauthorized users receive a 403 Forbidden."""
        mock_can_view.return_value = False

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion'
        ):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_get(feature_id=12345)


class SummarySuggestionGenerateAPITest(testing_config.CustomTestCase):
    """Tests for POST /features/{feature_id}/summary_suggestion/generate."""

    def setUp(self):
        """Set up test environment and mock data."""
        testing_config.sign_in('editor@example.com', 222)
        self.handler = summary_suggestion_api.SummarySuggestionGenerateAPI()
        self.feature = FeatureEntry(
            id=12345,
            name='Test Feature',
            summary='Technical description.',
            category=1,
        )
        self.feature.put()

    def tearDown(self):
        """Clean up datastore entities."""
        self.feature.key.delete()
        suggestion = FeatureSummarySuggestion.get_by_id(12345)
        if suggestion:
            suggestion.key.delete()

    @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
    @mock.patch('framework.permissions.can_review_release_notes')
    @mock.patch('framework.permissions.can_edit_feature')
    def test_post__success(self, mock_can_edit, mock_can_review, mock_enqueue):
        """Ensure authorized post enqueues Cloud Task and locks suggestion status."""
        mock_can_edit.return_value = True
        mock_can_review.return_value = False

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion/generate', method='POST'
        ):
            response = self.handler.do_post(feature_id=12345)

        self.assertEqual(
            response,
            {'message': 'AI summary generation task accepted and queued.'},
        )

        suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            suggestion.status, core_enums.SummarySuggestionStatus.IN_PROGRESS
        )

        mock_enqueue.assert_called_once_with(
            '/tasks/generate-summary',
            {
                'feature_id': 12345,
                'updated_time': self.feature.updated.timestamp(),
            },
        )

    @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
    @mock.patch('framework.permissions.can_review_release_notes')
    @mock.patch('framework.permissions.can_edit_feature')
    def test_post__rate_limited_in_progress(
        self, mock_can_edit, mock_can_review, mock_enqueue
    ):
        """Ensure repeating generation while IN_PROGRESS (< 15m) triggers 400."""
        mock_can_edit.return_value = True
        mock_can_review.return_value = True

        suggestion = FeatureSummarySuggestion(
            id=12345,
            status=core_enums.SummarySuggestionStatus.IN_PROGRESS,
            status_timestamp=datetime.datetime.utcnow()
            - datetime.timedelta(minutes=5),
        )
        suggestion.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion/generate', method='POST'
        ):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as context:
                self.handler.do_post(feature_id=12345)
            self.assertIn(
                'AI summary generation is already in progress.',
                context.exception.description,
            )

        mock_enqueue.assert_not_called()

    @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
    @mock.patch('framework.permissions.can_review_release_notes')
    @mock.patch('framework.permissions.can_edit_feature')
    def test_post__rate_limited_cooldown(
        self, mock_can_edit, mock_can_review, mock_enqueue
    ):
        """Ensure repeating generation while COMPLETE (< 30m) triggers 400."""
        mock_can_edit.return_value = True
        mock_can_review.return_value = True

        suggestion = FeatureSummarySuggestion(
            id=12345,
            status=core_enums.SummarySuggestionStatus.COMPLETE,
            status_timestamp=datetime.datetime.utcnow()
            - datetime.timedelta(minutes=10),
        )
        suggestion.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion/generate', method='POST'
        ):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as context:
                self.handler.do_post(feature_id=12345)
            self.assertIn(
                'Cooldown in progress. Try again in a few minutes.',
                context.exception.description,
            )

        mock_enqueue.assert_not_called()

    @mock.patch('framework.permissions.can_review_release_notes')
    @mock.patch('framework.permissions.can_edit_feature')
    def test_post__unauthorized(self, mock_can_edit, mock_can_review):
        """Ensure unauthorized users cannot trigger generation (returns 403)."""
        mock_can_edit.return_value = False
        mock_can_review.return_value = False

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion/generate', method='POST'
        ):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_post(feature_id=12345)


class SummarySuggestionPATCHAPITest(testing_config.CustomTestCase):
    """Tests for PATCH /features/{feature_id}/summary_suggestion."""

    def setUp(self):
        """Set up test environment and mock data."""
        testing_config.sign_in('reviewer@example.com', 333)
        self.handler = summary_suggestion_api.SummarySuggestionAPI()
        self.feature = FeatureEntry(
            id=12345,
            name='Test Feature',
            summary='Original technical summary.',
            doc_links=['https://original.example.com'],
            category=1,
            owner_emails=['reviewer@example.com'],
        )
        self.feature.put()

        # Insert a COMPLETE suggestion draft
        self.suggestion = FeatureSummarySuggestion(
            id=12345,
            suggested_summary='AI suggested summary.',
            suggested_doc_links=[
                'https://mdn.example.com/api',
                'https://another.link',
            ],
            status=core_enums.SummarySuggestionStatus.COMPLETE,
            version_token=1,
            summary_provenance={
                'original_author': 'SYSTEM',
                'modified_by': None,
                'reviewed_by': None,
                'state': 'original',
                'timestamp': '2026-06-01T12:00:00',
            },
            doc_links_provenance={
                'original_author': 'SYSTEM',
                'modified_by': None,
                'reviewed_by': None,
                'state': 'original',
                'timestamp': '2026-06-01T12:00:00',
            },
        )
        self.suggestion.put()

    def tearDown(self):
        """Clean up datastore entities and activity logs."""
        self.feature.key.delete()
        self.suggestion.key.delete()
        activities = Activity.get_activities(12345)
        for act in activities:
            act.key.delete()
        # Clean up progress steps parented under feature 12345 to prevent test pollution
        steps = FeatureSummaryProgressStep.query(
            ancestor=ndb.Key(FeatureSummarySuggestion, 12345)
        ).fetch(keys_only=True)
        ndb.delete_multi(steps)

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__success_apply_as_is(self, mock_can_review):
        """[T1.1 + T3.3 + T4.1] Apply summary as-is without edits, saving all suggested doc links.

        Verify original_author is SYSTEM, reviewed_by is populated, and state is original.
        """
        mock_can_review.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [
                    'https://mdn.example.com/api',
                    'https://another.link',
                ],
                'version_token': 1,
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )
        self.assertEqual(response['version_token'], 2)

        # Check FeatureEntry values
        updated_feature = FeatureEntry.get_by_id(12345)
        self.assertEqual(updated_feature.summary, 'AI suggested summary.')
        self.assertCountEqual(
            updated_feature.doc_links,
            ['https://mdn.example.com/api', 'https://another.link'],
        )

        # Check Suggestion status and provenance
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.status,
            core_enums.SummarySuggestionStatus.APPLIED,
        )
        self.assertEqual(
            updated_suggestion.summary_provenance['state'], 'original'
        )
        self.assertEqual(
            updated_suggestion.summary_provenance['reviewed_by'],
            'reviewer@example.com',
        )
        self.assertIsNone(updated_suggestion.summary_provenance['modified_by'])

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__success_apply_backup_saved(self, mock_can_review):
        """Verify that applying a suggestion backups the original feature values in the suggestion."""
        mock_can_review.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 1,
            },
        ):
            self.handler.do_patch(feature_id=12345)

        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.original_summary, 'Original technical summary.'
        )
        self.assertEqual(
            updated_suggestion.original_doc_links,
            ['https://original.example.com'],
        )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__success_apply_tweaked(self, mock_can_review):
        """[T1.1 + T3.4] Apply summary with text edits, setting modified_by and state = modified.

        Verify that summary text and modified state are saved correctly in suggestion and FeatureEntry.
        """
        mock_can_review.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary edited by DevRel.',
                'suggested_doc_links': [
                    'https://mdn.example.com/api',
                    'https://another.link',
                ],
                'version_token': 1,
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )

        # Check FeatureEntry has tweaked summary
        updated_feature = FeatureEntry.get_by_id(12345)
        self.assertEqual(
            updated_feature.summary, 'AI suggested summary edited by DevRel.'
        )

        # Check Provenance has modified_by populated
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.summary_provenance['state'], 'modified'
        )
        self.assertEqual(
            updated_suggestion.summary_provenance['modified_by'],
            'reviewer@example.com',
        )
        self.assertEqual(
            updated_suggestion.summary_provenance['reviewed_by'],
            'reviewer@example.com',
        )
        self.assertEqual(
            updated_suggestion.suggested_summary,
            'AI suggested summary edited by DevRel.',
        )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__success_apply_link_selection(self, mock_can_review):
        """[T4.1] Apply suggestion but deselect one link (Link selection subset).

        Verify that only the selected link subset is merged to FeatureEntry.doc_links.
        """
        mock_can_review.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                # Deselect 'https://another.link', select only MDN link
                'suggested_doc_links': ['https://mdn.example.com/api'],
                'version_token': 1,
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )

        # FeatureEntry contains only MDN link
        updated_feature = FeatureEntry.get_by_id(12345)
        self.assertEqual(
            updated_feature.doc_links, ['https://mdn.example.com/api']
        )

        # Doc links provenance marked as modified
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.doc_links_provenance['state'], 'modified'
        )
        self.assertEqual(
            updated_suggestion.doc_links_provenance['modified_by'],
            'reviewer@example.com',
        )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__success_apply_duplication_prevented(self, mock_can_review):
        """[T4.3] Verify that applying deduplicates duplicate link submissions in PATCH payload."""
        mock_can_review.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                # Submit duplicate links
                'suggested_doc_links': [
                    'https://mdn.example.com/api',
                    'https://mdn.example.com/api',
                ],
                'version_token': 1,
            },
        ):
            self.handler.do_patch(feature_id=12345)

        # FeatureEntry has only one copy of the link
        updated_feature = FeatureEntry.get_by_id(12345)
        self.assertEqual(
            updated_feature.doc_links, ['https://mdn.example.com/api']
        )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__success_discard(self, mock_can_review):
        """[T1.2 + T3.2] Discard the suggestion, setting status to DISCARDED.

        Verify suggestion data remains in DB, status becomes DISCARDED, and FeatureEntry is untouched.
        """
        mock_can_review.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'discarded',
                'version_token': 1,
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )

        # Verify suggestion is discarded
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.status,
            core_enums.SummarySuggestionStatus.DISCARDED,
        )
        self.assertEqual(
            updated_suggestion.summary_provenance['reviewed_by'],
            'reviewer@example.com',
        )

        # FeatureEntry is completely untouched
        untouched_feature = FeatureEntry.get_by_id(12345)
        self.assertEqual(
            untouched_feature.summary, 'Original technical summary.'
        )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__success_restore(self, mock_can_review):
        """[T1.3] Restore a discarded suggestion back to COMPLETE.

        Verify suggestion transitions back to COMPLETE without modification of original texts.
        """
        mock_can_review.return_value = True
        self.suggestion.status = core_enums.SummarySuggestionStatus.DISCARDED
        self.suggestion.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'complete',
                'version_token': 1,
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )

        # Status restored
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.status,
            core_enums.SummarySuggestionStatus.COMPLETE,
        )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__success_restore_reverts_overwritten_values(
        self, mock_can_review
    ):
        """Verify restoring/reverting a bypassed or discarded suggestion restores feature values from backup."""
        mock_can_review.return_value = True

        # Pre-populate backup fields and mock that the feature has already been overwritten
        self.suggestion.status = core_enums.SummarySuggestionStatus.BYPASSED
        self.suggestion.original_summary = 'Original summary text.'
        self.suggestion.original_doc_links = ['https://original.example.com']
        self.suggestion.put()

        self.feature.summary = 'AI overwritten summary.'
        self.feature.doc_links = ['https://mdn.example.com/api']
        self.feature.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'complete',
                'version_token': 1,
            },
        ):
            self.handler.do_patch(feature_id=12345)

        # FeatureEntry values restored
        updated_feature = FeatureEntry.get_by_id(12345)
        self.assertEqual(updated_feature.summary, 'Original summary text.')
        self.assertEqual(
            updated_feature.doc_links, ['https://original.example.com']
        )

        # Backup cleared in suggestion, status is complete
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.status,
            core_enums.SummarySuggestionStatus.COMPLETE,
        )
        self.assertIsNone(updated_suggestion.original_summary)
        self.assertEqual(updated_suggestion.original_doc_links, [])

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__concurrency_conflict_fails(self, mock_can_review):
        """[T2.2] Prevent stale writes when version token mismatches.

        Verify that PATCH returns 409 Conflict when version_token does not match DB.
        """
        mock_can_review.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 99,  # Stale token
            },
        ):
            with self.assertRaises(werkzeug.exceptions.Conflict) as context:
                self.handler.do_patch(feature_id=12345)

            self.assertIn(
                'Conflict: The suggestion has been modified by another request.',
                context.exception.description,
            )

        # FeatureEntry is completely untouched
        untouched_feature = FeatureEntry.get_by_id(12345)
        self.assertEqual(
            untouched_feature.summary, 'Original technical summary.'
        )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__invalid_transitions_rejected(self, mock_can_review):
        """[T1.5] Reject invalid transitions (e.g. from IN_PROGRESS or NONE to APPLIED)."""
        mock_can_review.return_value = True
        self.suggestion.status = core_enums.SummarySuggestionStatus.IN_PROGRESS
        self.suggestion.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 1,
            },
        ):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as context:
                self.handler.do_patch(feature_id=12345)

            self.assertIn(
                'Cannot transition from in_progress to applied.',
                context.exception.description,
            )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__bypass_success_with_justification(self, mock_can_review):
        """Bypass the 7-day grace period as a DevRel editor with justification."""
        mock_can_review.return_value = True
        self.feature.owner_emails = [
            'owner@example.com'
        ]  # Logged in reviewer is not an owner
        self.feature.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 1,
                'bypass_justification': 'Emergency release notes fix.',
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )

        # Check Suggestion status is saved as bypassed (not applied)
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.status,
            core_enums.SummarySuggestionStatus.BYPASSED,
        )

        # Check Activity Log contains the bypass justification
        activities = Activity.get_activities(12345)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].log_type, Activity.BYPASS_APPLIED)
        self.assertIn('Emergency release notes fix.', activities[0].content)

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__bypass_failure_without_justification(self, mock_can_review):
        """Bypass the 7-day grace period as a DevRel editor fails if no justification is given."""
        mock_can_review.return_value = True
        self.feature.owner_emails = [
            'owner@example.com'
        ]  # Logged in reviewer is not an owner
        self.feature.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 1,
            },
        ):
            with self.assertRaises(werkzeug.exceptions.Forbidden) as context:
                self.handler.do_patch(feature_id=12345)

            self.assertIn(
                'Bypass justification is required during the 7-day grace period.',
                context.exception.description,
            )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__owner_success_without_justification(self, mock_can_review):
        """Owners can patch suggestions during grace period without justification."""
        mock_can_review.return_value = True
        self.feature.owner_emails = [
            'reviewer@example.com'
        ]  # Logged in reviewer is the owner
        self.feature.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 1,
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )

        # Check Activity Log contains USER_CHANGE (not bypass)
        activities = Activity.get_activities(12345)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].log_type, Activity.USER_CHANGE)

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__bypass_whitespace_validation_failure(self, mock_can_review):
        """Bypass fails if justification consists only of whitespace."""
        mock_can_review.return_value = True
        self.feature.owner_emails = ['owner@example.com']  # Logged in reviewer is not an owner
        self.feature.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 1,
                'bypass_justification': '   ',  # Whitespace only justification
            },
        ):
            with self.assertRaises(werkzeug.exceptions.Forbidden) as context:
                self.handler.do_patch(feature_id=12345)

            self.assertIn(
                'Bypass justification is required during the 7-day grace period.',
                context.exception.description,
            )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__bypass_post_grace_period_success(self, mock_can_review):
        """After 7-day grace period, non-owners can commit directly without a justification."""
        mock_can_review.return_value = True
        self.feature.owner_emails = ['owner@example.com']  # Logged in reviewer is not an owner
        self.feature.put()

        # Mock that suggestion was generated 8 days ago
        now = datetime.datetime.utcnow()
        eight_days_ago = now - datetime.timedelta(days=8)
        self.suggestion.status_timestamp = eight_days_ago
        self.suggestion.generated_at = eight_days_ago
        self.suggestion.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 1,
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )

        # Check Suggestion status becomes APPLIED (not BYPASSED)
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.status,
            core_enums.SummarySuggestionStatus.APPLIED,
        )

        # Check Activity Log contains USER_CHANGE (not BYPASS_APPLIED)
        activities = Activity.get_activities(12345)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].log_type, Activity.USER_CHANGE)

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__markdown_format_transitions(self, mock_can_review):
        """Applying a suggestion with markdown format adds 'summary' to markdown_fields, and reverting clears it."""
        mock_can_review.return_value = True
        self.feature.owner_emails = ['owner@example.com']  # Logged in reviewer is not an owner
        self.feature.markdown_fields = []
        self.feature.put()

        self.suggestion.suggested_format = 'markdown'
        self.suggestion.put()

        # 1. Apply suggestion via DevRel bypass (status becomes BYPASSED, which is allowed to revert)
        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 1,
                'bypass_justification': 'Emergency release notes formatting fix.',
            },
        ):
            self.handler.do_patch(feature_id=12345)

        # Assert 'summary' is added to markdown_fields
        updated_feature = FeatureEntry.get_by_id(12345)
        self.assertIn('summary', updated_feature.markdown_fields or [])

        # Get the new OCC token to prevent 409 Conflict on the subsequent patch
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(updated_suggestion.status, core_enums.SummarySuggestionStatus.BYPASSED)
        new_token = updated_suggestion.version_token

        # 2. Revert/Restore suggestion (BYPASSED -> COMPLETE is allowed, but needs bypass justification for non-owners)
        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'complete',
                'version_token': new_token,
                'bypass_justification': 'Reverting formatting change.',
            },
        ):
            self.handler.do_patch(feature_id=12345)

        # Assert 'summary' is removed/restored from markdown_fields
        reverted_feature = FeatureEntry.get_by_id(12345)
        self.assertNotIn('summary', reverted_feature.markdown_fields or [])

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__apply_first_time_backups_baseline(self, mock_can_review):
        """Applying a suggestion for the first time backs up original baseline status to 'none'."""
        mock_can_review.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'applied',
                'suggested_summary': 'AI suggested summary.',
                'suggested_doc_links': [],
                'version_token': 1,
                'baseline_status': 'newly',
                'baseline_newly_date': '2024-03-20',
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )

        # Check DB suggestion has baseline status updated AND original_baseline_status is backed up to 'none'!
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(updated_suggestion.baseline_status, 'newly')
        self.assertEqual(updated_suggestion.baseline_newly_date, date(2024, 3, 20))
        self.assertEqual(updated_suggestion.original_baseline_status, 'none')
        self.assertIsNone(updated_suggestion.original_baseline_newly_date)

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_patch__revert_restores_baseline_status_and_dates(self, mock_can_review):
        """Reverting a suggestion (transitioning back to COMPLETE) restores baseline values."""
        mock_can_review.return_value = True

        # Pre-populate suggestion as BYPASSED with baseline values AND backed up original baseline values
        self.suggestion.status = core_enums.SummarySuggestionStatus.BYPASSED.value
        self.suggestion.baseline_status = 'newly'
        self.suggestion.baseline_newly_date = date(2024, 3, 20)
        self.suggestion.original_baseline_status = 'newly'
        self.suggestion.original_baseline_newly_date = date(2024, 3, 15)
        self.suggestion.original_summary = 'Original technical summary.'
        self.suggestion.original_doc_links = ['https://original.example.com']
        self.suggestion.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion',
            method='PATCH',
            json={
                'status': 'complete',  # Revert action
                'version_token': 1,
            },
        ):
            response = self.handler.do_patch(feature_id=12345)

        self.assertEqual(
            response['message'], 'AI suggestion status updated successfully.'
        )

        # Check that suggestion status is back to COMPLETE
        # And its baseline status/dates are restored to the backed up values (2024-03-15)!
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertEqual(
            updated_suggestion.status,
            core_enums.SummarySuggestionStatus.COMPLETE,
        )
        self.assertEqual(updated_suggestion.baseline_status, 'newly')
        self.assertEqual(updated_suggestion.baseline_newly_date, date(2024, 3, 15))
        
        # Verify backup fields are cleared!
        self.assertIsNone(updated_suggestion.original_baseline_status)
        self.assertIsNone(updated_suggestion.original_baseline_newly_date)


class PendingReviewsCountAPITest(testing_config.CustomTestCase):
    """Tests for GET /features/pending_reviews_count."""

    def setUp(self):
        """Set up test environment with mock suggestions."""
        testing_config.sign_in('reviewer@example.com', 333)
        self.handler = summary_suggestion_api.PendingReviewsCountAPI()
        self.suggestion_1 = FeatureSummarySuggestion(
            id=101, status=core_enums.SummarySuggestionStatus.COMPLETE
        )
        self.suggestion_2 = FeatureSummarySuggestion(
            id=102, status=core_enums.SummarySuggestionStatus.COMPLETE
        )
        self.suggestion_3 = FeatureSummarySuggestion(
            id=103, status=core_enums.SummarySuggestionStatus.IN_PROGRESS
        )
        ndb.put_multi([self.suggestion_1, self.suggestion_2, self.suggestion_3])

    def tearDown(self):
        """Clean up datastore entities."""
        ndb.delete_multi(
            [
                ndb.Key(FeatureSummarySuggestion, 101),
                ndb.Key(FeatureSummarySuggestion, 102),
                ndb.Key(FeatureSummarySuggestion, 103),
            ]
        )

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_get__success(self, mock_can_review):
        """Ensure review count API returns count of COMPLETE suggestion drafts only."""
        mock_can_review.return_value = True

        with test_app.test_request_context(
            '/api/v0/features/pending_reviews_count'
        ):
            response = self.handler.do_get()

        self.assertEqual(response, {'count': 2})


class PendingReviewsAPITest(testing_config.CustomTestCase):
    """Tests for GET /features/pending_reviews."""

    def setUp(self):
        """Set up test environment and mock data."""
        testing_config.sign_in('reviewer@example.com', 333)
        self.handler = summary_suggestion_api.PendingReviewsAPI()
        
        self.feature_1 = FeatureEntry(
            id=101,
            name='Feature One',
            summary='Technical description one.',
            category=1,
        )
        self.feature_2 = FeatureEntry(
            id=102,
            name='Feature Two',
            summary='Technical description two.',
            category=2,
        )
        ndb.put_multi([self.feature_1, self.feature_2])

        self.suggestion_1 = FeatureSummarySuggestion(
            id=101,
            suggested_summary='AI summary one.',
            suggested_doc_links=[],
            baseline_status='limited',
            status=core_enums.SummarySuggestionStatus.COMPLETE,
        )
        self.suggestion_2 = FeatureSummarySuggestion(
            id=102,
            suggested_summary='AI summary two.',
            suggested_doc_links=[],
            baseline_status='newly',
            status=core_enums.SummarySuggestionStatus.COMPLETE,
        )
        self.suggestion_3 = FeatureSummarySuggestion(
            id=103,  # In progress - should not be returned
            status=core_enums.SummarySuggestionStatus.IN_PROGRESS,
        )
        ndb.put_multi([self.suggestion_1, self.suggestion_2, self.suggestion_3])

    def tearDown(self):
        """Clean up datastore entities."""
        ndb.delete_multi([
            ndb.Key(FeatureEntry, 101),
            ndb.Key(FeatureEntry, 102),
            ndb.Key(FeatureSummarySuggestion, 101),
            ndb.Key(FeatureSummarySuggestion, 102),
            ndb.Key(FeatureSummarySuggestion, 103),
            ndb.Key(FeatureSummarySuggestion, 104),  # In case created
        ])

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_get__unauthorized(self, mock_can_review):
        """Ensure GET returns 403 Forbidden if user is not authorized."""
        mock_can_review.return_value = False

        with test_app.test_request_context('/api/v0/features/pending_reviews'):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_get()

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_get__empty(self, mock_can_review):
        """Ensure GET returns empty list if no suggestions are in COMPLETE status."""
        mock_can_review.return_value = True
        # Mark all as applied
        self.suggestion_1.status = core_enums.SummarySuggestionStatus.APPLIED
        self.suggestion_2.status = core_enums.SummarySuggestionStatus.APPLIED
        ndb.put_multi([self.suggestion_1, self.suggestion_2])

        with test_app.test_request_context('/api/v0/features/pending_reviews'):
            response = self.handler.do_get()

        self.assertEqual(response, {'features': [], 'total_count': 0})

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_get__success(self, mock_can_review):
        """Ensure GET returns features with complete suggestions correctly serialized."""
        mock_can_review.return_value = True

        with test_app.test_request_context('/api/v0/features/pending_reviews'):
            response = self.handler.do_get()

        self.assertIn('features', response)
        features = response['features']
        self.assertEqual(len(features), 2)

        # Map by ID for easy assertions (asserting the flat FeatureEntry verbose schema)
        feature_map = {f['id']: f for f in features}
        self.assertIn(101, feature_map)
        self.assertIn(102, feature_map)

        self.assertEqual(feature_map[101]['name'], 'Feature One')
        self.assertEqual(feature_map[101]['summary'], 'Technical description one.')

        self.assertEqual(feature_map[102]['name'], 'Feature Two')
        self.assertEqual(feature_map[102]['summary'], 'Technical description two.')

    @mock.patch('framework.permissions.can_review_release_notes')
    def test_get__dangling_suggestion(self, mock_can_review):
        """Ensure GET filters out dangling suggestions where the feature entry no longer exists."""
        mock_can_review.return_value = True
        
        # Suggestion 104 is COMPLETE but has NO matching FeatureEntry (104) in Datastore!
        dangling_suggestion = FeatureSummarySuggestion(
            id=104,
            suggested_summary='AI summary dangling.',
            suggested_doc_links=[],
            status=core_enums.SummarySuggestionStatus.COMPLETE,
        )
        dangling_suggestion.put()

        with test_app.test_request_context('/api/v0/features/pending_reviews'):
            response = self.handler.do_get()

        features = response['features']
        # Should only return features 101 and 102, filtering out the dangling 104 suggestion!
        self.assertEqual(len(features), 2)
        feature_ids = [f['id'] for f in features]
        self.assertNotIn(104, feature_ids)

