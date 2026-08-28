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

from google.cloud import ndb
from wptgen import generate_audit_report

import settings
from ai.progress_reporter import DatastoreProgressReporter, FeatureSummaryInput
from ai.summary_generator import GeminiSummaryGenerator
from framework import (
    basehandlers,
    feature_fingerprint,
    secrets,
    utils,
)
from internals import core_enums
from internals.core_models import (
    FeatureEntry,
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)


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
    """Cloud Task handler for generating an AI release note summary for a feature."""

    IS_INTERNAL_HANDLER = True

    def process_post_data(self, **kwargs):
        """Process POST data for generating an AI summary."""
        self.require_task_header()

        feature_id = self.get_int_param('feature_id')
        force = self.get_bool_param('force', default=False)
        feature = self.get_validated_entity(feature_id, FeatureEntry)

        if feature.deleted:
            logging.info(
                f'Feature {feature_id} is deleted, skipping generation.'
            )
            return {
                'message': f'Feature {feature_id} is deleted.',
                'skipped': True,
                'feature_id': feature_id,
            }

        fingerprint = feature_fingerprint.compute_feature_fingerprint(feature)
        suggestion_key = ndb.Key(FeatureSummarySuggestion, feature_id)
        suggestion: FeatureSummarySuggestion | None = suggestion_key.get()

        # Deduplication: Skip generation if already generated for the same fingerprint.
        if (
            not force
            and suggestion is not None
            and suggestion.source_fingerprint == fingerprint
            and suggestion.suggested_summary
        ):
            logging.info(
                f'Summary for feature {feature_id} is already up-to-date with '
                f'fingerprint {fingerprint}.'
            )
            return {
                'message': f'Summary for feature {feature_id} is already up-to-date.',
                'skipped': True,
                'feature_id': feature_id,
            }

        logging.info(
            f'Starting AI summary generation for feature {feature_id} (force={force})'
        )

        # Clear historical progress timeline steps.
        FeatureSummaryProgressStep.clear_timeline(feature_id, keep_count=0)

        # Ensure GEMINI_API_KEY is loaded and explicitly exposed in the OS environment for the SDK
        if not settings.GEMINI_API_KEY:
            secrets.load_gemini_api_key()
        if settings.GEMINI_API_KEY:
            os.environ['GEMINI_API_KEY'] = settings.GEMINI_API_KEY
            os.environ['GOOGLE_API_KEY'] = settings.GEMINI_API_KEY

        reporter = DatastoreProgressReporter(feature_id)
        feature_input = FeatureSummaryInput.from_feature(feature)
        generator = GeminiSummaryGenerator(
            model_name=settings.SUMMARY_GENERATOR_MODEL,
        )

        result = generator.generate_summary(feature_input, reporter=reporter)

        # Update or create FeatureSummarySuggestion in Datastore.
        if suggestion is None:
            suggestion = FeatureSummarySuggestion(
                id=feature_id,
                original_summary=feature.summary,
                original_doc_links=feature.doc_links or [],
                version_token=1,
            )

        suggestion.source_fingerprint = fingerprint
        suggestion.version_token = (suggestion.version_token or 1) + 1

        if result.error_message:
            suggestion.status = core_enums.SummarySuggestionStatus.UNKNOWN
            suggestion.put()
            error_msg = (
                f'AI summary generation failed for feature {feature_id}: '
                f'{result.error_message}'
            )
            logging.error(error_msg)
            return {'error': error_msg, 'feature_id': feature_id}

        suggestion.suggested_summary = result.suggested_summary
        suggestion.generation_rationale = result.generation_rationale
        suggestion.suggested_doc_links = result.suggested_doc_links
        suggestion.status = core_enums.SummarySuggestionStatus.PENDING
        suggestion.put()

        return {
            'message': f'AI summary generated for feature {feature_id}.',
            'feature_id': feature_id,
            'suggested_summary': result.suggested_summary,
        }
