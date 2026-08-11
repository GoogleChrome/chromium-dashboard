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

"""Unit tests for AI sandbox tools and SSRF-protected external fetchers."""

import testing_config  # isort: skip  # Must be imported before other project modules.
import io
import json
import urllib.error
from types import MappingProxyType
from unittest import mock

from framework.ai_tools import (
    AI_SUMMARY_TOOLS,
    TOOL_MAP,
    _fetch_url_chunked,
    _SimpleHTMLTextExtractor,
    read_spec_link_tool,
    search_mdn_tool,
    verify_doc_link_tool,
)
from internals.core_enums import AISummaryToolName


class AIToolsTest(testing_config.CustomTestCase):
    """Tests AI Sandbox tools and network parsing."""

    def test_simple_html_text_extractor(self):
        """Tests HTML title extraction and script/style tag stripping."""
        html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>CSS &amp; Anchor Positioning</title>
        <style>body { color: red; }</style>
        <script>console.log("ignore");</script>
      </head>
      <body>
        <nav><a href="/">Home</a></nav>
        <main>
          <h1>Overview</h1>
          <p>Enables tethering elements together.</p>
        </main>
        <footer>Copyright 2026</footer>
      </body>
    </html>
    """
        extractor = _SimpleHTMLTextExtractor()
        extractor.feed(html)
        self.assertEqual(extractor.title, 'CSS & Anchor Positioning')
        clean_text = extractor.get_clean_text()
        self.assertIn('Overview', clean_text)
        self.assertIn('Enables tethering elements together.', clean_text)
        self.assertNotIn('console.log', clean_text)
        self.assertNotIn('color: red', clean_text)
        self.assertNotIn('Home', clean_text)
        self.assertNotIn('Copyright 2026', clean_text)

    @mock.patch('wptgen.context._ssrf_safe_opener.open')
    @mock.patch('wptgen.context.validate_url_against_ssrf')
    def test_fetch_url_chunked__success(self, mock_validate, mock_open):
        """Tests chunked reading of HTTP responses."""
        mock_resp = mock.MagicMock()
        mock_resp.read.side_effect = [b'chunk1', b'chunk2', b'']
        mock_resp.__enter__.return_value = mock_resp
        mock_open.return_value = mock_resp

        data = _fetch_url_chunked('https://example.com/test')
        self.assertEqual(data, b'chunk1chunk2')
        mock_validate.assert_called_once_with('https://example.com/test')

    @mock.patch('wptgen.context._ssrf_safe_opener.open')
    @mock.patch('wptgen.context.validate_url_against_ssrf')
    def test_fetch_url_chunked__exceeds_max_size(
        self, mock_validate, mock_open
    ):
        """Tests ValueError raised when content exceeds max_bytes."""
        mock_resp = mock.MagicMock()
        mock_resp.read.side_effect = [b'x' * 1024, b'y' * 1024, b'']
        mock_resp.__enter__.return_value = mock_resp
        mock_open.return_value = mock_resp

        with self.assertRaises(ValueError) as cm:
            _fetch_url_chunked('https://example.com/huge', max_bytes=1000)
        self.assertIn('exceeded maximum allowed limit', str(cm.exception))

    def test_search_mdn_tool__empty_query(self):
        """Tests empty search query handling."""
        res = search_mdn_tool('')
        self.assertEqual(res['status'], 'failed')
        self.assertIn('empty', res['error'])

    @mock.patch('framework.ai_tools._fetch_url_chunked')
    def test_search_mdn_tool__success(self, mock_fetch):
        """Tests MDN search result parsing and URL absolute resolution."""
        mock_payload = {
            'documents': [
                {
                    'title': 'CSS anchor positioning',
                    'summary': 'Anchor positioning module.',
                    'mdn_url': '/en-US/docs/Web/CSS/CSS_anchor_positioning',
                },
                {
                    'title': 'anchor-name',
                    'summary': 'The anchor-name CSS property.',
                    'mdn_url': (
                        'https://developer.mozilla.org/en-US/docs/Web/CSS/anchor-name'
                    ),
                },
            ]
        }
        mock_fetch.return_value = json.dumps(mock_payload).encode('utf-8')

        res = search_mdn_tool('CSS anchor')
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['results_count'], 2)
        self.assertEqual(
            res['results'][0]['mdn_url'],
            'https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning',
        )
        self.assertEqual(
            res['results'][1]['mdn_url'],
            'https://developer.mozilla.org/en-US/docs/Web/CSS/anchor-name',
        )

    @mock.patch('framework.ai_tools._fetch_url_chunked')
    def test_search_mdn_tool__http_error_graceful(self, mock_fetch):
        """Tests graceful handling of HTTP 404 errors during MDN search."""
        mock_fetch.side_effect = urllib.error.HTTPError(
            'https://developer.mozilla.org/api/v1/search',
            404,
            'Not Found',
            hdrs=None,
            fp=io.BytesIO(b''),
        )
        res = search_mdn_tool('UnknownAPI')
        self.assertEqual(res['status'], 'failed')
        self.assertIn('404', res['error'])

    def test_verify_doc_link_tool__empty_url(self):
        """Tests empty URL handling for doc link verifier."""
        res = verify_doc_link_tool('')
        self.assertEqual(res['status'], 'failed')
        self.assertFalse(res['valid'])

    @mock.patch('framework.ai_tools._fetch_url_chunked')
    def test_verify_doc_link_tool__valid_html(self, mock_fetch):
        """Tests HTML title and snippet extraction for valid doc links."""
        mock_html = b"""
    <html>
      <head><title>WebGPU Guide</title></head>
      <body>
        <p>WebGPU unlocks modern 3D graphics and compute capabilities on the web platform.</p>
      </body>
    </html>
    """
        mock_fetch.return_value = mock_html

        res = verify_doc_link_tool('https://developer.chrome.com/docs/webgpu')
        self.assertEqual(res['status'], 'success')
        self.assertTrue(res['valid'])
        self.assertEqual(res['title'], 'WebGPU Guide')
        self.assertIn('WebGPU unlocks modern 3D graphics', res['snippet'])

    @mock.patch('framework.ai_tools._fetch_url_chunked')
    def test_verify_doc_link_tool__ssrf_blocked(self, mock_fetch):
        """Tests graceful handling when URL is blocked by SSRF checks."""
        mock_fetch.side_effect = ValueError(
            'URL resolves to a restricted IP address: 127.0.0.1'
        )
        res = verify_doc_link_tool('http://127.0.0.1/admin')
        self.assertEqual(res['status'], 'failed')
        self.assertFalse(res['valid'])
        self.assertIn('restricted IP', res['error'])

    def test_read_spec_link_tool__empty_url(self):
        """Tests empty URL handling for spec reader."""
        res = read_spec_link_tool('')
        self.assertEqual(res['status'], 'failed')
        self.assertIn('empty', res['error'])

    @mock.patch('framework.ai_tools._fetch_url_chunked')
    def test_read_spec_link_tool__valid_spec(self, mock_fetch):
        """Tests spec section and normative text extraction."""
        mock_html = b"""
    <html>
      <head><title>CSS Values and Units Module Level 4</title></head>
      <body>
        <section id="calc">
          <h2>The calc() Function</h2>
          <p>The calc() function allows mathematical expressions with addition, subtraction, multiplication, and division.</p>
        </section>
      </body>
    </html>
    """
        mock_fetch.return_value = mock_html

        res = read_spec_link_tool('https://drafts.csswg.org/css-values-4/#calc')
        self.assertEqual(res['status'], 'success')
        self.assertEqual(res['title'], 'CSS Values and Units Module Level 4')
        self.assertIn(
            'The calc() function allows mathematical expressions',
            res['spec_snippet'],
        )

    @mock.patch('framework.ai_tools._fetch_url_chunked')
    def test_read_spec_link_tool__ssrf_blocked(self, mock_fetch):
        """Tests graceful error recovery when spec URL resolves to internal IP."""
        mock_fetch.side_effect = ValueError(
            'URL resolves to a restricted IP address: 10.0.0.1'
        )
        res = read_spec_link_tool('http://10.0.0.1/internal-spec')
        self.assertEqual(res['status'], 'failed')
        self.assertIn('restricted IP', res['error'])

    def test_tool_map_and_list_parity(self):
        """Tests parity between AISummaryToolName enum, MappingProxyType, and tuple registry."""
        expected_tools = {
            AISummaryToolName.SEARCH_MDN.value,
            AISummaryToolName.VERIFY_DOC_LINK.value,
            AISummaryToolName.READ_SPEC_LINK.value,
        }
        self.assertIsInstance(TOOL_MAP, MappingProxyType)
        self.assertIsInstance(AI_SUMMARY_TOOLS, tuple)
        self.assertEqual(set(TOOL_MAP.keys()), expected_tools)
        self.assertEqual(len(AI_SUMMARY_TOOLS), 3)
