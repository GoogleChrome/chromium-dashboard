# Copyright 2026 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

"""Unit tests for pure AI release note summary generator engine."""

from __future__ import annotations

import testing_config  # isort: skip  # Must be imported before other project modules.

import json
from unittest import mock

from google.adk.events import Event
from google.genai import types

from ai.mock_summary_generator import MockSummaryGenerator
from ai.progress_reporter import (
    FeatureSummaryInput,
    ListProgressReporter,
    SummaryResult,
)
from ai.summary_generator import (
    GeminiSummaryGenerator,
    GeneratedSummaryPayload,
    build_summary_agent,
    parse_summary_result,
)
from internals.core_enums import (
    AISummaryToolName,
    ProgressStepId,
    ProgressStepStatus,
)
from prompts.renderer import FeaturePromptTemplate


class GeminiSummaryGeneratorTest(testing_config.CustomTestCase):
    """Tests pure multi-turn LLM generation, tool dispatching, and telemetry reporting."""

    def setUp(self):
        """Initializes generator and test feature input DTO."""
        self.generator = GeminiSummaryGenerator(
            model_name='gemini-3.1-pro-preview',
        )
        self.feature_input = FeatureSummaryInput(
            name='WebGPU Subgroups',
            summary='Enables SIMD operations across shader invocations in WGSL.',
            shipped_milestone=130,
            spec_link='https://gpuweb.github.io/gpuweb/',
            standard_maturity=1,
            category=2,
            search_tags=('webgpu', 'wgsl', 'subgroups'),
            doc_links=('https://developer.chrome.com/docs/webgpu',),
        )

    def test_parse_summary_result_clean_json(self):
        """Tests parsing clean JSON string into SummaryResult."""
        raw = (
            '{"summary": "Adds WebGPU subgroups.", "rationale": "High'
            ' performance.", "doc_links": ["https://web.dev/webgpu"]}'
        )
        result = parse_summary_result(raw)
        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.suggested_summary, 'Adds WebGPU subgroups.')
        self.assertEqual(result.generation_rationale, 'High performance.')
        self.assertEqual(
            result.suggested_doc_links, ('https://web.dev/webgpu',)
        )
        self.assertEqual(result.raw_response, raw)

    def test_parse_summary_result_markdown_fenced_json(self):
        """Tests parsing markdown code fenced JSON into SummaryResult."""
        raw = (
            '```json\n'
            '{\n'
            '  "summary": "Adds WebGPU subgroups.",\n'
            '  "rationale": "High performance.",\n'
            '  "doc_links": ["https://web.dev/webgpu"]\n'
            '}\n'
            '```'
        )
        result = parse_summary_result(raw)
        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.suggested_summary, 'Adds WebGPU subgroups.')
        self.assertEqual(result.generation_rationale, 'High performance.')
        self.assertEqual(
            result.suggested_doc_links, ('https://web.dev/webgpu',)
        )

    def test_parse_summary_result_empty_string_raises_value_error(self):
        """Tests that empty or whitespace-only strings raise ValueError."""
        with self.assertRaises(ValueError):
            parse_summary_result('')
        with self.assertRaises(ValueError):
            parse_summary_result('   \n\t  ')

    def test_parse_summary_result_non_dict_raises_type_error(self):
        """Tests that non-dict JSON raises TypeError during dataclass unpacking."""
        raw = '["item1", "item2"]'
        with self.assertRaises(TypeError):
            parse_summary_result(raw)

    def test_parse_summary_result_invalid_json_raises_json_decode_error(self):
        """Tests that invalid JSON raises json.JSONDecodeError."""
        raw = 'This is plain text without JSON'
        with self.assertRaises(json.JSONDecodeError):
            parse_summary_result(raw)

    def test_generator_initialization_with_prompt_template_instance(self):
        """Tests generator initialized with FeaturePromptTemplate instance."""
        template = FeaturePromptTemplate('generate_release_notes.md.jinja')
        generator = GeminiSummaryGenerator(
            model_name='gemini-3.1-pro-preview',
            prompt_template=template,
        )
        self.assertEqual(generator.prompt_template, template)

    def test_build_summary_agent_configuration(self):
        """Tests that build_summary_agent returns configured ADK Agent."""
        agent = build_summary_agent(
            model_name='gemini-3.1-pro-preview',
            instruction='Test instructions',
        )
        self.assertEqual(agent.name, 'release_notes_summary_agent')
        self.assertEqual(agent.model, 'gemini-3.1-pro-preview')
        self.assertEqual(agent.instruction, 'Test instructions')
        self.assertEqual(agent.output_schema, GeneratedSummaryPayload)
        self.assertTrue(len(agent.tools) >= 3)

    @mock.patch('ai.summary_generator.Runner')
    def test_generate_summary_single_turn_success(self, mock_runner_cls):
        """Tests successful single-turn generation with ADK Runner."""
        mock_runner = mock.MagicMock()
        event = Event(
            author='release_notes_summary_agent',
            message=types.Content(
                role='model',
                parts=[
                    types.Part.from_text(
                        text=(
                            '{"summary": "WebGPU subgroups allow SIMD.",'
                            ' "rationale": "Enriched.", "doc_links":'
                            ' ["https://web.dev/webgpu"]}'
                        )
                    )
                ],
            ),
        )
        mock_runner.run.return_value = [event]
        mock_runner_cls.return_value = mock_runner

        reporter = ListProgressReporter()
        result = self.generator.generate_summary(
            self.feature_input, reporter=reporter
        )

        self.assertEqual(
            result.suggested_summary, 'WebGPU subgroups allow SIMD.'
        )
        self.assertEqual(result.generation_rationale, 'Enriched.')
        self.assertEqual(
            result.suggested_doc_links, ('https://web.dev/webgpu',)
        )
        self.assertIsNone(result.error_message)

        # Verify telemetry steps
        step_ids = [s.step_id for s in reporter.steps]
        self.assertIn(ProgressStepId.START.value, step_ids)
        self.assertIn(ProgressStepId.LLM_GENERATION.value, step_ids)
        self.assertIn(ProgressStepId.SUCCESS.value, step_ids)

    @mock.patch('ai.summary_generator.Runner')
    def test_generate_summary_multi_turn_with_tool_events(
        self, mock_runner_cls
    ):
        """Tests multi-turn tool execution telemetry recording from ADK events."""
        mock_runner = mock.MagicMock()

        # Tool call event
        fn_call = mock.MagicMock()
        fn_call.name = AISummaryToolName.SEARCH_MDN.value
        fn_call.args = {'query': 'subgroups'}
        event_1 = mock.MagicMock()
        event_1.get_function_calls.return_value = [fn_call]
        event_1.get_function_responses.return_value = []
        event_1.message = None

        # Tool response event
        fn_resp = mock.MagicMock()
        fn_resp.name = AISummaryToolName.SEARCH_MDN.value
        fn_resp.response = {'status': 'success', 'results': []}
        event_2 = mock.MagicMock()
        event_2.get_function_calls.return_value = []
        event_2.get_function_responses.return_value = [fn_resp]
        event_2.message = types.Content(
            role='tool',
            parts=[
                types.Part.from_text(text='Intermediate tool execution text')
            ],
        )

        # Final response event
        event_3 = Event(
            author='release_notes_summary_agent',
            message=types.Content(
                role='model',
                parts=[
                    types.Part.from_text(
                        text=(
                            '{"summary": "Multi-turn summary.", "rationale": "Found'
                            ' in MDN.", "doc_links":'
                            ' ["https://developer.mozilla.org/subgroups"]}'
                        )
                    )
                ],
            ),
        )
        mock_runner.run.return_value = [event_1, event_2, event_3]
        mock_runner_cls.return_value = mock_runner

        reporter = ListProgressReporter()
        result = self.generator.generate_summary(
            self.feature_input, reporter=reporter
        )

        self.assertEqual(result.suggested_summary, 'Multi-turn summary.')
        self.assertEqual(
            result.suggested_doc_links,
            ('https://developer.mozilla.org/subgroups',),
        )

        step_ids = [s.step_id for s in reporter.steps]
        self.assertIn(ProgressStepId.SEARCH_MDN.value, step_ids)
        self.assertIn(ProgressStepId.SUCCESS.value, step_ids)

    @mock.patch('ai.summary_generator.Runner')
    def test_generate_summary_unparseable_output_returns_error_result(
        self, mock_runner_cls
    ):
        """Tests that unparseable model outputs are captured as JSON Parsing Error."""
        mock_runner = mock.MagicMock()
        event = Event(
            author='release_notes_summary_agent',
            message=types.Content(
                role='model',
                parts=[
                    types.Part.from_text(
                        text='This is unparseable plain text from model'
                    )
                ],
            ),
        )
        mock_runner.run.return_value = [event]
        mock_runner_cls.return_value = mock_runner

        reporter = ListProgressReporter()
        result = self.generator.generate_summary(
            self.feature_input, reporter=reporter
        )

        self.assertEqual(result.suggested_summary, '')
        self.assertIn('JSON Parsing Error', result.error_message or '')
        self.assertEqual(
            reporter.steps[-1].status, ProgressStepStatus.FAILED.value
        )

    @mock.patch('ai.summary_generator.Runner')
    def test_generate_summary_runner_exception_returns_error_result(
        self, mock_runner_cls
    ):
        """Tests that ADK Runner errors are captured in SummaryResult.error_message."""
        mock_runner = mock.MagicMock()
        mock_runner.run.side_effect = Exception('Gemini 503 Unavailable')
        mock_runner_cls.return_value = mock_runner

        reporter = ListProgressReporter()
        result = self.generator.generate_summary(
            self.feature_input, reporter=reporter
        )

        self.assertEqual(result.suggested_summary, '')
        self.assertIn('Gemini 503 Unavailable', result.error_message or '')
        self.assertEqual(
            reporter.steps[-1].status, ProgressStepStatus.FAILED.value
        )


class MockSummaryGeneratorTest(testing_config.CustomTestCase):
    """Tests deterministic MockSummaryGenerator."""

    def test_mock_generator_returns_canned_result(self):
        """Tests that MockSummaryGenerator returns canned response and logs steps."""
        mock_gen = MockSummaryGenerator(
            canned_summary='Mock summary.',
            canned_rationale='Mock rationale.',
            canned_doc_links=['https://web.dev/mock'],
        )
        reporter = ListProgressReporter()
        dummy_input = FeatureSummaryInput(name='Test', summary='Test summary')
        result = mock_gen.generate_summary(dummy_input, reporter=reporter)

        self.assertEqual(result.suggested_summary, 'Mock summary.')
        self.assertEqual(result.generation_rationale, 'Mock rationale.')
        self.assertEqual(result.suggested_doc_links, ('https://web.dev/mock',))
        self.assertEqual(len(reporter.steps), 2)
        self.assertEqual(reporter.steps[0].step_id, ProgressStepId.START.value)
        self.assertEqual(
            reporter.steps[1].step_id, ProgressStepId.SUCCESS.value
        )
