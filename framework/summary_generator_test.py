# -*- coding: utf-8 -*-
# Copyright 2026 Google Inc.
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

"""Unit tests for framework/summary_generator.py."""

from datetime import date
from unittest import mock

import testing_config
from framework import summary_generator
from internals import core_enums
from internals.core_models import FeatureEntry, FeatureSummarySuggestion


class SummaryGeneratorTest(testing_config.CustomTestCase):
    """Tests for the Summary Generator orchestrator and runner."""

    def setUp(self):
        """Set up test environment and mock data."""
        self.feature = FeatureEntry(
            id=12345,
            name='Test Feature',
            summary='Technical details of the feature.',
            category=1,
            explainer_links=['https://example.com/explainer'],
            spec_link='https://example.com/spec',
        )
        self.feature.put()

    def tearDown(self):
        """Clean up datastore entities."""
        self.feature.key.delete()
        suggestion = FeatureSummarySuggestion.get_by_id(12345)
        if suggestion:
            suggestion.key.delete()

    @mock.patch('settings.USE_MOCK_SUMMARY_GENERATOR', False)
    @mock.patch('settings.GEMINI_API_KEY', 'dummy-key')
    @mock.patch('framework.summary_generator.secrets')
    @mock.patch('google.adk.runners.InMemoryRunner')
    @mock.patch('google.adk.Agent')
    def test_generate_summary_for_feature__success(
        self, mock_agent, mock_runner, mock_secrets
    ):
        """Ensure model output is parsed correctly into SummaryResponseSchema."""
        mock_secrets.load_gemini_api_key.return_value = None

        # Set up runner mock response events
        mock_event = mock.Mock()
        mock_event.get_function_calls.return_value = []
        mock_event.get_function_responses.return_value = []
        mock_event.content = mock.Mock()
        mock_event.content.role = 'model'
        mock_part = mock.Mock()
        mock_part.text = """
        {
            "feasibility_decision": "generate",
            "suggested_summary": "A simplified overview of the feature.",
            "suggested_doc_links": ["https://developer.mozilla.org/docs/Web/API"],
            "baseline_status": "limited",
            "generation_rationale": "Enriched with MDN reference links."
        }
        """
        mock_event.content.parts = [mock_part]

        # InMemoryRunner.run_async returns an async generator of events
        async def mock_run_async(*args, **kwargs):
            yield mock_event

        runner_instance = mock_runner.return_value
        runner_instance.run_async.side_effect = mock_run_async

        result = summary_generator.generate_summary_for_feature(self.feature)

        self.assertIsNotNone(result)
        self.assertEqual(
            result.suggested_summary, 'A simplified overview of the feature.'
        )
        self.assertEqual(
            result.suggested_doc_links,
            ['https://developer.mozilla.org/docs/Web/API'],
        )
        self.assertEqual(result.baseline_status, 'limited')

    @mock.patch('settings.GEMINI_API_KEY', None)
    @mock.patch('framework.summary_generator.secrets')
    def test_generate_summary_for_feature__fallback_mock(self, mock_secrets):
        """Ensure local mock summary is generated if API key is missing."""
        mock_secrets.load_gemini_api_key.return_value = None

        result = summary_generator.generate_summary_for_feature(self.feature)

        self.assertIsNotNone(result)
        self.assertIn('mock summary suggestion', result.suggested_summary)
        self.assertEqual(result.baseline_status, 'limited')

    @mock.patch('framework.summary_generator.generate_summary_for_feature')
    def test_generate_summary_suggestion__success(self, mock_gen_summary):
        """Ensure successful orchestration saves COMPLETE suggestion to DB."""
        mock_schema = summary_generator.SummaryResponseSchema(
            feasibility_decision='generate',
            suggested_summary='AI summary text.',
            suggested_doc_links=['https://mdn.example.com'],
            baseline_status='limited',
            generation_rationale='Enriched with MDN reference links.',
        )
        mock_gen_summary.return_value = mock_schema

        summary_generator.generate_summary_suggestion(12345)

        # Check DB updates
        suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            suggestion.status, core_enums.SummarySuggestionStatus.COMPLETE
        )
        self.assertEqual(suggestion.suggested_summary, 'AI summary text.')
        self.assertEqual(
            suggestion.suggested_doc_links, ['https://mdn.example.com']
        )
        self.assertEqual(
            suggestion.baseline_status, core_enums.BaselineStatus.LIMITED
        )
        self.assertEqual(suggestion.version, summary_generator.GENERATOR_VERSION)
        self.assertEqual(
            suggestion.source_fingerprint,
            summary_generator.compute_feature_fingerprint(self.feature),
        )

    @mock.patch('framework.summary_generator.generate_summary_for_feature')
    def test_generate_summary_suggestion__skip_matching_fingerprint(
        self, mock_gen_summary
    ):
        """Ensure generation is skipped if a complete suggestion with matching fingerprint exists."""
        expected_fp = summary_generator.compute_feature_fingerprint(
            self.feature
        )

        # Pre-populate DB with complete matching suggestion
        suggestion = FeatureSummarySuggestion(
            id=12345,
            status=core_enums.SummarySuggestionStatus.COMPLETE,
            version=summary_generator.GENERATOR_VERSION,
            source_fingerprint=expected_fp,
            suggested_summary='Existing AI summary.',
        )
        suggestion.put()

        summary_generator.generate_summary_suggestion(12345)

        # generate_summary_for_feature should not be called
        mock_gen_summary.assert_not_called()

    @mock.patch('framework.summary_generator.generate_summary_for_feature')
    def test_generate_summary_suggestion__force_bypass(self, mock_gen_summary):
        """Ensure generation is executed if force is True, even if fingerprint matches."""
        expected_fp = summary_generator.compute_feature_fingerprint(
            self.feature
        )

        # Pre-populate DB with complete matching suggestion
        suggestion = FeatureSummarySuggestion(
            id=12345,
            status=core_enums.SummarySuggestionStatus.COMPLETE,
            version=summary_generator.GENERATOR_VERSION,
            source_fingerprint=expected_fp,
            suggested_summary='Existing AI summary.',
        )
        suggestion.put()

        mock_gen_summary.return_value = summary_generator.SummaryResponseSchema(
            feasibility_decision='generate',
            suggested_summary='New AI summary.',
            suggested_doc_links=[],
            baseline_status='widely',
            generation_rationale='Enriched with W3C specification links.',
        )

        summary_generator.generate_summary_suggestion(12345, force=True)

        # generate_summary_for_feature should be called
        mock_gen_summary.assert_called_once_with(
            mock.ANY,
            prompt_version=summary_generator.GENERATOR_VERSION,
            run_id=mock.ANY,
        )

    @mock.patch('framework.summary_generator.generate_summary_for_feature')
    def test_generate_summary_suggestion__skip_discarded_fingerprint(
        self, mock_gen_summary
    ):
        """Ensure generation is skipped if a discarded suggestion with matching fingerprint exists."""
        expected_fp = summary_generator.compute_feature_fingerprint(
            self.feature
        )

        # Pre-populate DB with discarded matching suggestion
        suggestion = FeatureSummarySuggestion(
            id=12345,
            status=core_enums.SummarySuggestionStatus.DISCARDED,
            version=summary_generator.GENERATOR_VERSION,
            source_fingerprint=expected_fp,
            suggested_summary='Rejected AI summary.',
        )
        suggestion.put()

        summary_generator.generate_summary_suggestion(12345)

        # generate_summary_for_feature should not be called
        mock_gen_summary.assert_not_called()

    @mock.patch('framework.summary_generator.generate_summary_for_feature')
    def test_generate_summary_suggestion__backup_on_regeneration(
        self, mock_gen_summary
    ):
        """Ensure regeneration of an already applied suggestion backs up approved values."""
        # 1. Pre-populate the suggestion as APPLIED
        suggestion = FeatureSummarySuggestion(
            id=12345,
            status=core_enums.SummarySuggestionStatus.APPLIED,
            version=summary_generator.GENERATOR_VERSION,
            suggested_summary='Old approved summary.',
            suggested_doc_links=['https://mdn.example.com/old'],
            baseline_status=core_enums.BaselineStatus.NEWLY,
            baseline_newly_date=date(2024, 3, 15),
        )
        suggestion.put()

        # Update the feature summary to match the approved value
        self.feature.summary = 'Old approved summary.'
        self.feature.doc_links = ['https://mdn.example.com/old']
        self.feature.put()

        # Mock generator output for the new generation
        mock_gen_summary.return_value = summary_generator.SummaryResponseSchema(
            feasibility_decision='generate',
            suggested_summary='New LLM suggestion summary.',
            suggested_doc_links=['https://mdn.example.com/new'],
            baseline_status='newly',
            baseline_newly_date='2024-03-20',
            generation_rationale='Enriched with newer MDN documents.',
        )

        summary_generator.generate_summary_suggestion(12345, force=True)

        # Verify that the DB suggestion has the new values, BUT has backed up the old approved ones!
        updated_suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertIsNotNone(updated_suggestion)
        self.assertEqual(
            updated_suggestion.status,
            core_enums.SummarySuggestionStatus.COMPLETE,
        )
        
        # New values from generator
        self.assertEqual(
            updated_suggestion.suggested_summary,
            'New LLM suggestion summary.',
        )
        self.assertEqual(
            updated_suggestion.baseline_status,
            core_enums.BaselineStatus.NEWLY,
        )
        self.assertEqual(
            updated_suggestion.baseline_newly_date, date(2024, 3, 20)
        )

        # Backed up values!
        self.assertEqual(
            updated_suggestion.original_summary, 'Old approved summary.'
        )
        self.assertCountEqual(
            updated_suggestion.original_doc_links,
            ['https://mdn.example.com/old'],
        )
        self.assertEqual(
            updated_suggestion.original_baseline_status, 'newly'
        )
        self.assertEqual(
            updated_suggestion.original_baseline_newly_date,
            date(2024, 3, 15),
        )
        self.assertIsNone(updated_suggestion.original_baseline_widely_date)

    @mock.patch('framework.summary_generator.generate_summary_for_feature')
    def test_generate_summary_suggestion__failure(self, mock_gen_summary):
        """Ensure failed orchestration sets status to FAILED."""
        mock_gen_summary.side_effect = Exception('Gemini API Error')

        summary_generator.generate_summary_suggestion(12345)

        # Check DB updates
        suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            suggestion.status, core_enums.SummarySuggestionStatus.FAILED
        )

    @mock.patch('framework.summary_generator.generate_summary_for_feature')
    def test_generate_summary_suggestion__permanent_failure_no_retry(self, mock_gen_summary):
        """Ensure a permanent error sets status to FAILED and does not re-raise."""
        mock_gen_summary.side_effect = ValueError('Invalid configuration')

        # Should not raise any exception
        try:
            summary_generator.generate_summary_suggestion(12345)
        except Exception as e:
            self.fail(f'Permanent error should not be re-raised, but got: {e}')

        suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            suggestion.status, core_enums.SummarySuggestionStatus.FAILED
        )

    @mock.patch('framework.summary_generator.get_task_retry_count')
    @mock.patch('framework.summary_generator.generate_summary_for_feature')
    def test_generate_summary_suggestion__transient_failure_triggers_retry(self, mock_gen_summary, mock_retry_count):
        """Ensure a transient error does not set status to FAILED, and re-raises to trigger retry."""
        from google.genai.errors import ServerError
        
        # ServerError is classified as a transient error
        mock_gen_summary.side_effect = ServerError(503, {'message': 'Service Unavailable'}, None)
        mock_retry_count.return_value = 0 # First attempt (0 retries)

        # Should re-raise the ServerError
        with self.assertRaises(ServerError):
            summary_generator.generate_summary_suggestion(12345)

        # Status should NOT be FAILED (should remain IN_PROGRESS)
        suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            suggestion.status, core_enums.SummarySuggestionStatus.IN_PROGRESS
        )

    @mock.patch('framework.summary_generator.get_task_retry_count')
    @mock.patch('framework.summary_generator.generate_summary_for_feature')
    def test_generate_summary_suggestion__transient_failure_exhausted_fails_permanently(self, mock_gen_summary, mock_retry_count):
        """Ensure that if transient errors persist and exceed MAX_TRANSIENT_RETRIES, it fails permanently."""
        from google.genai.errors import ServerError
        
        mock_gen_summary.side_effect = ServerError(503, {'message': 'Service Unavailable'}, None)
        mock_retry_count.return_value = 5 # 6th attempt (exceeds MAX_TRANSIENT_RETRIES = 5)

        # Should NOT raise any exception (swallowed to terminate the task)
        try:
            summary_generator.generate_summary_suggestion(12345)
        except Exception as e:
            self.fail(f'Exhausted transient error should not be re-raised, but got: {e}')

        # Status should be set to OVERLOADED permanently
        suggestion = FeatureSummarySuggestion.get_by_id(12345)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            suggestion.status, core_enums.SummarySuggestionStatus.OVERLOADED
        )
    @mock.patch('settings.USE_MOCK_SUMMARY_GENERATOR', False)
    @mock.patch('settings.GEMINI_API_KEY', 'dummy-key')
    @mock.patch('framework.summary_generator.secrets')
    def test_adk_client_initialization_smoke_test(self, mock_secrets):
        """Verify ADK Agent can be initialized without mock, validating env var contract."""
        mock_secrets.load_gemini_api_key.return_value = None

        # We want to ensure that the environment variables set by get_summary_generator
        # are sufficient for ADK to initialize its client without throwing ValueError.
        generator = summary_generator.get_summary_generator()
        self.assertIsNotNone(generator)

        # Import ADK Gemini model class
        from google.adk.models import Gemini

        import settings

        # Instantiate the model object directly (this is what ADK does internally)
        model = Gemini(model=settings.SUMMARY_GENERATOR_MODEL)
        self.assertIsNotNone(model)

        # Force client initialization by accessing the cached property.
        # This is where it will throw ValueError if the key is missing/unrecognized.
        try:
            client = model.api_client
            self.assertIsNotNone(client)
        except ValueError as e:
            self.fail(f'ADK failed to resolve API key from environment: {e}')


class SummaryGeneratorToolsTest(testing_config.CustomTestCase):
    """Tests for the helper tool functions inside summary_generator.py."""

    @mock.patch('framework.summary_generator.requests.get')
    def test_search_mdn__success(self, mock_get):
        """Ensure search_mdn handles success response and extracts details correctly."""
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'documents': [
                {
                    'title': 'Feature API',
                    'mdn_url': '/docs/Feature_API',
                    'summary': 'Docs for Feature API.',
                }
            ]
        }
        mock_get.return_value = mock_resp

        result = summary_generator.search_mdn('Feature')

        self.assertIn('Title: Feature API', result)
        self.assertIn(
            'URL: https://developer.mozilla.org/docs/Feature_API', result
        )
        self.assertIn('Summary: Docs for Feature API.', result)

    @mock.patch('framework.summary_generator.requests.get')
    def test_search_mdn__failure_http(self, mock_get):
        """Ensure search_mdn handles non-200 HTTP statuses gracefully."""
        mock_resp = mock.Mock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        result = summary_generator.search_mdn('Feature')

        self.assertEqual(result, 'MDN search failed with status 500.')

    @mock.patch('framework.summary_generator.requests.get')
    def test_search_mdn__failure_exception(self, mock_get):
        """Ensure search_mdn handles requests exceptions gracefully."""
        mock_get.side_effect = Exception('Connection Timeout')

        result = summary_generator.search_mdn('Feature')

        self.assertEqual(result, 'Error searching MDN: Connection Timeout')

    @mock.patch('framework.summary_generator.requests.get')
    @mock.patch('framework.summary_generator.requests.head')
    def test_verify_doc_link__success_head(self, mock_head, mock_get):
        """Ensure verify_doc_link succeeds if HEAD request returns 200."""
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_head.return_value = mock_resp

        result = summary_generator.verify_doc_link('https://developer.mozilla.org/en-US/')

        self.assertEqual(result, 'Valid')
        mock_head.assert_called_once()
        mock_get.assert_not_called()

    @mock.patch('framework.summary_generator.requests.get')
    @mock.patch('framework.summary_generator.requests.head')
    def test_verify_doc_link__success_get_fallback(self, mock_head, mock_get):
        """Ensure verify_doc_link falls back to GET if HEAD request returns non-200 and succeeds."""
        mock_resp_head = mock.Mock()
        mock_resp_head.status_code = 405  # Method Not Allowed
        mock_head.return_value = mock_resp_head

        mock_resp_get = mock.Mock()
        mock_resp_get.status_code = 200
        mock_get.return_value = mock_resp_get

        result = summary_generator.verify_doc_link('https://developer.mozilla.org/en-US/')

        self.assertEqual(result, 'Valid')
        mock_head.assert_called_once()
        mock_get.assert_called_once()

    @mock.patch('framework.summary_generator.requests.get')
    @mock.patch('framework.summary_generator.requests.head')
    def test_verify_doc_link__failure(self, mock_head, mock_get):
        """Ensure verify_doc_link returns failure string if both HEAD and GET fail."""
        mock_resp_head = mock.Mock()
        mock_resp_head.status_code = 404
        mock_head.return_value = mock_resp_head

        mock_resp_get = mock.Mock()
        mock_resp_get.status_code = 404
        mock_get.return_value = mock_resp_get

        result = summary_generator.verify_doc_link('https://developer.mozilla.org/en-US/')

        self.assertEqual(result, 'Invalid status: 404')

    @mock.patch('framework.summary_generator.requests.head')
    def test_verify_doc_link__exception(self, mock_head):
        """Ensure verify_doc_link handles network exceptions gracefully."""
        mock_head.side_effect = Exception('Host not found')

        result = summary_generator.verify_doc_link('https://developer.mozilla.org/en-US/')

        self.assertEqual(result, 'Error: Host not found')

    def test_is_safe_url__spec_allowlist(self):
        """Ensure is_safe_url correctly filters domains against ALLOWED_SPEC_DOMAINS."""
        # Allowed spec domains
        self.assertTrue(summary_generator.is_safe_url('https://w3.org/TR/css-paint/', summary_generator.ALLOWED_SPEC_DOMAINS))
        self.assertTrue(summary_generator.is_safe_url('https://drafts.csswg.org/css-grid/', summary_generator.ALLOWED_SPEC_DOMAINS))
        self.assertTrue(summary_generator.is_safe_url('https://w3c.github.io/webgpu/', summary_generator.ALLOWED_SPEC_DOMAINS))
        self.assertTrue(summary_generator.is_safe_url('https://github.com/w3c/explainer', summary_generator.ALLOWED_SPEC_DOMAINS))
        
        # Blocked domains (even if allowed in other lists, e.g. MDN)
        self.assertFalse(summary_generator.is_safe_url('https://developer.mozilla.org', summary_generator.ALLOWED_SPEC_DOMAINS))
        self.assertFalse(summary_generator.is_safe_url('https://web.dev/popover', summary_generator.ALLOWED_SPEC_DOMAINS))
        self.assertFalse(summary_generator.is_safe_url('https://evilsite.ru/exploit', summary_generator.ALLOWED_SPEC_DOMAINS))

    def test_is_safe_url__explainer_allowlist(self):
        """Ensure is_safe_url correctly filters domains against ALLOWED_EXPLAINER_DOMAINS."""
        # Allowed explainer domains
        self.assertTrue(summary_generator.is_safe_url('https://github.com/w3c/explainer', summary_generator.ALLOWED_EXPLAINER_DOMAINS))
        self.assertTrue(summary_generator.is_safe_url('https://raw.githubusercontent.com/explain.md', summary_generator.ALLOWED_EXPLAINER_DOMAINS))
        
        # Blocked domains (e.g. MDN or CSSWG)
        self.assertFalse(summary_generator.is_safe_url('https://developer.mozilla.org', summary_generator.ALLOWED_EXPLAINER_DOMAINS))
        self.assertFalse(summary_generator.is_safe_url('https://drafts.csswg.org/css-grid/', summary_generator.ALLOWED_EXPLAINER_DOMAINS))

    def test_is_safe_url__doc_allowlist(self):
        """Ensure is_safe_url correctly filters domains against ALLOWED_DOC_DOMAINS."""
        # Allowed doc domains
        self.assertTrue(summary_generator.is_safe_url('https://developer.mozilla.org/en-US/', summary_generator.ALLOWED_DOC_DOMAINS))
        self.assertTrue(summary_generator.is_safe_url('https://web.dev/popover/', summary_generator.ALLOWED_DOC_DOMAINS))
        
        # Blocked domains (e.g. GitHub or W3C specs)
        self.assertFalse(summary_generator.is_safe_url('https://github.com/w3c/explainer', summary_generator.ALLOWED_DOC_DOMAINS))
        self.assertFalse(summary_generator.is_safe_url('https://w3.org/TR/css-paint/', summary_generator.ALLOWED_DOC_DOMAINS))

    @mock.patch('framework.summary_generator.requests.head')
    def test_verify_doc_link__blocked_by_sandbox(self, mock_head):
        """Ensure verify_doc_link returns a blocked error without making HTTP calls for spec/explainer domains."""
        result = summary_generator.verify_doc_link('https://github.com/w3c/explainer')
        self.assertEqual(result, 'Error: Blocked untrusted URL (unauthorized domain)')
        mock_head.assert_not_called()

    @mock.patch('framework.summary_generator.requests.get')
    def test_read_spec_link__blocked_by_sandbox(self, mock_get):
        """Ensure read_spec_link returns blocked error for non-spec domains (like MDN or raw github)."""
        result = summary_generator.read_spec_link('https://developer.mozilla.org/docs')
        self.assertEqual(result, 'Error: Blocked untrusted URL (unauthorized domain)')
        mock_get.assert_not_called()

    @mock.patch('framework.summary_generator.requests.get')
    def test_read_explainer_link__blocked_by_sandbox(self, mock_get):
        """Ensure read_explainer_link returns blocked error for non-explainer domains (like MDN)."""
        result = summary_generator.read_explainer_link('https://developer.mozilla.org/docs')
        self.assertEqual(result, 'Error: Blocked untrusted URL (unauthorized domain)')
        mock_get.assert_not_called()
