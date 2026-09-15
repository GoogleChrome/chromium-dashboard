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

"""Telemetry interfaces, data contracts, and progress reporters for AI generation pipelines."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from datetime import datetime, timezone

from google.cloud import ndb

from internals.core_enums import (
    AISummaryToolName,
    ProgressStepId,
    ProgressStepStatus,
)
from internals.core_models import (
    FeatureEntry,
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)


@dataclass(frozen=True)
class FeatureSummaryInput:
    """Strongly-typed, immutable input DTO for the AI summary generation engine.

    Attributes:
      name: Name of the web platform feature.
      summary: Existing feature description or intent summary.
      shipped_milestone: Chrome milestone when feature ships (e.g. 130 or '130').
      spec_link: URL pointing to the W3C / WHATWG specification.
      doc_links: Documentation and explainer URLs.
      search_tags: Keywords associated with the feature.
      standard_maturity: Integer enum representing standard maturity level.
      category: Integer enum representing feature category.
    """

    name: str
    summary: str
    shipped_milestone: str | int | None = 'TBD'
    spec_link: str | None = None
    doc_links: tuple[str, ...] = ()
    search_tags: tuple[str, ...] = ()
    standard_maturity: int | None = 0
    category: int | None = 0

    @classmethod
    def from_feature(
        cls,
        feature: FeatureEntry,
        shipped_milestone: str | int | None = None,
    ) -> FeatureSummaryInput:
        """Constructs an immutable FeatureSummaryInput DTO from a Datastore FeatureEntry."""
        milestone = shipped_milestone or 'TBD'
        raw_docs = tuple(feature.doc_links or ())
        raw_tags = tuple(feature.search_tags or ())

        return cls(
            name=feature.name or '',
            summary=feature.summary or '',
            shipped_milestone=milestone,
            spec_link=feature.spec_link,
            doc_links=raw_docs,
            search_tags=raw_tags,
            standard_maturity=feature.standard_maturity or 0,
            category=feature.category or 0,
        )


@dataclass(frozen=True)
class SummaryResult:
    """Strongly-typed result container produced by the AI generation engine."""

    suggested_summary: str
    generation_rationale: str
    suggested_doc_links: tuple[str, ...] = ()
    error_message: str | None = None
    raw_response: str | None = None


@dataclass(frozen=True)
class ProgressStepRecord:
    """In-memory event record representing a discrete execution step in the generation pipeline."""

    step_id: str
    status: str
    message: str
    tool_name: str | None = None
    start_time: datetime | None = None
    end_time: datetime = datetime.now(timezone.utc)


class ProgressReporter(abc.ABC):
    """Abstract interface for observing and recording AI agent generation progress."""

    @abc.abstractmethod
    def log_step(
        self,
        step_id: ProgressStepId,
        status: ProgressStepStatus,
        tool_name: AISummaryToolName | None = None,
        message: str = '',
        start_time: datetime | None = None,
    ) -> None:
        """Logs a progress step event with the given status and message."""
        pass


class ListProgressReporter(ProgressReporter):
    """In-memory progress reporter that accumulates step records in a list.

    Useful for offline evaluations, unit testing, and benchmarking without Datastore.
    """

    def __init__(self) -> None:
        """Initializes empty in-memory step accumulator."""
        self.steps: list[ProgressStepRecord] = []

    def log_step(
        self,
        step_id: ProgressStepId,
        status: ProgressStepStatus,
        tool_name: AISummaryToolName | None = None,
        message: str = '',
        start_time: datetime | None = None,
    ) -> None:
        """Records step in the in-memory list."""
        self.steps.append(
            ProgressStepRecord(
                step_id=step_id.value,
                status=status.value,
                tool_name=tool_name.value if tool_name is not None else None,
                message=message,
                start_time=start_time,
                end_time=datetime.now(timezone.utc),
            )
        )


class DatastoreProgressReporter(ProgressReporter):
    """Progress reporter that writes ancestor progress steps directly to Cloud NDB Datastore.

    Entities are parented under the feature's `FeatureSummarySuggestion` ancestor key,
    guaranteeing strongly consistent reads for polling APIs.
    """

    def __init__(self, feature_id: int) -> None:
        """Initializes Datastore reporter with feature ID ancestor key."""
        self.feature_id = feature_id

    def log_step(
        self,
        step_id: ProgressStepId,
        status: ProgressStepStatus,
        tool_name: AISummaryToolName | None = None,
        message: str = '',
        start_time: datetime | None = None,
    ) -> None:
        """Persists a progress step under the FeatureSummarySuggestion ancestor key."""
        parent_key = ndb.Key(FeatureSummarySuggestion, self.feature_id)
        now = datetime.now(timezone.utc)
        step = FeatureSummaryProgressStep(
            parent=parent_key,
            step_id=step_id.value,
            status=status.value,
            tool_name=tool_name.value if tool_name is not None else None,
            message=message,
            start_timestamp=start_time or now,
            end_timestamp=now,
        )
        step.put()
