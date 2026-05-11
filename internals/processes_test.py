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

"""Tests for the processes module, verifying process dictionaries and review completion logic."""

import collections

import testing_config  # Must be imported before the module under test.
from internals import (
    approval_defs,
    core_enums,
    core_models,
    processes,
    stage_helpers,
)
from internals.metrics_models import WebDXFeatureObserver

BakeGateInfo = approval_defs.GateInfo(
    'Approval for baking',
    'The head chef must approve of you using the oven',
    9,
    approval_defs.ONE_LGTM,
    ['chef@example.com'],
    'Chef',
)

BAKE_APPROVAL_DEF_DICT = collections.OrderedDict(
    [
        ('name', 'Approval for baking'),
        ('team_name', 'Chef'),
        ('escalation_email', None),
        ('description', 'The head chef must approve of you using the oven'),
        ('gate_type', 9),
        ('rule', approval_defs.ONE_LGTM),
        ('approvers', ['chef@example.com']),
        ('slo_initial_response', 5),
        ('slo_resolve', 10),
    ]
)

PI_COLD_DOUGH = processes.ProgressItem('Cold dough', 'dough')
PI_LOAF = processes.ProgressItem('A loaf', None)
PI_DIRTY_PAN = processes.ProgressItem('A dirty pan', None)

STAGE_BAKE_DOUGH = 110
STAGE_BAKE_BAKE = 120


class HelperFunctionsTest(testing_config.CustomTestCase):
    """Tests for HelperFunctions."""

    def test_process_to_dict(self):
        """Test process to dict."""
        process = processes.Process(
            'Baking',
            'This is how you make bread',
            'Make it before you are hungry',
            [
                processes.ProcessStage(
                    'Make dough',
                    'Mix it and knead',
                    [PI_COLD_DOUGH],
                    [
                        processes.Action(
                            'Share kneading video', 'https://example.com', []
                        )
                    ],
                    [],
                    0,
                    1,
                    STAGE_BAKE_DOUGH,
                ),
                processes.ProcessStage(
                    'Bake it',
                    'Heat at 375 for 40 minutes',
                    [PI_LOAF, PI_DIRTY_PAN],
                    [],
                    [BakeGateInfo],
                    1,
                    2,
                    STAGE_BAKE_BAKE,
                ),
            ],
        )
        expected = {
            'name': 'Baking',
            'description': 'This is how you make bread',
            'applicability': 'Make it before you are hungry',
            'stages': [
                {
                    'name': 'Make dough',
                    'description': 'Mix it and knead',
                    'progress_items': [
                        {'name': 'Cold dough', 'field': 'dough'}
                    ],
                    'actions': [
                        {
                            'name': 'Share kneading video',
                            'url': 'https://example.com',
                            'prerequisites': [],
                        }
                    ],
                    'approvals': [],
                    'incoming_stage': 0,
                    'outgoing_stage': 1,
                    'stage_type': 110,
                },
                {
                    'name': 'Bake it',
                    'description': 'Heat at 375 for 40 minutes',
                    'progress_items': [
                        {'name': 'A loaf', 'field': None},
                        {'name': 'A dirty pan', 'field': None},
                    ],
                    'actions': [],
                    'approvals': [BAKE_APPROVAL_DEF_DICT],
                    'incoming_stage': 1,
                    'outgoing_stage': 2,
                    'stage_type': 120,
                },
            ],
        }
        actual = processes.process_to_dict(process)

        self.assertEqual(
            expected['stages'][1]['approvals'], actual['stages'][1]['approvals']
        )
        self.assertEqual(expected, actual)

    def test_review_is_done(self):
        """A review step is done if the review has completed or was N/a."""
        self.assertFalse(processes.review_is_done(None))
        self.assertFalse(processes.review_is_done(0))
        self.assertFalse(processes.review_is_done(core_enums.REVIEW_PENDING))
        self.assertFalse(
            processes.review_is_done(core_enums.REVIEW_ISSUES_OPEN)
        )
        self.assertTrue(
            processes.review_is_done(core_enums.REVIEW_ISSUES_ADDRESSED)
        )
        self.assertTrue(processes.review_is_done(core_enums.REVIEW_NA))


class ProcessesWellFormedTest(testing_config.CustomTestCase):
    """Verify that our processes have no undefined references."""

    def verify_references_to_prerequisites(self, process):
        """Verify references to prerequisites."""
        progress_items_so_far = {}
        for stage in process.stages:
            progress_items_so_far.update(
                {pi.name: pi for pi in stage.progress_items}
            )
            for action in stage.actions:
                for prereq_name in action.prerequisites:
                    self.assertIn(prereq_name, progress_items_so_far)
                    self.assertTrue(progress_items_so_far[prereq_name].field)

    def test_BLINK_LAUNCH_PROCESS(self):
        """Prerequisites in BLINK_LAUNCH_PROCESS are defined and actionable."""
        self.verify_references_to_prerequisites(processes.BLINK_LAUNCH_PROCESS)

    def test_BLINK_FAST_TRACK_PROCESS(self):
        """Prerequisites in BLINK_FAST_TRACK_PROCESS are defined and actionable."""
        self.verify_references_to_prerequisites(
            processes.BLINK_FAST_TRACK_PROCESS
        )

    def test_PSA_ONLY_PROCESS(self):
        """Prerequisites in PSA_ONLY_PROCESS are defined and actionable."""
        self.verify_references_to_prerequisites(processes.PSA_ONLY_PROCESS)

    def test_DEPRECATION_PROCESS(self):
        """Prerequisites in DEPRECATION_PROCESS are defined and actionable."""
        self.verify_references_to_prerequisites(processes.DEPRECATION_PROCESS)

    def test_ENTERPRISE_PROCESS(self):
        """Prerequisites in NTERPRISE_PROCESS are defined and actionable."""
        self.verify_references_to_prerequisites(processes.ENTERPRISE_PROCESS)


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

    def test_initial_public_proposal_url(self):
        """Test initial public proposal url."""
        detector = processes.PROGRESS_DETECTORS['Initial public proposal']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.initial_public_proposal_url = 'http://example.com'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_explainer(self):
        """Test explainer."""
        detector = processes.PROGRESS_DETECTORS['Explainer']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.explainer_links = ['http://example.com']
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_web__faeture(self):
        """Test web  faeture."""
        detector = processes.PROGRESS_DETECTORS['Web feature']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.web_feature = WebDXFeatureObserver.MISSING_FEATURE_ID
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.web_feature = 'array'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_security_review_completed(self):
        """Test security review completed."""
        detector = processes.PROGRESS_DETECTORS[
            'Security review issues addressed'
        ]
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.security_review_status = (
            core_enums.REVIEW_ISSUES_ADDRESSED
        )
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_privacy_review_completed(self):
        """Test privacy review completed."""
        detector = processes.PROGRESS_DETECTORS[
            'Privacy review issues addressed'
        ]
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.privacy_review_status = (
            core_enums.REVIEW_ISSUES_ADDRESSED
        )
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_intent_to_prototype_email(self):
        """Test intent to prototype email."""
        detector = processes.PROGRESS_DETECTORS['Intent to Prototype email']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[120][
            0
        ].intent_thread_url = 'http://example.com/prototype'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_intent_to_ship_email(self):
        """Test intent to ship email."""
        detector = processes.PROGRESS_DETECTORS['Intent to Ship email']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[160][0].intent_thread_url = 'http://example.com/ship'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_ready_for_trial_email(self):
        """Test ready for trial email."""
        detector = processes.PROGRESS_DETECTORS[
            'Ready for Developer Testing email'
        ]
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[130][
            0
        ].announcement_url = 'http://example.com/trial_ready'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_intent_to_experiment_email(self):
        """Test intent to experiment email."""
        detector = processes.PROGRESS_DETECTORS['Intent to Experiment email']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[150][0].intent_thread_url = 'http://example.com/ot'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_samples(self):
        """Test samples."""
        detector = processes.PROGRESS_DETECTORS['Samples']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.sample_links = ['http://example.com']
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_doc_links(self):
        """Test doc links."""
        detector = processes.PROGRESS_DETECTORS['Doc links']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.doc_links = ['http://example.com']
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_tag_review_requested(self):
        """Test tag review requested."""
        detector = processes.PROGRESS_DETECTORS['TAG review requested']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.tag_review = 'http://example.com'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_tag_review_completed(self):
        """Test tag review completed."""
        detector = processes.PROGRESS_DETECTORS['TAG review issues addressed']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.tag_review_status = core_enums.REVIEW_ISSUES_ADDRESSED
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_web_dev_signals(self):
        """Test web dev signals."""
        detector = processes.PROGRESS_DETECTORS['Web developer signals']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.web_dev_views = core_enums.PUBLIC_SUPPORT
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_vendor_signals(self):
        """Test vendor signals."""
        detector = processes.PROGRESS_DETECTORS['Vendor signals']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.ff_views = core_enums.PUBLIC_SUPPORT
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_estimated_target_milestone(self):
        """Test estimated target milestone."""
        detector = processes.PROGRESS_DETECTORS['Estimated target milestone']
        self.stages_dict[160][0].milestones = core_models.MilestoneSet()
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[160][0].milestones.desktop_first = 99
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_code_in_chromium(self):
        """Test code in chromium."""
        detector = processes.PROGRESS_DETECTORS['Code in Chromium']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.impl_status_chrome = core_enums.ENABLED_BY_DEFAULT
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_motivation(self):
        """Test motivation."""
        detector = processes.PROGRESS_DETECTORS['Motivation']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.motivation = 'test motivation'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_code_removed(self):
        """Test code removed."""
        detector = processes.PROGRESS_DETECTORS['Code removed']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.feature_1.impl_status_chrome = core_enums.REMOVED
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_impact(self):
        """Test rollout impact."""
        detector = processes.PROGRESS_DETECTORS['Rollout impact']
        # There is always a value for this
        self.assertTrue(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_impact = 1
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_milestone(self):
        """Test rollout milestone."""
        detector = processes.PROGRESS_DETECTORS['Rollout milestone']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_milestone = 99
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_platforms(self):
        """Test rollout platforms."""
        detector = processes.PROGRESS_DETECTORS['Rollout platforms']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_platforms = ['iOS', 'Android']
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_stage_plan(self):
        """Test rollout stage plan."""
        detector = processes.PROGRESS_DETECTORS['Rollout stage plan']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_stage_plan = 1
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_rollout_details(self):
        """Test rollout details."""
        detector = processes.PROGRESS_DETECTORS['Rollout details']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].rollout_details = 'Details'
        self.assertTrue(detector(self.feature_1, self.stages_dict))

    def test_enterprise_policies(self):
        """Test enterprise policies."""
        detector = processes.PROGRESS_DETECTORS['Enterprise policies']
        self.assertFalse(detector(self.feature_1, self.stages_dict))
        self.stages_dict[1061][0].enterprise_policies = ['Policy1', 'Policy2']
        self.assertTrue(detector(self.feature_1, self.stages_dict))


class WriteGatesAndStagesForFeatureTest(testing_config.CustomTestCase):
    """Tests for write_gates_and_stages_for_feature."""

    def tearDown(self):
        """Clean up the test environment."""
        from internals.review_models import Gate

        kinds = [core_models.FeatureEntry, core_models.Stage, Gate]
        for kind in kinds:
            entities = kind.query().fetch()
            for entity in entities:
                entity.key.delete()

    def test_write_gates_and_stages_for_feature(self):
        """Test that stages and gates are created for a feature."""
        from internals.review_models import Gate

        feature = core_models.FeatureEntry(
            name='feature one',
            summary='sum',
            category=1,
            feature_type=0,
        )
        feature.put()
        feature_id = feature.key.integer_id()

        processes.write_gates_and_stages_for_feature(feature_id, 0)

        stages = core_models.Stage.query().fetch()
        gates = Gate.query().fetch()
        self.assertEqual(len(stages), 6)
        self.assertEqual(len(gates), 12)
