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


async def _get_test_file_contents(test_locations: list[str]) -> utils.WPTContents:
  """Obtain the contents of test files, as well as the contents of their dependencies."""
  test_urls = []
  test_directories = []
  for test_loc in test_locations:
    if WPT_FILE_REGEX.search(test_loc):
      test_urls.append(test_loc)
    else:
      test_directories.append(test_loc)

  return await utils.get_mixed_wpt_contents_async(test_directories, test_urls)


def _generate_unified_prompt_text(
  feature: FeatureEntry,
  wpt_contents: utils.WPTContents,
) -> str:
  """Generates the text for the unified gap analysis prompt."""
  template_data = {
    'spec_url': feature.spec_link,
    'spec_content': _fetch_spec_content(feature.spec_link),
    'feature_name': feature.name,
    'feature_summary': feature.summary,
    'test_files': wpt_contents.test_contents,
    'dependency_files': wpt_contents.dependency_contents,
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


async def prompt_analysis(feature: FeatureEntry, wpt_contents: utils.WPTContents) -> str:
  """Evaluates WPT coverage using a multi-stage prompt flow.

  This method is used when the number of test files is too large for a single
  prompt. It breaks the analysis into three distinct stages:
  1. Spec Synthesis: Summarizes the spec into a concise reference.
  2. Test Analysis: Analyzes test files in packed batches to maximize context usage.
  3. Gap Analysis: Compares the spec synthesis with the aggregated test
     summaries to identify gaps.

  Args:
    feature: The feature entry containing metadata and the spec URL.
    wpt_contents: The contents of the test files and dependencies.

  Returns:
    A string containing the generated coverage report.

  Raises:
    PipelineError: If any critical stage of the prompt pipeline fails.
  """
  gemini_client = GeminiClient()
  prompts = []

  test_contents = wpt_contents.test_contents
  dependency_contents = wpt_contents.dependency_contents

  current_test_files: list[dict[str, Path | str]] = []
  current_dependencies: dict[Path, str] = {}

  for fpath, fc in test_contents.items():
    # 1. Identify dependencies for the current file
    file_deps = {}
    if fpath in wpt_contents.test_to_dependencies_map:
      for dep_path in wpt_contents.test_to_dependencies_map[fpath]:
        content = (
          dependency_contents[dep_path]
          if dep_path in dependency_contents else test_contents.get(dep_path)
        )
        if content:
          file_deps[dep_path] = content

    # 2. Create candidate batch (current batch + new file)
    candidate_test_files = current_test_files + [{'path': fpath, 'contents': fc}]
    candidate_dependencies = current_dependencies.copy()
    candidate_dependencies.update(file_deps)

    # Render candidate prompt to check token limits
    # dependency_files arg: list of (Path, content) tuples
    candidate_prompt = render_template(
      TEST_ANALYSIS_TEMPLATE_PATH,
      test_files=candidate_test_files,
      dependency_files=list(candidate_dependencies.items()),
    )

    # 3. Check token limit
    if gemini_client.prompt_exceeds_input_token_limit(candidate_prompt):
      # Commit the previous valid batch if it exists
      if current_test_files:
        prompts.append(
            render_template(
              TEST_ANALYSIS_TEMPLATE_PATH,
              test_files=current_test_files,
              dependency_files=list(current_dependencies.items()),
            )
        )
        # Reset the buffer; we will decide what to put in it next
        current_test_files = []
        current_dependencies = {}

      # Check if the current file + its dependencies fit on their own
      single_file_list: list[dict[str, Path | str]] = [{'path': fpath, 'contents': fc}]

      single_prompt_with_deps = render_template(
        TEST_ANALYSIS_TEMPLATE_PATH,
        test_files=single_file_list,
        dependency_files=list(file_deps.items())
      )
      if gemini_client.prompt_exceeds_input_token_limit(single_prompt_with_deps):
        # Edge Case: The file + deps is too large. (this should be very rare).
        # Create a prompt with ONLY the test file (omit dependencies) and commit immediately.
        logging.warning(
            f'Test file {fpath} with dependencies exceeds token limit. '
            'Generating prompt without dependencies.'
        )
        prompts.append(
            render_template(
              TEST_ANALYSIS_TEMPLATE_PATH,
              test_files=single_file_list,
              dependency_files=[]
            )
        )
        # Buffer remains empty for the next iteration
        current_test_files = []
        current_dependencies = {}
      else:
        # Start the new batch.
        current_test_files = single_file_list
        current_dependencies = file_deps

    else:
      # It fits; update the current batch state
      current_test_files = candidate_test_files
      current_dependencies = candidate_dependencies

  # 4. Commit any remaining tests in the buffer
  if current_test_files:
    prompts.append(
        render_template(
          TEST_ANALYSIS_TEMPLATE_PATH,
          test_files=current_test_files,
          dependency_files=list(current_dependencies.items()),
        )
    )

  template_data = {
    'spec_url': feature.spec_link,
    'spec_content': _fetch_spec_content(feature.spec_link),
    'feature_definition': _create_feature_definition(feature)
  }
  spec_synthesis_prompt = render_template(SPEC_SYNTHESIS_TEMPLATE_PATH, **template_data)
  # Add the spec synthesis prompt to the end for batch processing.
  prompts.append(spec_synthesis_prompt)

  all_responses = await gemini_client.get_batch_responses_async(prompts)

  spec_synthesis_response = all_responses.pop()
  if not isinstance(spec_synthesis_response, str):
    raise utils.PipelineError(f'Spec synthesis prompt failure: {spec_synthesis_response}')

  # Log if any test summary responses failed.
  for resp in all_responses:
    if not isinstance(resp, str):
      logging.error(f'Test analysis prompt failure: {resp}')
      continue
  test_analysis_responses = [resp for resp in all_responses if resp]

  if not test_analysis_responses:
    raise utils.PipelineError('No successful test analysis responses.')

  template_data = {
    'spec_synthesis': spec_synthesis_response,
    'test_summaries': test_analysis_responses,
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
    wpt_contents = await _get_test_file_contents(test_locations)
  except utils.PipelineError as e:
    feature.ai_test_eval_report = str(e)
    return core_enums.AITestEvaluationStatus.FAILED

  prompt_text = _generate_unified_prompt_text(feature, wpt_contents)

  gemini_client = GeminiClient()
  # Don't use the single prompt if it will overload the context.
  if gemini_client.prompt_exceeds_input_token_limit(prompt_text):
    logging.warning(
      'The unified gap analysis prompt is too large. '
      'Using the 3-prompt flow instead.'
    )
    gap_analysis_response = await prompt_analysis(feature, wpt_contents)
  else:
    gap_analysis_response = unified_prompt_analysis(prompt_text)

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
