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

"""Telemetry interfaces and progress reporters for AI generation pipelines."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone

from google.cloud import ndb

from internals.core_enums import (
    AISummaryToolName,
    ProgressStepId,
    ProgressStepStatus,
)
from internals.core_models import FeatureSummaryProgressStep


@dataclass(frozen=True)
class SummaryResult:
    """Structured result returned by the pure summary generator engine."""

    suggested_summary: str
    generation_rationale: str
    suggested_doc_links: list[str] = field(default_factory=list)
    error_message: str | None = None
    raw_response: str | None = None


@dataclass(frozen=True)
class ProgressStepRecord:
    """In-memory telemetry record for progress tracking and evaluations."""

    step_id: str
    status: str
    tool_name: str | None = None
    message: str = ''
    start_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    end_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ProgressReporter(abc.ABC):
    """Abstract telemetry reporter for observing agent execution steps."""

    @abc.abstractmethod
    def log_step(
        self,
        step_id: ProgressStepId | str,
        status: ProgressStepStatus | str,
        tool_name: AISummaryToolName | str | None = None,
        message: str = '',
        start_time: datetime | None = None,
    ) -> None:
        """Logs a single generator progress step."""
        pass


class ListProgressReporter(ProgressReporter):
    """In-memory reporter collecting progress steps for unit tests and eval scripts."""

    def __init__(self) -> None:
        """Initializes empty in-memory step list."""
        self.steps: list[ProgressStepRecord] = []

    def log_step(
        self,
        step_id: ProgressStepId | str,
        status: ProgressStepStatus | str,
        tool_name: AISummaryToolName | str | None = None,
        message: str = '',
        start_time: datetime | None = None,
    ) -> None:
        """Records a progress step in memory."""
        step_id_val = (
            step_id.value if hasattr(step_id, 'value') else str(step_id)
        )
        status_val = status.value if hasattr(status, 'value') else str(status)
        tool_val = (
            tool_name.value
            if (tool_name and hasattr(tool_name, 'value'))
            else (str(tool_name) if tool_name else None)
        )
        now = datetime.now(timezone.utc)
        self.steps.append(
            ProgressStepRecord(
                step_id=step_id_val,
                status=status_val,
                tool_name=tool_val,
                message=message,
                start_timestamp=start_time or now,
                end_timestamp=now,
            )
        )


class DatastoreProgressReporter(ProgressReporter):
    """Persists progress steps under FeatureSummarySuggestion ancestor key in Datastore."""

    def __init__(self, feature_id: int) -> None:
        """Initializes reporter with target feature ID."""
        self.feature_id = feature_id

    def log_step(
        self,
        step_id: ProgressStepId | str,
        status: ProgressStepStatus | str,
        tool_name: AISummaryToolName | str | None = None,
        message: str = '',
        start_time: datetime | None = None,
    ) -> None:
        """Persists a progress step under the FeatureSummarySuggestion ancestor key."""
        parent_key = ndb.Key('FeatureSummarySuggestion', self.feature_id)
        step_id_val = (
            step_id.value if hasattr(step_id, 'value') else str(step_id)
        )
        status_val = status.value if hasattr(status, 'value') else str(status)
        tool_val = (
            tool_name.value
            if (tool_name and hasattr(tool_name, 'value'))
            else (str(tool_name) if tool_name else None)
        )
        now = datetime.now(timezone.utc)
        step = FeatureSummaryProgressStep(
            parent=parent_key,
            step_id=step_id_val,
            status=status_val,
            tool_name=tool_val,
            message=message,
            start_timestamp=start_time or now,
            end_timestamp=now,
        )
        step.put()
