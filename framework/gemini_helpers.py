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
import re
from flask import render_template

from framework import basehandlers, utils
from framework.gemini_client import GeminiClient
from internals import core_enums
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


async def _get_test_analysis_prompts(test_locations: list[str]) -> dict[str, str]:
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
  return all_file_contents


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

  file_names: list[str] = []
  prompts = []
  for fname, fc in test_analysis_file_contents.items():
    prompts.append(
      render_template(TEST_ANALYSIS_TEMPLATE_PATH, testfile_contents=fc)
    )
    file_names.append(fname)
  # Add the spec synthesis prompt to the end for batch processing.
  prompts.append(spec_synthesis_prompt)

  gemini_client = GeminiClient()

  all_responses = await gemini_client.get_batch_responses_async(prompts)

  spec_synthesis_response = all_responses.pop()
  if not isinstance(spec_synthesis_response, str):
    raise PipelineError(f'Spec synthesis prompt failure: {spec_synthesis_response}')

  test_analysis_responses_formatted: list[str] = []
  for fname, resp in zip(file_names, all_responses):
    if not isinstance(resp, str):
      logging.error(f'Test analysis prompt failure: {resp}')
      continue
    print(f'\n\n\n\n TEST NAME: {fname}')
    test_analysis_responses_formatted.append(f'Test {fname} summary:\n')
    test_analysis_responses_formatted.append(resp)
    test_analysis_responses_formatted.append('\n\n')

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


class GenerateWPTCoverageEvalReportHandler(basehandlers.FlaskHandler):
  """Cloud Task handler for running the AI-powered WPT coverage evaluation."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self, **kwargs):
    self.require_task_header()

    feature_id = self.get_int_param('feature_id')
    feature = self.get_validated_entity(feature_id, FeatureEntry)

    logging.info(f'Starting WPT coverage evaluation pipeline for feature {feature_id}')

    try:
      asyncio.run(run_wpt_test_eval_pipeline(feature))
    except Exception as e:
      feature.ai_test_eval_run_status = core_enums.AITestEvaluationStatus.FAILED
      feature.ai_test_eval_status_timestamp = datetime.now()
      feature.ai_test_eval_report = (
        'Web Platform Tests coverage evaluation report failed to generate. '
        'Try again later.'
      )
      feature.put()
      error_message = ('WPT coverage evaluation report failure for feature '
                       f'{feature_id}: {e}')
      logging.error(error_message)
      return {'message': error_message}

    feature.ai_test_eval_run_status = core_enums.AITestEvaluationStatus.COMPLETE
    feature.ai_test_eval_status_timestamp = datetime.now()
    feature.put()
    return {'message': 'WPT coverage evaluation report generated.'}
