# Copyright 2026 Google LLC
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

"""Unit tests for framework/summary_generator module."""

import io
import json
import urllib.error
from unittest import mock

import testing_config
from framework import summary_generator
from internals.core_enums import AISummaryToolName
from internals.core_models import FeatureEntry


class SummaryGeneratorTest(testing_config.CustomTestCase):
    """Unit tests for feature fingerprint hashing and AI sandbox tools."""

    def setUp(self):
        """Set up test environment and mock feature instances."""
        super().setUp()
        self.sample_feature_dict = {
            'name': 'CSS Subgrid',
            'summary': 'Support for subgrid in CSS Grid Layout.',
            'shipped_milestone': 151,
            'spec_link': 'https://drafts.csswg.org/css-grid-2/',
            'doc_links': [
                'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid'
            ],
            'standard_maturity': 1,
            'category': 2,
            'feature_type': 0,
            'search_tags': ['css', 'grid', 'subgrid'],
            'impl_status_chrome': 1,
        }

    def test_compute_feature_fingerprint__deterministic(self):
        """It computes identical SHA-256 hashes for identical feature definitions."""
        hash1 = summary_generator.compute_feature_fingerprint(
            self.sample_feature_dict
        )
        hash2 = summary_generator.compute_feature_fingerprint(
            self.sample_feature_dict
        )
        self.assertEqual(hash1, hash2)
        self.assertEqual(64, len(hash1))

    def test_compute_feature_fingerprint__entity_vs_dict(self):
        """It produces identical fingerprints for a FeatureEntry entity and an equivalent dict."""
        feature_entity = FeatureEntry(
            id=12345,
            name='CSS Subgrid',
            summary='Support for subgrid in CSS Grid Layout.',
            spec_link='https://drafts.csswg.org/css-grid-2/',
            doc_links=[
                'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid'
            ],
            standard_maturity=1,
            category=2,
            feature_type=0,
            search_tags=['css', 'grid', 'subgrid'],
            impl_status_chrome=1,
        )
        feature_dict = {
            'name': 'CSS Subgrid',
            'summary': 'Support for subgrid in CSS Grid Layout.',
            'spec_link': 'https://drafts.csswg.org/css-grid-2/',
            'doc_links': [
                'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid'
            ],
            'standard_maturity': 1,
            'category': 2,
            'feature_type': 0,
            'search_tags': ['css', 'grid', 'subgrid'],
            'impl_status_chrome': 1,
        }
        hash_entity = summary_generator.compute_feature_fingerprint(
            feature_entity
        )
        hash_dict = summary_generator.compute_feature_fingerprint(feature_dict)
        self.assertEqual(hash_entity, hash_dict)

    def test_compute_feature_fingerprint__detects_summary_change(self):
        """It produces a different hash when the feature summary is modified."""
        original_hash = summary_generator.compute_feature_fingerprint(
            self.sample_feature_dict
        )
        modified_dict = dict(self.sample_feature_dict)
        modified_dict['summary'] = (
            'Updated summary description for CSS Subgrid.'
        )
        modified_hash = summary_generator.compute_feature_fingerprint(
            modified_dict
        )
        self.assertNotEqual(original_hash, modified_hash)

    def test_compute_feature_fingerprint__detects_milestone_change(self):
        """It produces a different hash when the shipped milestone changes."""
        original_hash = summary_generator.compute_feature_fingerprint(
            self.sample_feature_dict
        )
        modified_dict = dict(self.sample_feature_dict)
        modified_dict['shipped_milestone'] = 152
        modified_hash = summary_generator.compute_feature_fingerprint(
            modified_dict
        )
        self.assertNotEqual(original_hash, modified_hash)

    def test_compute_feature_fingerprint__doc_links_order_independent(self):
        """It normalizes doc links order so permutations produce identical fingerprints."""
        dict1 = dict(self.sample_feature_dict)
        dict1['doc_links'] = ['https://example.com/b', 'https://example.com/a']
        dict2 = dict(self.sample_feature_dict)
        dict2['doc_links'] = ['https://example.com/a', 'https://example.com/b']
        self.assertEqual(
            summary_generator.compute_feature_fingerprint(dict1),
            summary_generator.compute_feature_fingerprint(dict2),
        )

    def test_compute_feature_fingerprint__handles_none_and_empty_fields(self):
        """It cleanly handles None or missing feature fields without raising exceptions."""
        minimal_dict = {'name': 'Minimal Feature'}
        fingerprint = summary_generator.compute_feature_fingerprint(
            minimal_dict
        )
        self.assertIsInstance(fingerprint, str)
        self.assertEqual(64, len(fingerprint))

    @mock.patch('wptgen.context._ssrf_safe_opener.open')
    @mock.patch('wptgen.context.validate_url_against_ssrf')
    def test_fetch_url_chunked__success(self, mock_validate, mock_open):
        """It fetches URL bytes safely using the SSRF-safe opener."""
        mock_resp = mock.MagicMock()
        mock_resp.read.side_effect = [b'Hello ', b'World', b'']
        mock_resp.__enter__.return_value = mock_resp
        mock_open.return_value = mock_resp

        result = summary_generator._fetch_url_chunked(
            'https://example.com/test'
        )
        self.assertEqual(b'Hello World', result)
        mock_validate.assert_called_once_with('https://example.com/test')

    @mock.patch('wptgen.context._ssrf_safe_opener.open')
    @mock.patch('wptgen.context.validate_url_against_ssrf')
    def test_fetch_url_chunked__exceeds_max_size(
        self, mock_validate, mock_open
    ):
        """It raises ValueError if response payload exceeds the maximum byte size limit."""
        mock_resp = mock.MagicMock()
        mock_resp.read.side_effect = [
            b'A' * (summary_generator.CHUNK_SIZE)
        ] * 100
        mock_resp.__enter__.return_value = mock_resp
        mock_open.return_value = mock_resp

        with self.assertRaises(ValueError) as cm:
            summary_generator._fetch_url_chunked(
                'https://example.com/large', max_size=1000
            )
        self.assertIn('exceeded maximum allowed limit', str(cm.exception))

    def test_search_mdn_tool__empty_query(self):
        """It returns a failed status response when query is empty or whitespace."""
        res = summary_generator.search_mdn_tool('   ')
        self.assertEqual('failed', res['status'])
        self.assertIn('error', res)

    @mock.patch('framework.summary_generator._fetch_url_chunked')
    def test_search_mdn_tool__success(self, mock_fetch):
        """It successfully queries and parses MDN search API responses."""
        mock_fetch.return_value = json.dumps(
            {
                'documents': [
                    {
                        'title': 'Subgrid - CSS: Cascading Style Sheets | MDN',
                        'mdn_url': '/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid',
                        'summary': 'The subgrid value of grid-template-columns...',
                    }
                ]
            }
        ).encode('utf-8')

        res = summary_generator.search_mdn_tool('CSS Subgrid')
        self.assertEqual('success', res['status'])
        self.assertEqual(1, res['count'])
        self.assertEqual('CSS Subgrid', res['query'])
        self.assertEqual(
            'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid',
            res['results'][0]['url'],
        )

    @mock.patch('framework.summary_generator._fetch_url_chunked')
    def test_search_mdn_tool__http_error_graceful(self, mock_fetch):
        """It returns a structured error object on HTTP or network failures without throwing."""
        mock_fetch.side_effect = urllib.error.HTTPError(
            'https://mdn.example.com', 404, 'Not Found', {}, io.BytesIO()
        )
        res = summary_generator.search_mdn_tool('UnknownAPI')
        self.assertEqual('failed', res['status'])
        self.assertIn('404', res['error'])

    def test_verify_doc_link_tool__empty_url(self):
        """It returns valid=False for empty or whitespace URL inputs."""
        res = summary_generator.verify_doc_link_tool('')
        self.assertFalse(res['valid'])
        self.assertEqual('failed', res['status'])

    @mock.patch('framework.summary_generator._fetch_url_chunked')
    def test_verify_doc_link_tool__valid_html(self, mock_fetch):
        """It validates accessible documentation links and extracts content snippets."""
        mock_fetch.return_value = (
            b'<!DOCTYPE html><html><head><title>MDN Subgrid Guide</title></head>'
            b'<body><h1>Subgrid</h1><p>Subgrid provides grid alignment for children.</p></body></html>'
        )
        res = summary_generator.verify_doc_link_tool(
            'https://developer.mozilla.org/subgrid'
        )
        self.assertTrue(res['valid'])
        self.assertEqual('success', res['status'])
        self.assertEqual(200, res['status_code'])
        self.assertIn('Subgrid provides grid alignment', res['snippet'])

    @mock.patch('framework.summary_generator._fetch_url_chunked')
    def test_verify_doc_link_tool__ssrf_blocked(self, mock_fetch):
        """It handles SSRF rejection gracefully and returns valid=False."""
        mock_fetch.side_effect = ValueError(
            'URL resolves to a restricted IP address: 127.0.0.1'
        )
        res = summary_generator.verify_doc_link_tool('http://127.0.0.1/admin')
        self.assertFalse(res['valid'])
        self.assertEqual('failed', res['status'])
        self.assertIn('restricted IP address', res['error'])

    def test_read_spec_link_tool__empty_url(self):
        """It returns status='failed' for empty spec URLs."""
        res = summary_generator.read_spec_link_tool('')
        self.assertEqual('failed', res['status'])

    @mock.patch('framework.summary_generator._fetch_url_chunked')
    def test_read_spec_link_tool__valid_spec(self, mock_fetch):
        """It extracts clean normative specification text from HTML specifications."""
        mock_fetch.return_value = (
            b'<!DOCTYPE html><html><head><title>CSS Grid Layout Module Level 2</title></head>'
            b'<body><nav>TOC</nav><main><p>This module introduces subgrid features.</p></main>'
            b'<script>console.log("noisy script");</script></body></html>'
        )
        res = summary_generator.read_spec_link_tool(
            'https://drafts.csswg.org/css-grid-2/'
        )
        self.assertEqual('success', res['status'])
        self.assertEqual('CSS Grid Layout Module Level 2', res['title'])
        self.assertIn(
            'This module introduces subgrid features.', res['content_snippet']
        )
        self.assertNotIn('noisy script', res['content_snippet'])

    @mock.patch('framework.summary_generator._fetch_url_chunked')
    def test_read_spec_link_tool__ssrf_blocked(self, mock_fetch):
        """It catches SSRF violations on spec lookups and returns status='failed'."""
        mock_fetch.side_effect = ValueError(
            'URL resolves to a restricted IP address: 10.0.0.1'
        )
        res = summary_generator.read_spec_link_tool(
            'http://10.0.0.1/internal-spec'
        )
        self.assertEqual('failed', res['status'])
        self.assertIn('restricted IP address', res['error'])

    def test_compute_feature_fingerprint__invalid_enum_types_and_strings(self):
        """It safely handles non-digit and malformed enum fields without throwing ValueError."""
        feature_dict = {
            'name': 'CSS Subgrid',
            'summary': 'Support for subgrid.',
            'shipped_milestone': 'not-a-number',
            'standard_maturity': '',
            'category': 'invalid',
            'feature_type': None,
            'impl_status_chrome': False,
            'doc_links': ['https://example.com', None, 'None', ''],
            'search_tags': ['grid', None, 'None', ''],
        }
        fingerprint = summary_generator.compute_feature_fingerprint(
            feature_dict
        )
        self.assertIsInstance(fingerprint, str)
        self.assertEqual(64, len(fingerprint))

    @mock.patch('framework.summary_generator._fetch_url_chunked')
    def test_verify_doc_link_tool__strips_scripts_and_styles(self, mock_fetch):
        """It ensures script and style tags are stripped from doc snippets."""
        mock_fetch.return_value = (
            b'<!DOCTYPE html><html><head><style>body { color: red; }</style>'
            b'<title>Documentation Title</title></head>'
            b'<body><script>const tracker = 1;</script>'
            b'<p>Real documentation text here.</p></body></html>'
        )
        res = summary_generator.verify_doc_link_tool('https://example.com/docs')
        self.assertTrue(res['valid'])
        self.assertEqual('Documentation Title', res['title'])
        self.assertIn('Real documentation text here.', res['snippet'])
        self.assertNotIn('color: red', res['snippet'])
        self.assertNotIn('tracker', res['snippet'])

    @mock.patch('framework.summary_generator._fetch_url_chunked')
    def test_search_mdn_tool__handles_null_documents_and_relative_urls(
        self, mock_fetch
    ):
        """It handles null documents key and relative URLs gracefully."""
        mock_fetch.return_value = json.dumps(
            {
                'documents': [
                    {
                        'title': 'Subgrid',
                        'mdn_url': 'en-US/docs/Web/CSS/CSS_grid_layout/Subgrid',
                        'summary': 'Subgrid feature description.',
                    }
                ]
            }
        ).encode('utf-8')
        res = summary_generator.search_mdn_tool('subgrid')
        self.assertEqual('success', res['status'])
        self.assertEqual(1, res['count'])
        self.assertEqual(
            'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid',
            res['results'][0]['url'],
        )

    def test_tool_map_and_list_parity(self):
        """It verifies that all canonical AISummaryToolName enum entries are registered."""
        for tool_enum in (
            AISummaryToolName.SEARCH_MDN,
            AISummaryToolName.VERIFY_DOC_LINK,
            AISummaryToolName.READ_SPEC_LINK,
        ):
            self.assertIn(tool_enum.value, summary_generator.TOOL_MAP)
            self.assertTrue(
                callable(summary_generator.TOOL_MAP[tool_enum.value])
            )
        self.assertEqual(3, len(summary_generator.AI_SUMMARY_TOOLS))


class GeminiSummaryGeneratorTest(testing_config.CustomTestCase):
    """Unit tests for GeminiSummaryGenerator orchestration engine."""

    def setUp(self):
        """Set up test environment and mock generator dependencies."""
        super().setUp()
        self.mock_client = mock.MagicMock()
        self.generator_v1 = summary_generator.GeminiSummaryGenerator(
            model_name='gemini-2.0-flash',
            prompt_version='v1',
            api_key='test-key',
            client=self.mock_client,
        )
        self.generator_v2 = summary_generator.GeminiSummaryGenerator(
            model_name='gemini-2.0-flash',
            prompt_version='v2',
            api_key='test-key',
            client=self.mock_client,
        )
        self.sample_feature = FeatureEntry(
            id=12345,
            name='CSS Subgrid',
            summary='Support for subgrid in CSS Grid Layout.',
            spec_link='https://drafts.csswg.org/css-grid-2/',
            doc_links=[
                'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid'
            ],
            search_tags=['grid', 'subgrid'],
            category=1,
            feature_type=0,
            standard_maturity=1,
            impl_status_chrome=1,
        )
        self.sample_feature_dict = {
            'name': 'CSS Subgrid',
            'summary': 'Support for subgrid in CSS Grid Layout.',
            'shipped_milestone': 151,
            'spec_link': 'https://drafts.csswg.org/css-grid-2/',
            'doc_links': [
                'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid'
            ],
            'search_tags': ['grid', 'subgrid'],
            'category': 1,
            'feature_type': 0,
            'standard_maturity': 1,
            'impl_status_chrome': 1,
        }

    def tearDown(self):
        """Clean up Datastore entities after each test."""
        summary_generator.ndb.delete_multi(
            summary_generator.FeatureSummarySuggestion.query().fetch(
                keys_only=True
            )
        )
        summary_generator.ndb.delete_multi(
            summary_generator.FeatureSummaryProgressStep.query().fetch(
                keys_only=True
            )
        )
        super().tearDown()

    def test_load_prompt_template__success_and_missing(self):
        """It loads valid prompt templates and raises FileNotFoundError on invalid versions."""
        v1_template = (
            summary_generator.GeminiSummaryGenerator.load_prompt_template('v1')
        )
        self.assertIn('Role and Purpose', v1_template)
        self.assertIn('{{ name }}', v1_template)

        v2_template = (
            summary_generator.GeminiSummaryGenerator.load_prompt_template('v2')
        )
        self.assertIn('search_mdn_tool', v2_template)

        with self.assertRaises(FileNotFoundError):
            summary_generator.GeminiSummaryGenerator.load_prompt_template(
                'non_existent_v99'
            )

    def test_render_prompt(self):
        """It renders prompt templates with sanitized feature variables."""
        feature_dict = {
            'name': 'WebGPU',
            'summary': 'Next-gen graphics <API> with *performance* improvements.',
            'shipped_milestone': 113,
            'spec_link': 'https://www.w3.org/TR/webgpu/',
            'doc_links': [
                'https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API'
            ],
            'search_tags': ['graphics', 'gpu'],
            'standard_maturity': 2,
            'category': 1,
        }
        rendered = self.generator_v1._render_prompt(feature_dict)
        self.assertIn('WebGPU', rendered)
        self.assertIn('Chrome 113', rendered)
        self.assertIn(
            'Next-gen graphics &lt;API&gt; with \\*performance\\* improvements.',
            rendered,
        )
        self.assertIn('https://www.w3.org/TR/webgpu/', rendered)
        self.assertIn(
            'https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API',
            rendered,
        )
        self.assertIn('graphics, gpu', rendered)

    def test_parse_json_response(self):
        """It parses JSON from code fences, raw JSON, and fallback text."""
        # 1. Code fence with ```json
        fenced = (
            'Here is the response:\n```json\n'
            '{\n  "summary": "Subgrid support.",\n  "rationale": "Clear docs.",\n'
            '  "doc_links": ["https://developer.mozilla.org/"]\n}\n```'
        )
        parsed = summary_generator.GeminiSummaryGenerator._parse_json_response(
            fenced
        )
        self.assertEqual('Subgrid support.', parsed['summary'])
        self.assertEqual('Clear docs.', parsed['rationale'])
        self.assertEqual(
            ['https://developer.mozilla.org/'], parsed['doc_links']
        )

        # 2. Generic code fence ```
        generic_fence = '```\n{"summary": "Generic fence.", "rationale": "ok", "doc_links": []}\n```'
        parsed2 = summary_generator.GeminiSummaryGenerator._parse_json_response(
            generic_fence
        )
        self.assertEqual('Generic fence.', parsed2['summary'])

        # 3. Raw plain text fallback
        raw_text = 'Just plain summary text.'
        parsed3 = summary_generator.GeminiSummaryGenerator._parse_json_response(
            raw_text
        )
        self.assertEqual('Just plain summary text.', parsed3['summary'])

    def test_log_step__persists_step_with_utc_timezone_and_parent(self):
        """It logs progress steps parented under FeatureSummarySuggestion with UTC timestamps."""
        feature_id = 10001
        step = self.generator_v1._log_step(
            feature_id=feature_id,
            step_id=summary_generator.ProgressStepId.START,
            status=summary_generator.ProgressStepStatus.IN_PROGRESS,
            message='Step started.',
            tool_name=summary_generator.AISummaryToolName.SEARCH_MDN,
        )
        self.assertEqual('START', step.step_id)
        self.assertEqual('IN_PROGRESS', step.status)
        self.assertEqual('search_mdn_tool', step.tool_name)
        self.assertEqual('Step started.', step.message)
        self.assertIsNotNone(step.start_timestamp.tzinfo)

        # Verify ancestor query
        parent_key = summary_generator.ndb.Key(
            'FeatureSummarySuggestion', feature_id
        )
        persisted_steps = summary_generator.FeatureSummaryProgressStep.query(
            ancestor=parent_key
        ).fetch()
        self.assertEqual(1, len(persisted_steps))
        self.assertEqual(parent_key, persisted_steps[0].key.parent())

    def test_generate_summary__cached_fingerprint_skips_generation(self):
        """It skips LLM execution when feature fingerprint matches existing suggestion."""
        feature_id = 10002
        fingerprint = summary_generator.compute_feature_fingerprint(
            self.sample_feature
        )
        existing = summary_generator.FeatureSummarySuggestion(
            id=feature_id,
            suggested_summary='Existing cached summary.',
            source_fingerprint=fingerprint,
        )
        existing.put()

        suggestion, error = self.generator_v1.generate_summary(
            feature_id=feature_id,
            feature=self.sample_feature,
        )
        self.assertIsNone(error)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            'Existing cached summary.', suggestion.suggested_summary
        )
        self.mock_client.models.generate_content.assert_not_called()

    def test_generate_summary__v1_success(self):
        """It executes V1 generation flow, creates suggestion, and logs progress steps."""
        feature_id = 10003
        mock_response = mock.MagicMock()
        mock_response.text = json.dumps(
            {
                'summary': 'New AI generated subgrid summary.',
                'rationale': 'Detailed rationale.',
                'doc_links': [
                    'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid'
                ],
            }
        )
        self.mock_client.models.generate_content.return_value = mock_response

        suggestion, error = self.generator_v1.generate_summary(
            feature_id=feature_id,
            feature=self.sample_feature,
        )
        self.assertIsNone(error)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            'New AI generated subgrid summary.', suggestion.suggested_summary
        )
        self.assertEqual('Detailed rationale.', suggestion.generation_rationale)
        self.assertEqual(1, suggestion.version_token)
        self.assertEqual('PROPOSED', suggestion.status)

        # Check logged progress steps
        parent_key = summary_generator.ndb.Key(
            'FeatureSummarySuggestion', feature_id
        )
        steps = (
            summary_generator.FeatureSummaryProgressStep.query(
                ancestor=parent_key
            )
            .order(summary_generator.FeatureSummaryProgressStep.start_timestamp)
            .fetch()
        )
        step_ids = [s.step_id for s in steps]
        self.assertIn('START', step_ids)
        self.assertIn('LLM_GENERATION', step_ids)
        self.assertIn('SUCCESS', step_ids)

    def test_generate_summary__v2_multi_turn_tool_calling(self):
        """It executes V2 multi-turn tool calling loop and logs tool steps."""
        feature_id = 10004
        mock_call = mock.MagicMock()
        mock_call.name = 'search_mdn_tool'
        mock_call.args = {'query': 'CSS Subgrid'}

        mock_response = mock.MagicMock()
        mock_response.function_calls = [mock_call]
        mock_response.text = json.dumps(
            {
                'summary': 'Subgrid allows nested grids to participate in sizing.',
                'rationale': 'Verified via MDN tool search.',
                'doc_links': [
                    'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid'
                ],
            }
        )
        self.mock_client.models.generate_content.return_value = mock_response

        with mock.patch.object(self.generator_v2, '_execute_tool') as mock_exec:
            mock_exec.return_value = {
                'status': 'success',
                'results': [
                    {
                        'title': 'Subgrid',
                        'url': 'https://developer.mozilla.org/',
                    }
                ],
            }
            suggestion, error = self.generator_v2.generate_summary(
                feature_id=feature_id,
                feature=self.sample_feature,
            )

        self.assertIsNone(error)
        self.assertIsNotNone(suggestion)
        self.assertEqual(
            'Subgrid allows nested grids to participate in sizing.',
            suggestion.suggested_summary,
        )
        mock_exec.assert_called_once_with(
            'search_mdn_tool', {'query': 'CSS Subgrid'}
        )

        parent_key = summary_generator.ndb.Key(
            'FeatureSummarySuggestion', feature_id
        )
        steps = summary_generator.FeatureSummaryProgressStep.query(
            ancestor=parent_key
        ).fetch()
        tool_steps = [s for s in steps if s.tool_name == 'search_mdn_tool']
        self.assertTrue(len(tool_steps) >= 1)

    def test_generate_summary__dry_run(self):
        """It generates summary without saving to Datastore when dry_run=True."""
        feature_id = 10005
        mock_response = mock.MagicMock()
        mock_response.text = json.dumps(
            {
                'summary': 'Dry run summary.',
                'rationale': 'No DB writes.',
                'doc_links': [],
            }
        )
        self.mock_client.models.generate_content.return_value = mock_response

        suggestion, error = self.generator_v1.generate_summary(
            feature_id=feature_id,
            feature=self.sample_feature,
            dry_run=True,
        )
        self.assertIsNone(error)
        self.assertIsNotNone(suggestion)
        self.assertEqual('Dry run summary.', suggestion.suggested_summary)

        # Verify not in datastore
        persisted = summary_generator.FeatureSummarySuggestion.get_by_id(
            feature_id
        )
        self.assertIsNone(persisted)

    def test_generate_summary__error_handling(self):
        """It captures exceptions, logs FAILED status, and prunes timeline."""
        feature_id = 10006
        self.mock_client.models.generate_content.side_effect = RuntimeError(
            'Model quota exhausted.'
        )

        suggestion, error = self.generator_v1.generate_summary(
            feature_id=feature_id,
            feature=self.sample_feature,
        )
        self.assertIsNone(suggestion)
        self.assertIn('Model quota exhausted.', error)

        parent_key = summary_generator.ndb.Key(
            'FeatureSummarySuggestion', feature_id
        )
        steps = summary_generator.FeatureSummaryProgressStep.query(
            ancestor=parent_key
        ).fetch()
        failed_steps = [s for s in steps if s.status == 'FAILED']
        self.assertEqual(1, len(failed_steps))
        self.assertIn('Model quota exhausted.', failed_steps[0].message)

    def test_get_client__raises_without_api_key(self):
        """It raises ValueError when no GEMINI_API_KEY is provided."""
        gen = summary_generator.GeminiSummaryGenerator(
            model_name='gemini-2.0-flash',
            prompt_version='v1',
            api_key=None,
            client=None,
        )
        with (
            mock.patch('settings.GEMINI_API_KEY', None),
            mock.patch.dict('os.environ', {}, clear=True),
        ):
            with self.assertRaises(ValueError):
                gen._get_client()
