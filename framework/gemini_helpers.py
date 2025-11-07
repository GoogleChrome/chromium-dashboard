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

import logging
import re
from flask import render_template

from framework import utils
from framework.gemini_client import GeminiClient
from internals.core_models import FeatureEntry


SPEC_SYNTHESIS_TEMPLATE_PATH = 'prompts/spec-synthesis.html'
TEST_ANALYSIS_TEMPLATE_PATH = 'prompts/test-analysis.html'
GAP_ANALYSIS_TEMPLATE_PATH = 'prompts/gap-analysis.html'
# Regex to determine if the wpt.fyi URL is a test file link.
# Otherwise, it's a directory.
WPT_FILE_REGEX = re.compile(r"\/[^/]*\.[^/]*$")


class PipelineError(Exception):
  """Base exception for errors occurring during the AI evaluation pipeline."""
  pass


def _create_feature_definition(feature: FeatureEntry) -> str:
  return f'Name: {feature.name}\nDescription: {feature.summary}'


async def _get_test_analysis_prompts(test_locations: list[str]) -> list[str]:
  test_urls = []
  test_directories = []
  for test_loc in test_locations:
    if WPT_FILE_REGEX.search(test_loc):
      test_urls.append(test_loc)
    else:
      test_directories.append(test_loc)

  all_file_contents = await utils.get_mixed_wpt_contents_async(
    test_directories, test_urls
  )
  return list(all_file_contents.values())


async def run_wpt_test_eval_pipeline(feature: FeatureEntry) -> None:
  """Execute the three-stage AI pipeline for WPT coverage evaluation.

  This pipeline performs the following steps:
  1. Spec Synthesis: Summarizes the relevant specifications for the feature.
  2. Test Analysis: Analyzes existing WPT files for coverage concurrently.
  3. Gap Analysis: Compares the spec synthesis with test analyses to identify
     missing coverage.

  The final report is saved to `feature.ai_test_eval_report`.

  Args:
    feature: The FeatureEntry model containing spec links and WPT descriptions
      needed for the analysis.

  Raises:
    PipelineError: If the pipeline fails due to missing data (e.g., no spec URL)
      or if critical AI generation steps fail.
  """
  if not feature.spec_link:
    raise PipelineError('No spec URL provided.')

  test_locations = utils.extract_wpt_fyi_results_urls(feature.wpt_descr)
  if len(test_locations) == 0:
    raise PipelineError('No valid wpt.fyi results URLs found in WPT description.')

  template_data = {
    'spec_contents': feature.spec_link,
    'feature_definition': _create_feature_definition(feature)
  }
  spec_synthesis_prompt = render_template(SPEC_SYNTHESIS_TEMPLATE_PATH, **template_data)

  test_analysis_file_contents = await _get_test_analysis_prompts(test_locations)

  prompts = []
  for fc in test_analysis_file_contents:
    prompts.append(
      render_template(TEST_ANALYSIS_TEMPLATE_PATH, testfile_contents=fc)
    )
  # Add the spec synthesis prompt to the end for batch processing.
  prompts.append(spec_synthesis_prompt)

  gemini_client = GeminiClient()

  all_responses = await gemini_client.get_batch_responses_async(prompts)

  spec_synthesis_response = all_responses.pop()
  if not isinstance(spec_synthesis_response, str):
    raise PipelineError(f'Spec synthesis prompt failure: {spec_synthesis_response}')

  test_analysis_responses_formatted = []
  counter = 1
  for resp in all_responses:
    if not isinstance(resp, str):
      logging.warning(f'Test analysis prompt failure: {resp}')
      continue
    test_analysis_responses_formatted.append(f'Test {counter} summary:\n')
    test_analysis_responses_formatted.append(resp)
    test_analysis_responses_formatted.append('\n\n')
    counter += 1

  if not test_analysis_responses_formatted:
    raise PipelineError('No successful test analysis responses.')

  template_data = {
    'spec_synthesis': spec_synthesis_response,
    'test_analysis': ''.join(test_analysis_responses_formatted)
  }
  gap_analysis_prompt = render_template(GAP_ANALYSIS_TEMPLATE_PATH, **template_data)

  # Use the async version of get_response to keep the whole pipeline non-blocking.
  gap_analysis_response = await gemini_client.get_response_async(gap_analysis_prompt)

  feature.ai_test_eval_report = gap_analysis_response
