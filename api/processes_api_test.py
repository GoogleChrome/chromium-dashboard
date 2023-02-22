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

import testing_config  # Must be imported before the module under test.

import flask

from dataclasses import asdict
from api import processes_api
from internals import core_enums
from internals import core_models
from internals import processes
from internals import core_enums

test_app = flask.Flask(__name__)


class ProcessesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.FeatureEntry(
        name='feature one', summary='sum', category=1, feature_type=0)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()
    stage_types = [110, 120, 130, 140, 150, 151, 160]
    self.stages: list[core_models.Stage] = []
    for s_type in stage_types:
      stage = core_models.Stage(feature_id=self.feature_id, stage_type=s_type)
      stage.put()
      self.stages.append(stage)
    self.handler = processes_api.ProcessesAPI()
    self.request_path = f'/api/v0/features/{self.feature_id}/process'

  def tearDown(self):
    for stage in self.stages:
      stage.key.delete()
    self.feature_1.key.delete()

  def test_get__default_feature_type(self):
    """We can get process for features with the default feature type (New feature incubation)."""
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.BLINK_LAUNCH_PROCESS)
    self.assertEqual(expected, actual)

  def test_get__feature_type_0(self):
    """We can get process for features with feature type 0 (New feature incubation)."""
    self.feature_1.feature_type = 0
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.BLINK_LAUNCH_PROCESS)
    self.assertEqual(expected, actual)

  def test_get__feature_type_0_breaking_change(self):
    """We can get process for breaking features with feature type 0 (New feature incubation)."""
    self.feature_1.feature_type = 0
    self.feature_1.breaking_change = True
    self.feature_1.put()
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.BLINK_LAUNCH_PROCESS)
    expected['stages'].insert(-1, asdict(processes.FEATURE_ROLLOUT_STAGE))
    expected['stages'][-1]['incoming_stage'] = core_enums.INTENT_ROLLOUT

    self.assertEqual(expected, actual)

  def test_get__feature_type_1(self):
    """We can get process for features with feature type 1 (Existing feature implementation)."""
    self.feature_1.feature_type = 1
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.BLINK_FAST_TRACK_PROCESS)
    self.assertEqual(expected, actual)

  def test_get__feature_type_1_breaking_change(self):
    """We can get process for breaking features with feature type 1 (Existing feature implementation)."""
    self.feature_1.feature_type = 1
    self.feature_1.breaking_change = True
    self.feature_1.put()
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.BLINK_FAST_TRACK_PROCESS)
    expected['stages'].insert(-1, asdict(processes.FEATURE_ROLLOUT_STAGE))
    expected['stages'][-1]['incoming_stage'] = core_enums.INTENT_ROLLOUT

    self.assertEqual(expected, actual)

  def test_get__feature_type_2(self):
    """We can get process for features with feature type 2 (Web developer facing change to existing code)."""
    self.feature_1.feature_type = 2
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.PSA_ONLY_PROCESS)
    self.assertEqual(expected, actual)

  def test_get__feature_type_2_breaking_change(self):
    """We can get process for breaking features with feature type 2 (Web developer facing change to existing code)."""
    self.feature_1.feature_type = 2
    self.feature_1.breaking_change = True
    self.feature_1.put()
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.PSA_ONLY_PROCESS)
    expected['stages'].insert(-1, asdict(processes.FEATURE_ROLLOUT_STAGE))
    expected['stages'][-1]['incoming_stage'] = core_enums.INTENT_ROLLOUT

    self.assertEqual(expected, actual)

  def test_get__feature_type_3(self):
    """We can get process for features with feature type 3 (Feature deprecation)."""
    self.feature_1.feature_type = 3
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.DEPRECATION_PROCESS)
    self.assertEqual(expected, actual)

  def test_get__feature_type_3_breaking_change(self):
    """We can get process for breaking features with feature type 3 (Feature deprecation)."""
    self.feature_1.feature_type = 3
    self.feature_1.breaking_change = True
    self.feature_1.put()
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.DEPRECATION_PROCESS)
    expected['stages'].insert(-1, asdict(processes.FEATURE_ROLLOUT_STAGE))
    expected['stages'][-1]['incoming_stage'] = core_enums.INTENT_ROLLOUT

    self.assertEqual(expected, actual)

  def test_get__feature_type_4(self):
    """We can get process for features with feature type 4 (Enterprise feature)."""
    self.feature_1.feature_type = 4
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.ENTERPRISE_PROCESS)
    self.assertEqual(expected, actual)

  def test_get__feature_type_4_breaking_change(self):
    """We can get process for breaking features with feature type 4 (Enterprise feature)."""
    self.feature_1.feature_type = 4
    self.feature_1.breaking_change = True
    self.feature_1.put()
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)
    expected = processes.process_to_dict(processes.ENTERPRISE_PROCESS)

    self.assertEqual(expected, actual)


class ProgressAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.FeatureEntry(
        name='feature one', summary='sum Z',
        owner_emails=['feature_owner@example.com'],
        spec_link='fake spec link', category=1, web_dev_views=1,
        impl_status_chrome=5, intent_stage=core_enums.INTENT_IMPLEMENT,
        feature_type=0)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    stage_types = [110, 120, 130, 140, 150, 151, 160]
    self.stages: list[core_models.Stage] = []
    for s_type in stage_types:
      stage = core_models.Stage(feature_id=self.feature_id, stage_type=s_type)
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

    self.handler = processes_api.ProgressAPI()
    self.request_path = f'/api/v0/features/{self.feature_id}/progress'

  def tearDown(self):
    self.feature_1.key.delete()

  def test_get___feature_progress(self):
    """We can get progress of a feature."""
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get(feature_id=self.feature_id)

    self.assertEqual({
      'Code in Chromium': 'True',
      'Draft API spec': 'fake spec link',
      'Estimated target milestone': 'True',
      'Final target milestone': 'True',
      'Intent to Prototype email': 'https://example.com/prototype',
      'Intent to Experiment email': 'https://example.com/ot',
      'Ready for Trial email': 'https://example.com/ready_for_trial',
      'Intent to Ship email': 'https://example.com/ship',
      'Spec link': 'fake spec link',
      'Updated target milestone': 'True',
      'Web developer signals': 'True',
    }, actual)
