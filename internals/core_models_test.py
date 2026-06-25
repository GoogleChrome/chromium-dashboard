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

"""Unit tests for internals/core_models.py, focusing on AI summary progress steps."""

import time
import datetime
from google.cloud import ndb

import testing_config  # Must be imported before models under test
from internals.core_models import FeatureSummaryProgressStep, FeatureSummarySuggestion
from internals import core_enums


class FeatureSummaryProgressStepTest(testing_config.CustomTestCase):
    """Tests for FeatureSummaryProgressStep."""

    def setUp(self):
        """Set up test environment."""
        self.feature_id = 12345
        self.suggestion = FeatureSummarySuggestion(id=self.feature_id, status='complete')
        self.suggestion.put()

    def tearDown(self):
        """Clean up datastore entities."""
        self.suggestion.key.delete()
        # Clean up all progress steps parented under feature 12345
        steps = FeatureSummaryProgressStep.query(
            ancestor=ndb.Key(FeatureSummarySuggestion, self.feature_id)
        ).fetch(keys_only=True)
        ndb.delete_multi(steps)

    def test_clear_timeline__no_prune(self):
        """Ensure clear_timeline does not prune steps if the count is 20 or less."""
        # Insert exactly 15 steps
        for i in range(15):
            FeatureSummaryProgressStep.update_step(
                self.feature_id,
                f'step_{i}',
                f'Progress message {i}',
                core_enums.ProgressStepStatus.SUCCESS.value
            )

        # Call clear_timeline
        FeatureSummaryProgressStep.clear_timeline(self.feature_id)

        # Verify all 15 steps remain in the database
        steps = FeatureSummaryProgressStep.get_timeline(self.feature_id)
        self.assertEqual(len(steps), 15)

    def test_clear_timeline__prune_oldest(self):
        """Ensure clear_timeline prunes the oldest steps when count exceeds 20, keeping the last 20."""
        # Insert 25 steps sequentially. We add a tiny delay to ensure distinct auto_now_add timestamps.
        for i in range(25):
            FeatureSummaryProgressStep.update_step(
                self.feature_id,
                f'step_{i}',
                f'Progress message {i}',
                core_enums.ProgressStepStatus.SUCCESS.value
            )
            # Sleep briefly to ensure increasing start_timestamp
            time.sleep(0.001)

        # Confirm 25 steps exist before clear
        initial_steps = FeatureSummaryProgressStep.get_timeline(self.feature_id)
        self.assertEqual(len(initial_steps), 25)

        # Call clear_timeline
        FeatureSummaryProgressStep.clear_timeline(self.feature_id)

        # Verify exactly 20 steps remain
        remaining_steps = FeatureSummaryProgressStep.get_timeline(self.feature_id)
        self.assertEqual(len(remaining_steps), 20)

        # Verify that the 5 oldest steps ('step_0' to 'step_4') were pruned/deleted
        remaining_step_ids = [s.key.id() for s in remaining_steps]
        for i in range(5):
            self.assertNotIn(f'step_{i}', remaining_step_ids)

        # Verify that the 20 newest steps ('step_5' to 'step_24') remain intact
        for i in range(5, 25):
            self.assertIn(f'step_{i}', remaining_step_ids)
