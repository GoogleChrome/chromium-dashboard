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

from abc import ABC, abstractmethod
import hashlib
import logging
import os
from datetime import date, datetime

import requests
from google.cloud import ndb  # type: ignore
from pydantic import BaseModel, Field

import settings
from framework import secrets
from internals import core_enums
from internals.core_models import FeatureEntry, FeatureSummarySuggestion

GENERATOR_VERSION = 2


class SummaryResponseSchema(BaseModel):
    """Schema for the generated summary, doc links, and baseline status."""

    suggested_summary: str = Field(
        description='The 2-3 sentence developer-focused summary.'
    )
    suggested_doc_links: list[str] = Field(
        description='List of verified reference documentation links on MDN or web.dev.'
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


def verify_link(url: str) -> str:
    """Verify that a given URL is valid and returns a 200 OK status.

    Args:
        url: The absolute URL to verify.

    Returns:
        'Valid' if HTTP 200, otherwise an error description.
    """
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
def read_url(url: str) -> str:
    """Fetch and extract clean text content from a web page URL (such as a specification or explainer).

    Args:
        url: The absolute URL to read.

    Returns:
        The extracted text content of the page, or an error message.
    """
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
    @abstractmethod
    def generate_summary(
        self, feature: FeatureEntry, prompt_version: int
    ) -> SummaryResponseSchema:
        pass


class GeminiSummaryGenerator(SummaryGeneratorInterface):
    """Real implementation invoking the Gemini API via google-adk."""
    def generate_summary(
        self, feature: FeatureEntry, prompt_version: int
    ) -> SummaryResponseSchema:
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

        prompt = (
            template.replace('{{ name }}', feature.name)
            .replace('{{ category }}', category_str)
            .replace('{{ summary }}', feature.summary or '')
            .replace('{{ explainer_links }}', explainer_str)
            .replace('{{ spec_link }}', spec_str)
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
            tools=[search_mdn, verify_link, read_url],
        )

        runner = InMemoryRunner(agent=agent)
        runner.auto_create_session = True

        events = runner.run(
            user_id='system',
            session_id=f'summary_gen_{feature.key.id() if feature.key else "mock"}',
            new_message=types.Content(parts=[types.Part(text='Generate summary')]),
        )

        final_text = None
        for event in events:
            print(
                f'[AGENT EVENT] role={getattr(event.content, "role", None) if event.content else None}'
            )
            if hasattr(event, 'content') and event.content is not None:
                print(f'  Content parts: {event.content.parts}')
                if getattr(event.content, 'role', None) == 'model':
                    for part in event.content.parts:
                        if part.text:
                            final_text = part.text

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
        self, feature: FeatureEntry, prompt_version: int
    ) -> SummaryResponseSchema:
        return SummaryResponseSchema(
            suggested_summary=(
                f"This is a mock summary suggestion for the feature '{feature.name}'. "
                'It is generated locally.'
            ),
            suggested_doc_links=[
                'https://developer.mozilla.org/en-US/docs/Web/API'
            ],
            baseline_status='limited',
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
) -> SummaryResponseSchema:
    generator = get_summary_generator()
    return generator.generate_summary(feature, prompt_version)


def is_transient_error(e: Exception) -> bool:
    """Classifies whether an exception represents a transient/retryable error."""
    from google.genai.errors import APIError, ClientError, ServerError
    import httpx
    import requests

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
    suggestion.put()

    try:
        logging.info(f'Triggering AI generation for feature {feature_id}...')
        result = generate_summary_for_feature(
            feature, prompt_version=prompt_version
        )

        suggestion.suggested_summary = result.suggested_summary
        suggestion.suggested_doc_links = result.suggested_doc_links
        suggestion.baseline_status = result.baseline_status
        suggestion.baseline_newly_date = parse_baseline_date(result.baseline_newly_date)
        suggestion.baseline_widely_date = parse_baseline_date(result.baseline_widely_date)
        suggestion.status = core_enums.SummarySuggestionStatus.COMPLETE.value
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
        suggestion.put()
        logging.info(
            f'AI generation for feature {feature_id} completed successfully.'
        )

    except Exception as e:
        retry_count = get_task_retry_count()
        if is_transient_error(e) and retry_count < MAX_TRANSIENT_RETRIES:
            logging.warning(
                f'Transient failure during AI generation for feature {feature_id} '
                f'(Attempt {retry_count + 1}/{MAX_TRANSIENT_RETRIES + 1}): {e}. '
                'Re-raising to trigger Cloud Task retry with exponential backoff.'
            )
            # Update status timestamp to keep the lock fresh during retries
            suggestion.status_timestamp = datetime.now()
            suggestion.put()
            raise
        else:
            suggestion.status = core_enums.SummarySuggestionStatus.FAILED.value
            suggestion.put()
            if is_transient_error(e):
                logging.error(
                    f'Transient failure exhausted after {retry_count + 1} attempts for feature {feature_id}. '
                    f'Marking as FAILED permanently. Error: {e}'
                )
            else:
                logging.exception(f'Permanent failure during AI generation for feature {feature_id}: {e}')
