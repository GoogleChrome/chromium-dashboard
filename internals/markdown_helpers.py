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

import re
from typing import Any

from lxml_html_clean import Cleaner
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from markdown_it.token import Token
from markdown_it.utils import OptionsDict

_TRAILING_PUNCTUATION = '.,;:!?'

_ALLOWED_HTML_TAGS = {
    'p',
    'code',
    'a',
    'strong',
    'em',
    'ul',
    'ol',
    'li',
    'br',
    'pre',
}

_ALLOWED_HTML_ATTRS = {
    'href',
    'target',
    'rel',
    'class',
    'title',
}

_HTML_CLEANER = Cleaner(
    allow_tags=_ALLOWED_HTML_TAGS,
    safe_attrs_only=True,
    safe_attrs=_ALLOWED_HTML_ATTRS,
    remove_unknown_tags=False,
)


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
    """Constructs a CommonMark parser with raw HTML strictly disabled."""
    md = MarkdownIt('commonmark', {'html': False})
    md.add_render_rule('link_open', _custom_link_open_rule)
    return md


_MARKDOWN_PARSER = _build_markdown_parser()


def autolink_bare_urls(text: str) -> str:
    """Encloses bare http(s) URLs in CommonMark angle brackets (<url>) for autolinking.

    Avoids modifying URLs already inside inline code backticks or markdown link definitions.

    Args:
      text: Raw markdown text.

    Returns:
      Markdown text with bare URLs wrapped in CommonMark autolink brackets.
    """
    parts = re.split(r'(`[^`]+`)', text)
    for i, part in enumerate(parts):
        if not part.startswith('`'):

            def _replace_url(match: re.Match[str]) -> str:
                url = match.group(1)
                trailing = ''
                while url and url[-1] in _TRAILING_PUNCTUATION:
                    trailing = url[-1] + trailing
                    url = url[:-1]
                return f'<{url}>{trailing}'

            parts[i] = re.sub(
                r'(?<![\(<"\'])(https?://[^\s\)]+)', _replace_url, part
            )
    return ''.join(parts)


def render_markdown(text: str | None) -> str:
    """Renders CommonMark markdown text to safe, sanitized HTML.

    1. Autolinks bare http(s) URLs not enclosed in code backticks.
    2. Parses markdown using CommonMark rules (matching frontend marked.js).
    3. Neutralizes raw HTML tags and sanitizes output against XSS.
    4. Applies target='_blank' and rel='noopener noreferrer' to links.

    Args:
      text: Raw markdown string.

    Returns:
      Sanitized HTML string ready for safe server-side rendering.
    """
    if not text:
        return ''

    # 1. Preprocess bare URLs
    preprocessed_text = autolink_bare_urls(text)

    # 2. Render to HTML via CommonMark parser (html=False escapes raw HTML tags)
    rendered_html = _MARKDOWN_PARSER.render(preprocessed_text).strip()

    # 3. Sanitize HTML tree to enforce tag and attribute allowlists
    cleaned_html: str = _HTML_CLEANER.clean_html(rendered_html)
    return cleaned_html
