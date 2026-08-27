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

"""Unit tests for AI release note canonical prompt template."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


class GenerateReleaseNotesPromptTest(unittest.TestCase):
    """Tests canonical prompt template structure, XML tagging, and placeholder contracts."""

    def setUp(self):
        """Initializes prompt template path."""
        self.prompt_path = (
            Path(__file__).resolve().parent / 'generate_release_notes.md.jinja'
        )

    def test_prompt_template_exists_and_contains_placeholders(self):
        """Tests that generate_release_notes.md exists and includes exact expected placeholder variables."""
        self.assertTrue(
            self.prompt_path.exists(), f'Missing {self.prompt_path}'
        )

        content = self.prompt_path.read_text(encoding='utf-8')

        expected_placeholders = {
            'name',
            'shipped_milestone',
            'summary',
            'spec_link',
            'doc_links',
            'standard_maturity',
            'category',
            'search_tags',
        }
        found_placeholders = set(re.findall(r'\{\{\s*(\w+)\s*\}\}', content))
        self.assertEqual(
            found_placeholders,
            expected_placeholders,
            f'Mismatch in prompt template placeholders: {found_placeholders ^ expected_placeholders}',
        )

    def test_prompt_declares_tools_and_json_schema(self):
        """Tests that generate_release_notes.md documents interactive tools and valid JSON output schema."""
        content = self.prompt_path.read_text(encoding='utf-8')

        # Tools
        self.assertIn('search_mdn_tool', content)
        self.assertIn('verify_doc_link_tool', content)
        self.assertIn('read_spec_link_tool', content)

        # Verify embedded JSON example is syntactically valid JSON
        match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        self.assertIsNotNone(
            match,
            'JSON schema example block missing in generate_release_notes.md',
        )
        schema_obj = json.loads(match.group(1))
        self.assertEqual(
            set(schema_obj.keys()), {'summary', 'rationale', 'doc_links'}
        )

    def test_prompt_rendering_with_mock_data(self):
        """Tests that generate_release_notes.md renders cleanly with XML structure and mock data."""
        template = self.prompt_path.read_text(encoding='utf-8')

        mock_data = {
            'name': 'Popover API',
            'shipped_milestone': '114',
            'summary': 'Provides standard popover behavior.',
            'spec_link': 'https://html.spec.whatwg.org/multipage/popover.html',
            'doc_links': "['https://developer.chrome.com/docs/popover']",
            'standard_maturity': 'Standard Track',
            'category': 'HTML',
            'search_tags': "['popover', 'html']",
        }

        rendered = template
        for key, val in mock_data.items():
            rendered = rendered.replace(f'{{{{ {key} }}}}', val)

        # Ensure no unresolved placeholders remain
        remaining = re.findall(r'\{\{\s*(\w+)\s*\}\}', rendered)
        self.assertEqual(
            remaining,
            [],
            f'Unresolved placeholders in rendered prompt: {remaining}',
        )
        self.assertIn('<feature_metadata>', rendered)
        self.assertIn('</feature_metadata>', rendered)
        self.assertIn('<name>Popover API</name>', rendered)
        self.assertIn(
            '<feature_summary>Provides standard popover behavior.</feature_summary>',
            rendered,
        )
