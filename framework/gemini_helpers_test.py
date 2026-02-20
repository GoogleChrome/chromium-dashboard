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
    # Ensure PipelineError is the real exception class
    self.mock_utils.PipelineError = utils.PipelineError
    # Ensure WPTContents is the real dataclass
    self.mock_utils.WPTContents = utils.WPTContents

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
    """GitHub PR fetch failures should raise PipelineError."""
    url = 'https://github.com/w3c/fedid/pull/123'

    with mock.patch('framework.gemini_helpers.requests.get') as mock_get:
      mock_get.side_effect = requests.exceptions.RequestException("404 Not Found")

      with self.assertRaisesRegex(utils.PipelineError, "Error fetching GitHub Diff"):
        gemini_helpers._fetch_spec_content(url)

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
    """GitHub Blob fetch failures should raise PipelineError."""
    url = 'https://github.com/w3c/fedid/blob/main/index.html'

    with mock.patch('framework.gemini_helpers.requests.get') as mock_get:
      mock_get.side_effect = requests.exceptions.RequestException("Network Error")

      with self.assertRaisesRegex(utils.PipelineError, "Error fetching GitHub Raw"):
        gemini_helpers._fetch_spec_content(url)

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
    """If trafilatura fails to download (returns None), raise PipelineError."""
    url = 'https://example.com/bad-url'

    with mock.patch('framework.gemini_helpers.trafilatura') as mock_traf:
      mock_traf.fetch_url.return_value = None

      with self.assertRaisesRegex(utils.PipelineError, "Error: Could not fetch URL"):
        gemini_helpers._fetch_spec_content(url)
      # extract should not be called if fetch returns None
      mock_traf.extract.assert_not_called()

  def test_fetch_spec_content__web_spec_extract_failure(self):
    """If trafilatura returns None during extraction, raise PipelineError."""
    url = 'https://example.com/empty-page'

    with mock.patch('framework.gemini_helpers.trafilatura') as mock_traf:
      mock_traf.fetch_url.return_value = '<html></html>'
      mock_traf.extract.return_value = None

      with self.assertRaisesRegex(utils.PipelineError, "Error: No main content found"):
        gemini_helpers._fetch_spec_content(url)

  def test_fetch_spec_content__web_spec_exception(self):
    """General exceptions during trafilatura processing should raise PipelineError."""
    url = 'https://example.com/crash'

    with mock.patch('framework.gemini_helpers.trafilatura') as mock_traf:
      mock_traf.fetch_url.side_effect = Exception("Unexpected Crash")

      with self.assertRaisesRegex(utils.PipelineError, "Error processing Web Spec"):
        gemini_helpers._fetch_spec_content(url)

  def test_create_feature_definition(self):
    """Tests the internal helper for formatting feature definitions."""
    # Accessing the private function directly for unit testing
    result = gemini_helpers._create_feature_definition(self.feature)
    expected = 'Name: Test Feature\nDescription: A test feature summary'
    self.assertEqual(result, expected)

  def test_fetch_explainer_content__github_blob_success(self):
    """GitHub Blob URLs should be converted to raw content URLs for explainers."""
    url = 'https://github.com/WICG/explainer/blob/main/README.md'
    expected_raw_url = 'https://raw.githubusercontent.com/WICG/explainer/main/README.md'
    fake_content = '# Explainer\nCode block: `x = 1`'

    with mock.patch('framework.gemini_helpers.requests.get') as mock_get:
      mock_get.return_value.text = fake_content
      mock_get.return_value.raise_for_status = mock.Mock()

      result = gemini_helpers._fetch_explainer_content(url)

      self.assertEqual(result, fake_content)
      mock_get.assert_called_once_with(expected_raw_url)

  def test_fetch_explainer_content__web_success(self):
    """Standard web URLs should use trafilatura with formatting preserved."""
    url = 'https://explainer.example.com'
    fake_download = '<html>...</html>'
    fake_markdown = '# Explainer\n\n```js\nconst x = 1;\n```'

    with mock.patch('framework.gemini_helpers.trafilatura') as mock_traf:
      mock_traf.fetch_url.return_value = fake_download
      mock_traf.extract.return_value = fake_markdown

      result = gemini_helpers._fetch_explainer_content(url)

      self.assertEqual(result, fake_markdown)
      mock_traf.extract.assert_called_once_with(
          fake_download,
          include_comments=False,
          include_tables=True,
          include_formatting=True,
          output_format="markdown"
      )

  @mock.patch('framework.gemini_helpers._fetch_explainer_content')
  def test_fetch_explainer_content__empty(self, mock_fetch):
    """Empty explainer links should return empty string."""
    self.assertEqual(gemini_helpers._get_explainer_content([]), "")
    mock_fetch.assert_not_called()

  @mock.patch('framework.gemini_helpers._fetch_explainer_content')
  def test_fetch_explainer_content__valid_url(self, mock_fetch):
    """A single valid URL should be fetched and formatted."""
    mock_fetch.return_value = "Mocked content"
    links = ["https://example.com/explainer"]

    result = gemini_helpers._get_explainer_content(links)

    expected = "## Explainer Link: https://example.com/explainer\nMocked content"
    self.assertEqual(result, expected)
    mock_fetch.assert_called_once_with("https://example.com/explainer")

  @mock.patch('framework.gemini_helpers._fetch_explainer_content')
  def test_fetch_explainer_content__mixed_and_errors(self, mock_fetch):
    """Mixed content and fetch errors should be handled gracefully."""
    # First URL succeeds, second returns an error string (which should be skipped)
    mock_fetch.side_effect = ["Good content", "Error: failed to fetch"]

    links = [
        "we have https://good.com/explainer",
        "https://bad.com/explainer",
        "Just a note." # Should be skipped because no URL
    ]

    result = gemini_helpers._get_explainer_content(links)

    # Only the first link should be in the output
    expected = "## Explainer Link: https://good.com/explainer\nGood content"
    self.assertEqual(result, expected)

  @mock.patch('framework.gemini_helpers._fetch_explainer_content')
  def test_fetch_explainer_content__all_invalid_or_errors(self, mock_fetch):
    """Mixed content and fetch errors should be handled gracefully."""
    # First URL succeeds, second returns an error string (which should be skipped)
    mock_fetch.side_effect = ["Error: failed to fetch"]

    links = [
        "https://bad.com/explainer",
        "Just a note."
    ]

    result = gemini_helpers._get_explainer_content(links)

    # Only the first link should be in the output
    expected = ""
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

    # Construct the dataclass object expected as return
    mock_wpt_contents = utils.WPTContents(
        test_contents=expected_content_map,
        dependency_contents={},
        test_to_dependencies_map={}
    )

    self.mock_utils.get_mixed_wpt_contents_async = mock.AsyncMock(
      return_value=mock_wpt_contents
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
    self.assertEqual(result, mock_wpt_contents)

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_generate_unified_prompt_text(self, mock_fetch_spec):
    """Tests that the generator creates the template data and renders it."""
    test_files = {Path('test1.html'): 'content1'}
    dependency_files = {Path('dep.js'): 'dep_content'}

    # Create the dataclass input
    wpt_contents = utils.WPTContents(
        test_contents=test_files,
        dependency_contents=dependency_files
    )

    # Mock render_template to return a predictable string
    self.mock_render_template.return_value = "Rendered Prompt"

    result = gemini_helpers._generate_unified_prompt_text(
        self.feature, wpt_contents
    )

    self.assertEqual(result, "Rendered Prompt")

    # Verify render_template called with correct path and data
    self.mock_render_template.assert_called_once()
    args, kwargs = self.mock_render_template.call_args
    self.assertEqual(args[0], gemini_helpers.UNIFIED_GAP_ANALYSIS_TEMPLATE_PATH)
    self.assertEqual(kwargs['test_files'],
                     [{'path': Path('test1.html'), 'contents': 'content1'}])
    self.assertEqual(kwargs['dependency_files'],
                     [{'path': Path('dep.js'), 'contents': 'dep_content'}])

  def test_unified_prompt_analysis__success(self):
    """Tests that the unified evaluator calls Gemini with the provided text."""
    prompt_text = "The full unified prompt text"
    self.mock_gemini_client.get_response.return_value = 'Unified Report'

    result = gemini_helpers.unified_prompt_analysis(prompt_text)

    self.assertEqual(result, 'Unified Report')
    self.mock_gemini_client.get_response.assert_called_once_with(prompt_text)

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_analysis__success_batching(self, mock_fetch_spec):
    """Test that multiple small files are batched into a single prompt."""
    test_files = {
      Path('test1.html'): 'content1',
      Path('test2.html'): 'content2'
    }
    dependency_files = {}
    dependency_mapping = {
      Path('test1.html'): set(),
      Path('test2.html'): set()
    }
    wpt_contents = utils.WPTContents(
      test_contents=test_files,
      dependency_contents=dependency_files,
      test_to_dependencies_map=dependency_mapping,
    )

    # Mock token limit to always return False (never exceeds)
    self.mock_gemini_client.prompt_exceeds_input_token_limit.return_value = False

    self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
        return_value=['Analysis of Batch 1', 'Spec Summary']
    )
    self.mock_gemini_client.get_response_async = mock.AsyncMock(
        return_value='Final Gap Analysis Report'
    )

    result = asyncio.run(gemini_helpers.prompt_analysis(self.feature, wpt_contents))

    self.assertEqual(result, 'Final Gap Analysis Report')

    # Verify that get_batch_responses_async was called with 2 prompts:
    # 1. The batched test analysis (containing both files)
    # 2. The spec synthesis
    call_args = self.mock_gemini_client.get_batch_responses_async.call_args[0][0]
    self.assertEqual(len(call_args), 2)

    # Verify correct template rendering for the test batch
    # We check the call_args_list of render_template to ensure the batch was constructed
    found_batch_render = False
    for call in self.mock_render_template.call_args_list:
      kwargs = call.kwargs
      if 'test_files' in kwargs and len(kwargs['test_files']) == 2:
        found_batch_render = True
        self.assertEqual(kwargs['test_files'][0]['path'], Path('test1.html'))
        self.assertEqual(kwargs['test_files'][1]['path'], Path('test2.html'))
    self.assertTrue(found_batch_render, "Did not find a render call with both test files")

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_analysis__splitting_on_limit(self, mock_fetch_spec):
    """Test that files are split into separate batches when token limit is exceeded."""
    test_files = {
        Path('small.html'): 'small_content',
        Path('large.html'): 'large_content'
    }
    # Force sorted order for deterministic test execution if dict is unordered
    # (Note: Python 3.7+ preserves insertion order, but explicit key usage in loop ensures sequence)
    wpt_contents = utils.WPTContents(
      test_contents=test_files,
      dependency_contents={},
      test_to_dependencies_map={p: set() for p in test_files},
    )

    # Mock token limit:
    # 1. 'small.html' (Candidate) -> False (Fits)
    # 2. 'small.html' + 'large.html' (Candidate) -> True (Exceeds)
    # 3. 'large.html' (Candidate/Single) -> False (Fits in new batch)
    self.mock_gemini_client.prompt_exceeds_input_token_limit.side_effect = [False, True, False]

    self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
      return_value=['Analysis 1', 'Analysis 2', 'Spec Summary']
    )
    self.mock_gemini_client.get_response_async = mock.AsyncMock(
      return_value='Final Report'
    )

    asyncio.run(gemini_helpers.prompt_analysis(self.feature, wpt_contents))

    # Verify batch responses called with 3 prompts (Batch 1, Batch 2, Spec)
    call_args = self.mock_gemini_client.get_batch_responses_async.call_args[0][0]
    self.assertEqual(len(call_args), 3)

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_analysis__single_file_exceeds_drops_deps(self, mock_fetch_spec):
    """Test the edge case where a single file + deps exceeds limit, forcing dropped deps."""
    test_files = {Path('huge.html'): 'huge_content'}
    dependency_files = {Path('dep.js'): 'dep'}
    wpt_contents = utils.WPTContents(
      test_contents=test_files,
      dependency_contents=dependency_files,
      test_to_dependencies_map={Path('huge.html'): {Path('dep.js')}},
    )

    # Mock token limit:
    # 1. 'huge.html' + deps (Candidate) -> True (Exceeds)
    # 2. 'huge.html' + deps (Single check) -> True (Still Exceeds)
    self.mock_gemini_client.prompt_exceeds_input_token_limit.return_value = True

    self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
      return_value=['Analysis Huge', 'Spec Summary']
    )
    self.mock_gemini_client.get_response_async = mock.AsyncMock(return_value='Rep')

    asyncio.run(gemini_helpers.prompt_analysis(self.feature, wpt_contents))

    # Verify a warning was logged
    self.mock_logging.warning.assert_called_with(
      "Test file huge.html with dependencies exceeds token limit. Generating prompt without dependencies."
    )

    # Verify render_template was eventually called with empty dependencies list
    # Look for the specific call that commits the single file
    found_empty_deps = False
    for call in self.mock_render_template.call_args_list:
        kwargs = call.kwargs
        if 'test_files' in kwargs and kwargs['test_files'][0]['path'] == Path('huge.html'):
            if 'dependency_files' in kwargs and kwargs['dependency_files'] == []:
                found_empty_deps = True
    self.assertTrue(found_empty_deps, "Did not find render call forcing empty dependencies")

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_analysis__spec_synthesis_failure(self, mock_fetch_spec):
    """Prompt analysis should fail if spec synthesis prompt (popped last) fails."""
    test_path = Path('test.html')
    test_files = {Path('test.html'): 'content1'}
    dependency_files = {}
    dependency_mapping = {test_path: set()}
    wpt_contents = utils.WPTContents(
      test_contents=test_files,
      dependency_contents=dependency_files,
      test_to_dependencies_map=dependency_mapping
    )

    self.mock_gemini_client.prompt_exceeds_input_token_limit.return_value = False

    # The last item (spec synthesis) returns an Exception instead of str
    gemini_error = RuntimeError("Gemini overloaded")
    self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
        return_value=['Test analysis OK', gemini_error]
    )

    with self.assertRaisesRegex(utils.PipelineError,
                                'Spec synthesis prompt failure'):
      asyncio.run(gemini_helpers.prompt_analysis(self.feature, wpt_contents))

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_analysis__all_test_analysis_failure(self, mock_fetch_spec):
    """Prompt analysis should fail if ALL test analysis prompts fail."""
    test_files = {
      Path('f1.html'): 'content1',
      Path('f2.html'): 'content2'
    }
    dependency_files = {}
    dependency_mapping = {Path('f1.html'): set(), Path('f2.html'): set()}
    wpt_contents = utils.WPTContents(
      test_contents=test_files,
      dependency_contents=dependency_files,
      test_to_dependencies_map=dependency_mapping
    )

    self.mock_gemini_client.prompt_exceeds_input_token_limit.return_value = False

    self.mock_gemini_client.get_batch_responses_async = mock.AsyncMock(
      return_value=[
        RuntimeError("Fail 1"),
        'Spec Summary Success'
      ]
    )

    with self.assertRaisesRegex(utils.PipelineError,
                                'No successful test analysis responses'):
      asyncio.run(gemini_helpers.prompt_analysis(self.feature, wpt_contents))

    # Should have logged warnings for the failures
    self.assertEqual(self.mock_logging.error.call_count, 1)

  @mock.patch('framework.gemini_helpers._fetch_spec_content', return_value="Mock Spec Content")
  def test_prompt_analysis__partial_test_analysis_success(self, mock_fetch_spec):
    """Prompt analysis should continue if at least ONE test analysis succeeds."""
    test_files = {
      Path('f1.html'): 'content1',
      Path('f2.html'): 'content2'
    }
    dependency_files = {}
    dependency_mapping = {Path('f1.html'): set(), Path('f2.html'): set()}
    wpt_contents = utils.WPTContents(
      test_contents=test_files,
      dependency_contents=dependency_files,
      test_to_dependencies_map=dependency_mapping
    )

    # Mock split: f1 fits, f2 exceeds -> 2 batches
    self.mock_gemini_client.prompt_exceeds_input_token_limit.side_effect = [False, True, False]

    # One batch fails, one succeeds, spec succeeds
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
    result = asyncio.run(gemini_helpers.prompt_analysis(self.feature, wpt_contents))

    self.assertEqual(result, 'Final Report')
    # Verify one warning logged for the failure
    self.mock_logging.error.assert_called_once()

  def test_run_pipeline__routes_to_unified_eval(self):
    """Verify routing to unified_prompt_analysis when token count is low."""
    self.feature.spec_link = 'https://spec.example.com'
    self.feature.wpt_descr = 'https://wpt.fyi/results/test'

    # Return 1 file (less than MAX_SINGLE_PROMPT_TEST_COUNT)
    test_files = {Path('t1.html'): 'c1'}
    dependency_files = {}
    dependency_mapping = {Path('t1.html'): set()}
    wpt_contents = utils.WPTContents(
      test_contents=test_files,
      dependency_contents=dependency_files,
      test_to_dependencies_map=dependency_mapping
    )

    self.mock_utils.extract_wpt_fyi_results_urls.return_value = ['url1']
    self.mock_gemini_client.prompt_exceeds_input_token_limit.return_value = False

    with mock.patch('framework.gemini_helpers._get_test_file_contents',
                    new_callable=mock.AsyncMock) as mock_get_content, \
         mock.patch('framework.gemini_helpers.unified_prompt_analysis') as mock_unified, \
         mock.patch('framework.gemini_helpers._generate_unified_prompt_text') as mock_gen_prompt, \
         mock.patch('framework.gemini_helpers.prompt_analysis', new_callable=mock.AsyncMock) as mock_multi:

      mock_get_content.return_value = wpt_contents
      mock_gen_prompt.return_value = "Generated Prompt Text"
      mock_unified.return_value = "Unified Success"

      result = asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

      # Verify Generator Called
      mock_gen_prompt.assert_called_once_with(self.feature, wpt_contents)

      # Verify Token Count Checked
      self.mock_gemini_client.prompt_exceeds_input_token_limit.assert_called_once_with(
        "Generated Prompt Text")

      # Verify Unified Called
      mock_unified.assert_called_once_with("Generated Prompt Text")

      # Verify Multi NOT Called
      mock_multi.assert_not_called()
      self.assertEqual(self.feature.ai_test_eval_report, "Unified Success")
      self.assertEqual(result, core_enums.AITestEvaluationStatus.COMPLETE)

  def test_run_pipeline__routes_to_multi_prompt_due_to_tokens(self):
    """Verify routing to prompt_analysis when token count is high."""
    self.feature.spec_link = 'https://spec.example.com'
    self.feature.wpt_descr = 'https://wpt.fyi/results/test'

    # Create enough files to exceed threshold (10)
    test_files = {Path(f't{i}.html'): 'c' for i in range(12)}
    dependency_files = {}
    dependency_mapping = {Path(f't{i}.html'): set() for i in range(12)}
    wpt_contents = utils.WPTContents(
      test_contents=test_files,
      dependency_contents=dependency_files,
      test_to_dependencies_map=dependency_mapping
    )

    self.mock_utils.extract_wpt_fyi_results_urls.return_value = ['url1']

    self.mock_gemini_client.prompt_exceeds_input_token_limit.return_value = True

    with mock.patch('framework.gemini_helpers._get_test_file_contents',
                    new_callable=mock.AsyncMock) as mock_get_content, \
         mock.patch('framework.gemini_helpers.unified_prompt_analysis') as mock_unified, \
         mock.patch('framework.gemini_helpers._generate_unified_prompt_text') as mock_gen_prompt, \
         mock.patch('framework.gemini_helpers.prompt_analysis', new_callable=mock.AsyncMock) as mock_multi:

      mock_get_content.return_value = wpt_contents
      mock_gen_prompt.return_value = "Generated Huge Prompt"
      mock_multi.return_value = "Multi Success"

      result = asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

      # Verify Token Count Checked
      self.mock_gemini_client.prompt_exceeds_input_token_limit.assert_called_once_with(
        "Generated Huge Prompt")

      # Verify Multi Called
      mock_multi.assert_awaited_once_with(self.feature, wpt_contents)

      # Verify Unified NOT Called
      mock_unified.assert_not_called()

      self.assertEqual(self.feature.ai_test_eval_report, "Multi Success")
      self.assertEqual(result, core_enums.AITestEvaluationStatus.COMPLETE)

  def test_run_pipeline__missing_spec_link(self):
    """Pipeline should fail immediately if no spec link is present."""
    self.feature.spec_link = None
    result = asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

    self.assertEqual(result, core_enums.AITestEvaluationStatus.FAILED)
    self.assertEqual(self.feature.ai_test_eval_report, 'No spec URL provided.')
    self.mock_gemini_client_cls.assert_not_called()

  def test_run_pipeline__no_wpt_urls(self):
    """Pipeline should fail if no WPT URLs can be extracted."""
    self.mock_utils.extract_wpt_fyi_results_urls.return_value = []

    result = asyncio.run(gemini_helpers.run_wpt_test_eval_pipeline(self.feature))

    self.assertEqual(result, core_enums.AITestEvaluationStatus.FAILED)
    self.assertIn('No valid wpt.fyi results URLs found', self.feature.ai_test_eval_report)
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
      response, {'message': 'WPT coverage analysis report generated.'})

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
      'Web Platform Tests coverage analysis report failed to generate',
      updated_feature.ai_test_eval_report
    )

    self.assertIn('Test failure', response['message'])
