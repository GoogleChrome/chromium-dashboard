# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
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

"""Tests for the progress_api module, verifying the retrieval of feature progress."""

import datetime
from unittest import mock

import flask

import testing_config  # Must be imported before the module under test.
from api import progress_api
from internals import core_enums, core_models, progress, user_models

test_app = flask.Flask(__name__)

FAKE_NOW = datetime.datetime(2026, 9, 23, 12, 0, 0)


class ProgressAPITest(testing_config.CustomTestCase):
    """Tests for ProgressAPI."""

    def setUp(self):
        """Set up the test environment."""
        self.feature_1 = core_models.FeatureEntry(
            name='feature one',
            summary='sum Z',
            owner_emails=['feature_owner@example.com'],
            spec_link='fake spec link',
            category=1,
            web_dev_views=1,
            impl_status_chrome=5,
            intent_stage=core_enums.INTENT_IMPLEMENT,
            feature_type=0,
        )
        self.feature_1.put()
        self.feature_id = self.feature_1.key.integer_id()

        self.editor_user = user_models.AppUser(
            email='reviewer@example.com', is_site_editor=True
        )
        self.editor_user.put()

        stage_types = [110, 120, 130, 140, 150, 151, 160]
        self.stages: list[core_models.Stage] = []
        for s_type in stage_types:
            stage = core_models.Stage(
                feature_id=self.feature_id, stage_type=s_type
            )
            # Add separate intent URLs for each stage type.
            if s_type == 120:
                stage.intent_thread_url = 'https://example.com/prototype'
            elif s_type == 130:
                stage.announcement_url = 'https://example.com/ready_for_trial'
            elif s_type == 150:
                stage.intent_thread_url = 'https://example.com/ot'
            elif s_type == 151:
                stage.intent_thread_url = 'https://example.com/extend'
            elif s_type == 160:
                stage.milestones = core_models.MilestoneSet(desktop_first=1)
                stage.intent_thread_url = 'https://example.com/ship'
            stage.put()
            self.stages.append(stage)

        self.handler = progress_api.ProgressAPI()
        self.request_path = f'/api/v0/features/{self.feature_id}/progress'

    def tearDown(self):
        """Clean up the test environment."""
        self.feature_1.key.delete()
        self.editor_user.key.delete()
        for stage in self.stages:
            stage.key.delete()
        for vote in progress.ProgressVote.query().fetch():
            vote.key.delete()

    @mock.patch('api.progress_api.datetime')
    def test_get___feature_progress(self, mock_datetime):
        """We can get progress of a feature."""
        mock_datetime.datetime.now.return_value = FAKE_NOW
        expected_detected_vote = {
            'state': progress.ProgressVote.VERIFIED,
            'set_on': FAKE_NOW.isoformat(),
            'set_by': 'ChromeStatus',
        }

        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)

        self.assertEqual(
            {
                'Code in Chromium': expected_detected_vote,
                'Draft API spec': expected_detected_vote,
                'Estimated target milestone': expected_detected_vote,
                'Final target milestone': expected_detected_vote,
                'Intent to Prototype email': expected_detected_vote,
                'Intent to Experiment email': expected_detected_vote,
                'Ready for Developer Testing email': expected_detected_vote,
                'Intent to Ship email': expected_detected_vote,
                'Spec link': expected_detected_vote,
                'Updated target milestone': expected_detected_vote,
                'Web developer signals': expected_detected_vote,
            },
            actual,
        )

    @mock.patch('api.progress_api.datetime')
    def test_get___progress_votes_overwrite_detected(self, mock_datetime):
        """Stored ProgressVote entities overwrite detected progress items."""
        mock_datetime.datetime.now.return_value = FAKE_NOW
        vote_time = datetime.datetime(2026, 9, 23, 15, 30, 0)
        vote_1 = progress.ProgressVote(
            feature_id=self.feature_id,
            progress_item_name='Spec link',
            state=progress.ProgressVote.NEEDS_WORK,
            feedback='Spec link is broken',
            set_on=vote_time,
            set_by='reviewer@example.com',
        )
        vote_1.put()
        vote_2 = progress.ProgressVote(
            feature_id=self.feature_id,
            progress_item_name='Explainer',
            state=progress.ProgressVote.VERIFIED,
            feedback='Explainer verified manually',
            set_on=vote_time,
            set_by='reviewer@example.com',
        )
        vote_2.put()

        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)

        self.assertEqual(
            actual['Spec link'],
            {
                'state': progress.ProgressVote.NEEDS_WORK,
                'feedback': 'Spec link is broken',
                'set_on': vote_time.isoformat(),
                'set_by': 'reviewer@example.com',
            },
        )
        self.assertEqual(
            actual['Explainer'],
            {
                'state': progress.ProgressVote.VERIFIED,
                'feedback': 'Explainer verified manually',
                'set_on': vote_time.isoformat(),
                'set_by': 'reviewer@example.com',
            },
        )

    def test_post___create_and_overwrite_vote(self):
        """do_post stores a ProgressVote and overwrites any previous vote for the same (feature_id, progress_item_name)."""
        testing_config.sign_in('reviewer@example.com', 111)
        with test_app.test_request_context(
            self.request_path,
            json={
                'progress_item_name': 'Spec link',
                'state': progress.ProgressVote.NEEDS_WORK,
                'feedback': 'Needs anchor links',
            },
        ):
            res = self.handler.do_post(feature_id=self.feature_id)

        self.assertEqual(res, {'message': 'Done'})
        votes = progress.ProgressVote.query(
            progress.ProgressVote.feature_id == self.feature_id
        ).fetch()
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0].progress_item_name, 'Spec link')
        self.assertEqual(votes[0].state, progress.ProgressVote.NEEDS_WORK)
        self.assertEqual(votes[0].feedback, 'Needs anchor links')
        self.assertEqual(votes[0].set_by, 'reviewer@example.com')

        # Second post for the same (feature_id, progress_item_name) overwrites the existing entity.
        with test_app.test_request_context(
            self.request_path,
            json={
                'progress_item_name': 'Spec link',
                'state': progress.ProgressVote.VERIFIED,
            },
        ):
            res = self.handler.do_post(feature_id=self.feature_id)

        self.assertEqual(res, {'message': 'Done'})
        votes = progress.ProgressVote.query(
            progress.ProgressVote.feature_id == self.feature_id
        ).fetch()
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0].progress_item_name, 'Spec link')
        self.assertEqual(votes[0].state, progress.ProgressVote.VERIFIED)
        self.assertIsNone(votes[0].feedback)
        testing_config.sign_out()

    def test_post___anon_forbidden(self):
        """Anonymous users are rejected with 403."""
        import werkzeug.exceptions

        testing_config.sign_out()
        with test_app.test_request_context(
            self.request_path,
            json={
                'progress_item_name': 'Spec link',
                'state': progress.ProgressVote.VERIFIED,
            },
        ):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_post(feature_id=self.feature_id)

    def test_post___non_editor_forbidden(self):
        """Signed-in users without can_edit_any_feature permission are rejected with 403."""
        import werkzeug.exceptions

        testing_config.sign_in('regular@example.com', 222)
        with test_app.test_request_context(
            self.request_path,
            json={
                'progress_item_name': 'Spec link',
                'state': progress.ProgressVote.VERIFIED,
            },
        ):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_post(feature_id=self.feature_id)
        testing_config.sign_out()
