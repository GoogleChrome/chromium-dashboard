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

"""Unit tests for AI progress reporting interfaces, DTOs, and Datastore reporters."""

from __future__ import annotations

import testing_config  # isort: skip  # Must be imported before other project modules.

from datetime import datetime, timezone

from google.cloud import ndb

from ai.progress_reporter import (
    DatastoreProgressReporter,
    FeatureSummaryInput,
    ListProgressReporter,
    SummaryResult,
)
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


class ProgressReporterTest(testing_config.CustomTestCase):
    """Tests FeatureSummaryInput DTO, in-memory ListProgressReporter, and Datastore persistence."""

    def setUp(self):
        """Initializes test feature and Datastore entities."""
        self.feature_id = 10001
        self.parent_key = ndb.Key(FeatureSummarySuggestion, self.feature_id)
        self.suggestion = FeatureSummarySuggestion(
            id=self.feature_id,
            suggested_summary='Initial summary.',
            source_fingerprint='abc123hash',
        )
        self.suggestion.put()

    def tearDown(self):
        """Cleans up Datastore entities after each test."""
        steps = FeatureSummaryProgressStep.query(
            ancestor=self.parent_key
        ).fetch()
        ndb.delete_multi([s.key for s in steps])
        self.suggestion.key.delete()

    def test_feature_summary_input_from_feature(self):
        """Tests creating FeatureSummaryInput DTO from a Datastore FeatureEntry."""
        feature = FeatureEntry(
            name='CSS Anchor Positioning',
            summary='Allows tethering elements together.',
            spec_link='https://drafts.csswg.org/css-anchor-position-1/',
            doc_links=['https://developer.mozilla.org/docs/Web/CSS/anchor'],
            search_tags=['css', 'anchor', 'layout'],
            standard_maturity=1,
            category=2,
        )

        dto = FeatureSummaryInput.from_feature(feature, shipped_milestone='125')

        self.assertEqual(dto.name, 'CSS Anchor Positioning')
        self.assertEqual(dto.summary, 'Allows tethering elements together.')
        self.assertEqual(dto.shipped_milestone, '125')
        self.assertEqual(
            dto.spec_link,
            'https://drafts.csswg.org/css-anchor-position-1/',
        )
        self.assertEqual(
            dto.doc_links,
            ('https://developer.mozilla.org/docs/Web/CSS/anchor',),
        )
        self.assertEqual(dto.search_tags, ('css', 'anchor', 'layout'))
        self.assertEqual(dto.standard_maturity, 1)
        self.assertEqual(dto.category, 2)

    def test_summary_result_contract(self):
        """Tests SummaryResult frozen dataclass contract."""
        res = SummaryResult(
            suggested_summary='Popover API is enabled.',
            generation_rationale='Standard dialog replacement.',
            suggested_doc_links=(
                'https://developer.mozilla.org/en-US/docs/Web/API/Popover_API',
            ),
        )
        self.assertEqual(res.suggested_summary, 'Popover API is enabled.')
        self.assertEqual(
            res.suggested_doc_links[0],
            'https://developer.mozilla.org/en-US/docs/Web/API/Popover_API',
        )

    def test_list_progress_reporter(self):
        """Tests that ListProgressReporter records events in memory."""
        reporter = ListProgressReporter()
        start_time = datetime.now(timezone.utc)

        reporter.log_step(
            step_id=ProgressStepId.START,
            status=ProgressStepStatus.IN_PROGRESS,
            message='Starting summary generation',
            start_time=start_time,
        )
        reporter.log_step(
            step_id=ProgressStepId.SEARCH_MDN,
            status=ProgressStepStatus.SUCCESS,
            tool_name=AISummaryToolName.SEARCH_MDN,
            message='Completed MDN search query',
            start_time=start_time,
        )

        self.assertEqual(len(reporter.steps), 2)
        self.assertEqual(reporter.steps[0].step_id, ProgressStepId.START.value)
        self.assertEqual(
            reporter.steps[0].status, ProgressStepStatus.IN_PROGRESS.value
        )
        self.assertIsNone(reporter.steps[0].tool_name)

        self.assertEqual(
            reporter.steps[1].step_id, ProgressStepId.SEARCH_MDN.value
        )
        self.assertEqual(
            reporter.steps[1].status, ProgressStepStatus.SUCCESS.value
        )
        self.assertEqual(
            reporter.steps[1].tool_name, AISummaryToolName.SEARCH_MDN.value
        )

    def test_datastore_progress_reporter(self):
        """Tests that DatastoreProgressReporter persists steps under the suggestion ancestor key."""
        reporter = DatastoreProgressReporter(feature_id=self.feature_id)
        start_time = datetime.now(timezone.utc)

        reporter.log_step(
            step_id=ProgressStepId.READ_SPEC,
            status=ProgressStepStatus.SUCCESS,
            tool_name=AISummaryToolName.READ_SPEC_LINK,
            message='Fetched specification text',
            start_time=start_time,
        )

        persisted_steps = FeatureSummaryProgressStep.query(
            ancestor=self.parent_key
        ).fetch()
        self.assertEqual(len(persisted_steps), 1)
        step = persisted_steps[0]
        self.assertEqual(step.step_id, ProgressStepId.READ_SPEC.value)
        self.assertEqual(step.status, ProgressStepStatus.SUCCESS.value)
        self.assertEqual(step.tool_name, AISummaryToolName.READ_SPEC_LINK.value)
        self.assertEqual(step.message, 'Fetched specification text')
