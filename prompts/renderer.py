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

"""Prompt template loading and Jinja2 rendering infrastructure."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ai.progress_reporter import FeatureSummaryInput
from framework.utils import safe_plain_text_to_markdown

PROMPTS_DIR = Path(__file__).resolve().parent
DEFAULT_RELEASE_NOTES_TEMPLATE_NAME = 'generate_release_notes.md.jinja'

PROMPT_JINJA_ENV = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    undefined=StrictUndefined,
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


def get_feature_prompt_context(
    feature_input: FeatureSummaryInput,
) -> dict[str, Any]:
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

    return {
        'name': feature_input.name,
        'shipped_milestone': feature_input.shipped_milestone or 'TBD',
        'summary': formatted_summary or 'TBD',
        'spec_link': feature_input.spec_link or 'None',
        'doc_links': formatted_docs,
        'standard_maturity': feature_input.standard_maturity,
        'category': feature_input.category,
        'search_tags': formatted_tags,
    }


class FeaturePromptTemplate:
    """Encapsulates Jinja2 template loading and rendering for feature prompts."""

    def __init__(
        self,
        template_name: str = DEFAULT_RELEASE_NOTES_TEMPLATE_NAME,
    ) -> None:
        """Initializes template loader with template file name."""
        self.template_name = template_name
        self._template = PROMPT_JINJA_ENV.get_template(template_name)

    def render(
        self,
        feature_input: FeatureSummaryInput,
        extra_context: Mapping[str, Any] | None = None,
    ) -> str:
        """Renders the prompt for a feature with StrictUndefined validation."""
        context = get_feature_prompt_context(feature_input)
        if extra_context:
            context.update(extra_context)
        return self._template.render(**context)


CANONICAL_RELEASE_NOTES_TEMPLATE = FeaturePromptTemplate(
    DEFAULT_RELEASE_NOTES_TEMPLATE_NAME
)
