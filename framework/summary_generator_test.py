# Copyright 2026 Google Inc. All rights reserved.
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

"""Unit tests for GeminiSummaryGenerator orchestrator engine."""

import testing_config  # isort: skip  # Must be imported before other project modules.
import json
from unittest import mock

from google.cloud import ndb

from framework.summary_generator import (
    GeminiSummaryGenerator,
    MockSummaryGenerator,
    get_error_source_and_message,
    is_transient_error,
)
from internals.core_enums import (
    ProgressStepId,
    ProgressStepStatus,
    SummarySuggestionStatus,
)
from internals.core_models import (
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)


class GeminiSummaryGeneratorTest(testing_config.CustomTestCase):
    """Tests multi-turn orchestration, OCC versioning, and Datastore progress tracking."""

    def setUp(self):
        """Initializes generator and test feature dictionary."""
        self.generator = GeminiSummaryGenerator(
            api_key='fake-test-key',
            model_name='gemini-2.0-flash',
            prompt_version='v1',
        )
        self.feature_id = 10001
        self.feature_dict = {
            'id': self.feature_id,
            'name': 'WebGPU Subgroups',
            'summary': 'Enables SIMD operations across shader invocations in WGSL.',
            'shipped_milestone': 130,
            'spec_link': 'https://gpuweb.github.io/gpuweb/',
            'standard_maturity': 1,
            'category': 2,
            'feature_type': 0,
            'search_tags': ['webgpu', 'wgsl', 'subgroups'],
            'doc_links': ['https://developer.chrome.com/docs/webgpu/subgroups'],
        }

    def tearDown(self):
        """Cleans up Datastore entities between tests."""
        suggestions = FeatureSummarySuggestion.query().fetch(keys_only=True)
        steps = FeatureSummaryProgressStep.query().fetch(keys_only=True)
        ndb.delete_multi(suggestions + steps)

    def test_is_transient_error(self):
        """Tests transient error detection for retries."""
        self.assertTrue(
            is_transient_error(
                RuntimeError('429 ResourceExhausted: rate limit exceeded')
            )
        )
        self.assertTrue(
            is_transient_error(
                RuntimeError('503 Service Unavailable: temporary timeout')
            )
        )
        self.assertTrue(
            is_transient_error(json.JSONDecodeError('Expecting value', '', 0))
        )
        self.assertFalse(is_transient_error(ValueError('Invalid URL schema')))
        self.assertFalse(is_transient_error(KeyError('missing_key')))

    def test_get_error_source_and_message(self):
        """Tests user-friendly error source formatting."""
        src, msg = get_error_source_and_message(
            RuntimeError('429 Rate Limit Exceeded')
        )
        self.assertEqual(src, 'Rate Limit Exceeded')
        self.assertIn('quota exceeded', msg)

        src, msg = get_error_source_and_message(
            RuntimeError('503 Service Unavailable')
        )
        self.assertEqual(src, 'Gemini API Unavailable')
        self.assertIn('temporarily unavailable', msg)

        src, msg = get_error_source_and_message(
            json.JSONDecodeError('bad json', '', 0)
        )
        self.assertEqual(src, 'JSON Parsing Error')

        src, msg = get_error_source_and_message(ValueError('Bad argument'))
        self.assertEqual(src, 'Generation Error')
        self.assertEqual(msg, 'Bad argument')

    def test_mock_summary_generator(self):
        """Tests MockSummaryGenerator generating canned suggestions."""
        mock_gen = MockSummaryGenerator(
            canned_summary='Mock release note.',
            canned_rationale='Mock rationale note.',
            canned_doc_links=['https://example.com/mock-doc'],
        )
        suggestion, err = mock_gen.generate_summary(
            self.feature_id, self.feature_dict
        )
        self.assertIsNone(err)
        self.assertEqual(suggestion.suggested_summary, 'Mock release note.')
        self.assertEqual(
            suggestion.generation_rationale, 'Mock rationale note.'
        )
        self.assertEqual(
            suggestion.suggested_doc_links, ['https://example.com/mock-doc']
        )
        self.assertEqual(suggestion.version_token, 1)

        # Ensure saved to Datastore
        stored = FeatureSummarySuggestion.get_by_id(self.feature_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.suggested_summary, 'Mock release note.')

    def test_load_prompt_template__success_and_missing(self):
        """Tests loading prompt markdown from templates directory."""
        tmpl = self.generator.load_prompt_template('v1')
        self.assertIn('{{ name }}', tmpl)
        self.assertIn('{{ summary }}', tmpl)

        with self.assertRaises(FileNotFoundError):
            self.generator.load_prompt_template('nonexistent_v99')

    def test_render_prompt(self):
        """Tests variable substitution in prompt template."""
        rendered = self.generator._render_prompt(self.feature_dict)
        self.assertIn('WebGPU Subgroups', rendered)
        self.assertIn('Chrome 130', rendered)
        self.assertIn(
            'Enables SIMD operations across shader invocations in WGSL.',
            rendered,
        )
        self.assertIn('https://gpuweb.github.io/gpuweb/', rendered)

    def test_parse_json_response(self):
        """Tests extraction of JSON payload from markdown fences and raw text."""
        fenced_json = """```json
    {
      "summary": "Clean summary.",
      "rationale": "Clear and concise.",
      "doc_links": ["https://example.com/doc"]
    }
    ```"""
        parsed = self.generator._parse_json_response(fenced_json)
        self.assertEqual(parsed['summary'], 'Clean summary.')
        self.assertEqual(parsed['doc_links'], ['https://example.com/doc'])

        plain_text = 'Just plain summary without json.'
        fallback = self.generator._parse_json_response(plain_text)
        self.assertEqual(
            fallback['summary'], 'Just plain summary without json.'
        )

    def test_log_step__persists_step_with_utc_timezone_and_parent(self):
        """Tests progress step ancestor parenting and timestamping."""
        self.generator._log_step(
            feature_id=self.feature_id,
            step_id=ProgressStepId.START,
            status=ProgressStepStatus.SUCCESS,
            message='Rendered v1 template',
        )

        parent_key = ndb.Key('FeatureSummarySuggestion', self.feature_id)
        steps = (
            FeatureSummaryProgressStep.query(ancestor=parent_key)
            .order(FeatureSummaryProgressStep.start_timestamp)
            .fetch()
        )
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].step_id, ProgressStepId.START.value)
        self.assertEqual(steps[0].status, ProgressStepStatus.SUCCESS.value)
        self.assertIsNotNone(steps[0].start_timestamp)
        self.assertIsNotNone(steps[0].end_timestamp)

    def test_generate_summary__cached_fingerprint_skips_generation(self):
        """Tests skipping generation when feature fingerprint matches existing suggestion."""
        from framework.feature_fingerprint import compute_feature_fingerprint

        fingerprint = compute_feature_fingerprint(self.feature_dict)
        existing = FeatureSummarySuggestion(
            id=self.feature_id,
            suggested_summary='Existing summary.',
            generation_rationale='Existing rationale.',
            source_fingerprint=fingerprint,
            status=SummarySuggestionStatus.PROPOSED.value,
            version_token=1,
        )
        existing.put()

        with mock.patch.object(self.generator, '_get_client') as mock_client:
            suggestion, err = self.generator.generate_summary(
                self.feature_id, self.feature_dict
            )
            self.assertIsNone(err)
            self.assertIsNotNone(suggestion)
            self.assertEqual(suggestion.suggested_summary, 'Existing summary.')
            mock_client.assert_not_called()

    @mock.patch('google.genai.Client')
    def test_generate_summary__success_single_turn(self, mock_client_cls):
        """Tests single-turn LLM generation and entity persistence."""
        mock_client = mock.MagicMock()
        mock_client_cls.return_value = mock_client
        self.generator.api_key = 'test-key'

        mock_chat = mock.MagicMock()
        mock_client.chats.create.return_value = mock_chat

        mock_resp = mock.MagicMock()
        mock_resp.function_calls = None
        mock_resp.text = """```json
    {
      "summary": "WebGPU subgroups allow SIMD-level data exchange within compute shaders in Chrome 130.",
      "rationale": "High-impact developer note.",
      "doc_links": ["https://developer.chrome.com/docs/webgpu/subgroups"]
    }
    ```"""
        mock_chat.send_message.return_value = mock_resp

        suggestion, err = self.generator.generate_summary(
            self.feature_id, self.feature_dict
        )
        self.assertIsNone(err)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            suggestion.suggested_summary,
            'WebGPU subgroups allow SIMD-level data exchange within compute'
            ' shaders in Chrome 130.',
        )
        self.assertEqual(suggestion.version_token, 1)
        self.assertEqual(
            suggestion.status, SummarySuggestionStatus.PROPOSED.value
        )

    @mock.patch('google.genai.Client')
    def test_generate_summary__multi_turn_tool_calling(self, mock_client_cls):
        """Tests multi-turn function calling with tool execution."""
        mock_client = mock.MagicMock()
        mock_client_cls.return_value = mock_client
        self.generator.api_key = 'test-key'

        mock_chat = mock.MagicMock()
        mock_client.chats.create.return_value = mock_chat

        # Turn 1: tool call
        fn_call = mock.MagicMock()
        fn_call.name = 'search_mdn_tool'
        fn_call.args = {'query': 'WebGPU subgroups'}

        turn1_resp = mock.MagicMock()
        turn1_resp.function_calls = [fn_call]
        turn1_resp.text = None

        # Turn 2: final answer
        turn2_resp = mock.MagicMock()
        turn2_resp.function_calls = None
        turn2_resp.text = """```json
    {
      "summary": "WebGPU Subgroups enable fast thread communication.",
      "rationale": "Validated via MDN.",
      "doc_links": ["https://developer.mozilla.org/en-US/docs/Web/API/WebGPU"]
    }
    ```"""

        mock_chat.send_message.side_effect = [turn1_resp, turn2_resp]

        with mock.patch.object(
            self.generator,
            '_execute_tool',
            return_value={'status': 'success', 'results': []},
        ) as mock_exec:
            suggestion, err = self.generator.generate_summary(
                self.feature_id, self.feature_dict
            )
            self.assertIsNone(err)
            self.assertIsNotNone(suggestion)
            self.assertEqual(
                suggestion.suggested_summary,
                'WebGPU Subgroups enable fast thread communication.',
            )
            mock_exec.assert_called_once_with(
                'search_mdn_tool', {'query': 'WebGPU subgroups'}
            )

    @mock.patch('google.genai.Client')
    def test_generate_summary__dry_run(self, mock_client_cls):
        """Tests that dry_run=True returns entity without Datastore write."""
        mock_client = mock.MagicMock()
        mock_client_cls.return_value = mock_client
        self.generator.api_key = 'test-key'

        mock_chat = mock.MagicMock()
        mock_client.chats.create.return_value = mock_chat

        mock_resp = mock.MagicMock()
        mock_resp.function_calls = None
        mock_resp.text = """```json
    {
      "summary": "Dry run summary.",
      "rationale": "Testing dry run.",
      "doc_links": []
    }
    ```"""
        mock_chat.send_message.return_value = mock_resp

        suggestion, err = self.generator.generate_summary(
            self.feature_id, self.feature_dict, dry_run=True
        )
        self.assertIsNone(err)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.suggested_summary, 'Dry run summary.')

        # Ensure not stored in Datastore
        stored = FeatureSummarySuggestion.get_by_id(self.feature_id)
        self.assertIsNone(stored)

    @mock.patch('google.genai.Client')
    def test_generate_summary__error_handling(self, mock_client_cls):
        """Tests exception logging and FAILED progress step creation."""
        mock_client = mock.MagicMock()
        mock_client_cls.return_value = mock_client
        self.generator.api_key = 'test-key'

        mock_client.chats.create.side_effect = RuntimeError(
            'Model quota exhausted.'
        )

        suggestion, err = self.generator.generate_summary(
            self.feature_id, self.feature_dict
        )
        self.assertIsNone(suggestion)
        self.assertIn('Model quota exhausted', err)

        parent_key = ndb.Key('FeatureSummarySuggestion', self.feature_id)
        steps = (
            FeatureSummaryProgressStep.query(ancestor=parent_key)
            .order(-FeatureSummaryProgressStep.start_timestamp)
            .fetch()
        )
        self.assertTrue(
            any(s.status == ProgressStepStatus.FAILED.value for s in steps)
        )

    def test_get_client__raises_without_api_key(self):
        """Tests ValueError when no API key is provided."""
        gen = GeminiSummaryGenerator(api_key=None)
        with mock.patch('settings.GEMINI_API_KEY', None):
            with mock.patch.dict('os.environ', {}, clear=True):
                with self.assertRaises(ValueError):
                    gen._get_client()
