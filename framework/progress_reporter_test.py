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

"""Unit tests for AI progress reporter implementations."""

from __future__ import annotations

import testing_config  # isort: skip  # Must be imported before other project modules.

from google.cloud import ndb

from framework.progress_reporter import (
    DatastoreProgressReporter,
    ListProgressReporter,
    SummaryResult,
)
from internals.core_enums import (
    AISummaryToolName,
    ProgressStepId,
    ProgressStepStatus,
)
from internals.core_models import (
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
)


class ProgressReporterTest(testing_config.CustomTestCase):
    """Tests in-memory ListProgressReporter and Cloud Datastore reporter persistence."""

    def setUp(self):
        """Initializes test feature and Datastore entities."""
        self.feature_id = 10001
        self.parent_key = ndb.Key('FeatureSummarySuggestion', self.feature_id)
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
        ).fetch(keys_only=True)
        ndb.delete_multi(steps)
        self.suggestion.key.delete()

    def test_summary_result_dataclass_properties(self):
        """Tests that SummaryResult frozen dataclass stores structured fields."""
        res = SummaryResult(
            suggested_summary='Draft summary',
            generation_rationale='Draft rationale',
            suggested_doc_links=['https://developer.chrome.com/test'],
        )
        self.assertEqual(res.suggested_summary, 'Draft summary')
        self.assertEqual(res.generation_rationale, 'Draft rationale')
        self.assertEqual(
            res.suggested_doc_links, ['https://developer.chrome.com/test']
        )
        self.assertIsNone(res.error_message)

    def test_list_progress_reporter_records_steps(self):
        """Tests that ListProgressReporter accumulates records in memory."""
        reporter = ListProgressReporter()
        reporter.log_step(
            step_id=ProgressStepId.START,
            status=ProgressStepStatus.SUCCESS,
            message='Started generation',
        )
        reporter.log_step(
            step_id=ProgressStepId.SEARCH_MDN,
            status=ProgressStepStatus.IN_PROGRESS,
            tool_name=AISummaryToolName.SEARCH_MDN,
            message='Searching MDN',
        )

        self.assertEqual(len(reporter.steps), 2)
        self.assertEqual(reporter.steps[0].step_id, ProgressStepId.START.value)
        self.assertEqual(
            reporter.steps[0].status, ProgressStepStatus.SUCCESS.value
        )
        self.assertEqual(
            reporter.steps[1].step_id, ProgressStepId.SEARCH_MDN.value
        )
        self.assertEqual(
            reporter.steps[1].tool_name, AISummaryToolName.SEARCH_MDN.value
        )

    def test_datastore_progress_reporter_persists_ancestor_entities(self):
        """Tests that DatastoreProgressReporter writes FeatureSummaryProgressStep entities."""
        reporter = DatastoreProgressReporter(feature_id=self.feature_id)
        reporter.log_step(
            step_id=ProgressStepId.START,
            status=ProgressStepStatus.SUCCESS,
            message='Pipeline started',
        )
        reporter.log_step(
            step_id=ProgressStepId.VERIFY_DOC_LINK,
            status=ProgressStepStatus.SUCCESS,
            tool_name=AISummaryToolName.VERIFY_DOC_LINK,
            message='Verified documentation link',
        )

        persisted_steps = (
            FeatureSummaryProgressStep.query(ancestor=self.parent_key)
            .order(FeatureSummaryProgressStep.start_timestamp)
            .fetch()
        )

        self.assertEqual(len(persisted_steps), 2)
        self.assertEqual(persisted_steps[0].step_id, ProgressStepId.START.value)
        self.assertEqual(
            persisted_steps[0].status, ProgressStepStatus.SUCCESS.value
        )
        self.assertEqual(persisted_steps[0].message, 'Pipeline started')
        self.assertEqual(
            persisted_steps[1].step_id, ProgressStepId.VERIFY_DOC_LINK.value
        )
        self.assertEqual(
            persisted_steps[1].tool_name,
            AISummaryToolName.VERIFY_DOC_LINK.value,
        )
