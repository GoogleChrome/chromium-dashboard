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

"""Unit tests for internals/markdown_helpers module."""

import unittest

from internals import markdown_helpers


class MarkdownHelpersTest(unittest.TestCase):
    """Unit tests for CommonMark markdown rendering, autolinking, and XSS sanitization."""

    def test_render_markdown_empty_and_none(self):
        """Tests that empty strings, whitespace, or None return empty string."""
        self.assertEqual(markdown_helpers.render_markdown(None), '')
        self.assertEqual(markdown_helpers.render_markdown(''), '')

    def test_render_markdown_inline_code(self):
        """Tests that backticks are converted to <code> elements."""
        result = markdown_helpers.render_markdown(
            'Adds support for `WebGPU` subgroups.'
        )
        self.assertIn('<code>WebGPU</code>', result)
        self.assertTrue(result.startswith('<p>'))
        self.assertTrue(result.endswith('</p>'))

    def test_render_markdown_links(self):
        """Tests that markdown links render with target="_blank" and rel="noopener noreferrer"."""
        result = markdown_helpers.render_markdown(
            'See [MDN Documentation](https://developer.mozilla.org/en-US/) for details.'
        )
        self.assertIn(
            '<a href="https://developer.mozilla.org/en-US/" target="_blank" rel="noopener noreferrer">MDN Documentation</a>',
            result,
        )

    def test_render_markdown_bare_url_autolinking(self):
        """Tests that bare http(s) URLs are automatically converted to clickable links."""
        result = markdown_helpers.render_markdown(
            'Check out https://developer.chrome.com/release-notes for more info.'
        )
        self.assertIn(
            '<a href="https://developer.chrome.com/release-notes" target="_blank" rel="noopener noreferrer">https://developer.chrome.com/release-notes</a>',
            result,
        )

    def test_render_markdown_bare_url_trailing_punctuation(self):
        """Tests that trailing punctuation is excluded from the autolinked URL."""
        result = markdown_helpers.render_markdown(
            'Visit https://web.dev/webgpu. Also see https://chrome.com/!'
        )
        self.assertIn(
            '<a href="https://web.dev/webgpu" target="_blank" rel="noopener noreferrer">https://web.dev/webgpu</a>.',
            result,
        )
        self.assertIn(
            '<a href="https://chrome.com/" target="_blank" rel="noopener noreferrer">https://chrome.com/</a>!',
            result,
        )

    def test_render_markdown_code_url_not_autolinked(self):
        """Tests that URLs enclosed in code backticks remain plain code and are not linked."""
        result = markdown_helpers.render_markdown(
            'The URL is `https://example.com/api` in code.'
        )
        self.assertIn('<code>https://example.com/api</code>', result)
        self.assertNotIn('<a href', result)

    def test_render_markdown_intra_word_underscores(self):
        """Tests that CommonMark preserves intra-word underscores without converting to italics."""
        result = markdown_helpers.render_markdown(
            'Updates to navigator_gpu_device and request_video_frame_callback.'
        )
        self.assertIn('navigator_gpu_device', result)
        self.assertIn('request_video_frame_callback', result)
        self.assertNotIn('<em>', result)

    def test_render_markdown_emphasis(self):
        """Tests that bold and italic formatting are converted to strong and em tags."""
        result = markdown_helpers.render_markdown(
            'This is **very important** and *noteworthy*.'
        )
        self.assertIn('<strong>very important</strong>', result)
        self.assertIn('<em>noteworthy</em>', result)

    def test_render_markdown_lists(self):
        """Tests that bullet lists are rendered as unordered list HTML."""
        result = markdown_helpers.render_markdown(
            '* First feature item\n* Second feature item'
        )
        self.assertIn('<ul>', result)
        self.assertIn('<li>First feature item</li>', result)
        self.assertIn('<li>Second feature item</li>', result)
        self.assertIn('</ul>', result)

    def test_render_markdown_multi_paragraphs(self):
        """Tests that double newlines are separated into discrete paragraph tags."""
        result = markdown_helpers.render_markdown(
            'Paragraph one.\n\nParagraph two.'
        )
        self.assertIn('<p>Paragraph one.</p>', result)
        self.assertIn('<p>Paragraph two.</p>', result)

    def test_render_markdown_xss_protection_script_tags(self):
        """Tests that <script> tags in markdown are safely escaped."""
        result = markdown_helpers.render_markdown(
            '<script>alert("XSS")</script>'
        )
        self.assertNotIn('<script>', result)
        self.assertIn(
            '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;', result
        )

    def test_render_markdown_xss_protection_event_handlers(self):
        """Tests that HTML event handlers like onerror are safely escaped."""
        result = markdown_helpers.render_markdown(
            '<img src=x onerror=alert(1)>'
        )
        self.assertNotIn('<img', result)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', result)

    def test_render_markdown_xss_protection_javascript_urls(self):
        """Tests that javascript: URIs in markdown links are neutralized."""
        result = markdown_helpers.render_markdown(
            '[Click here](javascript:alert(1))'
        )
        self.assertNotIn('href="javascript:', result)

    def test_render_markdown_xss_protection_iframes(self):
        """Tests that <iframe> tags in markdown are safely escaped."""
        result = markdown_helpers.render_markdown(
            '<iframe src="https://evil.com"></iframe>'
        )
        self.assertNotIn('<iframe', result)
        self.assertIn('&lt;iframe', result)
