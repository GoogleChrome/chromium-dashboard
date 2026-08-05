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

"""AI Sandbox Tools, Feature Fingerprinting, and Summary Generator Engine.

Provides deterministic SHA-256 feature fingerprint hashing and SSRF-protected
Gemini Function Calling tools (search_mdn, verify_doc_link, read_spec_link)
for autonomous developer release note summary generation.
"""

import hashlib
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

import wptgen.context
from bs4 import BeautifulSoup

from internals.core_enums import AISummaryToolName

MAX_FETCH_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB maximum response size limit
CHUNK_SIZE = 64 * 1024  # 64 KB chunk size for streaming reads
DEFAULT_TIMEOUT_SECONDS = 10.0
USER_AGENT = 'ChromeStatus-AISummaryGenerator/1.0'
MDN_SEARCH_URL_TEMPLATE = (
    'https://developer.mozilla.org/api/v1/search?q={query}&locale=en-US'
)


def _safe_int(val: Any) -> int | None:
    """Safely converts an input value to an integer, returning None on failure."""
    if val is None or isinstance(val, bool):
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def compute_feature_fingerprint(feature: Any) -> str:
    """Computes a deterministic SHA-256 hash of a feature's core specification fields.

    Used to detect feature drift between AI summary generation runs and prevent
    redundant LLM invocations when feature inputs have not changed.

    Args:
        feature: Either a FeatureEntry NDB entity or a dictionary containing
          feature properties.

    Returns:
        A 64-character hexadecimal SHA-256 hash string.
    """
    if hasattr(feature, 'to_dict'):
        feature_dict = feature.to_dict()
    elif isinstance(feature, dict):
        feature_dict = feature
    else:
        feature_dict = {}
        for k in (
            'name',
            'summary',
            'shipped_milestone',
            'shipped_desktop_milestone',
            'spec_link',
            'doc_links',
            'standard_maturity',
            'category',
            'feature_type',
            'search_tags',
            'impl_status_chrome',
        ):
            val = getattr(feature, k, None)
            if val is not None:
                feature_dict[k] = val

    # Normalize shipped milestone across desktop/default fields
    shipped_m = feature_dict.get('shipped_milestone')
    if shipped_m is None:
        shipped_m = feature_dict.get('shipped_desktop_milestone')

    # Normalize doc_links to sorted unique strings
    raw_doc_links = feature_dict.get('doc_links') or []
    if isinstance(raw_doc_links, (list, tuple, set)):
        doc_links = sorted(
            {
                str(link).strip()
                for link in raw_doc_links
                if link is not None
                and str(link).strip()
                and str(link).strip() != 'None'
            }
        )
    elif (
        isinstance(raw_doc_links, str)
        and raw_doc_links.strip()
        and raw_doc_links.strip() != 'None'
    ):
        doc_links = [raw_doc_links.strip()]
    else:
        doc_links = []

    # Normalize search_tags to sorted unique strings
    raw_tags = feature_dict.get('search_tags') or []
    if isinstance(raw_tags, (list, tuple, set)):
        search_tags = sorted(
            {
                str(tag).strip()
                for tag in raw_tags
                if tag is not None
                and str(tag).strip()
                and str(tag).strip() != 'None'
            }
        )
    elif (
        isinstance(raw_tags, str)
        and raw_tags.strip()
        and raw_tags.strip() != 'None'
    ):
        search_tags = [raw_tags.strip()]
    else:
        search_tags = []

    canonical_payload = {
        'name': str(feature_dict.get('name') or '').strip(),
        'summary': str(feature_dict.get('summary') or '').strip(),
        'shipped_milestone': _safe_int(shipped_m),
        'spec_link': str(feature_dict.get('spec_link') or '').strip(),
        'doc_links': doc_links,
        'standard_maturity': _safe_int(feature_dict.get('standard_maturity')),
        'category': _safe_int(feature_dict.get('category')),
        'feature_type': _safe_int(feature_dict.get('feature_type')),
        'search_tags': search_tags,
        'impl_status_chrome': _safe_int(feature_dict.get('impl_status_chrome')),
    }

    canonical_json = json.dumps(
        canonical_payload, sort_keys=True, separators=(',', ':')
    )
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()


def _fetch_url_chunked(
    url: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_size: int = MAX_FETCH_SIZE_BYTES,
) -> bytes:
    """Fetches a URL safely with SSRF protection and a strict maximum byte size limit.

    Args:
        url: Absolute HTTP/HTTPS URL string to fetch.
        timeout: Socket timeout duration in seconds.
        max_size: Maximum allowable payload size in bytes (default 5 MB).

    Returns:
        Raw bytes payload of the fetched resource.

    Raises:
        ValueError: If URL fails SSRF validation or exceeds the maximum size limit.
        urllib.error.HTTPError: If the remote server responds with a non-2xx status.
        urllib.error.URLError: If network resolution or connection fails.
    """
    # Enforce SSRF protection via wptgen.context
    wptgen.context.validate_url_against_ssrf(url)

    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with wptgen.context._ssrf_safe_opener.open(
        req, timeout=timeout
    ) as response:
        total_bytes = 0
        chunks: list[bytes] = []
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
            total_bytes += len(chunk)
            if total_bytes > max_size:
                raise ValueError(
                    f'Response body exceeded maximum allowed limit of {max_size} bytes.'
                )
        return b''.join(chunks)


def search_mdn_tool(query: str) -> dict[str, Any]:
    """Gemini Function Calling tool: Searches MDN documentation for web platform APIs.

    Args:
        query: Search term or API interface name (e.g., 'WebGPU', 'CSS Subgrid').

    Returns:
        A dictionary containing search results or structured error details.
    """
    clean_query = str(query or '').strip()
    if not clean_query:
        return {
            'status': 'failed',
            'query': query,
            'error': 'Query string cannot be empty.',
        }

    encoded_query = urllib.parse.quote_plus(clean_query)
    search_url = MDN_SEARCH_URL_TEMPLATE.format(query=encoded_query)

    try:
        raw_bytes = _fetch_url_chunked(search_url)
        data = json.loads(raw_bytes.decode('utf-8', errors='replace'))
        documents = data.get('documents') or []

        results = []
        for doc in documents[:5]:  # Top 5 most relevant documents
            if not isinstance(doc, dict):
                continue
            mdn_url = doc.get('mdn_url') or ''
            if mdn_url and not mdn_url.startswith(('http://', 'https://')):
                mdn_url = urllib.parse.urljoin(
                    'https://developer.mozilla.org', mdn_url
                )

            results.append(
                {
                    'title': doc.get('title', ''),
                    'url': mdn_url,
                    'summary': doc.get('summary', ''),
                }
            )

        return {
            'status': 'success',
            'query': clean_query,
            'count': len(results),
            'results': results,
        }
    except Exception as e:
        logging.warning(
            'search_mdn_tool error for query %r: %s', clean_query, e
        )
        return {
            'status': 'failed',
            'query': clean_query,
            'error': str(e),
        }


def verify_doc_link_tool(url: str) -> dict[str, Any]:
    """Gemini Function Calling tool: Verifies that an external documentation link is live and accessible.

    Args:
        url: Absolute HTTP/HTTPS URL string of the documentation resource.

    Returns:
        A dictionary indicating link validity, HTTP status, and a content preview snippet.
    """
    clean_url = str(url or '').strip()
    if not clean_url:
        return {
            'valid': False,
            'status': 'failed',
            'url': url,
            'error': 'URL cannot be empty.',
        }

    try:
        raw_bytes = _fetch_url_chunked(clean_url)
        text = raw_bytes.decode('utf-8', errors='replace')

        # Extract title or snippet if HTML
        snippet = ''
        title = ''
        if '<html' in text.lower() or '<!doctype' in text.lower():
            soup = BeautifulSoup(text, 'html.parser')
            for tag in soup(
                ['script', 'style', 'nav', 'header', 'footer', 'noscript']
            ):
                tag.decompose()
            title = soup.title.get_text(strip=True) if soup.title else ''
            body_text = ' '.join(soup.stripped_strings)
            snippet = body_text[:500]
        else:
            snippet = text[:500].strip()

        return {
            'valid': True,
            'status': 'success',
            'url': clean_url,
            'title': title,
            'status_code': 200,
            'snippet': snippet,
        }
    except Exception as e:
        logging.warning(
            'verify_doc_link_tool error for URL %r: %s', clean_url, e
        )
        return {
            'valid': False,
            'status': 'failed',
            'url': clean_url,
            'error': str(e),
        }


def read_spec_link_tool(url: str) -> dict[str, Any]:
    """Gemini Function Calling tool: Reads and extracts text from a W3C/WHATWG specification URL.

    Args:
        url: Absolute HTTP/HTTPS specification URL.

    Returns:
        A dictionary containing the specification title and normative text content snippet.
    """
    clean_url = str(url or '').strip()
    if not clean_url:
        return {
            'status': 'failed',
            'url': url,
            'error': 'URL cannot be empty.',
        }

    try:
        raw_bytes = _fetch_url_chunked(clean_url)
        text = raw_bytes.decode('utf-8', errors='replace')

        soup = BeautifulSoup(text, 'html.parser')
        title = soup.title.get_text(strip=True) if soup.title else ''

        # Remove script, style, and navigation noise
        for tag in soup(
            ['script', 'style', 'nav', 'header', 'footer', 'noscript']
        ):
            tag.decompose()

        body_text = ' '.join(soup.stripped_strings)
        content_snippet = body_text[:2000]

        return {
            'status': 'success',
            'url': clean_url,
            'title': title,
            'content_snippet': content_snippet,
        }
    except Exception as e:
        logging.warning(
            'read_spec_link_tool error for URL %r: %s', clean_url, e
        )
        return {
            'status': 'failed',
            'url': clean_url,
            'error': str(e),
        }


# Map of canonical tool names to their callable function implementations
TOOL_MAP: dict[str, Callable[..., dict[str, Any]]] = {
    AISummaryToolName.SEARCH_MDN.value: search_mdn_tool,
    AISummaryToolName.VERIFY_DOC_LINK.value: verify_doc_link_tool,
    AISummaryToolName.READ_SPEC_LINK.value: read_spec_link_tool,
}

# List of tools provided to Gemini function calling declarations
AI_SUMMARY_TOOLS = [search_mdn_tool, verify_doc_link_tool, read_spec_link_tool]
