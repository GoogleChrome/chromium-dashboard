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

import json
import logging
import re
from collections.abc import Callable, Sequence
from typing import Any

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from ai.errors import get_error_source_and_message
from ai.mock_summary_generator import SummaryGenerator
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


def build_summary_agent(
    model_name: str,
    instruction: str,
    tools: Sequence[Callable[..., Any]] = AI_SUMMARY_TOOLS,
) -> Agent:
    """Builds a Google ADK Agent instance configured for developer release note generation."""
    return Agent(
        name='release_notes_summary_agent',
        model=model_name,
        instruction=instruction,
        tools=list(tools),
        description=(
            'Autonomous agent that researches web platform specifications and'
            ' MDN docs to generate developer release notes.'
        ),
    )


def extract_json_payload(text: str) -> dict[str, Any]:
    """Extracts and parses JSON object from model response text with defensive fallbacks."""
    clean_text = text.strip()
    match = re.search(r'```(?:json)?\s*([\s\S]*?)(?:```|$)', clean_text)
    if match:
        clean_text = match.group(1).strip()
    try:
        parsed = json.loads(clean_text)
        if isinstance(parsed, dict):
            return parsed
        logging.warning('Parsed JSON is not a dictionary: %s', type(parsed))
        return {
            'summary': clean_text,
            'rationale': '',
            'doc_links': [],
        }
    except json.JSONDecodeError as e:
        logging.warning('Failed to parse JSON payload from response: %s', e)
        return {
            'summary': clean_text,
            'rationale': '',
            'doc_links': [],
        }


class GeminiSummaryGenerator(SummaryGenerator):
    """Pure orchestrator for generating structured developer release notes using Google ADK."""

    def __init__(
        self,
        model_name: str,
        prompt_template: FeaturePromptTemplate = CANONICAL_RELEASE_NOTES_TEMPLATE,
        tools: Sequence[Callable[..., Any]] = AI_SUMMARY_TOOLS,
    ) -> None:
        """Initializes generator with model name, prompt template, and tools."""
        self.model_name = model_name
        self.tools = list(tools)
        self.prompt_template = prompt_template
        self.instruction = (
            'You are an expert technical writer and Chromium engineer'
            ' specializing in developer release notes.'
        )

        self.agent = build_summary_agent(
            model_name=self.model_name,
            instruction=self.instruction,
            tools=self.tools,
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

            session_id = f'summary_{feature_input.name}'
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

                # 3. Capture generated model text parts
                if event.message and event.message.parts:
                    text_parts = [p.text for p in event.message.parts if p.text]
                    if text_parts:
                        final_text = ''.join(text_parts)

            parsed = extract_json_payload(final_text)
            raw_docs = parsed.get('doc_links', ())
            doc_links = tuple(str(u) for u in raw_docs if u)

            rep.log_step(
                step_id=ProgressStepId.SUCCESS,
                status=ProgressStepStatus.SUCCESS,
                message='LLM generated release note candidate successfully',
            )

            return SummaryResult(
                suggested_summary=str(parsed.get('summary', '')).strip(),
                generation_rationale=str(parsed.get('rationale', '')).strip(),
                suggested_doc_links=doc_links,
                raw_response=final_text,
            )

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
