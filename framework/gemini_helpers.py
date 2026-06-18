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

"""Helper functions for interacting with Gemini AI models.

Provides utilities to evaluate WPT test coverage using Gemini.
"""

import logging
import os
from datetime import datetime

from wptgen import generate_audit_report

import settings
from framework import basehandlers, utils
from internals import core_enums
from internals.core_models import FeatureEntry, FeatureSummarySuggestion


def run_wpt_test_eval_pipeline(
    feature: FeatureEntry,
    include_explainer: bool = False,
) -> core_enums.AITestEvaluationStatus:
    """Execute the AI pipeline for WPT coverage analysis.

    The final report is saved to `feature.ai_test_eval_report`.

    Args:
      feature: The FeatureEntry model containing spec links and WPT descriptions
        needed for the analysis.
      include_explainer: Whether to include the explainer content in the prompt.

    Returns:
      AITestEvaluationStatus indicating success or failure.
    """
    try:
        if not feature.spec_link:
            raise utils.PipelineError('No spec URL provided.')

        test_locations = utils.extract_wpt_fyi_results_urls(feature.wpt_descr)
        if len(test_locations) == 0:
            raise utils.PipelineError(
                'No valid wpt.fyi results URLs found in WPT description.'
            )  # noqa: E501

        # Determine explainer_urls. Passing [] forces wpt-gen to ignore explainers.
        explainer_urls = feature.explainer_links if include_explainer else []

        # Ensure GEMINI_API_KEY is explicitly exposed in the OS environment for the SDK
        if settings.GEMINI_API_KEY:
            os.environ['GEMINI_API_KEY'] = settings.GEMINI_API_KEY

        # Call the programmatic wpt-gen API
        report_markdown = generate_audit_report(
            feature_id=str(feature.key.id()),
            provider='gemini',
            api_key=settings.GEMINI_API_KEY,
            explainer_urls=explainer_urls,
        )
        feature.ai_test_eval_report = report_markdown
        return core_enums.AITestEvaluationStatus.COMPLETE
    except utils.PipelineError as e:
        feature.ai_test_eval_report = str(e)
        return core_enums.AITestEvaluationStatus.FAILED
    except Exception as e:
        feature.ai_test_eval_report = (
            f'Failed to generate WPT coverage report: {e}'
        )
        return core_enums.AITestEvaluationStatus.FAILED


class GenerateWPTCoverageEvalReportHandler(basehandlers.FlaskHandler):
    """Cloud Task handler for running the AI-powered WPT coverage analysis."""

    IS_INTERNAL_HANDLER = True

    def process_post_data(self, **kwargs):
        """Process POST data for the handler."""
        self.require_task_header()

        feature_id = self.get_int_param('feature_id')
        include_explainer = self.get_bool_param('include_explainer', False)
        feature = self.get_validated_entity(feature_id, FeatureEntry)

        logging.info(
            f'Starting WPT coverage analysis pipeline for feature {feature_id}'
        )  # noqa: E501

        try:
            result_status = run_wpt_test_eval_pipeline(
                feature, include_explainer
            )
        except Exception as e:
            feature.ai_test_eval_run_status = (
                core_enums.AITestEvaluationStatus.FAILED
            )
            feature.ai_test_eval_status_timestamp = datetime.now()
            feature.ai_test_eval_report = (
                'Web Platform Tests coverage analysis report failed to generate. '
                'Try again later.'
            )
            feature.put()
            error_message = (
                'WPT coverage analysis report failure for feature '
                f'{feature_id}: {e}'
            )
            logging.error(error_message)
            return {'message': error_message}

        feature.ai_test_eval_run_status = result_status
        feature.ai_test_eval_status_timestamp = datetime.now()
        feature.put()
        return {'message': 'WPT coverage analysis report generated.'}


class GenerateSummaryHandler(basehandlers.FlaskHandler):
    """Cloud Task handler for generating release notes summaries."""

    IS_INTERNAL_HANDLER = True

    def process_post_data(self, **kwargs):
        """Process POST data for the handler."""
        self.require_task_header()

        feature_id = self.get_int_param('feature_id')
        updated_time = self.get_param('updated_time')

        feature = self.get_validated_entity(feature_id, FeatureEntry)

        # Optimistic Concurrency Control
        if updated_time:
            try:
                payload_updated = datetime.fromtimestamp(float(updated_time))
                if feature.updated > payload_updated:
                    logging.info(
                        f'Feature {feature_id} was updated since the task was enqueued. '
                        f'Skipping summary generation. '
                        f'Feature updated: {feature.updated}, Payload updated: {payload_updated}'
                    )
                    # Reset suggestion status to NONE to prevent hanging IN_PROGRESS lock
                    suggestion = FeatureSummarySuggestion.get_by_id(feature_id)
                    if suggestion:
                        suggestion.status = core_enums.SummarySuggestionStatus.NONE.value
                        suggestion.put()
                    return {'message': 'Skipped due to newer updates.'}
            except (ValueError, TypeError) as e:
                logging.warning(
                    f'Invalid updated_time: {updated_time}. Proceeding anyway. Error: {e}'
                )

        logging.info(
            f'Starting AI summary generation Cloud Task for feature {feature_id}'
        )

        from framework import summary_generator

        summary_generator.generate_summary_suggestion(feature_id)

        return {'message': 'AI summary generation task processed.'}
