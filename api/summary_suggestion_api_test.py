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
from unittest import mock

import flask
import werkzeug.exceptions
from google.cloud import ndb  # type: ignore

import testing_config
from api import summary_suggestion_api
from internals import core_enums
from internals.core_models import FeatureEntry, FeatureSummarySuggestion
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
                'suggested_summary': None,
                'suggested_doc_links': [],
                'baseline_status': None,
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
            status_timestamp=datetime.datetime(2026, 6, 1, 12, 0, 0),
            last_generation_attempt=datetime.datetime(2026, 6, 1, 11, 58, 0),
        )
        suggestion.put()

        with test_app.test_request_context(
            '/api/v0/features/12345/summary_suggestion'
        ):
            response = self.handler.do_get(feature_id=12345)

        self.assertEqual(response['status'], 'complete')
        self.assertEqual(response['suggested_summary'], 'Simplified summary.')
        self.assertEqual(
            response['suggested_doc_links'], ['https://example.com/doc']
        )
        self.assertEqual(response['baseline_status'], 'limited')
        self.assertEqual(
            response['last_generation_attempt'], '2026-06-01T11:58:00'
        )
        self.assertIsNotNone(response['status_timestamp'])

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
