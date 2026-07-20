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

"""Tests for AI Release Notes NDB models in internals.core_models."""

from __future__ import annotations

import datetime

from google.cloud import ndb  # type: ignore

import testing_config  # Must be imported before the module under test.
from internals import core_enums
from internals.core_models import (
    FeatureEntry,
    FeatureSummaryProgressStep,
    FeatureSummarySuggestion,
    MilestoneCuration,
)


class FeatureSummarySuggestionTest(testing_config.CustomTestCase):
    """Tests for the FeatureSummarySuggestion model."""

    def setUp(self):
        """Set up test data and FeatureEntry entities."""
        self.feature = FeatureEntry(
            name='Test AI Feature',
            summary='Standard summary',
            category=1,
        )
        self.feature.put()
        self.feature_id = self.feature.key.integer_id()

    def test_create_and_retrieve_suggestion(self):
        """Verify suggestion persistence and default OCC token."""
        suggestion = FeatureSummarySuggestion(
            id=self.feature_id,
            suggested_summary='AI suggested summary text.',
            suggested_doc_links=['https://developer.mozilla.org/docs/Web/Test'],
            status=core_enums.SummarySuggestionStatus.PROPOSED,
            baseline_status=core_enums.BaselineStatus.WIDELY,
            source_fingerprint='abc123hash',
        )
        suggestion.put()

        retrieved = ndb.Key('FeatureSummarySuggestion', self.feature_id).get()
        self.assertIsNotNone(retrieved)
        self.assertEqual(
            retrieved.suggested_summary, 'AI suggested summary text.'
        )
        self.assertEqual(
            retrieved.suggested_doc_links,
            ['https://developer.mozilla.org/docs/Web/Test'],
        )
        self.assertEqual(retrieved.version_token, 1)
        self.assertEqual(retrieved.status, 'PROPOSED')
        self.assertIsInstance(retrieved.status, str)
        self.assertEqual(retrieved.baseline_status, 'widely')
        self.assertIsInstance(retrieved.baseline_status, str)

    def test_occ_token_increment_on_update(self):
        """Verify OCC version_token can be incremented cleanly across edits."""
        suggestion = FeatureSummarySuggestion(
            id=self.feature_id,
            suggested_summary='Initial text.',
        )
        suggestion.put()

        retrieved = ndb.Key('FeatureSummarySuggestion', self.feature_id).get()
        retrieved.suggested_summary = 'Updated text by editor.'
        retrieved.version_token += 1
        retrieved.put()

        updated = ndb.Key('FeatureSummarySuggestion', self.feature_id).get()
        self.assertEqual(updated.version_token, 2)
        self.assertEqual(updated.suggested_summary, 'Updated text by editor.')


class FeatureSummaryProgressStepTest(testing_config.CustomTestCase):
    """Tests for the FeatureSummaryProgressStep model and timeline management."""

    def setUp(self):
        """Set up test feature id."""
        self.feature_id = 999001
        self.parent_key = ndb.Key('FeatureSummarySuggestion', self.feature_id)

    def test_create_progress_step(self):
        """Verify timeline step persistence and string properties."""
        now = datetime.datetime.now(datetime.timezone.utc)
        step = FeatureSummaryProgressStep(
            parent=self.parent_key,
            step=core_enums.ProgressStepId.SEARCH_MDN,
            status=core_enums.ProgressStepStatus.IN_PROGRESS,
            start_timestamp=now,
            message='Searching MDN for documentation.',
        )
        step.put()

        steps = FeatureSummaryProgressStep.query(
            ancestor=self.parent_key
        ).fetch()
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].step, 'SEARCH_MDN')
        self.assertIsInstance(steps[0].step, str)
        self.assertEqual(steps[0].status, 'IN_PROGRESS')
        self.assertIsInstance(steps[0].status, str)

    def test_clear_timeline__retains_twenty_most_recent(self):
        """Verify clear_timeline purges older steps, retaining exactly 20."""
        base_time = datetime.datetime(
            2026, 7, 13, 12, 0, 0, tzinfo=datetime.timezone.utc
        )
        for i in range(30):
            step_time = base_time + datetime.timedelta(seconds=i)
            step = FeatureSummaryProgressStep(
                parent=self.parent_key,
                step=core_enums.ProgressStepId.LLM_GENERATION,
                status=core_enums.ProgressStepStatus.IN_PROGRESS,
                start_timestamp=step_time,
                message=f'Step number {i}',
            )
            step.put()

        # Clear NDB cache to verify fresh Datastore retrieval and pruning.
        ndb.get_context().clear_cache()

        FeatureSummaryProgressStep.clear_timeline(
            self.feature_id, keep_count=20
        )

        ndb.get_context().clear_cache()
        remaining_steps = (
            FeatureSummaryProgressStep.query(ancestor=self.parent_key)
            .order(-FeatureSummaryProgressStep.start_timestamp)
            .fetch()
        )
        self.assertEqual(len(remaining_steps), 20)
        # Verify the most recent step (step number 29) is preserved at the top.
        self.assertEqual(remaining_steps[0].message, 'Step number 29')
        # Verify the 20th retained step is step number 10.
        self.assertEqual(remaining_steps[-1].message, 'Step number 10')


class MilestoneCurationTest(testing_config.CustomTestCase):
    """Tests for the MilestoneCuration model."""

    def test_create_and_retrieve_milestone_curation(self):
        """Verify milestone curation persistence and string keying."""
        milestone_num = 135
        curation = MilestoneCuration(
            id=str(milestone_num),
            milestone=milestone_num,
            curator_emails=['curator@google.com'],
            status=core_enums.MilestoneCurationStatus.IN_REVIEW,
        )
        curation.put()

        retrieved = ndb.Key('MilestoneCuration', str(milestone_num)).get()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.milestone, 135)
        self.assertEqual(retrieved.curator_emails, ['curator@google.com'])
        self.assertEqual(
            retrieved.status, core_enums.MilestoneCurationStatus.IN_REVIEW
        )
