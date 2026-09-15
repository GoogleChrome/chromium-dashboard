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

"""CommonMark Markdown rendering and autolinking utilities for server-side HTML."""

from __future__ import annotations

from typing import Any

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from markdown_it.token import Token
from markdown_it.utils import OptionsDict


def _custom_link_open_rule(
    self: RendererHTML,
    tokens: list[Token],
    idx: int,
    options: OptionsDict,
    env: dict[str, Any],
) -> str:
    """Renderer rule adding target='_blank' and rel='noopener noreferrer' to links."""
    token = tokens[idx]
    token.attrSet('target', '_blank')
    token.attrSet('rel', 'noopener noreferrer')
    return self.renderToken(tokens, idx, options, env)


def _build_markdown_parser() -> MarkdownIt:
    """Constructs a CommonMark parser with linkify-it-py autolinking and raw HTML disabled."""
    md = MarkdownIt(
        'commonmark',
        {
            'linkify': True,
            'html': False,
        },
    ).enable('linkify')
    md.add_render_rule('link_open', _custom_link_open_rule)
    return md


_MARKDOWN_PARSER = _build_markdown_parser()


def render_markdown(text: str | None) -> str:
    """Renders CommonMark markdown text to safe, sanitized HTML.

    1. Parses markdown using CommonMark rules (matching frontend marked.js).
    2. Autolinks bare URLs via linkify-it-py (RFC 3986 and Unicode compliant).
    3. Neutralizes raw HTML tags (html=False) escaping all embedded tags.
    4. Applies target='_blank' and rel='noopener noreferrer' to links.

    Args:
      text: Raw markdown string.

    Returns:
      Sanitized HTML string ready for safe server-side rendering.
    """
    if not text:
        return ''

    # Render to HTML via CommonMark parser with native linkify tokenization
    return _MARKDOWN_PARSER.render(text).strip()
