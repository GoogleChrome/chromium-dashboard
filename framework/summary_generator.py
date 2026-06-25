# -*- coding: utf-8 -*-
# Copyright 2026 Google Inc.
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

"""Orchestration and generation logic for AI-assisted feature summaries using google-adk."""

from __future__ import annotations

import hashlib
import logging
import os
from abc import ABC, abstractmethod
from datetime import date, datetime

import requests
from google.cloud import ndb  # type: ignore
from pydantic import BaseModel, Field

import settings
from framework import secrets
from internals import core_enums
from internals.core_models import (
    FeatureEntry,
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)

GENERATOR_VERSION = 2

# Constants for dynamic model safety limits
TOKEN_TO_CHAR_FACTOR = 4             # Approximate English characters per token
SAFE_HEADROOM_FACTOR = 0.1           # Safe budget allocation for input prompt (10%)
DEFAULT_INPUT_TOKEN_LIMIT = 1000000  # Default fallback token limit if API fails


class SummaryResponseSchema(BaseModel):
    """Schema for the generated summary, doc links, and baseline status."""

    feasibility_decision: str = Field(
        description='Whether the AI should generate a summary ("generate") or skip because of insufficient details ("skipped_insufficient_data") or because it looks like a test/spam entry ("skipped_spam_or_test").'
    )
    suggested_summary: str | None = Field(
        default=None,
        description='The 2-3 sentence developer-focused summary, or None if skipped.'
    )
    suggested_doc_links: list[str] = Field(
        description='List of verified reference documentation links on MDN or web.dev, or empty list if skipped.'
    )
    baseline_status: str = Field(
        description='Baseline compatibility status: limited, newly, widely.'
    )
    baseline_newly_date: str | None = Field(
        default=None,
        description='The date when the feature became interoperable (YYYY-MM-DD), or null.'
    )
    baseline_widely_date: str | None = Field(
        default=None,
        description='The date when the feature transitioned to widely available (YYYY-MM-DD), or null.'
    )
    generation_rationale: str = Field(
        description='A thorough explanation (formatted in markdown, using bullet points) explaining what key technical details were enriched, what sources were consulted, and why this summary improves upon the raw description, OR why generation was skipped.'
    )


def search_mdn(query: str) -> str:
    """Search Mozilla Developer Network (MDN) Web Docs for technical details and API references.

    Args:
        query: The search term or API name.

    Returns:
        A formatted string of matching document titles, URLs, and summaries.
    """
    url = f'https://developer.mozilla.org/api/v1/search?q={requests.utils.quote(query)}'
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return f'MDN search failed with status {resp.status_code}.'
        docs = resp.json().get('documents', [])
        if not docs:
            return 'No documents found on MDN.'
        results = []
        for d in docs[:5]:  # Limit to top 5
            title = d.get('title')
            mdn_url = 'https://developer.mozilla.org' + d.get('mdn_url')
            summary = d.get('summary')
            results.append(
                f'Title: {title}\nURL: {mdn_url}\nSummary: {summary}\n'
            )
        return '\n'.join(results)
    except Exception as e:
        return f'Error searching MDN: {e}'


# Isolated Allowlist Domains conforming to the Principle of Least Privilege
# Backed by a comprehensive audit of all 1,000+ features in production.
ALLOWED_SPEC_DOMAINS = [
    # W3C specifications (Example: https://www.w3.org/TR/css-paint-api-1/)
    r'^([a-z0-9-]+\.)*w3\.org$',
    
    # WHATWG specifications (Example: https://html.spec.whatwg.org/multipage/popover.html)
    r'^([a-z0-9-]+\.)*whatwg\.org$',
    
    # IETF RFC standards (Example: https://datatracker.ietf.org/doc/html/rfc9110)
    r'^([a-z0-9-]+\.)*ietf\.org$',
    
    # Khronos Group specifications (Example: https://registry.khronos.org/webgl/specs/latest/2.0/)
    r'^([a-z0-9-]+\.)*khronos\.org$',
    
    # ECMA TC39 JavaScript specifications (Example: https://tc39.es/ecma262/)
    r'^([a-z0-9-]+\.)*tc39\.es$',
    
    # CSS Working Group spec drafts (Example: https://drafts.csswg.org/css-grid-3/)
    r'^([a-z0-9-]+\.)*csswg\.org$',
    
    # SVG Working Group spec drafts (Example: https://svgwg.org/specs/)
    r'^([a-z0-9-]+\.)*svgwg\.org$',
    
    # GitHub Pages for spec drafts (Example: https://w3c.github.io/css-paint-api/)
    r'^([a-z0-9-]+\.)*github\.io$',
    
    # GitHub repositories used directly as spec references (Example: https://github.com/w3c/css-canvas-implementation)
    r'^([a-z0-9-]+\.)*github\.com$',
    
    # Raw GitHub spec files (Example: https://raw.githubusercontent.com/webmachinelearning/prompt-api/main/README.md)
    r'^([a-z0-9-]+\.)*githubusercontent\.com$',
    
    # CSS Houdini W3C taskforce spec drafts (Example: https://drafts.css-houdini.org/css-paint-api-1/)
    r'^([a-z0-9-]+\.)*css-houdini\.org$',
    
    # W3C FX Taskforce spec drafts (Example: https://drafts.fxtf.org/geometry-1/)
    r'^([a-z0-9-]+\.)*fxtf\.org$',
    
    # WHATWG Pull Request previews (Example: https://whatpr.org/html/1234/popover.html)
    r'^([a-z0-9-]+\.)*whatpr\.org$',
    
    # IETF RFC Editor standards (Example: https://www.rfc-editor.org/rfc/rfc9110.html)
    r'^([a-z0-9-]+\.)*rfc-editor\.org$',
    
    # IETF HTTP Working Group standards (Example: https://httpwg.org/specs/rfc9110.html)
    r'^([a-z0-9-]+\.)*httpwg\.org$',
    
    # Open UI community group standards (Example: https://open-ui.org/components/popover.research.explainer/)
    r'^([a-z0-9-]+\.)*open-ui\.org$',
]

ALLOWED_EXPLAINER_DOMAINS = [
    # GitHub repositories for explainers (Example: https://github.com/w3c/css-canvas-implementation)
    r'^([a-z0-9-]+\.)*github\.com$',
    
    # Raw GitHub content for markdown explainers (Example: https://raw.githubusercontent.com/webmachinelearning/prompt-api/main/README.md)
    r'^([a-z0-9-]+\.)*githubusercontent\.com$',
    
    # GitHub Pages hosting explainers (Example: https://explainers-by-googlers.github.io/my-explainer/)
    r'^([a-z0-9-]+\.)*github\.io$',
    
    # Open UI community group explainers (Example: https://open-ui.org/components/popover.research.explainer/)
    r'^([a-z0-9-]+\.)*open-ui\.org$',
    
    # Chrome DevRel and Developer blogs (Example: https://developer.chrome.com/blog/canvas-paint-worklet/)
    r'^([a-z0-9-]+\.)*chrome\.com$',
    
    # WebKit official explainers (Example: https://webkit.org/explainers/)
    r'^([a-z0-9-]+\.)*webkit\.org$',
    
    # Explainers can also reference official specifications as foundational context
    r'^([a-z0-9-]+\.)*w3\.org$',
    r'^([a-z0-9-]+\.)*whatwg\.org$',
]

ALLOWED_DOC_DOMAINS = [
    # MDN documentation (Example: https://developer.mozilla.org/en-US/docs/Web/API/CSS_Painting_API)
    r'^developer\.mozilla\.org$',
    
    # Chrome DevRel articles (Example: https://web.dev/blog/popover-api/)
    r'^([a-z0-9-]+\.)*web\.dev$',
    
    # Chrome Developer Portal (Example: https://developer.chrome.com/blog/canvas-paint-worklet/)
    r'^([a-z0-9-]+\.)*chrome\.com$',
    
    # Browser support tables (Example: https://caniuse.com/css-paint-api)
    r'^([a-z0-9-]+\.)*caniuse\.com$',
]


def is_safe_url(url: str, allowed_patterns: list[str]) -> bool:
    """Validates that a URL is safe and points to an approved domain under the allowlist.

    This acts as a strict sandbox to prevent Server-Side Request Forgery (SSRF)
    attacks against internal GCP metadata endpoints, loopback addresses,
    or corporate internal services.
    """
    from urllib.parse import urlparse
    import re
    import logging

    try:
        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ('http', 'https'):
            logging.warning(f'Rejected unsafe URL scheme: {url}')
            return False

        hostname = parsed.hostname
        if not hostname:
            logging.warning(f'Rejected URL with no hostname: {url}')
            return False

        # Convert hostname to lowercase for safe comparison
        hostname = hostname.lower().strip()

        for pattern in allowed_patterns:
            if re.match(pattern, hostname):
                return True

        logging.warning(f'SECURITY WARNING: Blocked untrusted URL fetch attempt: {url}')
        return False
    except Exception as e:
        logging.warning(f'Error validating URL safety: {url}. Error: {e}')
        return False


def verify_doc_link(url: str) -> str:
    """Verify that a given candidate documentation URL is valid and returns 200 OK.

    This tool is strictly restricted to reference and documentation domains.

    Args:
        url: The absolute documentation URL to verify.

    Returns:
        'Valid' if HTTP 200, otherwise an error description.
    """
    if not is_safe_url(url, ALLOWED_DOC_DOMAINS):
        return 'Error: Blocked untrusted URL (unauthorized domain)'
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True)
        if resp.status_code == 200:
            return 'Valid'
        resp = requests.get(url, timeout=5, allow_redirects=True)
        if resp.status_code == 200:
            return 'Valid'
        return f'Invalid status: {resp.status_code}'
    except Exception as e:
        return f'Error: {e}'


def read_spec_link(url: str) -> str:
    """Fetch and extract clean text content from an official specification URL.

    This tool is strictly restricted to official specification domains.

    Args:
        url: The absolute specification URL to read.

    Returns:
        The extracted text content of the page, or an error message.
    """
    if not is_safe_url(url, ALLOWED_SPEC_DOMAINS):
        return 'Error: Blocked untrusted URL (unauthorized domain)'
    import trafilatura
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return f"Failed to fetch URL: HTTP {resp.status_code}"
        downloaded = resp.text
        extracted = trafilatura.extract(downloaded)
        if not extracted:
            return "Could not extract text content from the page."
        return extracted
    except Exception as e:
        return f"Error reading URL: {e}"


def read_explainer_link(url: str) -> str:
    """Fetch and extract clean text content from a feature explainer URL.

    This tool is strictly restricted to explainer and repository domains (like GitHub).

    Args:
        url: The absolute explainer URL to read.

    Returns:
        The extracted text content of the page, or an error message.
    """
    if not is_safe_url(url, ALLOWED_EXPLAINER_DOMAINS):
        return 'Error: Blocked untrusted URL (unauthorized domain)'
    import trafilatura
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return f"Failed to fetch URL: HTTP {resp.status_code}"
        downloaded = resp.text
        extracted = trafilatura.extract(downloaded)
        if not extracted:
            return "Could not extract text content from the page."
        return extracted
    except Exception as e:
        return f"Error reading URL: {e}"



def compute_feature_fingerprint(feature: FeatureEntry) -> str:
    """Computes a SHA-256 fingerprint hash of the feature details used for summaries."""
    elements = [
        feature.name or '',
        str(feature.category or 0),
        feature.summary or '',
        ','.join(sorted(feature.explainer_links or [])),
        feature.spec_link or '',
    ]
    payload = '|'.join(elements).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def parse_baseline_date(date_str: str | None) -> date | None:
    """Parses a YYYY-MM-DD string from the AI response into a datetime.date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        logging.warning(f'Failed to parse baseline date string: {date_str}')
        return None


class SummaryGeneratorInterface(ABC):
    """Interface for feature summary generators."""

    @abstractmethod
    def generate_summary(
        self, feature: FeatureEntry, prompt_version: int, run_id: str | None = None
    ) -> SummaryResponseSchema:
        """Generates an AI summary suggestion for the given feature entry."""
        pass


class GeminiSummaryGenerator(SummaryGeneratorInterface):
    """Real implementation invoking the Gemini API via google-adk."""

    def generate_summary(
        self, feature: FeatureEntry, prompt_version: int, run_id: str | None = None
    ) -> SummaryResponseSchema:
        """Generates summary using the Gemini API via google-adk."""
        from google.adk import Agent
        from google.adk.runners import InMemoryRunner
        from google.genai import types

        # Load prompt template
        prompt_path = os.path.join(
            settings.ROOT_DIR, 'framework', 'prompts', f'v{prompt_version}.md'
        )
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Fill template variables
        category_str = core_enums.FEATURE_CATEGORIES.get(
            feature.category, 'Unknown'
        )
        explainer_str = ', '.join(feature.explainer_links or [])
        spec_str = feature.spec_link or 'None'

        # 1. Retrieve the model's actual token limit dynamically from the Gemini API
        from google.genai import Client
        api_key = os.environ.get('GEMINI_API_KEY') or settings.GEMINI_API_KEY
        client = Client(api_key=api_key)

        try:
            model_info = client.models.get(model=settings.SUMMARY_GENERATOR_MODEL)
            input_token_limit = model_info.input_token_limit or DEFAULT_INPUT_TOKEN_LIMIT
        except Exception as e:
            logging.warning(f'Failed to fetch model info from API: {e}. Falling back to default limits.')
            input_token_limit = DEFAULT_INPUT_TOKEN_LIMIT

        # Safe character limit is dynamic based on model capacity and safety margins
        safe_char_limit = int(input_token_limit * TOKEN_TO_CHAR_FACTOR * SAFE_HEADROOM_FACTOR)

        # 2. Context safety limits check on the raw summary input
        summary_raw = feature.summary or ''
        summary_truncated = False
        if len(summary_raw) > safe_char_limit:
            summary_raw = summary_raw[:safe_char_limit] + ' ... [Truncated to fit context safety limits]'
            summary_truncated = True

        prompt = (
            template.replace('{{ name }}', feature.name)
            .replace('{{ category }}', category_str)
            .replace('{{ summary }}', summary_raw)
            .replace('{{ explainer_links }}', explainer_str)
            .replace('{{ spec_link }}', spec_str)
        )

        # Log prompt context details
        run_suffix = f'_{run_id}' if run_id else ''
        FeatureSummaryProgressStep.update_step(
            feature.key.id() if (feature and feature.key) else 0,
            f'prompt_context{run_suffix}',
            f'Input payload: {len(prompt)} chars (Feature: "{feature.name}", Model Limit: {input_token_limit} tokens).',
            core_enums.ProgressStepStatus.SUCCESS.value
        )

        if summary_truncated:
            # Let the user know we shortened the context!
            FeatureSummaryProgressStep.update_step(
                feature.key.id() if (feature and feature.key) else 0,
                f'prompt_compression{run_suffix}',
                'Notice: Feature description was extremely long and was shortened to stay within safety limits.',
                core_enums.ProgressStepStatus.SUCCESS.value
            )

        from functools import cached_property

        from google.adk.models import Gemini
        from google.genai import Client

        class ConfiguredGemini(Gemini):
            """Subclass to explicitly inject the API key, bypassing implicit env resolution."""
            def __init__(self, model: str, api_key: str, **kwargs):
                super().__init__(model=model, **kwargs)
                self._custom_api_key = api_key

            @cached_property
            def api_client(self) -> Client:
                # Explicit api_key prevents the SDK from clearing it when running in GCP/GAE
                return Client(api_key=self._custom_api_key)

        configured_model = ConfiguredGemini(
            model=settings.SUMMARY_GENERATOR_MODEL,
            api_key=settings.GEMINI_API_KEY
        )

        # Instantiate ADK Agent
        agent = Agent(
            name='summary_suggestion_generator',
            description='Generates release notes summary suggestions.',
            model=configured_model,
            instruction=prompt,
            tools=[search_mdn, verify_doc_link, read_spec_link, read_explainer_link],
        )

        run_suffix = f'_{run_id}' if run_id else ''
        llm_step_id = f'{core_enums.ProgressStepId.LLM_GENERATION.value}{run_suffix}'

        runner = InMemoryRunner(agent=agent)
        runner.auto_create_session = True

        import asyncio

        async def run_agent_async():
            events = runner.run_async(
                user_id='system',
                session_id=f'summary_gen_{feature.key.id() if feature.key else "mock"}',
                new_message=types.Content(parts=[types.Part(text='Generate summary')]),
            )
            final_text = ""
            async for event in events:
                role = getattr(event.content, "role", None) if event.content else None
                event_dict = event.model_dump(exclude_none=True) if hasattr(event, 'model_dump') else event.dict(exclude_none=True)
                logging.info(f'[AGENT EVENT] role={role}, event={event_dict}')
                
                # --- EVENT INTERCEPTION FOR PROGRESS TRACKING ---
                feature_id = feature.key.id() if (feature and feature.key) else 0
                
                # 1. Capture Tool Calls (Function Calls)
                if hasattr(event, 'get_function_calls'):
                    for fc in event.get_function_calls():
                        step_id = f"tool_{fc.id}"
                        if fc.name == core_enums.AISummaryToolName.SEARCH_MDN.value:
                            query = fc.args.get('query', '')
                            msg = f"Searching MDN Web Docs for '{query}'..."
                        elif fc.name == core_enums.AISummaryToolName.VERIFY_LINK.value:
                            url = fc.args.get('url', '')
                            msg = f"Verifying documentation link: {url}..."
                        elif fc.name == core_enums.AISummaryToolName.READ_URL.value:
                            url = fc.args.get('url', '')
                            msg = f"Reading content from: {url}..."
                        else:
                            msg = f"Executing tool: {fc.name}..."
                            
                        FeatureSummaryProgressStep.update_step(
                            feature_id,
                            step_id,
                            msg,
                            core_enums.ProgressStepStatus.IN_PROGRESS.value
                        )
                
                # 2. Capture Tool Responses (Function Responses)
                if hasattr(event, 'get_function_responses'):
                    for resp in event.get_function_responses():
                        step_id = f"tool_{resp.id}"
                        step_key = ndb.Key(
                            'FeatureSummarySuggestion', feature_id,
                            'FeatureSummaryProgressStep', step_id
                        )
                        step = step_key.get()
                        
                        res_str = str(resp.response)
                        is_success = True
                        if 'Invalid' in res_str or 'Error' in res_str or 'failed' in res_str.lower():
                            is_success = False
                            
                        status = (
                            core_enums.ProgressStepStatus.SUCCESS.value
                            if is_success
                            else core_enums.ProgressStepStatus.FAILED.value
                        )
                        
                        if step:
                            base_msg = step.message.rstrip('.')
                            if base_msg.endswith('...'):
                                base_msg = base_msg[:-3]
                            msg = f"{base_msg}... {'Done' if is_success else 'Failed'}"
                        else:
                            msg = f"Executed tool: {resp.name}... {'Done' if is_success else 'Failed'}"
                            
                        FeatureSummaryProgressStep.update_step(
                            feature_id, step_id, msg, status
                        )

                # 3. Capture Silent Errors
                if getattr(event, 'error_code', None):
                    FeatureSummaryProgressStep.update_step(
                        feature_id,
                        llm_step_id,
                        f"AI generation failed: {event.error_message}",
                        core_enums.ProgressStepStatus.FAILED.value
                    )

                if role == 'model' and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            final_text += part.text
            return final_text

        final_text = asyncio.run(run_agent_async())

        if not final_text:
            raise ValueError('No text response received from the AI summary agent.')

        # Clean and parse JSON response
        import json

        clean_str = final_text.strip()
        if clean_str.startswith('```json'):
            clean_str = clean_str[7:]
        if clean_str.endswith('```'):
            clean_str = clean_str[:-3]

        data = json.loads(clean_str.strip())
        if isinstance(data, dict):
            return SummaryResponseSchema(**data)

        raise ValueError(f'Unexpected output structure from agent: {final_text}')


class MockSummaryGenerator(SummaryGeneratorInterface):
    """Mock implementation returning canned suggestion responses instantly."""

    def generate_summary(
        self, feature: FeatureEntry, prompt_version: int, run_id: str | None = None
    ) -> SummaryResponseSchema:
        """Generates a canned mock summary response locally."""
        return SummaryResponseSchema(
            feasibility_decision='generate',
            suggested_summary=(
                f"This is a mock summary suggestion for the feature '{feature.name}'. "
                'It is generated locally.'
            ),
            suggested_doc_links=[
                'https://developer.mozilla.org/en-US/docs/Web/API'
            ],
            baseline_status='limited',
            generation_rationale='Canned local mock summary suggestion.',
        )


def get_summary_generator() -> SummaryGeneratorInterface:
    """Factory method to return the configured generator implementor."""
    if settings.USE_MOCK_SUMMARY_GENERATOR:
        return MockSummaryGenerator()

    # Load and configure dynamic keys
    secrets.load_gemini_api_key()
    if settings.GEMINI_API_KEY:
        os.environ['GEMINI_API_KEY'] = settings.GEMINI_API_KEY
        os.environ['GOOGLE_API_KEY'] = settings.GEMINI_API_KEY
        return GeminiSummaryGenerator()

    if settings.DEV_MODE:
        logging.warning(
            'GEMINI_API_KEY not configured. Falling back to Mock Summary Generator.'
        )
        return MockSummaryGenerator()

    raise ValueError(
        'GEMINI_API_KEY is not configured in settings or environment.'
    )


def generate_summary_for_feature(
    feature: FeatureEntry,
    prompt_version: int = GENERATOR_VERSION,
    run_id: str | None = None,
) -> SummaryResponseSchema:
    """Helper to retrieve the active generator factory and run generation on a feature."""
    generator = get_summary_generator()
    return generator.generate_summary(feature, prompt_version, run_id=run_id)


def is_transient_error(e: Exception) -> bool:
    """Classifies whether an exception represents a transient/retryable error."""
    import httpx
    import requests
    from google.genai.errors import APIError, ClientError, ServerError

    # 1. Google GenAI SDK API Errors
    if isinstance(e, ServerError):
        return True
    if isinstance(e, ClientError):
        # 429 Too Many Requests (Rate Limit) is transient
        return getattr(e, 'code', None) == 429
    if isinstance(e, APIError):
        code = getattr(e, 'code', None)
        return code in [429, 500, 503, 504]

    # 2. HTTPX Network / Timeout Errors (used by google-genai SDK under the hood)
    if isinstance(e, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)):
        return True

    # 3. Standard requests Network / Timeout Errors (used by our tools)
    if isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True

    # 4. Specific system/SSL temporary errors
    # E.g., FileNotFoundError on ssl.py (transient environment path resolution error)
    if isinstance(e, FileNotFoundError):
        tb = e.__traceback__
        while tb:
            filename = tb.tb_frame.f_code.co_filename
            if 'ssl.py' in filename.lower():
                return True
            tb = tb.tb_next

    # Default: Any other unclassified exception (like ValueError, KeyError, etc.)
    # is treated as a permanent code/config error.
    return False


def get_error_source_and_message(e: Exception) -> tuple[str, str]:
    """Classifies the exception to return a user-friendly error source and the detailed message."""
    import httpx
    import requests
    from google.genai.errors import APIError, ClientError, ServerError

    if isinstance(e, ServerError):
        msg = getattr(e, 'message', str(e))
        return "Gemini API Server Error", f"503 {msg}"
    if isinstance(e, ClientError):
        code = getattr(e, 'code', 400)
        msg = getattr(e, 'message', str(e))
        return "Gemini API Client Error", f"{code} {msg}"
    if isinstance(e, APIError):
        code = getattr(e, 'code', 'Error')
        msg = getattr(e, 'message', str(e))
        return "Gemini API Error", f"{code} {msg}"
    if isinstance(e, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError,
                      requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return "Gemini API Network/Timeout Error", str(e)

    # Check for FileNotFoundError in ssl.py (transient environment path resolution error)
    if isinstance(e, FileNotFoundError):
        tb = e.__traceback__
        while tb:
            filename = tb.tb_frame.f_code.co_filename
            if 'ssl.py' in filename.lower():
                return "System SSL Error", "Temporary ssl.py resolution failure"
            tb = tb.tb_next

    return "System Error", str(e)


def get_task_retry_count() -> int:
    """Retrieves the current task retry count from Flask request headers."""
    try:
        import flask
        headers = flask.request.headers
        retry_hdr = headers.get('X-AppEngine-TaskRetryCount') or headers.get('X-CloudTasks-TaskRetryCount')
        if retry_hdr:
            return int(retry_hdr)
    except Exception:
        pass
    return 0


MAX_TRANSIENT_RETRIES = 5


def generate_summary_suggestion(
    feature_id: int,
    prompt_version: int = GENERATOR_VERSION,
    force: bool = False,
) -> None:
    """Orchestrates loading, generation, and updating of the FeatureSummarySuggestion."""
    feature = FeatureEntry.get_by_id(feature_id)
    if not feature:
        logging.error(f'Feature {feature_id} not found.')
        return

    suggestion_key = ndb.Key('FeatureSummarySuggestion', feature_id)
    suggestion = suggestion_key.get()
    if not suggestion:
        suggestion = FeatureSummarySuggestion(
            key=suggestion_key,
            status=core_enums.SummarySuggestionStatus.NONE.value,
        )

    current_fp = compute_feature_fingerprint(feature)

    # Check if we already have an up-to-date suggestion
    if (
        not force
        and suggestion.status
        in [
            core_enums.SummarySuggestionStatus.COMPLETE,
            core_enums.SummarySuggestionStatus.DISCARDED,
        ]
        and suggestion.version == prompt_version
        and suggestion.source_fingerprint == current_fp
    ):
        logging.info(
            f'AI summary suggestion for feature {feature_id} is already up-to-date (status: {suggestion.status}). Skipping generation.'
        )
        return



    # If the suggestion was already approved/applied, back up these values as the new "original" reference!
    if suggestion.status == core_enums.SummarySuggestionStatus.APPLIED.value:
        suggestion.original_summary = feature.summary
        suggestion.original_doc_links = feature.doc_links or []
        suggestion.original_baseline_status = suggestion.baseline_status
        suggestion.original_baseline_newly_date = suggestion.baseline_newly_date
        suggestion.original_baseline_widely_date = suggestion.baseline_widely_date

    suggestion.status = core_enums.SummarySuggestionStatus.IN_PROGRESS.value
    suggestion.last_generation_attempt = datetime.now()
    suggestion.status_message = 'Initializing summary generator...'
    suggestion.put()

    import time
    run_id = str(int(time.time()))
    run_suffix = f'_{run_id}'
    start_step_id = f'{core_enums.ProgressStepId.START.value}{run_suffix}'
    llm_step_id = f'{core_enums.ProgressStepId.LLM_GENERATION.value}{run_suffix}'

    # Count how many separators already exist to determine the absolute attempt number
    existing_steps = FeatureSummaryProgressStep.get_timeline(feature_id)
    separator_count = sum(1 for s in existing_steps if s.key.id().startswith('separator_'))
    attempt_number = separator_count + 1

    # Prune old progress steps (keeping the last 20) to prevent database bloat
    FeatureSummaryProgressStep.clear_timeline(feature_id)

    # Always write a separator line for every attempt
    model_name = settings.SUMMARY_GENERATOR_MODEL.split('/')[-1]
    service_version = os.environ.get('GAE_VERSION', 'localdev')
    FeatureSummaryProgressStep.update_step(
        feature_id,
        f'separator_{run_id}',
        f'--- New Generation Attempt #{attempt_number} (Model: {model_name}, Prompt: v{prompt_version}.md, Revision: {service_version}) ---',
        core_enums.ProgressStepStatus.SUCCESS.value
    )
    FeatureSummaryProgressStep.update_step(
        feature_id,
        start_step_id,
        'Initializing summary generator...',
        core_enums.ProgressStepStatus.SUCCESS.value
    )
    FeatureSummaryProgressStep.update_step(
        feature_id,
        llm_step_id,
        'Executing AI generation loop...',
        core_enums.ProgressStepStatus.IN_PROGRESS.value
    )

    try:
        logging.info(f'Triggering AI generation for feature {feature_id}...')
        result = generate_summary_for_feature(
            feature, prompt_version=prompt_version, run_id=run_id
        )

        if result.feasibility_decision != 'generate':
            suggestion.status = core_enums.SummarySuggestionStatus.SKIPPED.value
            suggestion.suggested_summary = None
            suggestion.suggested_doc_links = []
            suggestion.baseline_status = 'none'
            suggestion.baseline_newly_date = None
            suggestion.baseline_widely_date = None
            suggestion.generation_rationale = result.generation_rationale
            suggestion.status_message = (
                f'Generation skipped: {result.feasibility_decision}'
            )
        else:
            suggestion.suggested_summary = result.suggested_summary
            suggestion.suggested_doc_links = result.suggested_doc_links
            suggestion.baseline_status = result.baseline_status
            suggestion.baseline_newly_date = parse_baseline_date(result.baseline_newly_date)
            suggestion.baseline_widely_date = parse_baseline_date(result.baseline_widely_date)
            suggestion.generation_rationale = result.generation_rationale
            suggestion.status = core_enums.SummarySuggestionStatus.COMPLETE.value
            suggestion.status_message = 'Generation complete!'
        suggestion.model_used = settings.SUMMARY_GENERATOR_MODEL
        suggestion.version = prompt_version
        suggestion.source_fingerprint = current_fp
        suggestion.version_token = 1

        now_str = datetime.utcnow().isoformat()
        suggestion.summary_provenance = {
            'original_author': 'SYSTEM',
            'modified_by': None,
            'reviewed_by': None,
            'state': 'original',
            'timestamp': now_str,
        }
        suggestion.doc_links_provenance = {
            'original_author': 'SYSTEM',
            'modified_by': None,
            'reviewed_by': None,
            'state': 'original',
            'timestamp': now_str,
        }
        
        # Mark the LLM generation step as complete
        FeatureSummaryProgressStep.update_step(
            feature_id,
            llm_step_id,
            'AI generation complete!',
            core_enums.ProgressStepStatus.SUCCESS.value
        )
        suggestion.put()
        logging.info(
            f'AI generation for feature {feature_id} completed successfully.'
        )

    except Exception as e:
        retry_count = get_task_retry_count()
        error_source, error_msg = get_error_source_and_message(e)

        if is_transient_error(e) and retry_count < MAX_TRANSIENT_RETRIES:
            logging.warning(
                f'Transient failure during AI generation for feature {feature_id} '
                f'(Attempt {retry_count + 1}/{MAX_TRANSIENT_RETRIES + 1}): {e}. '
                'Re-raising to trigger Cloud Task retry with exponential backoff.'
            )
            # Mark the active loop execution step as failed
            FeatureSummaryProgressStep.update_step(
                feature_id,
                llm_step_id,
                'Executing AI generation loop... Failed',
                core_enums.ProgressStepStatus.FAILED.value
            )
            # Write a NEW chronologically correct retry step with the exact error
            FeatureSummaryProgressStep.update_step(
                feature_id,
                f'retry_{retry_count}_{run_id}',
                f'Attempt {retry_count + 1}/{MAX_TRANSIENT_RETRIES + 1} failed: {error_source} ({error_msg}). Retrying...',
                core_enums.ProgressStepStatus.RETRIYING.value
            )
            # Update status message and timestamp to keep the lock fresh during retries
            suggestion.status_message = f'Server busy (Attempt {retry_count + 1}/{MAX_TRANSIENT_RETRIES + 1}). Retrying...'
            suggestion.status_timestamp = datetime.now()
            suggestion.put()
            raise
        else:
            if is_transient_error(e):
                suggestion.status = core_enums.SummarySuggestionStatus.OVERLOADED.value
                suggestion.status_message = 'Gemini API is currently experiencing high demand. Retries exhausted.'
                logging.error(
                    f'Transient failure exhausted after {retry_count + 1} attempts for feature {feature_id}. '
                    f'Marking as OVERLOADED permanently. Error: {e}'
                )
                # Mark the active loop execution step as failed
                FeatureSummaryProgressStep.update_step(
                    feature_id,
                    llm_step_id,
                    'Executing AI generation loop... Failed',
                    core_enums.ProgressStepStatus.FAILED.value
                )
                # Write a NEW permanent failure step with the exhausted error details
                FeatureSummaryProgressStep.update_step(
                    feature_id,
                    f'fail_overloaded_{run_id}',
                    f'{error_source} (Retries exhausted). Error: {error_msg}',
                    core_enums.ProgressStepStatus.FAILED.value
                )
            else:
                suggestion.status = core_enums.SummarySuggestionStatus.FAILED.value
                suggestion.status_message = f'Generation failed: {e}'
                logging.exception(f'Permanent failure during AI generation for feature {feature_id}: {e}')
                # Mark the active loop execution step as failed
                FeatureSummaryProgressStep.update_step(
                    feature_id,
                    llm_step_id,
                    'Executing AI generation loop... Failed',
                    core_enums.ProgressStepStatus.FAILED.value
                )
                # Write a NEW permanent failure step with the exact error details
                FeatureSummaryProgressStep.update_step(
                    feature_id,
                    f'fail_permanent_{run_id}',
                    f'{error_source}: {error_msg}',
                    core_enums.ProgressStepStatus.FAILED.value
                )
            suggestion.put()
