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

"""Deterministic mock summary generator for offline tests and Playwright CI."""

from __future__ import annotations

import abc

from ai.progress_reporter import (
    FeatureSummaryInput,
    ListProgressReporter,
    ProgressReporter,
    SummaryResult,
)
from internals.core_enums import ProgressStepId, ProgressStepStatus


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


class MockSummaryGenerator(SummaryGenerator):
    """Deterministic mock summary generator for offline tests and Playwright CI."""

    def __init__(
        self,
        canned_summary: str = 'Mock developer release note summary.',
        canned_rationale: str = 'Mock rationale.',
        canned_doc_links: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        """Initializes mock generator with optional canned response fields."""
        self.canned_summary = canned_summary
        self.canned_rationale = canned_rationale
        self.canned_doc_links = tuple(canned_doc_links or ())

    def generate_summary(
        self,
        feature_input: FeatureSummaryInput,
        reporter: ProgressReporter | None = None,
    ) -> SummaryResult:
        """Returns deterministic canned SummaryResult and logs start/success steps."""
        rep = reporter or ListProgressReporter()
        rep.log_step(
            step_id=ProgressStepId.START,
            status=ProgressStepStatus.SUCCESS,
            message='Mock summary generator start',
        )
        rep.log_step(
            step_id=ProgressStepId.SUCCESS,
            status=ProgressStepStatus.SUCCESS,
            message='Mock summary generator success',
        )
        return SummaryResult(
            suggested_summary=self.canned_summary,
            generation_rationale=self.canned_rationale,
            suggested_doc_links=self.canned_doc_links,
        )
