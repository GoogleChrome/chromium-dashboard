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

"""Prompt template loading, strict contract validation, and placeholder rendering infrastructure."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from pathlib import Path

from ai.progress_reporter import FeatureSummaryInput
from framework.utils import safe_plain_text_to_markdown

DEFAULT_RELEASE_NOTES_PROMPT_PATH = (
    Path(__file__).resolve().parent / 'generate_release_notes.md'
)


def get_feature_prompt_context(
    feature_input: FeatureSummaryInput,
) -> dict[str, str]:
    """Extracts standard placeholder context dictionary from FeatureSummaryInput."""
    formatted_summary = safe_plain_text_to_markdown(feature_input.summary)
    formatted_docs = (
        ', '.join(feature_input.doc_links)
        if feature_input.doc_links
        else 'None'
    )
    formatted_tags = (
        ', '.join(feature_input.search_tags)
        if feature_input.search_tags
        else 'None'
    )
    shipped = (
        f'{feature_input.shipped_milestone}'
        if feature_input.shipped_milestone
        else 'TBD'
    )

    return {
        'name': feature_input.name,
        'shipped_milestone': shipped,
        'summary': formatted_summary or 'TBD',
        'spec_link': feature_input.spec_link or 'None',
        'doc_links': formatted_docs,
        'standard_maturity': f'{feature_input.standard_maturity}',
        'category': f'{feature_input.category}',
        'search_tags': formatted_tags,
    }


def render_prompt_template(
    template_str: str,
    context: Mapping[str, str],
) -> str:
    """Substitutes {{ key }} placeholders in template_str using context mapping."""
    rendered = template_str
    for key, value in context.items():
        rendered = rendered.replace(f'{{{{ {key} }}}}', value)
        rendered = rendered.replace(f'{{{{{key}}}}}', value)
    return rendered


class FeaturePromptTemplate:
    """Encapsulates prompt template loading, strict two-way contract validation, and rendering."""

    def __init__(
        self,
        template_path: str | Path,
        context_builder: Callable[
            [FeatureSummaryInput], Mapping[str, str]
        ] = get_feature_prompt_context,
    ) -> None:
        """Initializes prompt template with explicit path and context builder strategy."""
        self.template_path = Path(template_path)
        self.context_builder = context_builder
        self._raw_template: str | None = None

    def load(self) -> str:
        """Loads and caches raw markdown template text from disk."""
        if self._raw_template is None:
            if not self.template_path.exists():
                raise FileNotFoundError(
                    f'Prompt template {self.template_path} not found'
                )
            self._raw_template = self.template_path.read_text(encoding='utf-8')
        return self._raw_template

    def get_placeholders(self) -> set[str]:
        """Inspects the template file and extracts all declared {{ placeholder }} keys."""
        template_str = self.load()
        return set(re.findall(r'\{\{\s*(\w+)\s*\}\}', template_str))

    def validate_context(self, context: Mapping[str, str]) -> None:
        """Strictly validates context matches template placeholders to prevent false positives.

        Raises:
          ValueError: If any context variable is unused (prevents silent argument swallowing in evals)
            or if any required placeholder is missing (prevents unrendered prompts).
        """
        declared = self.get_placeholders()
        provided = set(context.keys())

        unused = provided - declared
        if unused:
            raise ValueError(
                f'Unused context arguments provided to prompt template'
                f' {self.template_path.name}: {sorted(unused)}. Declared template'
                f' placeholders: {sorted(declared)}'
            )

        missing = declared - provided
        if missing:
            raise ValueError(
                f'Missing required placeholders for prompt template'
                f' {self.template_path.name}: {sorted(missing)}'
            )

    def render(
        self,
        feature_input: FeatureSummaryInput,
        extra_context: Mapping[str, str] | None = None,
    ) -> str:
        """Renders the prompt for a feature with strict validation and leak defense.

        Args:
          feature_input: FeatureSummaryInput DTO.
          extra_context: Optional additional context mapping (e.g. evaluation few-shots).

        Returns:
          Fully interpolated prompt string ready for LLM invocation.

        Raises:
          ValueError: If context contains unused keys, missing keys, or if unrendered placeholders remain.
        """
        template_str = self.load()
        context = dict(self.context_builder(feature_input))
        if extra_context:
            context.update(extra_context)

        self.validate_context(context)

        rendered = render_prompt_template(template_str, context)

        # Post-render leak check: Ensure no un-substituted {{ ... }} remain
        leaked = re.findall(r'\{\{\s*(\w+)\s*\}\}', rendered)
        if leaked:
            raise ValueError(
                f'Rendered prompt contains un-substituted placeholders:'
                f' {sorted(set(leaked))}'
            )

        return rendered
