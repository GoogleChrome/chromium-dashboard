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

import asyncio
from datetime import datetime
import logging
from pathlib import Path
import re
import requests
import trafilatura
from flask import render_template
from urllib.parse import urlparse

from framework import basehandlers, utils
from framework.gemini_client import GeminiClient
from internals import core_enums
from internals.core_models import FeatureEntry


SPEC_SYNTHESIS_TEMPLATE_PATH = 'prompts/spec-synthesis.html'
TEST_ANALYSIS_TEMPLATE_PATH = 'prompts/test-analysis.html'
GAP_ANALYSIS_TEMPLATE_PATH = 'prompts/gap-analysis.html'
UNIFIED_GAP_ANALYSIS_TEMPLATE_PATH = 'prompts/unified-gap-analysis.html'
# Regex to determine if the wpt.fyi URL is a test file link.
# Otherwise, it's a directory.
WPT_FILE_REGEX = re.compile(r"\/[^/]*\.[^/]*$")

# Define the maximum number of listed tests for the feature that can be used in
# the single prompt format. Any more than this will cause the trigger the use
# of the three-prompt flow that utilizes separate test summaries.
MAX_SINGLE_PROMPT_TEST_COUNT = 10


def _create_feature_definition(feature: FeatureEntry) -> str:
  return f'Name: {feature.name}\nDescription: {feature.summary}'


def _fetch_spec_content(url: str) -> str:
  """
  Routes the URL to the correct extraction logic to return clean text.
  """
  parsed = urlparse(url)

  # URL type 1: GitHub pull requests
  if "github.com" in parsed.netloc and "/pull/" in parsed.path:
    diff_url = url.rstrip('/') + ".diff"
    try:
      resp = requests.get(diff_url)
      resp.raise_for_status()
      return resp.text
    except Exception as e:
      return f"Error fetching GitHub Diff: {e}"

  # URL type 2: GitHub file blobs
  if "github.com" in parsed.netloc and "/blob/" in parsed.path:
    raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    try:
      resp = requests.get(raw_url)
      resp.raise_for_status()
      return resp.text
    except Exception as e:
      return f"Error fetching GitHub Raw: {e}"

  # URL type 3: Standard W3C, Web specs, or other webpages
  try:
    downloaded = trafilatura.fetch_url(url)

    if downloaded is None:
      return f"Error: Could not fetch URL {url}"

    # Extract content to Markdown.
    # include_comments=False skips comments.
    # include_tables=True is critical for Specs which often use tables for definitions.
    result = trafilatura.extract(
      downloaded,
      include_comments=False,
      include_tables=True,
      output_format="markdown"
    )

    if not result:
      return f"Error: No main content found at {url}"

    return result

  except Exception as e:
    return f"Error processing Web Spec: {e}"


async def _get_test_file_contents(test_locations: list[str]) -> tuple[dict[Path, str], dict[Path, str]]:
  """Obtain the contents of test files, as well as the contents of their dependencies."""
  test_urls = []
  test_directories = []
  for test_loc in test_locations:
    if WPT_FILE_REGEX.search(test_loc):
      test_urls.append(test_loc)
    else:
      test_directories.append(test_loc)

  test_file_contents, dependency_contents = await utils.get_mixed_wpt_contents_async(
    test_directories, test_urls
  )
  return test_file_contents, dependency_contents


def _generate_unified_prompt_text(
  feature: FeatureEntry,
  test_files: dict[Path, str],
  dependency_files: dict[Path, str]
) -> str:
  """Generates the text for the unified gap analysis prompt."""
  template_data = {
    'spec_url': feature.spec_link,
    'spec_content': _fetch_spec_content(feature.spec_link),
    'feature_name': feature.name,
    'feature_summary': feature.summary,
    'test_files': test_files,
    'dependency_files': dependency_files,
  }
  return render_template(
    UNIFIED_GAP_ANALYSIS_TEMPLATE_PATH,
    **template_data,
  )


def unified_prompt_analysis(prompt_text: str) -> str:
  """Evaluates WPT coverage using a single, unified prompt.

  This method is used when the number of test files and the total token count
  are small enough to fit within the context window of a single prompt.

  Args:
    prompt_text: The complete text of the unified prompt to be sent to Gemini.

  Returns:
    A string containing the generated coverage report.
  """
  gemini_client = GeminiClient()
  gap_analysis_response = gemini_client.get_response(prompt_text)
  return gap_analysis_response


async def prompt_analysis(feature: FeatureEntry, test_files: dict[Path, str]) -> str:
  """Evaluates WPT coverage using a multi-stage prompt flow.

  This method is used when the number of test files is too large for a single
  prompt. It breaks the analysis into three distinct stages:
  1. Spec Synthesis: Summarizes the spec into a concise reference.
  2. Test Analysis: Analyzes each test file individually in parallel batches.
  3. Gap Analysis: Compares the spec synthesis with the aggregated test
     summaries to identify gaps.

  Args:
    feature: The feature entry containing metadata and the spec URL.
    test_files: A dictionary mapping test file paths to their raw text content.

  Returns:
    A string containing the generated coverage report.

  Raises:
    PipelineError: If any critical stage of the prompt pipeline fails (e.g.,
      spec synthesis failure or total failure of all test analyses).
  """
  prompts = []
  file_names: list[str] = []
  for fpath, fc in test_files.items():
    testfile_url = f'{utils.WPT_GITHUB_RAW_CONTENTS_URL}{fpath}'
    prompts.append(
      render_template(
        TEST_ANALYSIS_TEMPLATE_PATH,
        testfile_name=fpath.name,
        testfile_url=testfile_url,
        testfile_contents=fc
      )
    )
    file_names.append(fpath.name)

  template_data = {
    'spec_url': feature.spec_link,
    'spec_content': _fetch_spec_content(feature.spec_link),
    'feature_definition': _create_feature_definition(feature)
  }
  spec_synthesis_prompt = render_template(SPEC_SYNTHESIS_TEMPLATE_PATH, **template_data)
  # Add the spec synthesis prompt to the end for batch processing.
  prompts.append(spec_synthesis_prompt)

  gemini_client = GeminiClient()

  all_responses = await gemini_client.get_batch_responses_async(prompts)

  spec_synthesis_response = all_responses.pop()
  if not isinstance(spec_synthesis_response, str):
    raise utils.PipelineError(f'Spec synthesis prompt failure: {spec_synthesis_response}')

  test_analysis_responses_formatted: list[str] = []
  for fname, resp in zip(file_names, all_responses):
    if not isinstance(resp, str):
      logging.error(f'Test analysis prompt failure: {resp}')
      continue
    test_analysis_responses_formatted.append(f'Test {fname} summary:\n')
    test_analysis_responses_formatted.append(resp)
    test_analysis_responses_formatted.append('\n\n')

  if not test_analysis_responses_formatted:
    raise utils.PipelineError('No successful test analysis responses.')

  template_data = {
    'spec_synthesis': spec_synthesis_response,
    'test_analysis': ''.join(test_analysis_responses_formatted)
  }
  gap_analysis_prompt = render_template(GAP_ANALYSIS_TEMPLATE_PATH, **template_data)

  # Use the async version of get_response to keep the whole pipeline non-blocking.
  gap_analysis_response = await gemini_client.get_response_async(gap_analysis_prompt)
  return gap_analysis_response


async def run_wpt_test_eval_pipeline(feature: FeatureEntry) -> core_enums.AITestEvaluationStatus:
  """Execute the AI pipeline for WPT coverage analysis.

  The final report is saved to `feature.ai_test_eval_report`.

  Args:
    feature: The FeatureEntry model containing spec links and WPT descriptions
      needed for the analysis.

  Raises:
    PipelineError: If the pipeline fails due to missing data (e.g., no spec URL)
      or if critical AI generation steps fail.
  """
  if not feature.spec_link:
    raise utils.PipelineError('No spec URL provided.')

  test_locations = utils.extract_wpt_fyi_results_urls(feature.wpt_descr)
  if len(test_locations) == 0:
    raise utils.PipelineError('No valid wpt.fyi results URLs found in WPT description.')

  try:
    test_files, dependency_files = await _get_test_file_contents(test_locations)
  except utils.PipelineError as e:
    feature.ai_test_eval_report = str(e)
    return core_enums.AITestEvaluationStatus.FAILED

  if len(test_files) <= MAX_SINGLE_PROMPT_TEST_COUNT:
    prompt_text = _generate_unified_prompt_text(feature, test_files, dependency_files)

    gemini_client = GeminiClient()
    # Don't use the single prompt if it will overload the context.
    if gemini_client.prompt_exceeds_input_token_limit(prompt_text):
      logging.warning(
        'The unified gap analysis prompt is too large. '
        'Using the 3-prompt flow instead.'
      )
      gap_analysis_response = await prompt_analysis(feature, test_files)
    else:
      gap_analysis_response = unified_prompt_analysis(prompt_text)
  else:
    gap_analysis_response = await prompt_analysis(feature, test_files)

  feature.ai_test_eval_report = gap_analysis_response
  return core_enums.AITestEvaluationStatus.COMPLETE


class GenerateWPTCoverageEvalReportHandler(basehandlers.FlaskHandler):
  """Cloud Task handler for running the AI-powered WPT coverage analysis."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self, **kwargs):
    self.require_task_header()

    feature_id = self.get_int_param('feature_id')
    feature = self.get_validated_entity(feature_id, FeatureEntry)

    logging.info(f'Starting WPT coverage analysis pipeline for feature {feature_id}')

    try:
      result_status = asyncio.run(run_wpt_test_eval_pipeline(feature))
    except Exception as e:
      feature.ai_test_eval_run_status = core_enums.AITestEvaluationStatus.FAILED
      feature.ai_test_eval_status_timestamp = datetime.now()
      feature.ai_test_eval_report = (
        'Web Platform Tests coverage analysis report failed to generate. '
        'Try again later.'
      )
      feature.put()
      error_message = ('WPT coverage analysis report failure for feature '
                       f'{feature_id}: {e}')
      logging.error(error_message)
      return {'message': error_message}

    feature.ai_test_eval_run_status = result_status
    feature.ai_test_eval_status_timestamp = datetime.now()
    feature.put()
    return {'message': 'WPT coverage analysis report generated.'}
