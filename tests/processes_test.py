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

import unittest
import testing_config  # Must be imported before the module under test.

import mock

import models
import processes


class HelperFunctionsTest(unittest.TestCase):

  def test_process_to_dict(self):
    process = processes.Process(
        'Baking',
        'This is how you make bread',
        'Make it before you are hungry',
        [processes.ProcessStage(
            'Make dough',
            'Mix it and kneed',
            ['Cold dough'],
            [('Share kneeding video', 'https://example.com')],
            0, 1),
         processes.ProcessStage(
             'Bake it',
             'Heat at 375 for 40 minutes',
             ['A loaf', 'A dirty pan'],
             [],
             1, 2),
         ])
    expected = {
        'name': 'Baking',
        'description': 'This is how you make bread',
        'applicability': 'Make it before you are hungry',
        'stages': [
            {'name': 'Make dough',
             'description': 'Mix it and kneed',
             'progress_items': ['Cold dough'],
             'actions': [('Share kneeding video', 'https://example.com')],
             'incoming_stage': 0,
             'outgoing_stage': 1},
            {'name': 'Bake it',
             'description': 'Heat at 375 for 40 minutes',
             'progress_items': ['A loaf', 'A dirty pan'],
             'actions': [],
             'incoming_stage': 1,
             'outgoing_stage': 2},
        ]
    }
    actual = processes.process_to_dict(process)
    self.assertEqual(expected, actual)


class ProgressDetectorsTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=models.INTENT_IMPLEMENT)
    self.feature_1.put()

  def tearDown(self):
    self.feature_1.delete()

  def test_initial_public_proposal_url(self):
    detector = processes.PROGRESS_DETECTORS['Initial public proposal']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.initial_public_proposal_url = 'http://example.com'
    self.assertTrue(detector(self.feature_1))

  def test_explainer(self):
    detector = processes.PROGRESS_DETECTORS['Explainer']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.explainer_links = ['http://example.com']
    self.assertTrue(detector(self.feature_1))

  def test_intent_to_prototype_email(self):
    detector = processes.PROGRESS_DETECTORS['Intent to Prototype email']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.intent_to_implement_url = 'http://example.com'
    self.assertTrue(detector(self.feature_1))

  def test_intent_to_ship_email(self):
    detector = processes.PROGRESS_DETECTORS['Intent to Ship email']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.intent_to_ship_url = 'http://example.com'
    self.assertTrue(detector(self.feature_1))

  def test_ready_for_trial_email(self):
    detector = processes.PROGRESS_DETECTORS['Ready for Trial email']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.ready_for_trial_url = 'http://example.com'
    self.assertTrue(detector(self.feature_1))

  def test_intent_to_experiment_email(self):
    detector = processes.PROGRESS_DETECTORS['Intent to Experiment email']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.intent_to_experiment_url = 'http://example.com'
    self.assertTrue(detector(self.feature_1))

  def test_samples(self):
    detector = processes.PROGRESS_DETECTORS['Samples']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.sample_links = ['http://example.com']
    self.assertTrue(detector(self.feature_1))

  def test_doc_links(self):
    detector = processes.PROGRESS_DETECTORS['Doc links']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.doc_links = ['http://example.com']
    self.assertTrue(detector(self.feature_1))

  def test_tag_review_request(self):
    detector = processes.PROGRESS_DETECTORS['TAG review request']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.tag_review = 'http://example.com'
    self.assertTrue(detector(self.feature_1))

  def test_vendor_signals(self):
    detector = processes.PROGRESS_DETECTORS['Vendor signals']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.ff_views = models.PUBLIC_SUPPORT
    self.assertTrue(detector(self.feature_1))

  def test_estimated_target_milestone(self):
    detector = processes.PROGRESS_DETECTORS['Estimated target milestone']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.shipped_milestone = 99
    self.assertTrue(detector(self.feature_1))

  def test_code_in_chromium(self):
    detector = processes.PROGRESS_DETECTORS['Code in Chromium']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.impl_status_chrome = models.ENABLED_BY_DEFAULT
    self.assertTrue(detector(self.feature_1))

  def test_motivation(self):
    detector = processes.PROGRESS_DETECTORS['Motivation']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.motivation = 'test motivation'
    self.assertTrue(detector(self.feature_1))

  def test_code_removed(self):
    detector = processes.PROGRESS_DETECTORS['Code removed']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.impl_status_chrome = models.REMOVED
    self.assertTrue(detector(self.feature_1))
