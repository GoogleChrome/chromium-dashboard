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

import testing_config
from api import converters, summary_suggestion_api
from internals import core_enums
from internals.core_models import (
    FeatureEntry,
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)

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
    def test_get__success_read_only(
        self, mock_step_query, mock_suggestion_get, mock_feature_get
    ):
        """It returns 200 OK with READ_ONLY access for anonymous users."""
        testing_config.sign_out()
        mock_feature_get.return_value = self.feature_1
        mock_suggestion_get.return_value = self.suggestion_1
        mock_step_query.return_value.order.return_value.fetch.return_value = [
            self.step_1
        ]

        with test_app.test_request_context('/api/v0/summary-suggestions/101'):
            actual = self.handler.do_get(feature_id=101)

        self.assertEqual(
            converters.OpenAPISummarySuggestionAccessLevel.READ_ONLY.value,
            actual['access_level'],
        )
        self.assertEqual(
            'AI summary text.', actual['suggestion']['suggested_summary']
        )
        self.assertEqual(1, len(actual['progress_steps']))
        self.assertEqual(
            converters.OpenAPIProgressStepId.SEARCH_MDN.value,
            actual['progress_steps'][0]['step'],
        )

    @mock.patch('internals.core_models.FeatureEntry.get_by_id')
    @mock.patch('internals.core_models.FeatureSummarySuggestion.get_by_id')
    @mock.patch('internals.core_models.FeatureSummaryProgressStep.query')
    def test_get__success_can_edit(
        self, mock_step_query, mock_suggestion_get, mock_feature_get
    ):
        """It returns 200 OK with CAN_EDIT access for feature owners."""
        testing_config.sign_in('owner@example.com', 12345)
        mock_feature_get.return_value = self.feature_1
        mock_suggestion_get.return_value = self.suggestion_1
        mock_step_query.return_value.order.return_value.fetch.return_value = []

        with test_app.test_request_context('/api/v0/summary-suggestions/101'):
            actual = self.handler.do_get(feature_id=101)

        self.assertEqual(
            converters.OpenAPISummarySuggestionAccessLevel.CAN_EDIT.value,
            actual['access_level'],
        )
        self.assertEqual(
            'AI summary text.', actual['suggestion']['suggested_summary']
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
