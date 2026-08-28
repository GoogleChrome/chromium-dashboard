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

"""Tests for summary_suggestion_api module."""

import json
from datetime import datetime, timezone
from unittest import mock

import flask
import werkzeug.exceptions
from google.cloud import ndb

import testing_config
from api import converters, summary_suggestion_api
from internals import core_enums
from internals.core_models import (
    FeatureEntry,
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)
from internals.user_models import AppUser

test_app = flask.Flask(__name__)


class SummarySuggestionAPITest(testing_config.CustomTestCase):
    """Tests for SummarySuggestionAPI handler."""

    def setUp(self):
        """Set up test features and suggestions."""
        self.feature_1 = FeatureEntry(
            id=101,
            name='CSS Anchor Positioning',
            summary='Summary for anchor positioning.',
            category=1,
            feature_type=1,
            unlisted=False,
            confidential=False,
            owner_emails=['owner@example.com'],
        )
        self.suggestion_1 = FeatureSummarySuggestion(
            id=101,
            suggested_summary='AI summary text.',
            suggested_doc_links=['https://developer.mozilla.org/'],
            version_token=1,
            status=core_enums.SummarySuggestionStatus.PROPOSED.value,
            baseline_status=core_enums.BaselineStatus.WIDELY.value,
            generation_rationale='Rationale text.',
            created=datetime(2026, 1, 1, tzinfo=timezone.utc),
            updated=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        self.step_1 = FeatureSummaryProgressStep(
            parent=self.suggestion_1.key,
            step_id=core_enums.ProgressStepId.SEARCH_MDN.value,
            status=core_enums.ProgressStepStatus.SUCCESS.value,
            message='Searched MDN.',
            start_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        self.handler = summary_suggestion_api.SummarySuggestionAPI()

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    @mock.patch('internals.core_models.FeatureSummaryProgressStep.query')
    def test_get__success(
        self, mock_step_query, mock_suggestion_get, mock_feature_get
    ):
        """It returns 200 OK with suggestion payload and progress steps timeline."""
        mock_feature_get.return_value = self.feature_1
        mock_suggestion_get.return_value = self.suggestion_1
        mock_step_query.return_value.order.return_value.fetch.return_value = [
            self.step_1
        ]

        with test_app.test_request_context('/api/v0/summary-suggestions/101'):
            actual = self.handler.do_get(feature_id=101)

        self.assertNotIn('access_level', actual)
        self.assertEqual(
            'AI summary text.', actual['suggestion']['suggested_summary']
        )
        self.assertEqual(1, len(actual['progress_steps']))
        self.assertEqual(
            converters.OpenAPIProgressStepId.SEARCH_MDN.value,
            actual['progress_steps'][0]['step'],
        )

    def test_get__invalid_id(self):
        """It aborts HTTP 400 for non-integer feature IDs."""
        with test_app.test_request_context('/api/v0/summary-suggestions/abc'):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get(feature_id='abc')
            self.assertEqual(400, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    def test_get__feature_not_found(self, mock_feature_get):
        """It aborts HTTP 404 when feature does not exist."""
        mock_feature_get.return_value = None
        with test_app.test_request_context('/api/v0/summary-suggestions/999'):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get(feature_id=999)
            self.assertEqual(404, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    def test_get__confidential_feature(self, mock_feature_get):
        """It aborts HTTP 403 for confidential features requested by unauthorized users."""
        self.feature_1.confidential = True
        mock_feature_get.return_value = self.feature_1
        testing_config.sign_out()

        with test_app.test_request_context('/api/v0/summary-suggestions/101'):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get(feature_id=101)
            self.assertEqual(403, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    @mock.patch('internals.core_models.FeatureSummaryProgressStep.query')
    def test_patch__success_status_update(
        self, mock_step_query, mock_suggestion_get, mock_feature_get
    ):
        """It updates suggestion status and increments version token on valid OCC request."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1
        mock_suggestion_get.return_value = self.suggestion_1
        mock_suggestion_get.return_value.put = mock.MagicMock()
        mock_step_query.return_value.order.return_value.fetch.return_value = []

        payload = {
            'version_token': 1,
            'status': converters.OpenAPISuggestionStatus.APPLIED.value,
        }
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            actual = self.handler.do_patch(feature_id=101)

        self.assertEqual(
            converters.OpenAPISuggestionStatus.APPLIED.value,
            actual['suggestion']['status'],
        )
        self.assertEqual(2, actual['suggestion']['version_token'])
        self.assertEqual(
            core_enums.SummarySuggestionStatus.APPLIED.value,
            self.suggestion_1.status,
        )
        self.assertEqual(2, self.suggestion_1.version_token)
        mock_suggestion_get.return_value.put.assert_called_once()

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    def test_patch__occ_conflict_409(
        self, mock_suggestion_get, mock_feature_get
    ):
        """It aborts HTTP 409 Conflict when version_token does not match datastore token."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1
        mock_suggestion_get.return_value = self.suggestion_1
        payload = {'version_token': 999, 'status': 'APPLIED'}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(feature_id=101)
            self.assertEqual(409, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    def test_patch__missing_version_token(
        self, mock_suggestion_get, mock_feature_get
    ):
        """It aborts HTTP 400 when version_token parameter is missing."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1
        mock_suggestion_get.return_value = self.suggestion_1
        payload = {'status': 'APPLIED'}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(feature_id=101)
            self.assertEqual(400, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    def test_patch__non_integer_version_token_400(
        self, mock_suggestion_get, mock_feature_get
    ):
        """It aborts HTTP 400 when version_token parameter is a string or invalid type."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1
        mock_suggestion_get.return_value = self.suggestion_1
        payload = {'version_token': '1', 'status': 'APPLIED'}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(feature_id=101)
            self.assertEqual(400, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    def test_patch__invalid_status(self, mock_suggestion_get, mock_feature_get):
        """It aborts HTTP 400 when an invalid status enum string is provided."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1
        mock_suggestion_get.return_value = self.suggestion_1
        payload = {'version_token': 1, 'status': 'INVALID_STATUS'}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(feature_id=101)
            self.assertEqual(400, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    def test_patch__unhashable_status_type_400(
        self, mock_suggestion_get, mock_feature_get
    ):
        """It aborts HTTP 400 when status parameter is an unhashable type (e.g. list)."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1
        mock_suggestion_get.return_value = self.suggestion_1
        payload = {'version_token': 1, 'status': ['APPLIED']}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(feature_id=101)
            self.assertEqual(400, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    def test_patch__unauthorized_403(self, mock_feature_get):
        """It aborts HTTP 403 Forbidden when caller lacks edit permissions for feature."""
        mock_feature_get.return_value = self.feature_1
        testing_config.sign_out()
        payload = {'version_token': 1, 'status': 'APPLIED'}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(feature_id=101)
            self.assertEqual(403, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
    def test_post__success_enqueues_cloud_task(
        self, mock_enqueue_task, mock_feature_get
    ):
        """It enqueues a Cloud Task for summary generation when user has edit access."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='POST',
            data=json.dumps({}),
            content_type='application/json',
        ):
            response = self.handler.do_post(feature_id=101)
            self.assertEqual(
                'Summary generation task enqueued for feature 101',
                response['message'],
            )
            mock_enqueue_task.assert_called_once_with(
                '/tasks/generate-summary',
                {'feature_id': 101, 'force': False},
            )

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
    def test_post__with_force_true_enqueues_cloud_task(
        self, mock_enqueue_task, mock_feature_get
    ):
        """It passes force=True to Cloud Tasks when specified in request payload."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='POST',
            data=json.dumps({'force': True}),
            content_type='application/json',
        ):
            response = self.handler.do_post(feature_id=101)
            self.assertEqual(
                'Summary generation task enqueued for feature 101',
                response['message'],
            )
            mock_enqueue_task.assert_called_once_with(
                '/tasks/generate-summary',
                {'feature_id': 101, 'force': True},
            )

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
    def test_post__initializes_anchor_step_and_resets_draft(
        self, mock_enqueue_task, mock_feature_get
    ):
        """It writes an initial START progress step and clears old suggested_summary."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1
        self.suggestion_1.put()

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='POST',
            data=json.dumps({}),
            content_type='application/json',
        ):
            response = self.handler.do_post(feature_id=101)

        self.assertEqual(
            'Summary generation task enqueued for feature 101',
            response['message'],
        )
        # Check initial anchor step
        ancestor_key = ndb.Key(FeatureSummarySuggestion, 101)
        steps = FeatureSummaryProgressStep.query(ancestor=ancestor_key).fetch()
        self.assertEqual(1, len(steps))
        self.assertEqual(
            core_enums.ProgressStepId.START.value, steps[0].step_id
        )
        self.assertEqual(
            core_enums.ProgressStepStatus.IN_PROGRESS.value, steps[0].status
        )
        self.assertEqual(
            'Summary generation task enqueued in Cloud Tasks', steps[0].message
        )

        # Check that existing suggestion's draft was reset
        reloaded_suggestion = FeatureSummarySuggestion.get_by_id(101)
        self.assertIsNotNone(reloaded_suggestion)
        self.assertIsNone(reloaded_suggestion.suggested_summary)
        self.assertIsNone(reloaded_suggestion.generation_rationale)
        self.assertEqual([], reloaded_suggestion.suggested_doc_links)

    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    @mock.patch('internals.core_models.FeatureSummaryProgressStep.query')
    def test_patch__applied_updates_feature_summary(
        self, mock_step_query, mock_suggestion_get
    ):
        """It updates feature.summary when suggestion status is set to APPLIED."""
        testing_config.sign_in('owner@example.com', 12345)
        self.feature_1.put()
        mock_suggestion_get.return_value = self.suggestion_1
        mock_step_query.return_value.order.return_value.fetch.return_value = []

        payload = {
            'version_token': 1,
            'status': 'APPLIED',
            'suggested_summary': 'Newly accepted AI summary.',
        }
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            self.handler.do_patch(feature_id=101)

        reloaded_feature = FeatureEntry.get_by_id(101)
        self.assertEqual('Newly accepted AI summary.', reloaded_feature.summary)
        self.assertEqual(
            ['https://developer.mozilla.org/'], reloaded_feature.doc_links
        )
        self.assertIn('summary', reloaded_feature.markdown_fields)

    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    @mock.patch('internals.core_models.FeatureSummaryProgressStep.query')
    def test_patch__permitted_for_release_note_reviewers(
        self, mock_step_query, mock_suggestion_get
    ):
        """It allows users with can_review_release_notes to patch a suggestion."""
        testing_config.sign_in('elmirakalali@google.com', 54321)
        self.feature_1.put()
        mock_suggestion_get.return_value = self.suggestion_1
        mock_step_query.return_value.order.return_value.fetch.return_value = []

        payload = {
            'version_token': 1,
            'status': 'APPLIED',
            'suggested_summary': 'Reviewed and applied by release editor.',
        }
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json.dumps(payload),
            content_type='application/json',
        ):
            actual = self.handler.do_patch(feature_id=101)

        self.assertEqual(
            'Reviewed and applied by release editor.',
            actual['suggestion']['suggested_summary'],
        )

    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    @mock.patch('internals.core_models.FeatureSummaryProgressStep.query')
    def test_patch__sanitizes_untrusted_doc_links(
        self, mock_step_query, mock_suggestion_get
    ):
        """It filters out javascript: and data: URIs when applying doc links."""
        testing_config.sign_in('owner@example.com', 12345)
        self.feature_1.doc_links = ['https://existing.example.com']
        self.feature_1.put()

        untrusted_suggestion = FeatureSummarySuggestion(
            id=101,
            suggested_summary='AI summary.',
            suggested_doc_links=[
                'javascript:alert(1)',
                'data:text/html,<script>alert(1)</script>',
                '   https://safe.example.com/spec   ',
                'invalid-url-schema',
            ],
            version_token=1,
            status=core_enums.SummarySuggestionStatus.PENDING.value,
        )
        mock_suggestion_get.return_value = untrusted_suggestion
        mock_step_query.return_value.order.return_value.fetch.return_value = []

        payload = {'version_token': 1, 'status': 'APPLIED'}
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='PATCH',
            data=json.dumps(payload),
            content_type='application/json',
        ):
            self.handler.do_patch(feature_id=101)

        reloaded_feature = FeatureEntry.get_by_id(101)
        self.assertEqual(
            ['https://existing.example.com', 'https://safe.example.com/spec'],
            reloaded_feature.doc_links,
        )

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    def test_post__unauthorized_403(self, mock_feature_get):
        """It aborts HTTP 403 when user lacks edit permissions."""
        mock_feature_get.return_value = self.feature_1
        testing_config.sign_out()

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='POST',
            data=json.dumps({}),
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_post(feature_id=101)
            self.assertEqual(403, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    def test_post__feature_not_found_404(self, mock_feature_get):
        """It aborts HTTP 404 when feature does not exist."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = None

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/999',
            method='POST',
            data=json.dumps({}),
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_post(feature_id=999)
            self.assertEqual(404, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    def test_post__deleted_feature_404(self, mock_feature_get):
        """It aborts HTTP 404 when target feature is marked deleted."""
        testing_config.sign_in('owner@example.com', 12345)
        deleted_feature = FeatureEntry(
            id=102,
            name='Deleted Feature',
            summary='Summary',
            deleted=True,
            owner_emails=['owner@example.com'],
        )
        mock_feature_get.return_value = deleted_feature

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/102',
            method='POST',
            data=json.dumps({}),
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_post(feature_id=102)
            self.assertEqual(404, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    def test_post__invalid_force_type_400(self, mock_feature_get):
        """It aborts HTTP 400 when force parameter is not a boolean."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='POST',
            data=json.dumps({'force': 'true'}),
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_post(feature_id=101)
            self.assertEqual(400, cm.exception.code)

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    def test_post__authenticated_non_editor_403(self, mock_feature_get):
        """It aborts HTTP 403 when an authenticated user lacks edit permissions."""
        testing_config.sign_in('random_user@example.com', 98765)
        mock_feature_get.return_value = self.feature_1

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/101',
            method='POST',
            data=json.dumps({}),
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_post(feature_id=101)
            self.assertEqual(403, cm.exception.code)


class PendingSuggestionsCountAPITest(testing_config.CustomTestCase):
    """Unit tests for PendingSuggestionsCountAPI handler."""

    def setUp(self):
        """Set up test environment and pending suggestions."""
        super().setUp()
        self.handler = summary_suggestion_api.PendingSuggestionsCountAPI()
        self.app_user = AppUser(email='admin@example.com', is_site_editor=True)
        self.app_user.put()
        testing_config.sign_in('admin@example.com', 12345)

        self.suggestion_1 = FeatureSummarySuggestion(
            id=101,
            suggested_summary='Pending summary 1',
            status=core_enums.SummarySuggestionStatus.PENDING.value,
        )
        self.suggestion_2 = FeatureSummarySuggestion(
            id=102,
            suggested_summary='Applied summary 2',
            status=core_enums.SummarySuggestionStatus.APPLIED.value,
        )
        self.suggestion_3 = FeatureSummarySuggestion(
            id=103,
            suggested_summary='Pending summary 3',
            status=core_enums.SummarySuggestionStatus.PENDING.value,
        )
        ndb.put_multi([self.suggestion_1, self.suggestion_2, self.suggestion_3])

    def tearDown(self):
        """Clean up test NDB entities."""
        ndb.delete_multi(
            [
                self.app_user.key,
                self.suggestion_1.key,
                self.suggestion_2.key,
                self.suggestion_3.key,
            ]
        )
        testing_config.sign_out()
        super().tearDown()

    def test_get__unauthorized_403(self):
        """It aborts HTTP 403 when user is not a site editor or admin."""
        testing_config.sign_out()
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending-count'
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get()
            self.assertEqual(403, cm.exception.code)

    def test_get__success_count(self):
        """It returns the accurate count of PENDING summary suggestions."""
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending-count'
        ):
            actual = self.handler.do_get()
            self.assertEqual(2, actual['count'])

    def test_get__permitted_for_release_note_reviewers(self):
        """It allows users with can_review_release_notes to query the pending count."""
        testing_config.sign_in('elmirakalali@google.com', 54321)
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending-count'
        ):
            actual = self.handler.do_get()
            self.assertEqual(2, actual['count'])

    def test_get__includes_legacy_proposed_status(self):
        """It includes both PENDING and legacy PROPOSED suggestions in the count."""
        legacy_suggestion = FeatureSummarySuggestion(
            id=104,
            suggested_summary='Proposed summary 4',
            status=core_enums.SummarySuggestionStatus.PROPOSED.value,
        )
        legacy_suggestion.put()
        try:
            with test_app.test_request_context(
                '/api/v0/summary-suggestions/pending-count'
            ):
                actual = self.handler.do_get()
                self.assertEqual(3, actual['count'])
        finally:
            legacy_suggestion.key.delete()


class PendingSuggestionsQueueAPITest(testing_config.CustomTestCase):
    """Unit tests for PendingSuggestionsQueueAPI handler."""

    def setUp(self):
        """Set up test environment, features, and pending suggestions."""
        super().setUp()
        self.handler = summary_suggestion_api.PendingSuggestionsQueueAPI()
        self.app_user = AppUser(email='admin@example.com', is_site_editor=True)
        self.app_user.put()
        testing_config.sign_in('admin@example.com', 12345)

        self.feature_1 = FeatureEntry(
            id=101, name='Feature One', summary='F1', category=1, feature_type=1
        )
        self.feature_2 = FeatureEntry(
            id=102, name='Feature Two', summary='F2', category=1, feature_type=1
        )
        ndb.put_multi([self.feature_1, self.feature_2])

        self.suggestion_1 = FeatureSummarySuggestion(
            id=101,
            suggested_summary='[Link](http://example.com) *Pending* suggestion **one**.',
            status=core_enums.SummarySuggestionStatus.PENDING.value,
        )
        self.suggestion_2 = FeatureSummarySuggestion(
            id=102,
            suggested_summary='Pending suggestion two.',
            status=core_enums.SummarySuggestionStatus.PENDING.value,
        )
        ndb.put_multi([self.suggestion_1, self.suggestion_2])

    def tearDown(self):
        """Clean up test NDB entities."""
        ndb.delete_multi(
            [
                self.app_user.key,
                self.feature_1.key,
                self.feature_2.key,
                self.suggestion_1.key,
                self.suggestion_2.key,
            ]
        )
        testing_config.sign_out()
        super().tearDown()

    def test_get__unauthorized_403(self):
        """It aborts HTTP 403 when user lacks permissions to view pending queue."""
        testing_config.sign_out()
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending'
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get()
            self.assertEqual(403, cm.exception.code)

    def test_get__non_editor_user_403(self):
        """It aborts HTTP 403 when user is authenticated but not a site editor or admin."""
        testing_config.sign_in('regular_user@example.com', 54321)
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending'
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get()
            self.assertEqual(403, cm.exception.code)

    def test_get__invalid_limit_400(self):
        """It aborts HTTP 400 when limit parameter is invalid or out of bounds."""
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending?limit=invalid'
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending?limit=0'
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending?limit=150'
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)

    def test_get__invalid_cursor_400(self):
        """It aborts HTTP 400 when cursor parameter is malformed."""
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending?cursor=invalid_base64_garbage'
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)

    def test_get__success_queue_multipage(self):
        """It returns paginated pending suggestions across multiple pages using cursor tokens."""
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending?limit=1'
        ):
            page1 = self.handler.do_get()
            self.assertEqual(2, page1['total_count'])
            self.assertEqual(1, len(page1['suggestions']))
            self.assertIsNotNone(page1['next_cursor'])

        cursor_token_1 = page1['next_cursor']
        with test_app.test_request_context(
            f'/api/v0/summary-suggestions/pending?limit=1&cursor={cursor_token_1}'
        ):
            page2 = self.handler.do_get()
            self.assertEqual(2, page2['total_count'])
            self.assertEqual(1, len(page2['suggestions']))
            self.assertIsNotNone(page2['next_cursor'])

        cursor_token_2 = page2['next_cursor']
        with test_app.test_request_context(
            f'/api/v0/summary-suggestions/pending?limit=1&cursor={cursor_token_2}'
        ):
            page3 = self.handler.do_get()
            self.assertEqual(2, page3['total_count'])
            self.assertEqual(0, len(page3['suggestions']))
            self.assertIsNone(page3['next_cursor'])

    def test_get__success_queue(self):
        """It returns paginated pending suggestions with plain-text hover snippets."""
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending?limit=25'
        ):
            actual = self.handler.do_get()
            self.assertEqual(2, actual['total_count'])
            self.assertEqual(2, len(actual['suggestions']))
            self.assertIsNone(actual['next_cursor'])

            # Verify plain-text markdown stripping on hover snippet
            first_sug = next(
                s for s in actual['suggestions'] if s['feature_id'] == 101
            )
            self.assertEqual(101, first_sug['feature_id'])
            hover = summary_suggestion_api.strip_markdown_hover_snippet(
                first_sug['suggested_summary']
            )
            self.assertEqual('Link Pending suggestion one.', hover)

    def test_get__permitted_for_release_note_reviewers(self):
        """It allows users with can_review_release_notes to query the pending queue."""
        testing_config.sign_in('elmirakalali@google.com', 54321)
        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending?limit=25'
        ):
            actual = self.handler.do_get()
            self.assertEqual(2, actual['total_count'])
            self.assertEqual(2, len(actual['suggestions']))

    def test_get__filters_deleted_features(self):
        """It excludes suggestions whose parent FeatureEntry is soft-deleted."""
        self.feature_2.deleted = True
        self.feature_2.put()

        with test_app.test_request_context(
            '/api/v0/summary-suggestions/pending?limit=25'
        ):
            actual = self.handler.do_get()
            # suggestion_2 is excluded from returned suggestions because feature_2 is deleted
            self.assertEqual(1, len(actual['suggestions']))
            self.assertEqual(101, actual['suggestions'][0]['feature_id'])


class StripMarkdownHoverSnippetTest(testing_config.CustomTestCase):
    """Unit tests for strip_markdown_hover_snippet helper utility."""

    def test_strip_markdown_hover_snippet(self):
        """It strips links, markdown formatting characters, and collapses whitespace."""
        self.assertEqual(
            '', summary_suggestion_api.strip_markdown_hover_snippet(None)
        )
        self.assertEqual(
            '', summary_suggestion_api.strip_markdown_hover_snippet('')
        )

        text = '  [MDN Documentation](https://developer.mozilla.org) for *CSS* `anchor` **positioning**.  '
        expected = 'MDN Documentation for CSS anchor positioning.'
        self.assertEqual(
            expected, summary_suggestion_api.strip_markdown_hover_snippet(text)
        )

        long_text = 'A' * 200
        truncated = summary_suggestion_api.strip_markdown_hover_snippet(
            long_text, max_len=50
        )
        self.assertEqual(50, len(truncated))
        self.assertTrue(truncated.endswith('...'))
