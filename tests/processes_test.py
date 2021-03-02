from __future__ import division
from __future__ import print_function

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

from google.appengine.ext import db

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

  def test_review_is_done(self):
    """A review step is done if the review has completed or was N/a."""
    self.assertFalse(processes.review_is_done(None))
    self.assertFalse(processes.review_is_done(0))
    self.assertFalse(processes.review_is_done(models.REVIEW_PENDING))
    self.assertFalse(processes.review_is_done(models.REVIEW_ISSUES_OPEN))
    self.assertTrue(processes.review_is_done(models.REVIEW_ISSUES_ADDRESSED))
    self.assertTrue(processes.review_is_done(models.REVIEW_NA))


class ProgressDetectorsTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=models.DEV_NO_SIGNALS,
        impl_status_chrome=1,
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

  def test_security_review_completed(self):
    detector = processes.PROGRESS_DETECTORS['Security review issues addressed']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.security_review_status = models.REVIEW_ISSUES_ADDRESSED
    self.assertTrue(detector(self.feature_1))

  def test_privacy_review_completed(self):
    detector = processes.PROGRESS_DETECTORS['Privacy review issues addressed']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.privacy_review_status = models.REVIEW_ISSUES_ADDRESSED
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

  def test_one_i2e_lgtm(self):
    detector = processes.PROGRESS_DETECTORS['One LGTM on Intent to Experiment']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.i2e_lgtms = [db.Email('api_owner@chromium.org')]
    self.assertTrue(detector(self.feature_1))

  def test_one_i2e_lgtm(self):
    detector = processes.PROGRESS_DETECTORS[
        'One LGTM on Request for Deprecation Trial']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.i2e_lgtms = [db.Email('api_owner@chromium.org')]
    self.assertTrue(detector(self.feature_1))

  def test_three_i2s_lgtm(self):
    detector = processes.PROGRESS_DETECTORS['Three LGTMs on Intent to Ship']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.i2s_lgtms = [
        db.Email('one@chromium.org'),
        db.Email('two@chromium.org'),
        db.Email('three@chromium.org')]
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

  def test_tag_review_requested(self):
    detector = processes.PROGRESS_DETECTORS['TAG review requested']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.tag_review = 'http://example.com'
    self.assertTrue(detector(self.feature_1))

  def test_tag_review_completed(self):
    detector = processes.PROGRESS_DETECTORS['TAG review issues addressed']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.tag_review_status = models.REVIEW_ISSUES_ADDRESSED
    self.assertTrue(detector(self.feature_1))

  def test_web_dav_signals(self):
    detector = processes.PROGRESS_DETECTORS['Web developer signals']
    self.assertFalse(detector(self.feature_1))
    self.feature_1.web_dev_views = models.PUBLIC_SUPPORT
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
