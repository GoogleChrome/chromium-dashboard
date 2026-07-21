# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the releasenotes_api module."""

import testing_config  # isort: split

import flask
import werkzeug.exceptions  # Flask HTTP stuff.

from api import releasenotes_api
from internals import core_enums
from internals.core_models import (
    FeatureEntry,
    FeatureSummarySuggestion,
    MilestoneSet,
    Stage,
)
from internals.review_models import Gate

test_app = flask.Flask(__name__)


class ReleaseNotesL10nAPITest(testing_config.CustomTestCase):
    """Tests for ReleaseNotesL10nAPI."""

    def setUp(self):
        """Set up the test case."""
        self.handler = releasenotes_api.ReleaseNotesL10nAPI()
        self.request_path = '/api/v0/releasenotes/l10n'

        # Create a base approved feature entry within range (shipping milestone 1)
        # to be used in tests
        self.feature_1 = FeatureEntry(
            name='feature one',
            summary='summary one',
            feature_type=0,
            category=1,
            enterprise_impact=2,
            is_releasenotes_content_reviewed=True,
            is_releasenotes_publish_ready=True,
        )
        self.feature_1.put()
        self.feature_1_id = self.feature_1.key.integer_id()

        self.ship_stage_1 = Stage(
            feature_id=self.feature_1_id,
            stage_type=160,
            milestones=MilestoneSet(desktop_first=1),
        )
        self.ship_stage_1.put()
        self.ship_stage_1_id = self.ship_stage_1.key.integer_id()

        self.gate_1 = Gate(
            feature_id=self.feature_1_id,
            stage_id=self.ship_stage_1_id,
            gate_type=core_enums.GATE_ENTERPRISE_SHIP,
            state=5,  # Vote.APPROVED
        )
        self.gate_1.put()

    def tearDown(self):
        """Tear down the test database."""
        self.feature_1.key.delete()
        self.ship_stage_1.key.delete()
        self.gate_1.key.delete()

    def test_do_get__missing_start(self):
        """It aborts with 400 if startMilestone is missing."""
        path = self.request_path + '?endMilestone=120'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)
            self.assertEqual(
                '400 Bad Request: Missing startMilestone', str(cm.exception)
            )

    def test_do_get__missing_end(self):
        """It aborts with 400 if endMilestone is missing."""
        path = self.request_path + '?startMilestone=110'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)
            self.assertEqual(
                '400 Bad Request: Missing endMilestone', str(cm.exception)
            )

    def test_do_get__invalid_start(self):
        """It aborts with 400 if startMilestone is not an integer."""
        path = self.request_path + '?startMilestone=abc&endMilestone=120'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)

    def test_do_get__negative_or_zero_milestones(self):
        """It aborts with 400 if milestones are not positive integers."""
        # startMilestone is 0
        path = self.request_path + '?startMilestone=0&endMilestone=120'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)
            self.assertEqual(
                '400 Bad Request: Milestones must be positive integers',
                str(cm.exception),
            )

        # endMilestone is negative
        path = self.request_path + '?startMilestone=10&endMilestone=-5'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)
            self.assertEqual(
                "400 Bad Request: Request parameter 'endMilestone' out of range: '-5'",
                str(cm.exception),
            )

    def test_do_get__invalid_range(self):
        """It aborts with 400 if startMilestone is greater than endMilestone."""
        path = self.request_path + '?startMilestone=120&endMilestone=110'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)
            self.assertEqual(
                '400 Bad Request: startMilestone must be less than or equal to endMilestone',
                str(cm.exception),
            )

    def test_do_get__success(self):
        """It returns features structured for l10n extraction on success."""
        # Set up additional scenario features:

        # 1. Valid feature before start_milestone (milestone = 0)
        # Excluded because its shipping milestone is 0 (which is < start_milestone 1).
        feature_before = FeatureEntry(
            name='feature before',
            summary='sum before',
            feature_type=0,
            category=1,
            enterprise_impact=2,
            is_releasenotes_content_reviewed=True,
            is_releasenotes_publish_ready=True,
        )
        feature_before.put()
        before_feat_id = feature_before.key.integer_id()
        before_stage = Stage(
            feature_id=before_feat_id,
            stage_type=160,
            milestones=MilestoneSet(desktop_first=0),
        )
        before_stage.put()
        before_gate = Gate(
            feature_id=before_feat_id,
            stage_id=before_stage.key.integer_id(),
            gate_type=core_enums.GATE_ENTERPRISE_SHIP,
            state=5,  # APPROVED
        )
        before_gate.put()

        # 2. Valid feature after end_milestone (milestone = 3)
        # INCLUDED because the milestone `>= start_milestone` check succeeds, and
        # `end_milestone` only filters features that have a non-null
        # `first_enterprise_notification_milestone` field. Since it is None here,
        # it is not filtered out.
        feature_after = FeatureEntry(
            name='feature after',
            summary='sum after',
            feature_type=0,
            category=1,
            enterprise_impact=2,
            is_releasenotes_content_reviewed=True,
            is_releasenotes_publish_ready=True,
        )
        feature_after.put()
        after_feat_id = feature_after.key.integer_id()
        after_stage = Stage(
            feature_id=after_feat_id,
            stage_type=160,
            milestones=MilestoneSet(desktop_first=3),
        )
        after_stage.put()
        after_gate = Gate(
            feature_id=after_feat_id,
            stage_id=after_stage.key.integer_id(),
            gate_type=core_enums.GATE_ENTERPRISE_SHIP,
            state=5,  # APPROVED
        )
        after_gate.put()

        # 3. Feature in range but not approved
        # Excluded because its Gate state is not APPROVED.
        feature_unapproved = FeatureEntry(
            name='feature unapproved',
            summary='sum unapproved',
            feature_type=0,
            category=1,
            enterprise_impact=2,
            is_releasenotes_content_reviewed=True,
            is_releasenotes_publish_ready=True,
        )
        feature_unapproved.put()
        unapproved_feat_id = feature_unapproved.key.integer_id()
        unapproved_stage = Stage(
            feature_id=unapproved_feat_id,
            stage_type=160,
            milestones=MilestoneSet(desktop_first=1),
        )
        unapproved_stage.put()
        unapproved_gate = Gate(
            feature_id=unapproved_feat_id,
            stage_id=unapproved_stage.key.integer_id(),
            gate_type=core_enums.GATE_ENTERPRISE_SHIP,
            state=Gate.PREPARING,  # Truly unapproved state
        )
        unapproved_gate.put()

        # 4. Feature first enterprise notification in range (first_enterprise_notification_milestone = 2)
        # INCLUDED because the milestone `>= start_milestone` check succeeds, and
        # `first_enterprise_notification_milestone` is 2 (which is <= end_milestone 2).
        feature_first_enterprise = FeatureEntry(
            name='feature first enterprise',
            summary='sum first',
            feature_type=0,
            category=1,
            enterprise_impact=2,
            first_enterprise_notification_milestone=2,
            is_releasenotes_content_reviewed=True,
            is_releasenotes_publish_ready=True,
        )
        feature_first_enterprise.put()
        first_enterprise_feat_id = feature_first_enterprise.key.integer_id()
        first_enterprise_stage = Stage(
            feature_id=first_enterprise_feat_id,
            stage_type=160,
            milestones=MilestoneSet(desktop_first=2),
        )
        first_enterprise_stage.put()
        first_enterprise_gate = Gate(
            feature_id=first_enterprise_feat_id,
            stage_id=first_enterprise_stage.key.integer_id(),
            gate_type=core_enums.GATE_ENTERPRISE_SHIP,
            state=5,  # APPROVED
        )
        first_enterprise_gate.put()

        # 5. Valid feature after end_milestone with first_enterprise_notification_milestone > end_milestone (milestone = 4)
        # EXCLUDED because `first_enterprise_notification_milestone` is 4 (which is > end_milestone 2).
        feature_after_filtered = FeatureEntry(
            name='feature after filtered',
            summary='sum after filtered',
            feature_type=0,
            category=1,
            enterprise_impact=2,
            first_enterprise_notification_milestone=4,
            is_releasenotes_content_reviewed=True,
            is_releasenotes_publish_ready=True,
        )
        feature_after_filtered.put()
        after_filtered_feat_id = feature_after_filtered.key.integer_id()
        after_filtered_stage = Stage(
            feature_id=after_filtered_feat_id,
            stage_type=160,
            milestones=MilestoneSet(desktop_first=4),
        )
        after_filtered_stage.put()
        after_filtered_gate = Gate(
            feature_id=after_filtered_feat_id,
            stage_id=after_filtered_stage.key.integer_id(),
            gate_type=core_enums.GATE_ENTERPRISE_SHIP,
            state=5,  # APPROVED
        )
        after_filtered_gate.put()

        path = self.request_path + '?startMilestone=1&endMilestone=2'
        with test_app.test_request_context(path):
            actual = self.handler.do_get()

        # Extract and sort returned features to ignore irrelevant ordering and unneeded keys
        returned_features = [
            {'id': f['id'], 'name': f['name']} for f in actual['features']
        ]
        returned_features.sort(key=lambda f: f['id'])

        # We expect self.feature_1, feature_first_enterprise, and feature_after to be returned.
        # feature_after_filtered is excluded because of its first_enterprise_notification_milestone.
        expected_features = [
            {'id': self.feature_1_id, 'name': 'feature one'},
            {
                'id': first_enterprise_feat_id,
                'name': 'feature first enterprise',
            },
            {'id': after_feat_id, 'name': 'feature after'},
        ]
        expected_features.sort(key=lambda f: f['id'])

        self.assertEqual(
            {
                'descriptions': core_enums.RELEASE_NOTES_L10N_FIELDS_DESCRIPTIONS,
                'features': expected_features,
            },
            {
                'descriptions': actual.get('descriptions'),
                'features': returned_features,
            },
        )

        # Clean up DB
        feature_before.key.delete()
        before_stage.key.delete()
        before_gate.key.delete()

        feature_after.key.delete()
        after_stage.key.delete()
        after_gate.key.delete()

        feature_unapproved.key.delete()
        unapproved_stage.key.delete()
        unapproved_gate.key.delete()

        feature_first_enterprise.key.delete()
        first_enterprise_stage.key.delete()
        first_enterprise_gate.key.delete()

        feature_after_filtered.key.delete()
        after_filtered_stage.key.delete()
        after_filtered_gate.key.delete()


class ReleaseNotesAPITest(testing_config.CustomTestCase):
    """Tests for ReleaseNotesAPI (GET /api/v0/releasenotes/{milestone})."""

    def setUp(self):
        """Set up test fixtures."""
        self.handler = releasenotes_api.ReleaseNotesAPI()

        self.feature_1 = FeatureEntry(
            id=101,
            name='CSS Anchor Positioning',
            summary='Human summary for anchor positioning.',
            category=1,
            feature_type=1,
            unlisted=False,
            confidential=False,
        )
        self.feature_1.put()

        self.stage_1 = Stage(
            feature_id=101,
            stage_type=core_enums.STAGE_BLINK_SHIPPING,
            milestones=MilestoneSet(desktop_first=132),
        )
        self.stage_1.put()

    def tearDown(self):
        """Tear down test database."""
        self.feature_1.key.delete()
        self.stage_1.key.delete()
        for s in FeatureSummarySuggestion.query():
            s.key.delete()

    def test_do_get__invalid_milestone(self):
        """It aborts HTTP 400 if milestone <= 0."""
        with test_app.test_request_context('/api/v0/releasenotes/0'):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get(milestone=0)
            self.assertEqual(400, cm.exception.code)

        with test_app.test_request_context('/api/v0/releasenotes/-5'):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get(milestone=-5)
            self.assertEqual(400, cm.exception.code)

        with test_app.test_request_context('/api/v0/releasenotes/abc'):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get(milestone='abc')
            self.assertEqual(400, cm.exception.code)

    def test_do_get__success_human_fallback(self):
        """It returns feature with summary_source = HUMAN when no AI suggestion exists."""
        with test_app.test_request_context('/api/v0/releasenotes/132'):
            response = self.handler.do_get(milestone=132)

        self.assertEqual(132, response['milestone'])
        self.assertEqual(1, len(response['features']))
        feat = response['features'][0]
        self.assertEqual(101, feat['id'])
        self.assertEqual('CSS Anchor Positioning', feat['name'])
        self.assertEqual(
            'Human summary for anchor positioning.', feat['summary']
        )
        self.assertEqual('HUMAN', feat['summary_source'])

    def test_do_get__success_ai_applied(self):
        """It overrides summary and sets summary_source = AI_APPLIED when an applied suggestion exists."""
        suggestion = FeatureSummarySuggestion(
            id=101,
            suggested_summary='AI-generated approved summary text.',
            status=core_enums.SummarySuggestionStatus.APPLIED,
            baseline_status=core_enums.BaselineStatus.NEWLY,
        )
        suggestion.put()

        with test_app.test_request_context('/api/v0/releasenotes/132'):
            response = self.handler.do_get(milestone=132)

        self.assertEqual(132, response['milestone'])
        self.assertEqual(1, len(response['features']))
        feat = response['features'][0]
        self.assertEqual(101, feat['id'])
        self.assertEqual('AI-generated approved summary text.', feat['summary'])
        self.assertEqual('AI_APPLIED', feat['summary_source'])
        self.assertEqual('newly', feat['baseline_status'])

    def test_do_get__unapplied_suggestion_ignored(self):
        """It ignores PROPOSED or REJECTED suggestions and falls back to HUMAN summary."""
        suggestion = FeatureSummarySuggestion(
            id=101,
            suggested_summary='Unapproved draft summary.',
            status=core_enums.SummarySuggestionStatus.PROPOSED,
        )
        suggestion.put()

        with test_app.test_request_context('/api/v0/releasenotes/132'):
            response = self.handler.do_get(milestone=132)

        feat = response['features'][0]
        self.assertEqual(
            'Human summary for anchor positioning.', feat['summary']
        )
        self.assertEqual('HUMAN', feat['summary_source'])

    def test_do_get__excludes_unlisted_and_deleted_features(self):
        """It excludes unlisted, confidential, or deleted features from release notes."""
        # 1. Unlisted feature
        self.feature_1.unlisted = True
        self.feature_1.put()
        with test_app.test_request_context('/api/v0/releasenotes/132'):
            response = self.handler.do_get(milestone=132)
        self.assertEqual([], response['features'])

        # 2. Confidential feature
        self.feature_1.unlisted = False
        self.feature_1.confidential = True
        self.feature_1.put()
        with test_app.test_request_context('/api/v0/releasenotes/132'):
            response = self.handler.do_get(milestone=132)
        self.assertEqual([], response['features'])

        # 3. Deleted feature
        self.feature_1.confidential = False
        self.feature_1.deleted = True
        self.feature_1.put()
        with test_app.test_request_context('/api/v0/releasenotes/132'):
            response = self.handler.do_get(milestone=132)
        self.assertEqual([], response['features'])
