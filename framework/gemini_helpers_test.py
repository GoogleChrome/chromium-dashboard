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
import requests
from unittest import mock
from pathlib import Path
from framework import gemini_helpers
from framework import utils
from internals import core_enums
from internals.core_models import FeatureEntry


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

  def test_fetch_spec_content__github_pull_request_success(self):
    """GitHub PR URLs should be converted to .diff URLs and fetched."""
    url = 'https://github.com/w3c/fedid/pull/123'
    expected_diff_url = 'https://github.com/w3c/fedid/pull/123.diff'
    fake_content = 'diff --git a/spec.bs b/spec.bs...'

    with mock.patch('framework.gemini_helpers.requests.get') as mock_get:
      mock_get.return_value.text = fake_content
      mock_get.return_value.raise_for_status = mock.Mock()

      result = gemini_helpers._fetch_spec_content(url)

      self.assertEqual(result, fake_content)
      mock_get.assert_called_once_with(expected_diff_url)

  def test_fetch_spec_content__github_pull_request_failure(self):
    """GitHub PR fetch failures should return an error string."""
    url = 'https://github.com/w3c/fedid/pull/123'

    with mock.patch('framework.gemini_helpers.requests.get') as mock_get:
      mock_get.side_effect = requests.exceptions.RequestException("404 Not Found")

      result = gemini_helpers._fetch_spec_content(url)

      self.assertIn("Error fetching GitHub Diff", result)
      self.assertIn("404 Not Found", result)

  def test_fetch_spec_content__github_blob_success(self):
    """GitHub Blob URLs should be converted to raw content URLs."""
    url = 'https://github.com/w3c/fedid/blob/main/index.html'
    expected_raw_url = 'https://raw.githubusercontent.com/w3c/fedid/main/index.html'
    fake_content = '<html>...</html>'

    with mock.patch('framework.gemini_helpers.requests.get') as mock_get:
      mock_get.return_value.text = fake_content
      mock_get.return_value.raise_for_status = mock.Mock()

      result = gemini_helpers._fetch_spec_content(url)

      self.assertEqual(result, fake_content)
      mock_get.assert_called_once_with(expected_raw_url)

  def test_fetch_spec_content__github_blob_failure(self):
    """GitHub Blob fetch failures should return an error string."""
    url = 'https://github.com/w3c/fedid/blob/main/index.html'

    with mock.patch('framework.gemini_helpers.requests.get') as mock_get:
      mock_get.side_effect = requests.exceptions.RequestException("Network Error")

      result = gemini_helpers._fetch_spec_content(url)

      self.assertIn("Error fetching GitHub Raw", result)
      self.assertIn("Network Error", result)

  def test_fetch_spec_content__web_spec_success(self):
    """Standard web URLs should use trafilatura to extract markdown."""
    url = 'https://drafts.csswg.org/css-grid/'
    fake_download = '<html><body><h1>Grid</h1><p>Content</p></body></html>'
    fake_markdown = '# Grid\n\nContent'

    with mock.patch('framework.gemini_helpers.trafilatura') as mock_traf:
      mock_traf.fetch_url.return_value = fake_download
      mock_traf.extract.return_value = fake_markdown

      result = gemini_helpers._fetch_spec_content(url)

      self.assertEqual(result, fake_markdown)
      mock_traf.fetch_url.assert_called_once_with(url)
      mock_traf.extract.assert_called_once_with(
        fake_download,
        include_comments=False,
        include_tables=True,
        output_format="markdown"
      )

  def test_fetch_spec_content__web_spec_fetch_failure(self):
    """If trafilatura fails to download (returns None), return error."""
    url = 'https://example.com/bad-url'

    with mock.patch('framework.gemini_helpers.trafilatura') as mock_traf:
      mock_traf.fetch_url.return_value = None

      result = gemini_helpers._fetch_spec_content(url)

      self.assertIn("Error: Could not fetch URL", result)
      # extract should not be called if fetch returns None
      mock_traf.extract.assert_not_called()

  def test_fetch_spec_content__web_spec_extract_failure(self):
    """If trafilatura returns None during extraction, return error."""
    url = 'https://example.com/empty-page'

    with mock.patch('framework.gemini_helpers.trafilatura') as mock_traf:
      mock_traf.fetch_url.return_value = '<html></html>'
      mock_traf.extract.return_value = None

      result = gemini_helpers._fetch_spec_content(url)

      self.assertIn("Error: No main content found", result)

  def test_fetch_spec_content__web_spec_exception(self):
    """General exceptions during trafilatura processing should be caught."""
    url = 'https://example.com/crash'

    with mock.patch('framework.gemini_helpers.trafilatura') as mock_traf:
      mock_traf.fetch_url.side_effect = Exception("Unexpected Crash")

      result = gemini_helpers._fetch_spec_content(url)

      self.assertIn("Error processing Web Spec", result)
      self.assertIn("Unexpected Crash", result)

  def test_create_feature_definition(self):
    """Tests the internal helper for formatting feature definitions."""
    # Accessing the private function directly for unit testing
    result = gemini_helpers._create_feature_definition(self.feature)
    expected = 'Name: Test Feature\nDescription: A test feature summary'
    self.assertEqual(result, expected)

  def test_get_test_file_contents(self):
    """Tests splitting of URLs and directories and fetching content."""
    test_locations = [
        'https://wpt.fyi/results/foo/bar.html',  # Matches file regex
        'https://wpt.fyi/results/foo/baz/',      # Does not match file regex (directory)
        '/css/css-grid/grid-definition.html'     # Matches file regex
    ]

    # Mock the util that returns content map
    expected_content_map = {
      Path('https://wpt.fyi/results/foo/bar.html'): 'content1',
      Path('/css/css-grid/grid-definition.html'): 'content2'
    }
    self.mock_utils.get_mixed_wpt_contents_async = mock.AsyncMock(
      return_value=(expected_content_map, {})
    )

    # Run the async helper
    result = asyncio.run(
        gemini_helpers._get_test_file_contents(test_locations)
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
    self.assertEqual(result, (expected_content_map, {}))

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_unified_prompt_evaluation__success(self, mock_fetch_spec):
    """Tests that the unified evaluator renders the template and calls Gemini."""
    test_files = {Path('test1.html'): 'content1'}
    dependency_files = {Path('dep.js'): 'dep_content'}

    self.mock_gemini_client.get_response.return_value = 'Unified Report'

    result = gemini_helpers.unified_prompt_evaluation(
        self.feature, test_files, dependency_files
    )

    self.assertEqual(result, 'Unified Report')

    # Verify render_template called with correct path and data
    self.mock_render_template.assert_called_once()
    args, kwargs = self.mock_render_template.call_args
    self.assertEqual(args[0], gemini_helpers.UNIFIED_GAP_ANALYSIS_TEMPLATE_PATH)
    self.assertEqual(kwargs['test_files'], test_files)
    self.assertEqual(kwargs['dependency_files'], dependency_files)

    self.mock_gemini_client.get_response.assert_called_once()

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_evaluation__success(self, mock_fetch_spec):
    """Test the multi-prompt path where all steps and API calls succeed."""
    test_files = {Path('test.html'): 'file_content_1'}

    # Setup mocks for template rendering
    def fake_render(template_path, **kwargs):
      return f'RENDERED: {template_path}'
    self.mock_render_template.side_effect = fake_render

    # Batch response (test_analysis_response, spec_synthesis_response)
    self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
        return_value=['Analysis of Test 1', 'Spec Summary']
    )
    self.mock_gemini_client.get_response_async = mock.AsyncMock(
        return_value='Final Gap Analysis Report'
    )

    result = asyncio.run(gemini_helpers.prompt_evaluation(self.feature, test_files))

    self.assertEqual(result, 'Final Gap Analysis Report')

    # Verify template calls involved correct data
    self.assertEqual(self.mock_render_template.call_count, 3)

    # Verify final gap analysis prompt received the filename in the summary
    call_kwargs = self.mock_render_template.call_args[1]
    test_analysis_summary = call_kwargs.get('test_analysis', '')
    self.assertIn('Test test.html summary:', test_analysis_summary)
    self.assertIn('Analysis of Test 1', test_analysis_summary)

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_evaluation__spec_synthesis_failure(self, mock_fetch_spec):
    """Prompt evaluation should fail if spec synthesis prompt (popped last) fails."""
    test_files = {Path('f1.html'): 'content1'}

    # The last item (spec synthesis) returns an Exception instead of str
    gemini_error = RuntimeError("Gemini overloaded")
    self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
        return_value=['Test analysis OK', gemini_error]
    )

    with self.assertRaisesRegex(utils.PipelineError,
                                'Spec synthesis prompt failure'):
      asyncio.run(gemini_helpers.prompt_evaluation(self.feature, test_files))

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_evaluation__all_test_analysis_failure(self, mock_fetch_spec):
    """Prompt evaluation should fail if ALL test analysis prompts fail."""
    test_files = {
      Path('f1.html'): 'content1',
      Path('f2.html'): 'content2'
    }

    # Both tests fail, but Spec succeeds (last item)
    self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
      return_value=[
        RuntimeError("Fail 1"),
        RuntimeError("Fail 2"),
        'Spec Summary Success'
      ]
    )

    with self.assertRaisesRegex(utils.PipelineError,
                                'No successful test analysis responses'):
      asyncio.run(gemini_helpers.prompt_evaluation(self.feature, test_files))

    # Should have logged warnings for the failures
    self.assertEqual(self.mock_logging.error.call_count, 2)

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_evaluation__partial_test_analysis_success(self, mock_fetch_spec):
    """Prompt evaluation should continue if at least ONE test analysis succeeds."""
    test_files = {
      Path('f1.html'): 'content1',
      Path('f2.html'): 'content2'
    }

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
    result = asyncio.run(gemini_helpers.prompt_evaluation(self.feature, test_files))

    self.assertEqual(result, 'Final Report')
    # Verify one warning logged for the failure
    self.mock_logging.error.assert_called_once()

  def test_run_pipeline__routes_to_unified_eval(self):
    """If file count is small, verify routing to unified_prompt_evaluation."""
    self.feature.spec_link = 'https://spec.example.com'
    self.feature.wpt_descr = 'https://wpt.fyi/results/test'

    # Return 1 file (less than MAX_SINGLE_PROMPT_TEST_COUNT)
    mock_test_files = {Path('t1.html'): 'c1'}
    mock_deps = {}

    self.mock_utils.extract_wpt_fyi_results_urls.return_value = ['url1']

    with mock.patch('framework.gemini_helpers._get_test_file_contents',
                    new_callable=mock.AsyncMock) as mock_get_content, \
         mock.patch('framework.gemini_helpers.unified_prompt_evaluation') as mock_unified, \
         mock.patch('framework.gemini_helpers.prompt_evaluation', new_callable=mock.AsyncMock) as mock_multi:

      mock_get_content.return_value = (mock_test_files, mock_deps)
      mock_unified.return_value = "Unified Success"

      result = asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

      # Verify Unified Called
      mock_unified.assert_called_once_with(self.feature, mock_test_files, mock_deps)
      # Verify Multi NOT Called
      mock_multi.assert_not_called()
      self.assertEqual(self.feature.ai_test_eval_report, "Unified Success")
      self.assertEqual(result, core_enums.AITestEvaluationStatus.COMPLETE)

  def test_run_pipeline__routes_to_multi_prompt_eval(self):
    """If file count is large, verify routing to prompt_evaluation."""
    self.feature.spec_link = 'https://spec.example.com'
    self.feature.wpt_descr = 'https://wpt.fyi/results/test'

    # Create enough files to exceed threshold (10)
    mock_test_files = {Path(f't{i}.html'): 'c' for i in range(12)}
    mock_deps = {}

    self.mock_utils.extract_wpt_fyi_results_urls.return_value = ['url1']

    with mock.patch('framework.gemini_helpers._get_test_file_contents',
                    new_callable=mock.AsyncMock) as mock_get_content, \
         mock.patch('framework.gemini_helpers.unified_prompt_evaluation') as mock_unified, \
         mock.patch('framework.gemini_helpers.prompt_evaluation', new_callable=mock.AsyncMock) as mock_multi:

      mock_get_content.return_value = (mock_test_files, mock_deps)
      mock_multi.return_value = "Multi Success"

      result = asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

      # Verify Multi Called
      mock_multi.assert_awaited_once_with(self.feature, mock_test_files)
      # Verify Unified NOT Called
      mock_unified.assert_not_called()
      self.assertEqual(self.feature.ai_test_eval_report, "Multi Success")
      self.assertEqual(result, core_enums.AITestEvaluationStatus.COMPLETE)

  def test_run_pipeline__missing_spec_link(self):
    """Pipeline should fail immediately if no spec link is present."""
    self.feature.spec_link = None
    with self.assertRaisesRegex(utils.PipelineError, 'No spec URL provided'):
      asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

    self.mock_gemini_client_cls.assert_not_called()

  def test_run_pipeline__no_wpt_urls(self):
    """Pipeline should fail if no WPT URLs can be extracted."""
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = []

    with self.assertRaisesRegex(utils.PipelineError,
                                'No valid wpt.fyi results URLs found'):
      asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

    self.mock_gemini_client_cls.assert_not_called()

  def test_run_pipeline__content_fetch_failure(self):
    """Pipeline should return FAILED status if test content fetching fails."""
    self.feature.spec_link = 'https://spec.example.com'
    self.feature.wpt_descr = 'https://wpt.fyi/results/test'
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = ['url1']

    error_msg = "Content Fetch Error"
    with mock.patch('framework.gemini_helpers._get_test_file_contents',
                    new_callable=mock.AsyncMock) as mock_get_content:
      mock_get_content.side_effect = utils.PipelineError(error_msg)

      result = asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

      self.assertEqual(result, core_enums.AITestEvaluationStatus.FAILED)
      self.assertEqual(self.feature.ai_test_eval_report, error_msg)


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
    self.mock_pipeline.return_value = core_enums.AITestEvaluationStatus.COMPLETE

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
    self.mock_pipeline.side_effect = utils.PipelineError('Test failure')

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
