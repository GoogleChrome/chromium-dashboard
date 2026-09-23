# Copyright 2020 Google Inc.
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

"""Tests for the progress module, verifying progress detectors and review completion logic."""

import datetime

from google.cloud import ndb  # type: ignore

import testing_config  # Must be imported before the module under test.
from internals import (
    core_enums,
    core_models,
    progress,
    stage_helpers,
)
from internals.metrics_models import WebDXFeatureObserver


class ProgressVoteTest(testing_config.CustomTestCase):
    """Tests for ProgressVote NDB model."""

    def tearDown(self):
        """Clean up the test environment."""
        for entity in progress.ProgressVote.query().fetch():
            entity.key.delete()

    def test_create_progress_vote(self):
        """We can create and store a valid ProgressVote."""
        now = datetime.datetime(2026, 9, 23, 0, 0, 0)
        vote = progress.ProgressVote(
            feature_id=12345,
            progress_item_name='Explainer',
            state=progress.ProgressVote.VERIFIED,
            feedback='Looks good',
            set_on=now,
            set_by='reviewer@example.com',
        )
        vote.put()

        fetched = vote.key.get()
        self.assertEqual(fetched.feature_id, 12345)
        self.assertEqual(fetched.progress_item_name, 'Explainer')
        self.assertEqual(fetched.state, progress.ProgressVote.VERIFIED)
        self.assertEqual(fetched.feedback, 'Looks good')
        self.assertEqual(fetched.set_on, now)
        self.assertEqual(fetched.set_by, 'reviewer@example.com')

    def test_progress_vote_invalid_state(self):
        """ProgressVote rejects invalid state values."""
        with self.assertRaises(ndb.exceptions.BadValueError):
            progress.ProgressVote(
                feature_id=12345,
                progress_item_name='Explainer',
                state=999,
                feedback='Bad state',
                set_on=datetime.datetime(2026, 9, 23, 0, 0, 0),
                set_by='reviewer@example.com',
            )


class ProgressDetectorsTest(testing_config.CustomTestCase):
    """Tests for ProgressDetectors."""

    def setUp(self):
        """Set up the test environment."""
        self.feature_1 = core_models.FeatureEntry(
            name='feature one',
            summary='sum',
            category=1,
            intent_stage=core_enums.INTENT_IMPLEMENT,
            feature_type=0,
        )
        self.feature_1.put()
        stage_types = [110, 120, 130, 140, 150, 151, 160, 1061]
        self.stages: list[core_models.Stage] = []
        for s_type in stage_types:
            stage = core_models.Stage(
                feature_id=self.feature_1.key.integer_id(), stage_type=s_type
            )
            stage.put()
            self.stages.append(stage)
        self.stages_dict = stage_helpers.get_feature_stages(
            self.feature_1.key.integer_id()
        )

    def tearDown(self):
        """Clean up the test environment."""
        self.feature_1.key.delete()
        for stage in self.stages:
            stage.key.delete()

    def test_review_is_done(self):
        """A review step is done if the review has completed or was N/a."""
        self.assertFalse(progress.review_is_done(None))
        self.assertFalse(progress.review_is_done(0))
        self.assertFalse(progress.review_is_done(core_enums.REVIEW_PENDING))
        self.assertFalse(progress.review_is_done(core_enums.REVIEW_ISSUES_OPEN))
        self.assertTrue(
            progress.review_is_done(core_enums.REVIEW_ISSUES_ADDRESSED)
        )
        self.assertTrue(progress.review_is_done(core_enums.REVIEW_NA))

    def test_initial_public_proposal_url(self):
        """Test initial public proposal url."""
        detector = progress.PROGRESS_DETECTORS['Initial public proposal']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.initial_public_proposal_url = 'http://example.com'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_explainer(self):
        """Test explainer."""
        detector = progress.PROGRESS_DETECTORS['Explainer']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.explainer_links = ['http://example.com']
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_web__faeture(self):
        """Test web  faeture."""
        detector = progress.PROGRESS_DETECTORS['Web feature']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.web_feature = WebDXFeatureObserver.MISSING_FEATURE_ID
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.web_feature = 'array'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_security_review_completed(self):
        """Test security review completed."""
        detector = progress.PROGRESS_DETECTORS[
            'Security review issues addressed'
        ]
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.security_review_status = (
            core_enums.REVIEW_ISSUES_ADDRESSED
        )
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_privacy_review_completed(self):
        """Test privacy review completed."""
        detector = progress.PROGRESS_DETECTORS[
            'Privacy review issues addressed'
        ]
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.privacy_review_status = (
            core_enums.REVIEW_ISSUES_ADDRESSED
        )
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_intent_to_prototype_email(self):
        """Test intent to prototype email."""
        detector = progress.PROGRESS_DETECTORS['Intent to Prototype email']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[120][
            0
        ].intent_thread_url = 'http://example.com/prototype'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_intent_to_ship_email(self):
        """Test intent to ship email."""
        detector = progress.PROGRESS_DETECTORS['Intent to Ship email']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[160][0].intent_thread_url = 'http://example.com/ship'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_ready_for_trial_email(self):
        """Test ready for trial email."""
        detector = progress.PROGRESS_DETECTORS[
            'Ready for Developer Testing email'
        ]
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[130][
            0
        ].announcement_url = 'http://example.com/trial_ready'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_intent_to_experiment_email(self):
        """Test intent to experiment email."""
        detector = progress.PROGRESS_DETECTORS['Intent to Experiment email']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[150][0].intent_thread_url = 'http://example.com/ot'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_samples(self):
        """Test samples."""
        detector = progress.PROGRESS_DETECTORS['Samples']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.sample_links = ['http://example.com']
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_doc_links(self):
        """Test doc links."""
        detector = progress.PROGRESS_DETECTORS['Doc links']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.doc_links = ['http://example.com']
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_tag_review_requested(self):
        """Test tag review requested."""
        detector = progress.PROGRESS_DETECTORS['TAG review requested']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.tag_review = 'http://example.com'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_tag_review_completed(self):
        """Test tag review completed."""
        detector = progress.PROGRESS_DETECTORS['TAG review issues addressed']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.tag_review_status = core_enums.REVIEW_ISSUES_ADDRESSED
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_web_dev_signals(self):
        """Test web dev signals."""
        detector = progress.PROGRESS_DETECTORS['Web developer signals']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.web_dev_views = core_enums.PUBLIC_SUPPORT
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_vendor_signals(self):
        """Test vendor signals."""
        detector = progress.PROGRESS_DETECTORS['Vendor signals']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.ff_views = core_enums.PUBLIC_SUPPORT
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_estimated_target_milestone(self):
        """Test estimated target milestone."""
        detector = progress.PROGRESS_DETECTORS['Estimated target milestone']
        self.stages_dict[160][0].milestones = core_models.MilestoneSet()
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[160][0].milestones.desktop_first = 99
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_code_in_chromium(self):
        """Test code in chromium."""
        detector = progress.PROGRESS_DETECTORS['Code in Chromium']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.impl_status_chrome = core_enums.ENABLED_BY_DEFAULT
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_motivation(self):
        """Test motivation."""
        detector = progress.PROGRESS_DETECTORS['Motivation']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.motivation = 'test motivation'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_code_removed(self):
        """Test code removed."""
        detector = progress.PROGRESS_DETECTORS['Code removed']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.impl_status_chrome = core_enums.REMOVED
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_impact(self):
        """Test rollout impact."""
        detector = progress.PROGRESS_DETECTORS['Rollout impact']
        # There is always a value for this
        self.assertTrue(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_impact = 1
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_milestone(self):
        """Test rollout milestone."""
        detector = progress.PROGRESS_DETECTORS['Rollout milestone']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_milestone = 99
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_platforms(self):
        """Test rollout platforms."""
        detector = progress.PROGRESS_DETECTORS['Rollout platforms']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_platforms = ['iOS', 'Android']
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_stage_plan(self):
        """Test rollout stage plan."""
        detector = progress.PROGRESS_DETECTORS['Rollout stage plan']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_stage_plan = 1
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_details(self):
        """Test rollout details."""
        detector = progress.PROGRESS_DETECTORS['Rollout details']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_details = 'Details'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_enterprise_policies(self):
        """Test enterprise policies."""
        detector = progress.PROGRESS_DETECTORS['Enterprise policies']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].enterprise_policies = ['Policy1', 'Policy2']
        self.assertTrue(detector(self.feature_1, self.stages_dict))
