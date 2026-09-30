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

    def test_set_progress_vote_creates_and_overwrites(self):
        """set_progress_vote creates a ProgressVote and overwrites matching (feature_id, progress_item_name)."""
        vote_1 = progress.set_progress_vote(
            feature_id=12345,
            progress_item_name='Explainer',
            state=progress.ProgressVote.NEEDS_WORK,
            set_by='reviewer1@example.com',
            feedback='Needs more detail',
        )
        all_votes = progress.ProgressVote.query().fetch()
        self.assertEqual(len(all_votes), 1)
        self.assertEqual(all_votes[0].state, progress.ProgressVote.NEEDS_WORK)
        self.assertEqual(all_votes[0].feedback, 'Needs more detail')
        self.assertEqual(all_votes[0].set_by, 'reviewer1@example.com')

        # Overwrite the same (feature_id, progress_item_name)
        vote_2 = progress.set_progress_vote(
            feature_id=12345,
            progress_item_name='Explainer',
            state=progress.ProgressVote.VERIFIED,
            set_by='reviewer2@example.com',
            feedback='Looks great now',
        )
        all_votes = progress.ProgressVote.query().fetch()
        self.assertEqual(len(all_votes), 1)
        self.assertEqual(vote_1.key, vote_2.key)
        self.assertEqual(all_votes[0].state, progress.ProgressVote.VERIFIED)
        self.assertEqual(all_votes[0].feedback, 'Looks great now')
        self.assertEqual(all_votes[0].set_by, 'reviewer2@example.com')


NOT_STARTED = progress.ProgressDetectorResult(progress.ProgressVote.NOT_STARTED)
NEEDS_REVIEW = progress.ProgressDetectorResult(
    progress.ProgressVote.NEEDS_REVIEW
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
        self.assertEqual(
            progress._detect_initial_public_proposal(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.feature_1.initial_public_proposal_url = 'http://example.com'
        self.assertEqual(
            progress._detect_initial_public_proposal(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_explainer(self):
        """Test explainer."""
        self.assertEqual(
            progress._detect_explainer(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.explainer_links = ['http://example.com']
        self.assertEqual(
            progress._detect_explainer(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_web__faeture(self):
        """Test web  faeture."""
        self.assertEqual(
            progress._detect_web_feature(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.web_feature = WebDXFeatureObserver.MISSING_FEATURE_ID
        self.assertEqual(
            progress._detect_web_feature(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.web_feature = 'array'
        self.assertEqual(
            progress._detect_web_feature(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_security_review_completed(self):
        """Test security review completed."""
        self.assertEqual(
            progress._detect_security_review_issues_addressed(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.feature_1.security_review_status = (
            core_enums.REVIEW_ISSUES_ADDRESSED
        )
        self.assertEqual(
            progress._detect_security_review_issues_addressed(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_privacy_review_completed(self):
        """Test privacy review completed."""
        self.assertEqual(
            progress._detect_privacy_review_issues_addressed(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.feature_1.privacy_review_status = (
            core_enums.REVIEW_ISSUES_ADDRESSED
        )
        self.assertEqual(
            progress._detect_privacy_review_issues_addressed(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_samples(self):
        """Test samples."""
        self.assertEqual(
            progress._detect_samples(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.sample_links = ['http://example.com']
        self.assertEqual(
            progress._detect_samples(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_doc_links(self):
        """Test doc links."""
        self.assertEqual(
            progress._detect_doc_links(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.doc_links = ['http://example.com']
        self.assertEqual(
            progress._detect_doc_links(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_tag_review_requested(self):
        """Test tag review requested."""
        self.assertEqual(
            progress._detect_tag_review_requested(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.feature_1.tag_review = 'http://example.com'
        self.assertEqual(
            progress._detect_tag_review_requested(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_tag_review_completed(self):
        """Test tag review completed."""
        self.assertEqual(
            progress._detect_tag_review_issues_addressed(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.feature_1.tag_review_status = core_enums.REVIEW_ISSUES_ADDRESSED
        self.assertEqual(
            progress._detect_tag_review_issues_addressed(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_web_dev_views(self):
        """Test web dev views."""
        self.assertEqual(
            progress._detect_web_dev_views(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.web_dev_views = core_enums.PUBLIC_SUPPORT
        self.assertEqual(
            progress._detect_web_dev_views(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_firefox_views(self):
        """Test firefox views."""
        self.assertEqual(
            progress._detect_firefox_views(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.ff_views = core_enums.PUBLIC_SUPPORT
        self.assertEqual(
            progress._detect_firefox_views(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_safari_views(self):
        """Test safari views."""
        self.assertEqual(
            progress._detect_safari_views(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.safari_views = core_enums.PUBLIC_SUPPORT
        self.assertEqual(
            progress._detect_safari_views(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_desktop_milestone(self):
        """Test desktop milestone."""
        self.stages_dict[160][0].milestones = core_models.MilestoneSet()
        self.assertEqual(
            progress._detect_desktop_milestone(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.stages_dict[160][0].milestones.desktop_first = 99
        self.assertEqual(
            progress._detect_desktop_milestone(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_android_milestone(self):
        """Test android milestone."""
        self.stages_dict[160][0].milestones = core_models.MilestoneSet()
        self.assertEqual(
            progress._detect_android_milestone(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.stages_dict[160][0].milestones.android_first = 99
        self.assertEqual(
            progress._detect_android_milestone(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )
        self.stages_dict[160][0].milestones = core_models.MilestoneSet(
            desktop_first=100
        )
        self.assertEqual(
            progress._detect_android_milestone(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_webview_milestone(self):
        """Test webview milestone."""
        self.stages_dict[160][0].milestones = core_models.MilestoneSet()
        self.assertEqual(
            progress._detect_webview_milestone(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.stages_dict[160][0].milestones.webview_first = 99
        self.assertEqual(
            progress._detect_webview_milestone(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )
        self.stages_dict[160][0].milestones = core_models.MilestoneSet(
            desktop_first=100
        )
        self.assertEqual(
            progress._detect_webview_milestone(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_motivation(self):
        """Test motivation."""
        self.assertEqual(
            progress._detect_motivation(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.motivation = 'test motivation'
        self.assertEqual(
            progress._detect_motivation(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_code_removed(self):
        """Test code removed."""
        self.assertEqual(
            progress._detect_code_removed(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.feature_1.impl_status_chrome = core_enums.REMOVED
        self.assertEqual(
            progress._detect_code_removed(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_rollout_impact(self):
        """Test rollout impact."""
        # There is always a value for this
        self.assertEqual(
            progress._detect_rollout_impact(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )
        self.stages_dict[1061][0].rollout_impact = 1
        self.assertEqual(
            progress._detect_rollout_impact(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_rollout_milestone(self):
        """Test rollout milestone."""
        self.assertEqual(
            progress._detect_rollout_milestone(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.stages_dict[1061][0].rollout_milestone = 99
        self.assertEqual(
            progress._detect_rollout_milestone(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_rollout_platforms(self):
        """Test rollout platforms."""
        self.assertEqual(
            progress._detect_rollout_platforms(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.stages_dict[1061][0].rollout_platforms = ['iOS', 'Android']
        self.assertEqual(
            progress._detect_rollout_platforms(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_rollout_stage_plan(self):
        """Test rollout stage plan."""
        self.assertEqual(
            progress._detect_rollout_stage_plan(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.stages_dict[1061][0].rollout_stage_plan = 1
        self.assertEqual(
            progress._detect_rollout_stage_plan(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )

    def test_rollout_details(self):
        """Test rollout details."""
        self.assertEqual(
            progress._detect_rollout_details(self.feature_1, self.stages_dict),
            NOT_STARTED,
        )
        self.stages_dict[1061][0].rollout_details = 'Details'
        self.assertEqual(
            progress._detect_rollout_details(self.feature_1, self.stages_dict),
            NEEDS_REVIEW,
        )

    def test_enterprise_policies(self):
        """Test enterprise policies."""
        self.assertEqual(
            progress._detect_enterprise_policies(
                self.feature_1, self.stages_dict
            ),
            NOT_STARTED,
        )
        self.stages_dict[1061][0].enterprise_policies = ['Policy1', 'Policy2']
        self.assertEqual(
            progress._detect_enterprise_policies(
                self.feature_1, self.stages_dict
            ),
            NEEDS_REVIEW,
        )
