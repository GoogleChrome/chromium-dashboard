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

"""Unit tests for the gemini_helpers module."""

from unittest import mock

from google.cloud import ndb

import testing_config  # Must be imported before the module under test.
from framework import gemini_helpers, utils
from internals import core_enums
from internals.core_models import FeatureEntry


class GeminiHelpersTest(testing_config.CustomTestCase):
    """Tests for the gemini_helpers module."""

    def setUp(self):
        """Set up the test environment."""
        self.feature = FeatureEntry(
            name='Test Feature',
            summary='A test feature summary',
            spec_link='https://spec.example.com',
            wpt_descr='https://wpt.fyi/results/test',
        )
        self.feature.key = ndb.Key(FeatureEntry, 123)

        self.mock_extract_urls = mock.patch(
            'framework.gemini_helpers.utils.extract_wpt_fyi_results_urls'
        ).start()
        self.addCleanup(mock.patch.stopall)

    @mock.patch('framework.gemini_helpers.generate_audit_report')
    @mock.patch('framework.gemini_helpers.settings')
    def test_run_pipeline__success(self, mock_settings, mock_generate):
        """Pipeline runs successfully and returns COMPLETE status, saving the report."""
        mock_settings.GEMINI_API_KEY = 'fake_api_key'
        self.feature.spec_link = 'https://spec.example.com'
        self.feature.wpt_descr = 'https://wpt.fyi/results/test'
        self.feature.explainer_links = ['https://explainer.example.com']

        mock_report = '# Mock WPT Coverage Report'
        mock_generate.return_value = mock_report
        self.mock_extract_urls.return_value = ['https://wpt.fyi/url1']

        result = gemini_helpers.run_wpt_test_eval_pipeline(
            self.feature, include_explainer=True
        )

        self.assertEqual(result, core_enums.AITestEvaluationStatus.COMPLETE)
        self.assertEqual(self.feature.ai_test_eval_report, mock_report)
        mock_generate.assert_called_once_with(
            feature_id=str(self.feature.key.id()),
            provider='gemini',
            api_key='fake_api_key',
            explainer_urls=['https://explainer.example.com'],
        )

    @mock.patch('framework.gemini_helpers.generate_audit_report')
    @mock.patch('framework.gemini_helpers.settings')
    def test_run_pipeline__generate_audit_report_exception(
        self, mock_settings, mock_generate
    ):
        """Pipeline fails if generate_audit_report raises an exception."""
        mock_settings.GEMINI_API_KEY = 'fake_api_key'
        self.feature.spec_link = 'https://spec.example.com'
        self.feature.wpt_descr = 'https://wpt.fyi/results/test'
        self.mock_extract_urls.return_value = ['https://wpt.fyi/url1']

        mock_generate.side_effect = Exception('Upstream API Failure')

        result = gemini_helpers.run_wpt_test_eval_pipeline(self.feature)

        self.assertEqual(result, core_enums.AITestEvaluationStatus.FAILED)
        self.assertIn(
            'Failed to generate WPT coverage report: Upstream API Failure',
            self.feature.ai_test_eval_report,
        )
        mock_generate.assert_called_once()


class GenerateWPTCoverageEvalReportHandlerTest(testing_config.CustomTestCase):
    """Tests for the GenerateWPTCoverageEvalReportHandler class."""

    def setUp(self):
        """Set up the test environment."""
        super(GenerateWPTCoverageEvalReportHandlerTest, self).setUp()
        self.feature = FeatureEntry(
            name='Test Feature',
            summary='A test feature summary',
            feature_type=0,
            category=1,
            spec_link='https://spec.example.com',
            wpt_descr='https://wpt.fyi/results/test',
        )
        self.feature.put()
        self.feature_id = self.feature.key.integer_id()

        # Instantiate handler
        self.handler = gemini_helpers.GenerateWPTCoverageEvalReportHandler()

        self.handler.require_task_header = mock.Mock()
        self.handler.get_int_param = mock.Mock(return_value=self.feature_id)
        self.handler.get_bool_param = mock.Mock(return_value=False)
        self.handler.get_validated_entity = mock.Mock(return_value=self.feature)

        self.mock_pipeline = mock.patch(
            'framework.gemini_helpers.run_wpt_test_eval_pipeline',
        ).start()

    def tearDown(self):
        """Clean up the test environment."""
        mock.patch.stopall()

    def test_process_post_data__success(self):
        """Tests that a successful pipeline run updates status to COMPLETE."""
        self.mock_pipeline.return_value = (
            core_enums.AITestEvaluationStatus.COMPLETE
        )

        response = self.handler.process_post_data()

        # Verify inputs were retrieved
        self.handler.require_task_header.assert_called_once()
        self.handler.get_int_param.assert_called_with('feature_id')
        self.handler.get_bool_param.assert_called_with(
            'include_explainer', False
        )
        self.handler.get_validated_entity.assert_called_with(
            self.feature_id, FeatureEntry
        )

        # Verify pipeline was called
        self.mock_pipeline.assert_called_once_with(self.feature, False)

        # Verify feature state was updated correctly
        updated_feature = FeatureEntry.get_by_id(self.feature_id)
        self.assertEqual(
            updated_feature.ai_test_eval_run_status,
            core_enums.AITestEvaluationStatus.COMPLETE.value,
        )
        self.assertIsNotNone(updated_feature.ai_test_eval_status_timestamp)

        # Verify response.
        self.assertEqual(
            response, {'message': 'WPT coverage analysis report generated.'}
        )

    def test_process_post_data__pipeline_failure(self):
        """Tests that a pipeline exception updates status to FAILED and saves report."""
        self.mock_pipeline.side_effect = utils.PipelineError('Test failure')

        with mock.patch(
            'framework.gemini_helpers.logging.error'
        ) as mock_log_error:
            response = self.handler.process_post_data()
            mock_log_error.assert_called_once()

        # Verify feature state was updated to FAILED
        updated_feature = FeatureEntry.get_by_id(self.feature_id)
        self.assertEqual(
            updated_feature.ai_test_eval_run_status,
            core_enums.AITestEvaluationStatus.FAILED.value,
        )
        self.assertIsNotNone(updated_feature.ai_test_eval_status_timestamp)

        # Verify a user-friendly error report was saved to the feature.
        self.assertIn(
            'Web Platform Tests coverage analysis report failed to generate',
            updated_feature.ai_test_eval_report,
        )

        self.assertIn('Test failure', response['message'])
