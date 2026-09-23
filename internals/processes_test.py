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

"""Tests for the processes module, verifying process dictionaries and stage definitions."""

import collections

import testing_config  # Must be imported before the module under test.
from internals import (
    approval_defs,
    core_models,
    processes,
)

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

PI_COLD_DOUGH = processes.ProgressItem(
    'Cold dough', 'dough', 'Moist and plyable', 'No longer sticky'
)
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
                            'Share kneading video',
                            'https://example.com',
                            [PI_COLD_DOUGH.name],
                            [],
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
                        {
                            'name': 'Cold dough',
                            'field': 'dough',
                            'description': 'Moist and plyable',
                            'criteria': 'No longer sticky',
                        },
                    ],
                    'actions': [
                        {
                            'name': 'Share kneading video',
                            'url': 'https://example.com',
                            'prerequisites': ['Cold dough'],
                            'gate_types': [],
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
                        {
                            'name': 'A loaf',
                            'field': None,
                            'description': None,
                            'criteria': None,
                        },
                        {
                            'name': 'A dirty pan',
                            'field': None,
                            'description': None,
                            'criteria': None,
                        },
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
        self.maxDiff = None
        self.assertEqual(expected, actual)


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
