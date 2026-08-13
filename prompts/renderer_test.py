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

"""Unit tests for prompt template loading and Jinja2 rendering infrastructure."""

from __future__ import annotations

import testing_config  # isort: skip  # Must be imported before other project modules.

import jinja2.exceptions

from ai.progress_reporter import FeatureSummaryInput
from prompts.renderer import (
    CANONICAL_RELEASE_NOTES_TEMPLATE,
    DEFAULT_RELEASE_NOTES_TEMPLATE_NAME,
    FeaturePromptTemplate,
    get_feature_prompt_context,
)


class PromptRendererTest(testing_config.CustomTestCase):
    """Tests loading, context mapping, and rendering of prompt templates."""

    def setUp(self):
        """Initializes standard FeatureSummaryInput and canonical prompt template."""
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
        self.prompt_template = FeaturePromptTemplate(
            DEFAULT_RELEASE_NOTES_TEMPLATE_NAME
        )

    def test_get_feature_prompt_context_mapping(self):
        """Tests converting FeatureSummaryInput into context mapping."""
        context = get_feature_prompt_context(self.feature_input)
        self.assertEqual(context['name'], 'WebGPU Subgroups')
        self.assertEqual(context['shipped_milestone'], 130)
        self.assertEqual(
            context['summary'],
            'Enables SIMD operations across shader invocations in WGSL.',
        )
        self.assertEqual(
            context['spec_link'], 'https://gpuweb.github.io/gpuweb/'
        )
        self.assertEqual(
            context['doc_links'], 'https://developer.chrome.com/docs/webgpu'
        )
        self.assertEqual(context['standard_maturity'], 1)
        self.assertEqual(context['category'], 2)
        self.assertEqual(context['search_tags'], 'webgpu, wgsl, subgroups')

    def test_get_feature_prompt_context_defaults_for_empty_fields(self):
        """Tests that empty/None optional fields have clean fallbacks."""
        empty_input = FeatureSummaryInput(
            name='Minimal Feature',
            summary='Minimal description.',
        )
        context = get_feature_prompt_context(empty_input)
        self.assertEqual(context['name'], 'Minimal Feature')
        self.assertEqual(context['shipped_milestone'], 'TBD')
        self.assertEqual(context['spec_link'], 'None')
        self.assertEqual(context['doc_links'], 'None')
        self.assertEqual(context['search_tags'], 'None')

    def test_template_missing_file_raises_error(self):
        """Tests that constructing template with non-existent name raises TemplateNotFound."""
        with self.assertRaises(jinja2.exceptions.TemplateNotFound):
            FeaturePromptTemplate('non_existent_prompt.md.jinja')

    def test_render_canonical_template_success(self):
        """Tests rendering canonical release notes template with standard feature input."""
        rendered = self.prompt_template.render(self.feature_input)
        self.assertIn('<name>WebGPU Subgroups</name>', rendered)
        self.assertIn(
            '<shipped_milestone>Chrome 130</shipped_milestone>', rendered
        )
        self.assertIn(
            '<feature_summary>Enables SIMD operations across shader invocations in'
            ' WGSL.</feature_summary>',
            rendered,
        )
        self.assertNotIn('{{ name }}', rendered)
        self.assertNotIn('{{ summary }}', rendered)

    def test_render_canonical_template_singleton(self):
        """Tests rendering canonical release notes template via singleton."""
        rendered = CANONICAL_RELEASE_NOTES_TEMPLATE.render(self.feature_input)
        self.assertIn('<name>WebGPU Subgroups</name>', rendered)

    def test_render_canonical_template_with_extra_context(self):
        """Tests rendering with additional context fields."""
        rendered = self.prompt_template.render(
            self.feature_input,
            extra_context={'custom_eval_note': 'eval_123'},
        )
        self.assertIn('<name>WebGPU Subgroups</name>', rendered)
