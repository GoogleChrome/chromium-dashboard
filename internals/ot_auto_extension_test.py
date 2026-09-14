# Copyright 2025 Google Inc.
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
"""Tests for the ot_auto_extension module."""

from unittest import mock

import testing_config  # Must be imported before the module under test.
from internals import core_enums, ot_auto_extension
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote


class OTAutoExtensionTest(testing_config.CustomTestCase):
    """Tests for automatic OT extensions on approved Intent to Ship."""

    def setUp(self):
        """Set up a feature with an active OT stage and a ship stage."""
        self.feature = FeatureEntry(
            id=1,
            name='feature one',
            summary='sum',
            category=1,
            feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
        )
        self.feature.put()
        self.feature_id = self.feature.key.integer_id()

        self.ot_stage = Stage(
            id=100,
            feature_id=self.feature_id,
            stage_type=core_enums.STAGE_BLINK_ORIGIN_TRIAL,
            origin_trial_id='1234567890',
            ot_owner_email='ot_owner@example.com',
            ot_display_name='Feature One Trial',
            milestones=MilestoneSet(desktop_first=100, desktop_last=106),
        )
        self.ot_stage.put()

        self.ship_stage = Stage(
            id=200,
            feature_id=self.feature_id,
            stage_type=core_enums.STAGE_BLINK_SHIPPING,
            intent_thread_url='https://example.com/i2s_thread',
            milestones=MilestoneSet(desktop_first=107),
        )
        self.ship_stage.put()

    def tearDown(self):
        """Clean up all entities created during the test."""
        for kind in [FeatureEntry, Stage, Gate, Vote]:
            for entity in kind.query():
                entity.key.delete()

    def get_extension_stages(self) -> list[Stage]:
        """Return any extension stages for the OT stage."""
        return Stage.query(
            Stage.ot_stage_id == self.ot_stage.key.integer_id()
        ).fetch()

    @mock.patch(
        'internals.notifier_helpers.send_trial_extension_approved_notification'
    )
    def test_extension_created__trial_ends_before_shipping(self, mock_notify):
        """An approved extension is created when the trial ends too early."""
        ot_auto_extension.maybe_extend_trials_for_shipping(
            self.feature, self.ship_stage, 'approver@example.com'
        )

        extension_stages = self.get_extension_stages()
        self.assertEqual(len(extension_stages), 1)
        extension_stage = extension_stages[0]
        self.assertEqual(
            extension_stage.stage_type,
            core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
        )
        self.assertEqual(extension_stage.milestones.desktop_last, 107)
        self.assertEqual(
            extension_stage.intent_thread_url,
            'https://example.com/i2s_thread',
        )
        self.assertEqual(extension_stage.ot_owner_email, 'ot_owner@example.com')
        self.assertTrue(extension_stage.ot_action_requested)
        self.assertEqual(
            extension_stage.experiment_extension_reason,
            ot_auto_extension.AUTO_EXTENSION_REASON,
        )

        gate = Gate.query(
            Gate.stage_id == extension_stage.key.integer_id()
        ).get()
        self.assertIsNotNone(gate)
        self.assertEqual(
            gate.gate_type, core_enums.GATE_API_EXTEND_ORIGIN_TRIAL
        )
        self.assertIn(gate.state, Gate.APPROVED_STATES)

        votes = Vote.get_votes(gate_id=gate.key.integer_id())
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0].state, Vote.NA)
        self.assertEqual(votes[0].set_by, 'approver@example.com')

        mock_notify.assert_called_once()

    @mock.patch(
        'internals.notifier_helpers.send_trial_extension_approved_notification'
    )
    def test_no_extension__trial_covers_shipping(self, mock_notify):
        """No extension is created if the trial already covers shipping."""
        self.ot_stage.milestones.desktop_last = 107
        self.ot_stage.put()

        ot_auto_extension.maybe_extend_trials_for_shipping(
            self.feature, self.ship_stage, 'approver@example.com'
        )

        self.assertEqual(len(self.get_extension_stages()), 0)
        mock_notify.assert_not_called()

    @mock.patch(
        'internals.notifier_helpers.send_trial_extension_approved_notification'
    )
    def test_no_extension__no_active_trial(self, mock_notify):
        """No extension is created if the trial was never created."""
        self.ot_stage.origin_trial_id = None
        self.ot_stage.put()

        ot_auto_extension.maybe_extend_trials_for_shipping(
            self.feature, self.ship_stage, 'approver@example.com'
        )

        self.assertEqual(len(self.get_extension_stages()), 0)
        mock_notify.assert_not_called()

    @mock.patch(
        'internals.notifier_helpers.send_trial_extension_approved_notification'
    )
    def test_no_extension__no_shipping_milestone(self, mock_notify):
        """No extension is created if the ship stage has no milestone."""
        self.ship_stage.milestones = MilestoneSet()
        self.ship_stage.put()

        ot_auto_extension.maybe_extend_trials_for_shipping(
            self.feature, self.ship_stage, 'approver@example.com'
        )

        self.assertEqual(len(self.get_extension_stages()), 0)
        mock_notify.assert_not_called()

    @mock.patch(
        'internals.notifier_helpers.send_trial_extension_approved_notification'
    )
    def test_no_extension__deprecation_feature(self, mock_notify):
        """No extension is created for deprecation features."""
        self.feature.feature_type = core_enums.FEATURE_TYPE_DEPRECATION_ID
        self.feature.put()

        ot_auto_extension.maybe_extend_trials_for_shipping(
            self.feature, self.ship_stage, 'approver@example.com'
        )

        self.assertEqual(len(self.get_extension_stages()), 0)
        mock_notify.assert_not_called()

    @mock.patch(
        'internals.notifier_helpers.send_trial_extension_approved_notification'
    )
    def test_no_extension__approved_extension_covers_shipping(
        self, mock_notify
    ):
        """No new extension if an approved extension covers shipping."""
        existing_extension = Stage(
            id=300,
            feature_id=self.feature_id,
            stage_type=core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
            ot_stage_id=self.ot_stage.key.integer_id(),
            milestones=MilestoneSet(desktop_last=108),
        )
        existing_extension.put()
        gate = Gate(
            feature_id=self.feature_id,
            stage_id=300,
            gate_type=core_enums.GATE_API_EXTEND_ORIGIN_TRIAL,
            state=Vote.APPROVED,
        )
        gate.put()

        ot_auto_extension.maybe_extend_trials_for_shipping(
            self.feature, self.ship_stage, 'approver@example.com'
        )

        self.assertEqual(len(self.get_extension_stages()), 1)
        mock_notify.assert_not_called()

    @mock.patch(
        'internals.notifier_helpers.send_trial_extension_approved_notification'
    )
    def test_extension_created__pending_extension_not_counted(
        self, mock_notify
    ):
        """A pending (unapproved) extension does not prevent auto-extension."""
        existing_extension = Stage(
            id=300,
            feature_id=self.feature_id,
            stage_type=core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
            ot_stage_id=self.ot_stage.key.integer_id(),
            milestones=MilestoneSet(desktop_last=108),
        )
        existing_extension.put()
        gate = Gate(
            feature_id=self.feature_id,
            stage_id=300,
            gate_type=core_enums.GATE_API_EXTEND_ORIGIN_TRIAL,
            state=Vote.REVIEW_REQUESTED,
        )
        gate.put()

        ot_auto_extension.maybe_extend_trials_for_shipping(
            self.feature, self.ship_stage, 'approver@example.com'
        )

        extension_stages = self.get_extension_stages()
        self.assertEqual(len(extension_stages), 2)
        mock_notify.assert_called_once()

    @mock.patch(
        'internals.notifier_helpers.send_trial_extension_approved_notification'
    )
    def test_extension_created__latest_shipping_milestone_used(
        self, mock_notify
    ):
        """The latest milestone across platforms is used for the extension."""
        self.ship_stage.milestones = MilestoneSet(
            desktop_first=107, android_first=109
        )
        self.ship_stage.put()

        ot_auto_extension.maybe_extend_trials_for_shipping(
            self.feature, self.ship_stage, 'approver@example.com'
        )

        extension_stages = self.get_extension_stages()
        self.assertEqual(len(extension_stages), 1)
        self.assertEqual(extension_stages[0].milestones.desktop_last, 109)
        mock_notify.assert_called_once()
