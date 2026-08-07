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

"""AI Sandbox Tools for Autonomous Web Platform Feature Research.

Provides SSRF-protected interactive tools (search_mdn, verify_doc_link, read_spec_link)
that Gemini 2.0 can invoke during multi-turn developer release note generation.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from types import MappingProxyType
from typing import Any, Callable

import wptgen.context

from internals.core_enums import AISummaryToolName

# Network limits
CHUNK_SIZE = 64 * 1024  # 64 KB per read chunk
MAX_FETCH_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB maximum payload ceiling
DEFAULT_TIMEOUT_SECONDS = 10.0


class _SimpleHTMLTextExtractor(HTMLParser):
    """Extracts clean text and page title from HTML while stripping noise elements."""

    def __init__(self) -> None:
        super().__init__()
        self.title: str = ''
        self._in_title: bool = False
        self._ignored_tags: set[str] = {
            'script',
            'style',
            'nav',
            'header',
            'footer',
            'noscript',
            'svg',
        }
        self._ignore_depth: int = 0
        self._text_chunks: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        tag_lower = tag.lower()
        if tag_lower == 'title':
            self._in_title = True
        if tag_lower in self._ignored_tags:
            self._ignore_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower == 'title':
            self._in_title = False
        if tag_lower in self._ignored_tags and self._ignore_depth > 0:
            self._ignore_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title and not self.title:
            self.title = data.strip()
        if self._ignore_depth == 0:
            cleaned = data.strip()
            if cleaned:
                self._text_chunks.append(cleaned)

    def get_clean_text(self) -> str:
        """Returns space-joined extracted text."""
        return ' '.join(self._text_chunks)


def _fetch_url_chunked(
    url: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = MAX_FETCH_SIZE_BYTES,
) -> bytes:
    """Fetches a URL with SSRF protection and chunked byte limits.

    Args:
      url: The HTTP/HTTPS URL to fetch.
      timeout: Socket timeout in seconds.
      max_bytes: Maximum allowed bytes before raising ValueError.

    Returns:
      The response content bytes.

    Raises:
      ValueError: If URL is invalid, blocked by SSRF, or exceeds max_bytes.
    """
    wptgen.context.validate_url_against_ssrf(url)
    opener = wptgen.context._ssrf_safe_opener

    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': (
                'ChromeStatus-Summary-Generator/1.0 (+https://chromestatus.com)'
            )
        },
    )

    with opener.open(req, timeout=timeout) as response:
        chunks: list[bytes] = []
        total_bytes = 0
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                raise ValueError(
                    f'Response from {url} exceeded maximum allowed limit of'
                    f' {max_bytes} bytes'
                )
            chunks.append(chunk)
        return b''.join(chunks)


def search_mdn_tool(query: str) -> dict[str, Any]:
    """Searches MDN Web Docs for documentation on a Web API, CSS property, or JS feature.

    Args:
      query: Search keywords (e.g., "WebGPU subgroups", "popover attribute").

    Returns:
      A dictionary containing query status and list of matching MDN document
      references.
    """
    clean_query = str(query).strip() if query else ''
    if not clean_query:
        return {
            'status': 'failed',
            'query': clean_query,
            'error': 'Query string cannot be empty.',
        }

    encoded_query = urllib.parse.quote(clean_query)
    url = f'https://developer.mozilla.org/api/v1/search?q={encoded_query}'

    try:
        data_bytes = _fetch_url_chunked(url)
        data = json.loads(data_bytes.decode('utf-8'))
        documents = data.get('documents', []) or []
        results = []
        for doc in documents[:5]:
            mdn_url = doc.get('mdn_url', '')
            if mdn_url and not mdn_url.startswith('http'):
                mdn_url = f'https://developer.mozilla.org{mdn_url}'
            results.append(
                {
                    'title': doc.get('title', ''),
                    'summary': doc.get('summary', ''),
                    'mdn_url': mdn_url,
                }
            )
        return {
            'status': 'success',
            'query': clean_query,
            'results_count': len(results),
            'results': results,
        }
    except Exception as e:
        logging.warning(
            'search_mdn_tool error for query %r: %s', clean_query, e
        )
        return {'status': 'failed', 'query': clean_query, 'error': str(e)}


def verify_doc_link_tool(url: str) -> dict[str, Any]:
    """Verifies an external developer documentation URL is reachable and extracts a summary snippet.

    Args:
      url: Target developer documentation URL (e.g. Chrome developer blog post,
        MDN page).

    Returns:
      A dictionary containing validity status, HTTP status, page title, and text
      snippet.
    """
    clean_url = str(url).strip() if url else ''
    if not clean_url:
        return {
            'status': 'failed',
            'url': clean_url,
            'valid': False,
            'error': 'URL cannot be empty.',
        }

    try:
        html_bytes = _fetch_url_chunked(clean_url)
        html_text = html_bytes.decode('utf-8', errors='replace')
        extractor = _SimpleHTMLTextExtractor()
        extractor.feed(html_text)

        clean_text = extractor.get_clean_text()
        snippet = clean_text[:500] + ('...' if len(clean_text) > 500 else '')

        return {
            'status': 'success',
            'url': clean_url,
            'valid': True,
            'title': extractor.title,
            'snippet': snippet,
        }
    except Exception as e:
        logging.warning(
            'verify_doc_link_tool error for URL %r: %s', clean_url, e
        )
        return {
            'status': 'failed',
            'url': clean_url,
            'valid': False,
            'error': str(e),
        }


def read_spec_link_tool(url: str) -> dict[str, Any]:
    """Fetches and extracts normative description text from a W3C, WHATWG, or TC39 spec link.

    Args:
      url: The specification URL.

    Returns:
      A dictionary containing extracted specification section titles and
      normative snippets.
    """
    clean_url = str(url).strip() if url else ''
    if not clean_url:
        return {
            'status': 'failed',
            'url': clean_url,
            'error': 'Spec URL cannot be empty.',
        }

    try:
        html_bytes = _fetch_url_chunked(clean_url)
        html_text = html_bytes.decode('utf-8', errors='replace')
        extractor = _SimpleHTMLTextExtractor()
        extractor.feed(html_text)

        clean_text = extractor.get_clean_text()
        snippet = clean_text[:2000] + ('...' if len(clean_text) > 2000 else '')

        return {
            'status': 'success',
            'url': clean_url,
            'title': extractor.title,
            'spec_snippet': snippet,
        }
    except Exception as e:
        logging.warning(
            'read_spec_link_tool error for URL %r: %s', clean_url, e
        )
        return {'status': 'failed', 'url': clean_url, 'error': str(e)}


# Centralized immutable tool dispatch map mapping AISummaryToolName string keys to callables.
# Uses MappingProxyType to expose a read-only mapping and prevent runtime mutation.
# Used downstream by the GeminiSummaryGenerator engine and background task workers
# during multi-turn LLM function call execution.
TOOL_MAP: MappingProxyType[str, Callable[..., dict[str, Any]]] = (
    MappingProxyType(
        {
            AISummaryToolName.SEARCH_MDN.value: search_mdn_tool,
            AISummaryToolName.VERIFY_DOC_LINK.value: verify_doc_link_tool,
            AISummaryToolName.READ_SPEC_LINK.value: read_spec_link_tool,
        }
    )
)

# Standardized immutable tool definitions tuple passed to the Google GenAI SDK GenerateContentConfig.
# Used downstream by the GeminiSummaryGenerator engine to expose interactive sandbox capabilities.
AI_SUMMARY_TOOLS: tuple[Callable[..., dict[str, Any]], ...] = (
    search_mdn_tool,
    verify_doc_link_tool,
    read_spec_link_tool,
)
