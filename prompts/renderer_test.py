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

"""Unit tests for prompt template loading, strict validation, and rendering infrastructure."""

from __future__ import annotations

import testing_config  # isort: skip  # Must be imported before other project modules.

import tempfile
from pathlib import Path

from ai.progress_reporter import FeatureSummaryInput
from prompts.renderer import (
    DEFAULT_RELEASE_NOTES_PROMPT_PATH,
    FeaturePromptTemplate,
    get_feature_prompt_context,
    render_prompt_template,
)


class PromptRendererTest(testing_config.CustomTestCase):
    """Tests loading, context mapping, strict validation, and rendering of prompt templates."""

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
            DEFAULT_RELEASE_NOTES_PROMPT_PATH
        )

    def test_get_feature_prompt_context_mapping(self):
        """Tests converting FeatureSummaryInput into string context mapping."""
        context = get_feature_prompt_context(self.feature_input)
        self.assertEqual(context['name'], 'WebGPU Subgroups')
        self.assertEqual(context['shipped_milestone'], '130')
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
        self.assertEqual(context['standard_maturity'], '1')
        self.assertEqual(context['category'], '2')
        self.assertEqual(context['search_tags'], 'webgpu, wgsl, subgroups')

    def test_get_feature_prompt_context_defaults_for_empty_fields(self):
        """Tests that empty/None optional fields have clean string fallbacks."""
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

    def test_render_prompt_template_substitutions(self):
        """Tests placeholder replacement with spaced and unspaced syntax."""
        template = 'Feature: {{ name }} (Chrome {{shipped_milestone}})'
        context = {'name': 'CSS Anchor Positioning', 'shipped_milestone': '125'}
        rendered = render_prompt_template(template, context)
        self.assertEqual(
            rendered, 'Feature: CSS Anchor Positioning (Chrome 125)'
        )

    def test_template_load_and_placeholders(self):
        """Tests loading canonical prompt template and extracting declared placeholders."""
        raw = self.prompt_template.load()
        self.assertIn('### Task', raw)
        self.assertIn('<feature_metadata>', raw)

        placeholders = self.prompt_template.get_placeholders()
        expected = {
            'name',
            'shipped_milestone',
            'summary',
            'spec_link',
            'doc_links',
            'standard_maturity',
            'category',
            'search_tags',
        }
        self.assertEqual(placeholders, expected)

    def test_template_missing_file_raises_error(self):
        """Tests that constructing template with non-existent path raises FileNotFoundError."""
        invalid_template = FeaturePromptTemplate('/non/existent/prompt.md')
        with self.assertRaises(FileNotFoundError):
            invalid_template.load()

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

    def test_strict_validation_fails_on_unused_extra_args(self):
        """Tests that passing unused context variables raises ValueError to prevent false positives."""
        with self.assertRaises(ValueError) as ctx:
            self.prompt_template.render(
                self.feature_input,
                extra_context={'unused_eval_arg': 'some_value'},
            )
        self.assertIn('Unused context arguments', str(ctx.exception))
        self.assertIn('unused_eval_arg', str(ctx.exception))

    def test_strict_validation_fails_on_missing_placeholders(self):
        """Tests that missing required placeholders in custom context builder raises ValueError."""

        def incomplete_builder(feat: FeatureSummaryInput) -> dict[str, str]:
            return {'name': feat.name}

        incomplete_template = FeaturePromptTemplate(
            DEFAULT_RELEASE_NOTES_PROMPT_PATH,
            context_builder=incomplete_builder,
        )
        with self.assertRaises(ValueError) as ctx:
            incomplete_template.render(self.feature_input)
        self.assertIn('Missing required placeholders', str(ctx.exception))

    def test_render_with_custom_template_and_extra_context(self):
        """Tests custom template file with dynamic extra context (eval pattern)."""
        with tempfile.NamedTemporaryFile(
            mode='w+', suffix='.md', delete=False
        ) as tmp:
            tmp.write(
                '### Experiment\nFeature: {{ name }}\nRubric: {{ rubric_version }}'
            )
            tmp_path = Path(tmp.name)

        try:
            custom_template = FeaturePromptTemplate(
                tmp_path,
                context_builder=lambda f: {'name': f.name},
            )
            rendered = custom_template.render(
                self.feature_input,
                extra_context={'rubric_version': '2026-Q3-v1'},
            )
            self.assertEqual(
                rendered,
                '### Experiment\nFeature: WebGPU Subgroups\nRubric: 2026-Q3-v1',
            )
        finally:
            tmp_path.unlink(missing_ok=True)
