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

from __future__ import division
from __future__ import print_function

import datetime
import unittest
import testing_config  # Must be imported before the module under test.
import urllib

import mock
import flask
import werkzeug

import admin
import models
import processes

class FetchMetricsTest(unittest.TestCase):

  @mock.patch('settings.PROD', True)
  @mock.patch('requests.request')
  def test__prod(self, mock_fetch):
    """In prod, we actually request metrics from uma-export."""
    mock_fetch.return_value = 'mock response'
    actual = admin._FetchMetrics('a url')

    self.assertEqual('mock response', actual)
    mock_fetch.assert_called_once_with('GET',
        'a url', timeout=120, allow_redirects=False)


  @mock.patch('settings.STAGING', True)
  @mock.patch('requests.request')
  def test__staging(self, mock_fetch):
    """In prod, we actually request metrics from uma-export."""
    mock_fetch.return_value = 'mock response'
    actual = admin._FetchMetrics('a url')

    self.assertEqual('mock response', actual)
    mock_fetch.assert_called_once_with('GET',
        'a url', timeout=120, allow_redirects=False)

  @mock.patch('requests.request')
  def test__dev(self, mock_fetch):
    """In Dev, we cannot access uma-export."""
    actual = admin._FetchMetrics('a url')

    self.assertIsNone(actual)
    mock_fetch.assert_not_called()


class UmaQueryTest(unittest.TestCase):

  def setUp(self):
    self.uma_query = admin.UmaQuery(
        query_name='usecounter.features',
        model_class=models.FeatureObserver,
        property_map_class=models.FeatureObserverHistogram)

  def testHasCapstone__not_found(self):
    """If there is no capstone entry, we get False."""
    query_date = datetime.date(2021, 1, 20)
    actual = self.uma_query._HasCapstone(query_date)
    self.assertFalse(actual)

  def testHasCapstone__found(self):
    """If we set a capstone entry, we can find it."""
    query_date = datetime.date(2021, 1, 20)
    capstone = self.uma_query._SetCapstone(query_date)

    try:
      actual = self.uma_query._HasCapstone(query_date)
    finally:
      capstone.delete()

    self.assertTrue(actual)


class YesterdayHandlerTest(unittest.TestCase):

  def setUp(self):
    self.request_path = '/cron/metrics'
    self.handler = admin.YesterdayHandler()

  @mock.patch('admin.UmaQuery.FetchAndSaveData')
  def test_get__normal(self, mock_FetchAndSaveData):
    """When requested with no date, we check the previous 5 days."""
    mock_FetchAndSaveData.return_value = 200
    today = datetime.date(2021, 1, 20)

    with admin.app.test_request_context(self.request_path):
      actual_response = self.handler.get_template_data(today=today)

    self.assertEqual('Success', actual_response)
    expected_calls = [
        mock.call(datetime.date(2021, 1, day))
        for day in [19, 18, 17, 16, 15]
        for query in admin.UMA_QUERIES]
    mock_FetchAndSaveData.assert_has_calls(expected_calls)

  @mock.patch('admin.UmaQuery.FetchAndSaveData')
  def test_get__debugging(self, mock_FetchAndSaveData):
    """We can request that the app get metrics for one specific day."""
    mock_FetchAndSaveData.return_value = 200
    today = datetime.date(2021, 1, 20)

    with admin.app.test_request_context(
        self.request_path, query_string={'date': '20210120'}):
      actual_response = self.handler.get_template_data(today=today)

    self.assertEqual('Success', actual_response)
    expected_calls = [
        mock.call(datetime.date(2021, 1, 20))
        for query in admin.UMA_QUERIES]
    mock_FetchAndSaveData.assert_has_calls(expected_calls)


class IntentEmailPreviewHandlerTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=models.INTENT_IMPLEMENT)
    self.feature_1.put()

    self.request_path = '/admin/features/launch/%d/%d?intent' % (
        models.INTENT_SHIP, self.feature_1.key().id())
    self.handler = admin.IntentEmailPreviewHandler()

  def tearDown(self):
    self.feature_1.delete()

  def test_get__anon(self):
    """Anon cannot view this preview features, gets redirected to login."""
    testing_config.sign_out()
    feature_id = self.feature_1.key().id()
    with admin.app.test_request_context(self.request_path):
      actual_response = self.handler.get_template_data(feature_id=feature_id)
    self.assertEqual('302 FOUND', actual_response.status)

  def test_get__no_existing(self):
    """Trying to view a feature that does not exist gives a 404."""
    testing_config.sign_in('user1@google.com', 123567890)
    bad_feature_id = self.feature_1.key().id() + 1
    with admin.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(feature_id=bad_feature_id)

  def test_get__no_stage_specified(self):
    """Allowed user can preview intent email for a feature using an old URL."""
    request_path = (
        '/admin/features/launch/%d?intent' % self.feature_1.key().id())
    testing_config.sign_in('user1@google.com', 123567890)
    feature_id = self.feature_1.key().id()
    with admin.app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(feature_id=feature_id)
    self.assertIn('feature', actual_data)
    self.assertEqual('feature one', actual_data['feature']['name'])

  def test_get__normal(self):
    """Allowed user can preview intent email for a feature."""
    testing_config.sign_in('user1@google.com', 123567890)
    feature_id = self.feature_1.key().id()
    with admin.app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(feature_id=feature_id)
    self.assertIn('feature', actual_data)
    self.assertEqual('feature one', actual_data['feature']['name'])

  def test_get_page_data(self):
    """page_data has correct values."""
    feature_id = self.feature_1.key().id()
    with admin.app.test_request_context(self.request_path):
      page_data = self.handler.get_page_data(
          feature_id, self.feature_1, models.INTENT_IMPLEMENT)
    self.assertEqual(
        'http://localhost/feature/%d' % feature_id,
        page_data['default_url'])
    self.assertEqual(
        ['motivation'],
        page_data['sections_to_show'])
    self.assertEqual(
        'Intent to Prototype',
        page_data['subject_prefix'])

  def test_compute_subject_prefix__incubate_new_feature(self):
    """We offer users the correct subject line for each intent stage."""
    self.assertEqual(
        'Intent stage "None"',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_NONE))

    self.assertEqual(
        'Intent stage "Start incubating"',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_INCUBATE))

    self.assertEqual(
        'Intent to Prototype',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_IMPLEMENT))

    self.assertEqual(
        'Ready for Trial',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_EXPERIMENT))

    self.assertEqual(
        'Intent stage "Evaluate readiness to ship"',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_IMPLEMENT_SHIP))

    self.assertEqual(
        'Intent to Experiment',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_EXTEND_TRIAL))

    self.assertEqual(
        'Intent to Ship',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_SHIP))

    self.assertEqual(
        'Intent stage "Removed"',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_REMOVED))

    self.assertEqual(
        'Intent stage "Shipped"',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_SHIPPED))

    self.assertEqual(
        'Intent stage "Parked"',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_PARKED))

  def test_compute_subject_prefix__deprecate_feature(self):
    """We offer users the correct subject line for each intent stage."""
    self.feature_1.feature_type = models.FEATURE_TYPE_DEPRECATION_ID
    self.assertEqual(
        'Intent stage "None"',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_NONE))

    self.assertEqual(
        'Intent to Deprecate and Remove',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_INCUBATE))

    self.assertEqual(
        'Request for Deprecation Trial',
        self.handler.compute_subject_prefix(
            self.feature_1, models.INTENT_EXTEND_TRIAL))
