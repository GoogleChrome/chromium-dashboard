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
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from google.cloud import ndb

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore

import wptgen.context
from bs4 import BeautifulSoup

import settings
from framework.utils import safe_plain_text_to_markdown
from internals.core_enums import (
    AISummaryToolName,
    ProgressStepId,
    ProgressStepStatus,
    SummarySuggestionStatus,
)
from internals.core_models import (
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)

MAX_FETCH_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB maximum response size limit
CHUNK_SIZE = 64 * 1024  # 64 KB chunk size for streaming reads
DEFAULT_TIMEOUT_SECONDS = 10.0
USER_AGENT = 'ChromeStatus-AISummaryGenerator/1.0'
MDN_SEARCH_URL_TEMPLATE = (
    'https://developer.mozilla.org/api/v1/search?q={query}&locale=en-US'
)
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

TOOL_STEP_MAP: dict[str, ProgressStepId] = {
    AISummaryToolName.SEARCH_MDN.value: ProgressStepId.SEARCH_MDN,
    AISummaryToolName.VERIFY_DOC_LINK.value: ProgressStepId.VERIFY_DOC_LINK,
    AISummaryToolName.READ_SPEC_LINK.value: ProgressStepId.READ_SPEC,
}


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
AI_SUMMARY_TOOLS: list[Any] = [
    search_mdn_tool,
    verify_doc_link_tool,
    read_spec_link_tool,
]


class GeminiSummaryGenerator:
    """Autonomous LLM engine orchestrating Gemini summary generation and tool calling.

    Executes multi-turn tool loops with Gemini (via google.genai), logs real-time
    strongly consistent FeatureSummaryProgressStep entities, and updates
    FeatureSummarySuggestion records upon completion.
    """

    def __init__(
        self,
        model_name: str = 'gemini-2.0-flash',
        prompt_version: str = 'v2',
        api_key: str | None = None,
        client: Any = None,
    ) -> None:
        """Initialize the generator engine with model configuration and prompt template."""
        self.model_name = model_name
        self.prompt_version = prompt_version
        self.api_key = api_key
        self.client = client
        self.prompt_template = self.load_prompt_template(prompt_version)

    @staticmethod
    def load_prompt_template(version: str) -> str:
        """Loads a versioned markdown prompt template from framework/prompts/{version}.md."""
        prompt_file = os.path.join(PROMPTS_DIR, f'{version}.md')
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f'Prompt template not found: {prompt_file}')
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()

    def _get_client(self) -> Any:
        """Returns the initialized GenAI Client instance."""
        if self.client is not None:
            return self.client
        if genai is None:
            raise RuntimeError('google-genai SDK is not installed.')
        api_key = (
            self.api_key
            or getattr(settings, 'GEMINI_API_KEY', None)
            or os.environ.get('GEMINI_API_KEY')
        )
        if not api_key:
            raise ValueError(
                'GEMINI_API_KEY must be configured to use GeminiSummaryGenerator.'
            )
        return genai.Client(api_key=api_key)

    def _log_step(
        self,
        feature_id: int,
        step_id: ProgressStepId | str,
        status: ProgressStepStatus | str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        message: str | None = None,
        tool_name: AISummaryToolName | str | None = None,
        attempt_count: int = 1,
    ) -> FeatureSummaryProgressStep:
        """Logs a discrete progress step parented under FeatureSummarySuggestion."""
        parent_key = ndb.Key('FeatureSummarySuggestion', feature_id)
        step_id_str = str(
            step_id.value if hasattr(step_id, 'value') else step_id
        )
        status_str = str(status.value if hasattr(status, 'value') else status)
        tool_name_str = (
            str(tool_name.value if hasattr(tool_name, 'value') else tool_name)
            if tool_name
            else None
        )
        now = datetime.now(timezone.utc)

        step = FeatureSummaryProgressStep(
            parent=parent_key,
            step_id=step_id_str,
            status=status_str,
            start_timestamp=start_time or now,
            end_timestamp=end_time,
            message=message,
            tool_name=tool_name_str,
            attempt_count=attempt_count,
        )
        step.put()
        return step

    def _render_prompt(self, feature_dict: dict[str, Any]) -> str:
        """Renders the loaded prompt template with feature context."""
        shipped_m = feature_dict.get('shipped_milestone')
        if shipped_m is None:
            shipped_m = feature_dict.get('shipped_desktop_milestone')

        raw_doc_links = feature_dict.get('doc_links') or []
        if isinstance(raw_doc_links, (list, tuple, set)):
            doc_links_str = ', '.join(
                str(link)
                for link in raw_doc_links
                if link and str(link) != 'None'
            )
        else:
            doc_links_str = str(raw_doc_links)

        raw_tags = feature_dict.get('search_tags') or []
        if isinstance(raw_tags, (list, tuple, set)):
            tags_str = ', '.join(
                str(tag) for tag in raw_tags if tag and str(tag) != 'None'
            )
        else:
            tags_str = str(raw_tags)

        summary_md = safe_plain_text_to_markdown(
            str(feature_dict.get('summary') or '')
        )

        rendered = self.prompt_template
        rendered = rendered.replace(
            '{{ name }}', str(feature_dict.get('name') or '')
        )
        rendered = rendered.replace(
            '{{ shipped_milestone }}', str(shipped_m or 'TBD')
        )
        rendered = rendered.replace('{{ summary }}', summary_md)
        rendered = rendered.replace(
            '{{ spec_link }}', str(feature_dict.get('spec_link') or 'None')
        )
        rendered = rendered.replace('{{ doc_links }}', doc_links_str or 'None')
        rendered = rendered.replace('{{ search_tags }}', tags_str or 'None')
        rendered = rendered.replace(
            '{{ standard_maturity }}',
            str(feature_dict.get('standard_maturity') or 'None'),
        )
        rendered = rendered.replace(
            '{{ category }}', str(feature_dict.get('category') or 'None')
        )
        return rendered

    @staticmethod
    def _parse_json_response(text: str) -> dict[str, Any]:
        """Parses JSON content from raw LLM responses, stripping code fences if present."""
        clean_text = text.strip()
        if '```json' in clean_text:
            match = re.search(r'```json\s*([\s\S]*?)\s*```', clean_text)
            if match:
                clean_text = match.group(1).strip()
        elif '```' in clean_text:
            match = re.search(r'```\s*([\s\S]*?)\s*```', clean_text)
            if match:
                clean_text = match.group(1).strip()

        try:
            parsed = json.loads(clean_text)
            if isinstance(parsed, dict):
                return parsed
        except Exception as e:
            logging.warning('Failed to parse JSON from LLM response: %s', e)

        return {
            'summary': clean_text,
            'rationale': 'Direct model output generation.',
            'doc_links': [],
        }

    def _execute_tool(
        self, fn_name: str, fn_args: dict[str, Any]
    ) -> dict[str, Any]:
        """Executes a sandbox tool by name from TOOL_MAP."""
        tool_fn = TOOL_MAP.get(fn_name)
        if tool_fn:
            return tool_fn(**fn_args)
        return {
            'status': 'failed',
            'error': f'Tool {fn_name} not found in registry.',
        }

    def generate_summary(
        self,
        feature_id: int,
        feature: Any,
        dry_run: bool = False,
    ) -> tuple[FeatureSummarySuggestion | None, str | None]:
        """Generates an AI summary suggestion for a feature with multi-turn tool execution.

        Args:
            feature_id: The integer ID of the FeatureEntry.
            feature: FeatureEntry NDB model or dictionary containing feature details.
            dry_run: If True, avoids persisting changes to Datastore.

        Returns:
            A tuple of (FeatureSummarySuggestion entity or None, error message string or None).
        """
        if hasattr(feature, 'to_dict'):
            feature_dict = feature.to_dict()
        elif isinstance(feature, dict):
            feature_dict = feature
        else:
            feature_dict = {}

        current_fingerprint = compute_feature_fingerprint(feature)
        start_time = datetime.now(timezone.utc)

        # Check for existing suggestion with matching fingerprint
        existing = FeatureSummarySuggestion.get_by_id(feature_id)
        is_new = existing is None
        if (
            existing
            and existing.source_fingerprint == current_fingerprint
            and existing.suggested_summary
        ):
            logging.info(
                'Feature %d specification unchanged; skipping LLM generation.',
                feature_id,
            )
            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.START,
                status=ProgressStepStatus.SUCCESS,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                message='Feature unchanged; cached summary is up to date.',
            )
            FeatureSummaryProgressStep.clear_timeline(feature_id, keep_count=20)
            return existing, None

        try:
            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.START,
                status=ProgressStepStatus.IN_PROGRESS,
                start_time=start_time,
                message='Starting AI summary generation workflow.',
            )

            rendered_prompt = self._render_prompt(feature_dict)
            client = self._get_client()

            llm_start_time = datetime.now(timezone.utc)
            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.LLM_GENERATION,
                status=ProgressStepStatus.IN_PROGRESS,
                start_time=llm_start_time,
                message=(
                    f'Invoking {self.model_name} with prompt version'
                    f' {self.prompt_version}.'
                ),
            )

            # Build config for model execution
            tools = AI_SUMMARY_TOOLS if self.prompt_version == 'v2' else None
            config = None
            if tools and types:
                config = types.GenerateContentConfig(tools=tools)

            # Generate content with tool calling support
            response = client.models.generate_content(
                model=self.model_name,
                contents=rendered_prompt,
                config=config,
            )

            # Handle function calling turns if present
            if hasattr(response, 'function_calls') and response.function_calls:
                for call in response.function_calls:
                    fn_name = getattr(call, 'name', '')
                    fn_args = getattr(call, 'args', {}) or {}
                    step_id = TOOL_STEP_MAP.get(fn_name, ProgressStepId.UNKNOWN)

                    tool_start = datetime.now(timezone.utc)
                    self._log_step(
                        feature_id=feature_id,
                        step_id=step_id,
                        status=ProgressStepStatus.IN_PROGRESS,
                        start_time=tool_start,
                        tool_name=fn_name,
                        message=f'Calling tool {fn_name} with args {fn_args}',
                    )

                    tool_result = self._execute_tool(fn_name, fn_args)
                    tool_status = (
                        ProgressStepStatus.SUCCESS
                        if tool_result.get('status') != 'failed'
                        and tool_result.get('valid', True)
                        else ProgressStepStatus.FAILED
                    )

                    self._log_step(
                        feature_id=feature_id,
                        step_id=step_id,
                        status=tool_status,
                        start_time=tool_start,
                        end_time=datetime.now(timezone.utc),
                        tool_name=fn_name,
                        message=str(
                            tool_result.get('error')
                            or f'Tool {fn_name} completed.'
                        ),
                    )

            final_text = getattr(response, 'text', '') or str(response)

            parsed_result = self._parse_json_response(final_text)
            suggested_summary = str(parsed_result.get('summary') or '').strip()
            rationale = str(parsed_result.get('rationale') or '').strip()
            raw_doc_links = parsed_result.get('doc_links') or []
            suggested_doc_links = (
                [
                    str(link).strip()
                    for link in raw_doc_links
                    if str(link).strip()
                ]
                if isinstance(raw_doc_links, list)
                else []
            )

            if not existing:
                existing = FeatureSummarySuggestion(id=feature_id)

            existing.suggested_summary = suggested_summary
            existing.generation_rationale = rationale
            existing.suggested_doc_links = suggested_doc_links
            existing.source_fingerprint = current_fingerprint
            existing.original_summary = str(feature_dict.get('summary') or '')
            existing.original_doc_links = feature_dict.get('doc_links') or []
            existing.status = SummarySuggestionStatus.PROPOSED.value
            existing.version_token = (
                1 if is_new else ((existing.version_token or 1) + 1)
            )

            if not dry_run:
                existing.put()

            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.SUCCESS,
                status=ProgressStepStatus.SUCCESS,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                message='AI summary suggestion successfully generated.',
            )
            return existing, None

        except Exception as e:
            logging.error(
                'GeminiSummaryGenerator error for feature %d: %s', feature_id, e
            )
            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.UNKNOWN,
                status=ProgressStepStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
                message=str(e),
            )
            return None, str(e)
        finally:
            FeatureSummaryProgressStep.clear_timeline(feature_id, keep_count=20)
