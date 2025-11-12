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

from internals import core_enums
import testing_config  # Must be imported before the module under test.

import asyncio
from unittest import mock
from internals import core_enums
from internals.core_models import FeatureEntry
from framework import gemini_helpers

class GeminiHelpersTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature = FeatureEntry(
        name='Test Feature',
        summary='A test feature summary',
        spec_link='https://spec.example.com',
        wpt_descr='https://wpt.fyi/results/test'
    )

    # Patch external dependencies
    self.mock_render_template = mock.patch(
        'framework.gemini_helpers.render_template').start()
    self.mock_utils = mock.patch('framework.gemini_helpers.utils').start()
    self.mock_logging = mock.patch('framework.gemini_helpers.logging').start()

    # Mock GeminiClient and its instance
    self.mock_gemini_client_cls = mock.patch(
        'framework.gemini_helpers.GeminiClient').start()
    self.mock_gemini_client = self.mock_gemini_client_cls.return_value

    self.addCleanup(mock.patch.stopall)

  def tearDown(self):
    for f in FeatureEntry.query():
      f.key.delete()

  def test_create_feature_definition(self):
    """Tests the internal helper for formatting feature definitions."""
    # Accessing the private function directly for unit testing
    result = gemini_helpers._create_feature_definition(self.feature)
    expected = 'Name: Test Feature\nDescription: A test feature summary'
    self.assertEqual(result, expected)

  def test_get_test_analysis_prompts(self):
    """Tests splitting of URLs and directories and fetching content."""
    test_locations = [
        'https://wpt.fyi/results/foo/bar.html',  # Matches file regex
        'https://wpt.fyi/results/foo/baz/',      # Does not match file regex (directory)
        '/css/css-grid/grid-definition.html'     # Matches file regex
    ]

    # Mock the util that returns content map
    expected_content_map = {
      'https://wpt.fyi/results/foo/bar.html': 'content1',
      '/css/css-grid/grid-definition.html': 'content2'
    }
    self.mock_utils.get_mixed_wpt_contents_async = mock.AsyncMock(
      return_value=expected_content_map
    )

    # Run the async helper
    result = asyncio.run(
        gemini_helpers._get_test_analysis_prompts(test_locations)
    )

    # Verify it split the locations correctly based on the regex
    expected_urls = [
        'https://wpt.fyi/results/foo/bar.html',
        '/css/css-grid/grid-definition.html'
    ]
    expected_dirs = ['https://wpt.fyi/results/foo/baz/']

    self.mock_utils.get_mixed_wpt_contents_async.assert_called_once_with(
        expected_dirs, expected_urls
    )
    self.assertEqual(result, expected_content_map)

  def test_run_pipeline__success(self):
    """Test the happy path where all steps and API calls succeed."""
    self.feature.spec_link = 'https://spec.example.com'
    self.feature.wpt_descr = 'See https://wpt.fyi/results/foo'

    # 1. Setup Mocks for initial data gathering.
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = [
        'https://wpt.fyi/results/foo/test.html'
    ]
    # Mock the internal helper to simplify this higher-level test
    with mock.patch('framework.gemini_helpers._get_test_analysis_prompts',
                    new_callable=mock.AsyncMock) as mock_get_prompts:
      mock_get_prompts.return_value = {'test.html': 'file_content_1'}

      # 2. Setup Mocks for template rendering
      # Make render_template return a string that identifies which template it was
      def fake_render(template_path, **kwargs):
        return f'RENDERED: {template_path}'
      self.mock_render_template.side_effect = fake_render

      # 3. Setup Gemini Mocks
      # Batch response: [test_analysis_response, spec_synthesis_response]
      self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
          return_value=['Analysis of Test 1', 'Spec Summary']
      )
      self.mock_gemini_client.get_response_async = mock.AsyncMock(
          return_value='Final Gap Analysis Report'
      )

      # Execute Pipeline
      asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

      # Verification
      self.assertEqual(self.feature.ai_test_eval_report, 'Final Gap Analysis Report')

      # Verify template calls involved correct data
      self.assertEqual(self.mock_render_template.call_count, 3)

      # Verify final gap analysis prompt received the filename in the summary
      # The last call to render_template is for GAP_ANALYSIS_TEMPLATE_PATH
      call_kwargs = self.mock_render_template.call_args[1]
      test_analysis_summary = call_kwargs.get('test_analysis', '')
      # Verify the filename 'test.html' is in the summary string
      self.assertIn('Test test.html summary:', test_analysis_summary)
      self.assertIn('Analysis of Test 1', test_analysis_summary)

  def test_run_pipeline__missing_spec_link(self):
    """Pipeline should fail immediately if no spec link is present."""
    self.feature.spec_link = None
    with self.assertRaisesRegex(gemini_helpers.PipelineError, 'No spec URL provided'):
      asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

    self.mock_gemini_client_cls.assert_not_called()

  def test_run_pipeline__no_wpt_urls(self):
    """Pipeline should fail if no WPT URLs can be extracted."""
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = []

    with self.assertRaisesRegex(gemini_helpers.PipelineError,
                                'No valid wpt.fyi results URLs found'):
      asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

    self.mock_gemini_client_cls.assert_not_called()

  def test_run_pipeline__spec_synthesis_failure(self):
    """Pipeline should fail if the spec synthesis prompt (popped last) fails."""
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = ['url1']

    with mock.patch('framework.gemini_helpers._get_test_analysis_prompts',
                    new_callable=mock.AsyncMock) as mock_get_prompts:
      mock_get_prompts.return_value = {'f1.html': 'content1'}

      # The last item (spec synthesis) returns an Exception instead of str
      gemini_error = RuntimeError("Gemini overloaded")
      self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
          return_value=['Test analysis OK', gemini_error]
      )

      with self.assertRaisesRegex(gemini_helpers.PipelineError,
                                  'Spec synthesis prompt failure'):
        asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

  def test_run_pipeline__all_test_analysis_failure(self):
    """Pipeline should fail if ALL test analysis prompts fail."""
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = ['url1', 'url2']

    with mock.patch('framework.gemini_helpers._get_test_analysis_prompts',
                    new_callable=mock.AsyncMock) as mock_get_prompts:
      mock_get_prompts.return_value = {'f1.html': 'content1', 'f2.html': 'content2'}

      # Both tests fail, but Spec succeeds (last item)
      self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
          return_value=[
              RuntimeError("Fail 1"),
              RuntimeError("Fail 2"),
              'Spec Summary Success'
          ]
      )

      with self.assertRaisesRegex(gemini_helpers.PipelineError,
                                  'No successful test analysis responses'):
        asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

      # Should have logged warnings for the failures
      self.assertEqual(self.mock_logging.error.call_count, 2)

  def test_run_pipeline__partial_test_analysis_success(self):
    """Pipeline should continue if at least ONE test analysis succeeds."""
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = ['url1', 'url2']

    with mock.patch('framework.gemini_helpers._get_test_analysis_prompts',
                    new_callable=mock.AsyncMock) as mock_get_prompts:
      mock_get_prompts.return_value = {'f1.html': 'content1', 'f2.html': 'content2'}

      # One fails, one succeeds, spec succeeds
      self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
          return_value=[
              RuntimeError("Fail 1"),
              'Analysis 2 Success',
              'Spec Summary Success'
          ]
      )
      self.mock_gemini_client.get_response_async = mock.AsyncMock(
          return_value='Final Report'
      )

      # Should NOT raise exception
      asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

      self.assertEqual(self.feature.ai_test_eval_report, 'Final Report')
      # Verify one warning logged for the failure
      self.mock_logging.error.assert_called_once()

      # Verify the gap analysis prompt only contains the successful one AND its filename
      call_args_list = self.mock_render_template.call_args_list
      gap_call_kwargs = call_args_list[-1][1]
      gap_prompt_test_analysis = gap_call_kwargs.get('test_analysis', '')

      # assert filename 'f2.html' is present for the successful one
      self.assertIn('Test f2.html summary:', gap_prompt_test_analysis)
      self.assertIn('Analysis 2 Success', gap_prompt_test_analysis)
      # Ensure failed one is missing
      self.assertNotIn('f1.html', gap_prompt_test_analysis)


class GenerateWPTCoverageEvalReportHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    super(GenerateWPTCoverageEvalReportHandlerTest, self).setUp()
    self.feature = FeatureEntry(
      name='Test Feature',
      summary='A test feature summary',
      feature_type=0,
      category=1,
      spec_link='https://spec.example.com',
      wpt_descr='https://wpt.fyi/results/test'
    )
    self.feature.put()
    self.feature_id = self.feature.key.integer_id()

    # Instantiate handler
    self.handler = gemini_helpers.GenerateWPTCoverageEvalReportHandler()

    self.handler.require_task_header = mock.Mock()
    self.handler.get_int_param = mock.Mock(return_value=self.feature_id)
    self.handler.get_validated_entity = mock.Mock(return_value=self.feature)

    self.mock_pipeline = mock.patch(
      'framework.gemini_helpers.run_wpt_test_eval_pipeline',
      new_callable=mock.AsyncMock).start()

  def tearDown(self):
    mock.patch.stopall()
    self.feature.key.delete()

  def test_process_post_data__success(self):
    """Tests that a successful pipeline run updates status to COMPLETE."""
    self.mock_pipeline.return_value = None

    response = self.handler.process_post_data()

    # Verify inputs were retrieved
    self.handler.require_task_header.assert_called_once()
    self.handler.get_int_param.assert_called_with('feature_id')
    self.handler.get_validated_entity.assert_called_with(
      self.feature_id, FeatureEntry)

    # Verify pipeline was called
    self.mock_pipeline.assert_awaited_once_with(self.feature)

    # Verify feature state was updated correctly
    updated_feature = FeatureEntry.get_by_id(self.feature_id)
    self.assertEqual(
      updated_feature.ai_test_eval_run_status,
      core_enums.AITestEvaluationStatus.COMPLETE.value
    )
    self.assertIsNotNone(updated_feature.ai_test_eval_status_timestamp)

    # Verify response.
    self.assertEqual(
      response, {'message': 'WPT coverage evaluation report generated.'})

  def test_process_post_data__pipeline_failure(self):
    """Tests that a pipeline exception updates status to FAILED and saves report."""
    self.mock_pipeline.side_effect = gemini_helpers.PipelineError('Test failure')

    with mock.patch('framework.gemini_helpers.logging.error') as mock_log_error:
      response = self.handler.process_post_data()
      mock_log_error.assert_called_once()

    # Verify feature state was updated to FAILED
    updated_feature = FeatureEntry.get_by_id(self.feature_id)
    self.assertEqual(
      updated_feature.ai_test_eval_run_status,
      core_enums.AITestEvaluationStatus.FAILED.value
    )
    self.assertIsNotNone(updated_feature.ai_test_eval_status_timestamp)

    # Verify a user-friendly error report was saved to the feature.
    self.assertIn(
      'Web Platform Tests coverage evaluation report failed to generate',
      updated_feature.ai_test_eval_report
    )

    self.assertIn('Test failure', response['message'])
