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

"""Core Gemini Summary Generator Orchestrator for Developer Release Notes.

Orchestrates multi-turn LLM generation with Google GenAI SDK, calling interactive
sandbox tools, tracking ancestor Datastore progress steps, enforcing Optimistic
Concurrency Control (OCC), classifying transient errors, and pruning timeline history.
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

from google import genai
from google.cloud import ndb

import settings
from framework.ai_tools import AI_SUMMARY_TOOLS, TOOL_MAP
from framework.feature_fingerprint import compute_feature_fingerprint
from framework.utils import safe_plain_text_to_markdown
from internals.core_enums import (
    AISummaryToolName,
    ProgressStepId,
    ProgressStepStatus,
    SummarySuggestionStatus,
)
from internals.core_models import (
    FeatureEntry,
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)

DEFAULT_MODEL = getattr(settings, 'SUMMARY_GENERATOR_MODEL', 'gemini-2.0-flash')
DEFAULT_PROMPT_VERSION = 'v1'


def is_transient_error(e: Exception) -> bool:
    """Classifies whether an exception represents a transient/retryable error.

    Used downstream by background Cloud Task workers and batch generation pipelines
    to distinguish retryable rate limits (429), timeouts, and service unavailability (503)
    from permanent specification or parsing failures.
    """
    if isinstance(e, json.JSONDecodeError):
        return True
    err_str = str(e).lower()
    transient_keywords = [
        '429',
        '503',
        '504',
        'rate limit',
        'quota',
        'timeout',
        'temporary',
    ]
    return any(kw in err_str for kw in transient_keywords)


def get_error_source_and_message(e: Exception) -> tuple[str, str]:
    """Returns a user-friendly error source and detailed message for UI presentation.

    Used downstream by frontend API handlers and review error dialogs to display
    actionable failure reasons to editors and feature owners.
    """
    err_str = str(e)
    if '429' in err_str or 'quota' in err_str.lower():
        return (
            'Rate Limit Exceeded',
            'Gemini API quota exceeded. Please retry shortly.',
        )
    if '503' in err_str or '504' in err_str or 'temporary' in err_str.lower():
        return (
            'Gemini API Unavailable',
            'Service temporarily unavailable. Please retry.',
        )
    if isinstance(e, json.JSONDecodeError):
        return (
            'JSON Parsing Error',
            f'Failed to parse LLM structured output: {err_str}',
        )
    return 'Generation Error', err_str


class GeminiSummaryGenerator:
    """Orchestrator for generating structured developer release notes using Gemini."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = DEFAULT_MODEL,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
    ) -> None:
        """Initializes generator with model name, prompt version, and optional API key."""
        self.api_key = api_key
        self.model_name = model_name
        self.prompt_version = prompt_version
        self.prompt_template = self.load_prompt_template(prompt_version)

    @staticmethod
    def load_prompt_template(version: str) -> str:
        """Loads markdown prompt template from framework/prompts/<version>.md."""
        base_dir = os.path.dirname(__file__)
        prompt_path = os.path.join(base_dir, 'prompts', f'{version}.md')
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f'Prompt template {prompt_path} not found')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _get_client(self) -> genai.Client:
        """Instantiates Google GenAI Client with configured API key."""
        key = (
            self.api_key
            or getattr(settings, 'GEMINI_API_KEY', None)
            or os.environ.get('GEMINI_API_KEY')
        )
        if not key:
            raise ValueError(
                'GEMINI_API_KEY must be provided via constructor, settings.py, or'
                ' environment variable.'
            )
        return genai.Client(api_key=key)

    def _log_step(
        self,
        feature_id: int,
        step_id: ProgressStepId | str,
        status: ProgressStepStatus | str,
        tool_name: AISummaryToolName | str | None = None,
        message: str = '',
        start_time: datetime | None = None,
    ) -> None:
        """Persists a fine-grained progress step under the FeatureSummarySuggestion ancestor key."""
        parent_key = ndb.Key('FeatureSummarySuggestion', feature_id)
        step_id_val = (
            step_id.value if hasattr(step_id, 'value') else str(step_id)
        )
        status_val = status.value if hasattr(status, 'value') else str(status)
        tool_val = None
        if tool_name:
            tool_val = (
                tool_name.value
                if hasattr(tool_name, 'value')
                else str(tool_name)
            )

        step = FeatureSummaryProgressStep(
            parent=parent_key,
            step_id=step_id_val,
            status=status_val,
            tool_name=tool_val,
            message=message,
            start_timestamp=start_time or datetime.now(timezone.utc),
            end_timestamp=datetime.now(timezone.utc),
        )
        step.put()

    def _render_prompt(self, feature_dict: dict[str, Any]) -> str:
        """Populates template placeholders with sanitized feature metadata."""
        prompt = self.prompt_template
        raw_summary = feature_dict.get('summary', '') or ''
        formatted_summary = safe_plain_text_to_markdown(raw_summary)

        doc_links = feature_dict.get('doc_links', []) or []
        formatted_docs = (
            ', '.join(doc_links)
            if isinstance(doc_links, list)
            else str(doc_links)
        )

        search_tags = feature_dict.get('search_tags', []) or []
        formatted_tags = (
            ', '.join(search_tags)
            if isinstance(search_tags, list)
            else str(search_tags)
        )

        replacements = {
            '{{ name }}': str(feature_dict.get('name', 'TBD')),
            '{{ shipped_milestone }}': str(
                feature_dict.get('shipped_milestone', 'TBD')
            ),
            '{{ summary }}': formatted_summary,
            '{{ spec_link }}': str(feature_dict.get('spec_link', 'None')),
            '{{ doc_links }}': formatted_docs or 'None',
            '{{ standard_maturity }}': str(
                feature_dict.get('standard_maturity', '0')
            ),
            '{{ category }}': str(feature_dict.get('category', '0')),
            '{{ search_tags }}': formatted_tags or 'None',
        }

        for placeholder, val in replacements.items():
            prompt = prompt.replace(placeholder, val)
        return prompt

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        """Extracts and parses JSON object from model response text."""
        clean_text = text.strip()
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', clean_text)
        if match:
            clean_text = match.group(1).strip()

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError as e:
            logging.warning('Failed to parse JSON from LLM response: %s', e)
            return {
                'summary': clean_text,
                'rationale': 'Direct model output generation.',
                'doc_links': [],
            }

    def _execute_tool(
        self, fn_name: str, fn_args: dict[str, Any]
    ) -> dict[str, Any]:
        """Executes sandbox tool by name with exception isolation."""
        tool_fn = TOOL_MAP.get(fn_name)
        if not tool_fn or not callable(tool_fn):
            return {
                'status': 'failed',
                'error': f'Tool {fn_name} is not recognized.',
            }
        try:
            return tool_fn(**fn_args)  # type: ignore[no-any-return]
        except Exception as e:
            logging.warning('Error executing tool %s: %s', fn_name, e)
            return {'status': 'failed', 'error': str(e)}

    def generate_summary(
        self,
        feature_id: int,
        feature: FeatureEntry | dict[str, Any],
        dry_run: bool = False,
    ) -> tuple[FeatureSummarySuggestion | None, str | None]:
        """Generates release note summary for a feature using multi-turn LLM loop.

        Args:
          feature_id: ID of the feature.
          feature: FeatureEntry entity or dictionary.
          dry_run: If True, executes full LLM generation and returns candidate suggestion
            without persisting to Datastore (used for offline evaluation benchmarks).

        Returns:
          Tuple of (FeatureSummarySuggestion entity or None, error_message or None).
        """
        feature_dict = (
            feature if isinstance(feature, dict) else feature.to_dict()
        )
        current_fingerprint = compute_feature_fingerprint(feature)

        existing = FeatureSummarySuggestion.get_by_id(feature_id)
        if (
            existing
            and existing.source_fingerprint == current_fingerprint
            and existing.status != SummarySuggestionStatus.REJECTED.value
        ):
            logging.info(
                'Feature %d fingerprint matches existing suggestion; skipping'
                ' generation.',
                feature_id,
            )
            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.START,
                status=ProgressStepStatus.SUCCESS,
                message='Source fingerprint unchanged. Skipping generation.',
            )
            FeatureSummaryProgressStep.clear_timeline(feature_id, keep_count=20)
            return existing, None

        client = self._get_client()
        user_prompt = self._render_prompt(feature_dict)

        try:
            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.START,
                status=ProgressStepStatus.SUCCESS,
                message=f'Rendered prompt template {self.prompt_version}',
            )

            chat = client.chats.create(
                model=self.model_name,
                config=genai.types.GenerateContentConfig(
                    tools=list(AI_SUMMARY_TOOLS),
                    temperature=0.2,
                ),
            )

            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.LLM_GENERATION,
                status=ProgressStepStatus.IN_PROGRESS,
                message=f'Invoking {self.model_name} with tools',
            )

            response = chat.send_message(user_prompt)

            while response.function_calls:
                for fn_call in response.function_calls:
                    tool_name = fn_call.name or ''
                    tool_args = fn_call.args or {}
                    if not tool_name:
                        continue

                    step_id = ProgressStepId.SEARCH_MDN
                    if tool_name == AISummaryToolName.VERIFY_DOC_LINK.value:
                        step_id = ProgressStepId.VERIFY_DOC_LINK
                    elif tool_name == AISummaryToolName.READ_SPEC_LINK.value:
                        step_id = ProgressStepId.READ_SPEC

                    tool_start = datetime.now(timezone.utc)
                    self._log_step(
                        feature_id=feature_id,
                        step_id=step_id,
                        status=ProgressStepStatus.IN_PROGRESS,
                        tool_name=tool_name,
                        message=f'Calling sandbox tool {tool_name}',
                        start_time=tool_start,
                    )

                    tool_output = self._execute_tool(tool_name, tool_args)

                    self._log_step(
                        feature_id=feature_id,
                        step_id=step_id,
                        status=ProgressStepStatus.SUCCESS,
                        tool_name=tool_name,
                        message=f'Completed sandbox tool {tool_name}',
                        start_time=tool_start,
                    )

                    response = chat.send_message(
                        genai.types.Part.from_function_response(
                            name=tool_name,
                            response={'result': tool_output},
                        )
                    )

            parsed = self._parse_json_response(response.text or '')
            summary_text = parsed.get('summary', '').strip()
            rationale_text = parsed.get('rationale', '').strip()
            suggested_doc_links = parsed.get('doc_links', []) or []

            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.SUCCESS,
                status=ProgressStepStatus.SUCCESS,
                message='LLM generated release note candidate successfully',
            )

            is_new = existing is None
            if is_new:
                existing = FeatureSummarySuggestion(id=feature_id)

            existing.suggested_summary = summary_text
            existing.generation_rationale = rationale_text
            existing.suggested_doc_links = suggested_doc_links
            existing.source_fingerprint = current_fingerprint
            existing.status = SummarySuggestionStatus.PROPOSED.value
            existing.version_token = (
                1 if is_new else ((existing.version_token or 1) + 1)
            )
            existing.updated = datetime.now(timezone.utc)

            if not dry_run:
                existing.put()

            return existing, None

        except Exception as e:
            logging.error(
                'GeminiSummaryGenerator error for feature %d: %s', feature_id, e
            )
            self._log_step(
                feature_id=feature_id,
                step_id=ProgressStepId.LLM_GENERATION,
                status=ProgressStepStatus.FAILED,
                message=f'Generation failed: {e}',
            )
            return None, str(e)

        finally:
            FeatureSummaryProgressStep.clear_timeline(feature_id, keep_count=20)


class MockSummaryGenerator:
    """Deterministic mock summary generator for offline tests, dev emulator, and Playwright CI.

    Provides deterministic canned responses to allow unit tests, local emulator runs, and Playwright
    end-to-end suites to execute without live Gemini API quota consumption.
    """

    def __init__(
        self,
        canned_summary: str = 'Mock developer release note summary.',
        canned_rationale: str = 'Mock rationale.',
        canned_doc_links: list[str] | None = None,
    ) -> None:
        """Initializes mock generator with canned responses."""
        self.canned_summary = canned_summary
        self.canned_rationale = canned_rationale
        self.canned_doc_links = canned_doc_links or []

    def generate_summary(
        self,
        feature_id: int,
        feature: FeatureEntry | dict[str, Any],
        dry_run: bool = False,
    ) -> tuple[FeatureSummarySuggestion, None]:
        """Returns canned summary suggestion immediately without external API calls."""
        current_fingerprint = compute_feature_fingerprint(feature)
        existing = FeatureSummarySuggestion.get_by_id(feature_id)
        is_new = existing is None
        if is_new:
            existing = FeatureSummarySuggestion(id=feature_id)

        existing.suggested_summary = self.canned_summary
        existing.generation_rationale = self.canned_rationale
        existing.suggested_doc_links = self.canned_doc_links
        existing.source_fingerprint = current_fingerprint
        existing.status = SummarySuggestionStatus.PROPOSED.value
        existing.version_token = (
            1 if is_new else ((existing.version_token or 1) + 1)
        )
        existing.updated = datetime.now(timezone.utc)

        if not dry_run:
            existing.put()

        return existing, None
