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

import testing_config  # Must be imported before the module under test.

import asyncio
from unittest import mock
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
    self.mock_utils.get_mixed_wpt_contents_async = mock.AsyncMock(return_value={
        'loc1': 'content1',
        'loc2': 'content2'
    })

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
    # Should return just the values from the content map.
    self.assertEqual(result, ['content1', 'content2'])

  def test_run_pipeline__success(self):
    """Test the happy path where all steps and API calls succeed."""
    self.feature.spec_link = 'https://spec.example.com'
    self.feature.wpt_descr = 'See https://wpt.fyi/results/foo'

    # 1. Setup Mocks for initial data gathering.
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = [
        'https://wpt.fyi/results/foo/test.html'
    ]
    # Mock the internal helper to simplify this higher-level test
    # (Alternatively, we could mock utils.get_mixed_wpt_contents_async like above)
    with mock.patch('framework.gemini_helpers._get_test_analysis_prompts',
                    new_callable=mock.AsyncMock) as mock_get_prompts:
      mock_get_prompts.return_value = ['file_content_1']

      # 2. Setup Mocks for template rendering
      # Make render_template return a string that identifies which template it was
      def fake_render(template_path, **kwargs):
        return f'RENDERED: {template_path}'
      self.mock_render_template.side_effect = fake_render

      # 3. Setup Gemini Mocks
      # Batch response: [test_analysis_response, spec_synthesis_response]
      # Note: Implementation appends spec prompt LAST, so it pops LAST.
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
      # We expect 3 render calls: spec synthesis, 1 test analysis, gap analysis
      self.assertEqual(self.mock_render_template.call_count, 3)

      # Verify Gemini calls
      # Batch call should have received [test_prompt, spec_prompt]
      self.mock_gemini_client.get_batch_responses_async.assert_called_once()
      call_args = self.mock_gemini_client.get_batch_responses_async.call_args[0][0]
      self.assertEqual(len(call_args), 2)
      self.assertIn('prompts/test-analysis.html', call_args[0])
      self.assertIn('prompts/spec-synthesis.html', call_args[1])

      # Final Gap analysis call
      self.mock_gemini_client.get_response_async.assert_called_once()
      gap_prompt = self.mock_gemini_client.get_response_async.call_args[0][0]
      self.assertIn('prompts/gap-analysis.html', gap_prompt)

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
      mock_get_prompts.return_value = ['content1']

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
      # Two tests found
      mock_get_prompts.return_value = ['content1', 'content2']

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
      self.assertEqual(self.mock_logging.warning.call_count, 2)

  def test_run_pipeline__partial_test_analysis_success(self):
    """Pipeline should continue if at least ONE test analysis succeeds."""
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = ['url1', 'url2']

    with mock.patch('framework.gemini_helpers._get_test_analysis_prompts',
                    new_callable=mock.AsyncMock) as mock_get_prompts:
      mock_get_prompts.return_value = ['content1', 'content2']

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
      self.mock_logging.warning.assert_called_once()
      # Verify the gap analysis prompt only contains the successful one
      # We can check the 'test_analysis' kwarg passed to render_template for the gap analysis
      call_args_list = self.mock_render_template.call_args_list
      # The last call should be the gap analysis
      gap_call_kwargs = call_args_list[-1][1]
      self.assertIn('Analysis 2 Success', gap_call_kwargs.get('test_analysis', ''))
      self.assertNotIn('Fail 1', gap_call_kwargs.get('test_analysis', ''))
