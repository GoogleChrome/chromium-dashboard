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

import os
import unittest


class PromptsTest(unittest.TestCase):
    """Tests prompt template structure and placeholder contracts."""

    def setUp(self):
        """Initializes prompt directory path."""
        self.prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')

    def test_v1_prompt_template_exists_and_contains_placeholders(self):
        """Tests that v1.md exists and includes all required placeholder variables."""
        v1_path = os.path.join(self.prompts_dir, 'v1.md')
        self.assertTrue(os.path.exists(v1_path), f'Missing {v1_path}')

        with open(v1_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_placeholders = [
            '{{ name }}',
            '{{ shipped_milestone }}',
            '{{ summary }}',
            '{{ spec_link }}',
            '{{ doc_links }}',
            '{{ standard_maturity }}',
            '{{ category }}',
            '{{ search_tags }}',
        ]
        for placeholder in required_placeholders:
            self.assertIn(
                placeholder,
                content,
                f'Prompt template v1.md is missing required placeholder: {placeholder}',
            )

    def test_v1_prompt_declares_tools_and_json_schema(self):
        """Tests that v1.md documents interactive tools and valid JSON output schema."""
        v1_path = os.path.join(self.prompts_dir, 'v1.md')
        with open(v1_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Tools
        self.assertIn('search_mdn_tool', content)
        self.assertIn('verify_doc_link_tool', content)
        self.assertIn('read_spec_link_tool', content)

        # JSON keys
        self.assertIn('"summary"', content)
        self.assertIn('"rationale"', content)
        self.assertIn('"doc_links"', content)
