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

"""Unit tests for AI release note markdown prompt templates."""

import testing_config  # isort: skip  # Must be imported before other project modules.
import json
import re
from pathlib import Path


class PromptsTest(testing_config.CustomTestCase):
    """Tests prompt template structure and placeholder contracts."""

    def setUp(self):
        """Initializes prompt directory path."""
        self.prompts_dir = Path(__file__).resolve().parent / 'prompts'

    def test_v1_prompt_template_exists_and_contains_placeholders(self):
        """Tests that v1.md exists and includes exact expected placeholder variables."""
        v1_path = self.prompts_dir / 'v1.md'
        self.assertTrue(v1_path.exists(), f'Missing {v1_path}')

        content = v1_path.read_text(encoding='utf-8')

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

    def test_v1_prompt_declares_tools_and_json_schema(self):
        """Tests that v1.md documents interactive tools and valid JSON output schema."""
        v1_path = self.prompts_dir / 'v1.md'
        content = v1_path.read_text(encoding='utf-8')

        # Tools
        self.assertIn('search_mdn_tool', content)
        self.assertIn('verify_doc_link_tool', content)
        self.assertIn('read_spec_link_tool', content)

        # Verify embedded JSON example is syntactically valid JSON
        match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        self.assertIsNotNone(
            match, 'JSON schema example block missing in v1.md'
        )
        schema_obj = json.loads(match.group(1))
        self.assertEqual(
            set(schema_obj.keys()), {'summary', 'rationale', 'doc_links'}
        )

    def test_v1_prompt_rendering_with_mock_data(self):
        """Tests that v1.md renders cleanly with sample feature dictionary."""
        v1_path = self.prompts_dir / 'v1.md'
        template = v1_path.read_text(encoding='utf-8')

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
        self.assertIn('Popover API', rendered)
