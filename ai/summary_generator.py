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

"""Pure multi-turn AI release note summary generator engine using Google ADK."""

from __future__ import annotations

import abc
import dataclasses
import json
import logging
import os
import uuid
from collections.abc import Callable, Sequence
from typing import Any

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ai.errors import get_error_source_and_message
from ai.progress_reporter import (
    FeatureSummaryInput,
    ListProgressReporter,
    ProgressReporter,
    SummaryResult,
)
from framework.ai_tools import AI_SUMMARY_TOOLS
from internals.core_enums import (
    AISummaryToolName,
    ProgressStepId,
    ProgressStepStatus,
)
from prompts.renderer import (
    CANONICAL_RELEASE_NOTES_TEMPLATE,
    FeaturePromptTemplate,
)

DEFAULT_SYSTEM_INSTRUCTION = (
    'You are an expert technical writer and Chromium engineer specializing in'
    ' developer release notes.'
)


class SummaryGenerator(abc.ABC):
    """Abstract interface for release note summary generators."""

    @abc.abstractmethod
    def generate_summary(
        self,
        feature_input: FeatureSummaryInput,
        reporter: ProgressReporter | None = None,
    ) -> SummaryResult:
        """Generates release note summary for a typed feature input."""
        pass


@dataclasses.dataclass(frozen=True)
class GeneratedSummaryPayload:
    """Matches the structured response schema emitted by the Gemini model."""

    summary: str = ''
    rationale: str = ''
    doc_links: Sequence[str] = ()


def build_summary_agent(
    model_name: str,
    instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
    tools: Sequence[Callable[..., Any]] = AI_SUMMARY_TOOLS,
    output_schema: type | None = GeneratedSummaryPayload,
) -> Agent:
    """Builds a Google ADK Agent instance configured for release note generation.

    Args:
      model_name: Identifier of the Gemini model (e.g. 'gemini-3.1-pro-preview').
      instruction: System instruction prompt guiding agent behavior.
      tools: Sequence of tool functions available to the agent for research.
      output_schema: Optional type or schema class for structured output.

    Returns:
      Configured Google ADK Agent.
    """
    return Agent(
        name='release_notes_summary_agent',
        model=model_name,
        instruction=instruction,
        tools=list(tools),
        output_schema=output_schema,
        description=(
            'Autonomous agent that analyzes ChromeStatus feature entries and'
            ' researches web platform specifications and MDN docs to generate'
            ' developer release notes.'
        ),
    )


def strip_json_markdown(text: str) -> str:
    """Strips markdown code fences (```json ... ``` or ``` ... ```) from LLM output."""
    stripped = text.strip()
    if stripped.startswith('```'):
        lines = stripped.splitlines()
        if lines and lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        stripped = '\n'.join(lines).strip()
    return stripped


def parse_summary_result(raw_text: str) -> SummaryResult:
    """Parses raw model response text into a strongly-typed SummaryResult.

    Extracts the structured JSON payload matching GeneratedSummaryPayload.
    The extracted summary string within the JSON payload contains
    Markdown-formatted developer release notes.

    Example input payload:
      {
        "summary": "Adds support for `WebGPU` subgroups.",
        "rationale": "High-impact compute feature for shader developers.",
        "doc_links": ["https://developer.chrome.com/docs/webgpu"]
      }

    Args:
      raw_text: Raw LLM output JSON string matching GeneratedSummaryPayload schema.

    Returns:
      SummaryResult containing suggested summary, rationale, and doc links.

    Raises:
      ValueError: If raw_text is empty or blank.
      json.JSONDecodeError: If raw_text is not valid JSON.
      TypeError: If payload structure does not match GeneratedSummaryPayload schema.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError('Model returned an empty response.')
    cleaned = strip_json_markdown(raw_text)
    data = json.loads(cleaned)
    payload = GeneratedSummaryPayload(**data)
    return SummaryResult(
        suggested_summary=payload.summary.strip(),
        generation_rationale=payload.rationale.strip(),
        suggested_doc_links=tuple(payload.doc_links),
        raw_response=raw_text,
    )


class GeminiSummaryGenerator(SummaryGenerator):
    """Pure orchestrator for generating structured developer release notes using Google ADK."""

    def __init__(
        self,
        model_name: str,
        prompt_template: FeaturePromptTemplate = CANONICAL_RELEASE_NOTES_TEMPLATE,
        tools: Sequence[Callable[..., Any]] = AI_SUMMARY_TOOLS,
        output_schema: type | None = GeneratedSummaryPayload,
    ) -> None:
        """Initializes generator with model name, prompt template, and tools.

        Args:
          model_name: Identifier of the Gemini model to invoke.
          prompt_template: Template loader used to format feature prompts.
          tools: Tool functions available for research in the ADK loop.
          output_schema: Optional type or schema class for structured output.
        """
        self.model_name = model_name
        self.tools = list(tools)
        self.prompt_template = prompt_template
        self.instruction = DEFAULT_SYSTEM_INSTRUCTION
        self.output_schema = output_schema

        self.agent = build_summary_agent(
            model_name=self.model_name,
            instruction=self.instruction,
            tools=self.tools,
            output_schema=self.output_schema,
        )

    def _map_tool_to_step_id(
        self, tool_name: str
    ) -> tuple[ProgressStepId, AISummaryToolName | None]:
        """Maps tool name string to ProgressStepId and AISummaryToolName enum."""
        if tool_name == AISummaryToolName.VERIFY_DOC_LINK.value:
            return (
                ProgressStepId.VERIFY_DOC_LINK,
                AISummaryToolName.VERIFY_DOC_LINK,
            )
        if tool_name == AISummaryToolName.READ_SPEC_LINK.value:
            return ProgressStepId.READ_SPEC, AISummaryToolName.READ_SPEC_LINK
        if tool_name == AISummaryToolName.SEARCH_MDN.value:
            return ProgressStepId.SEARCH_MDN, AISummaryToolName.SEARCH_MDN
        return ProgressStepId.SEARCH_MDN, None

    def generate_summary(
        self,
        feature_input: FeatureSummaryInput,
        reporter: ProgressReporter | None = None,
    ) -> SummaryResult:
        """Generates release note summary for a feature input using Google ADK Runner.

        Args:
          feature_input: Strongly-typed FeatureSummaryInput DTO.
          reporter: Optional ProgressReporter instance for telemetry logging.

        Returns:
          SummaryResult containing suggested summary, rationale, and doc links.
        """
        rep = reporter or ListProgressReporter()

        # Defense-in-depth: ensure GEMINI_API_KEY or GOOGLE_API_KEY is loaded into os.environ
        if not os.environ.get('GEMINI_API_KEY') and not os.environ.get(
            'GOOGLE_API_KEY'
        ):
            try:
                from framework import secrets

                secrets.load_gemini_api_key()
            except Exception as sec_err:
                logging.warning(
                    'Could not load Gemini API key from secrets: %s', sec_err
                )

        try:
            rep.log_step(
                step_id=ProgressStepId.START,
                status=ProgressStepStatus.SUCCESS,
                message='Rendered prompt template for feature',
            )

            user_prompt = self.prompt_template.render(feature_input)

            runner = Runner(
                app_name='chromestatus_ai_summary',
                agent=self.agent,
                session_service=InMemorySessionService(),
                auto_create_session=True,
            )

            rep.log_step(
                step_id=ProgressStepId.LLM_GENERATION,
                status=ProgressStepStatus.IN_PROGRESS,
                message=f'Invoking {self.model_name} with ADK Runner',
            )

            session_id = f'summary_{uuid.uuid4().hex}'
            new_message = types.Content(
                role='user', parts=[types.Part.from_text(text=user_prompt)]
            )

            final_text = ''
            for event in runner.run(
                user_id='system',
                session_id=session_id,
                new_message=new_message,
            ):
                # 1. Capture tool invocations
                for fn_call in event.get_function_calls():
                    tool_name = fn_call.name or ''
                    step_id, tool_enum = self._map_tool_to_step_id(tool_name)
                    rep.log_step(
                        step_id=step_id,
                        status=ProgressStepStatus.IN_PROGRESS,
                        tool_name=tool_enum,
                        message=f'Calling sandbox tool {tool_name}',
                    )

                # 2. Capture tool completion responses
                for fn_resp in event.get_function_responses():
                    tool_name = fn_resp.name or ''
                    step_id, tool_enum = self._map_tool_to_step_id(tool_name)
                    resp_dict = fn_resp.response or {}
                    is_success = resp_dict.get('status') == 'success'
                    rep.log_step(
                        step_id=step_id,
                        status=(
                            ProgressStepStatus.SUCCESS
                            if is_success
                            else ProgressStepStatus.FAILED
                        ),
                        tool_name=tool_enum,
                        message=(
                            f'Completed sandbox tool {tool_name}'
                            if is_success
                            else f'Sandbox tool {tool_name} failed:'
                            f' {resp_dict.get("error", "Unknown error")}'
                        ),
                    )

                # 3. Capture model response text parts
                if event.message and event.message.parts:
                    text_parts = [p.text for p in event.message.parts if p.text]
                    if text_parts:
                        final_text = ''.join(text_parts)

            result = parse_summary_result(final_text)

            rep.log_step(
                step_id=ProgressStepId.SUCCESS,
                status=ProgressStepStatus.SUCCESS,
                message='LLM generated release note candidate successfully',
            )

            return result

        except Exception as e:
            logging.error('GeminiSummaryGenerator error: %s', e, exc_info=True)
            source, user_error_message = get_error_source_and_message(e)
            rep.log_step(
                step_id=ProgressStepId.LLM_GENERATION,
                status=ProgressStepStatus.FAILED,
                message=f'{source}: {user_error_message}',
            )
            return SummaryResult(
                suggested_summary='',
                generation_rationale='',
                suggested_doc_links=(),
                error_message=f'{source}: {user_error_message}',
            )
