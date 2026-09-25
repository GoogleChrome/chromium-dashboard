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

"""Tests for the processes_api module, verifying the retrieval of process stages and feature progress."""

from dataclasses import asdict

import flask

import testing_config  # Must be imported before the module under test.
from api import processes_api
from internals import core_enums, core_models, processes

test_app = flask.Flask(__name__)


class ProcessesAPITest(testing_config.CustomTestCase):
    """Tests for ProcessesAPI."""

    def setUp(self):
        """Set up the test environment."""
        self.feature_1 = core_models.FeatureEntry(
            name='feature one', summary='sum', category=1, feature_type=0
        )
        self.feature_1.put()
        self.feature_id = self.feature_1.key.integer_id()
        stage_types = [110, 120, 130, 140, 150, 151, 160]
        self.stages: list[core_models.Stage] = []
        for s_type in stage_types:
            stage = core_models.Stage(
                feature_id=self.feature_id, stage_type=s_type
            )
            stage.put()
            self.stages.append(stage)
        self.handler = processes_api.ProcessesAPI()
        self.request_path = f'/api/v0/features/{self.feature_id}/process'

    def tearDown(self):
        """Clean up the test environment."""
        for stage in self.stages:
            stage.key.delete()
        self.feature_1.key.delete()

    def test_get__default_feature_type(self):
        """We can get process for features with the default feature type (New feature incubation)."""  # noqa: E501
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.BLINK_LAUNCH_PROCESS)
        self.assertEqual(expected, actual)

    def test_get__feature_type_0(self):
        """We can get process for features with feature type 0 (New feature incubation)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_INCUBATE_ID
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.BLINK_LAUNCH_PROCESS)
        self.assertEqual(expected, actual)

    def test_get__feature_type_0_impact_enterprise(self):
        """We can get process for breaking features with feature type 0 (New feature incubation)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_INCUBATE_ID
        self.feature_1.enterprise_impact = core_enums.ENTERPRISE_IMPACT_LOW
        self.feature_1.put()
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.BLINK_LAUNCH_PROCESS)
        expected['stages'].insert(-1, asdict(processes.FEATURE_ROLLOUT_STAGE))
        expected['stages'][-1]['incoming_stage'] = core_enums.INTENT_ROLLOUT

        self.assertEqual(expected, actual)

    def test_get__feature_type_1(self):
        """We can get process for features with feature type 1 (Existing feature implementation)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_EXISTING_ID
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.BLINK_FAST_TRACK_PROCESS)
        self.assertEqual(expected, actual)

    def test_get__feature_type_1_impact_enterprise(self):
        """We can get process for breaking features with feature type 1 (Existing feature implementation)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_EXISTING_ID
        self.feature_1.enterprise_impact = core_enums.ENTERPRISE_IMPACT_MEDIUM
        self.feature_1.put()
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.BLINK_FAST_TRACK_PROCESS)
        expected['stages'].insert(-1, asdict(processes.FEATURE_ROLLOUT_STAGE))
        expected['stages'][-1]['incoming_stage'] = core_enums.INTENT_ROLLOUT

        self.assertEqual(expected, actual)

    def test_get__feature_type_2(self):
        """We can get process for features with feature type 2 (Web developer facing change to existing code)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_CODE_CHANGE_ID
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.PSA_ONLY_PROCESS)
        self.assertEqual(expected, actual)

    def test_get__feature_type_2_impact_enterprise(self):
        """We can get process for breaking features with feature type 2 (Web developer facing change to existing code)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_CODE_CHANGE_ID
        self.feature_1.enterprise_impact = core_enums.ENTERPRISE_IMPACT_HIGH
        self.feature_1.put()
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.PSA_ONLY_PROCESS)
        expected['stages'].insert(-1, asdict(processes.FEATURE_ROLLOUT_STAGE))
        expected['stages'][-1]['incoming_stage'] = core_enums.INTENT_ROLLOUT

        self.assertEqual(expected, actual)

    def test_get__feature_type_3(self):
        """We can get process for features with feature type 3 (Feature deprecation)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_DEPRECATION_ID
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.DEPRECATION_PROCESS)
        self.assertEqual(expected, actual)

    def test_get__feature_type_3_impact_enterprise(self):
        """We can get process for breaking features with feature type 3 (Feature deprecation)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_DEPRECATION_ID
        self.feature_1.enterprise_impact = core_enums.ENTERPRISE_IMPACT_LOW
        self.feature_1.put()
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.DEPRECATION_PROCESS)
        expected['stages'].insert(-1, asdict(processes.FEATURE_ROLLOUT_STAGE))
        expected['stages'][-1]['incoming_stage'] = core_enums.INTENT_ROLLOUT

        self.assertEqual(expected, actual)

    def test_get__feature_type_4(self):
        """We can get process for features with feature type 4 (Enterprise feature)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_ENTERPRISE_ID
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.ENTERPRISE_PROCESS)
        self.assertEqual(expected, actual)

    def test_get__feature_type_4_impact_enterprise(self):
        """We can get process for breaking features with feature type 4 (Enterprise feature)."""  # noqa: E501
        self.feature_1.feature_type = core_enums.FEATURE_TYPE_ENTERPRISE_ID
        self.feature_1.enterprise_impact = core_enums.ENTERPRISE_IMPACT_LOW
        self.feature_1.put()
        with test_app.test_request_context(self.request_path):
            actual = self.handler.do_get(feature_id=self.feature_id)
        expected = processes.process_to_dict(processes.ENTERPRISE_PROCESS)

        self.assertEqual(expected, actual)
