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


import base64
import datetime
import json
import testing_config  # Must be imported before the module under test.
import urllib.request, urllib.parse, urllib.error

import mock
import flask
import werkzeug

from internals import fetchmetrics
from internals import models

test_app = flask.Flask(__name__)


class FetchMetricsTest(testing_config.CustomTestCase):

  @mock.patch('settings.PROD', True)
  @mock.patch('google.oauth2.id_token.fetch_id_token')
  @mock.patch('requests.request')
  def test__prod(self, mock_fetch, mock_fetch_id_token):
    """In prod, we actually request metrics from uma-export."""
    mock_fetch.return_value = 'mock response'
    mock_fetch_id_token.return_value = 'fake-token'

    actual = fetchmetrics._FetchMetrics('a url')

    self.assertEqual('mock response', actual)
    mock_fetch.assert_called_once_with(
        'GET', 'a url', timeout=120, allow_redirects=False,
        headers={'Authorization': 'Bearer fake-token'})


  @mock.patch('settings.STAGING', True)
  @mock.patch('google.oauth2.id_token.fetch_id_token')
  @mock.patch('requests.request')
  def test__staging(self, mock_fetch, mock_fetch_id_token):
    """In staging, we actually request metrics from uma-export."""
    mock_fetch.return_value = 'mock response'
    mock_fetch_id_token.return_value = 'fake-token'

    actual = fetchmetrics._FetchMetrics('a url')

    self.assertEqual('mock response', actual)
    mock_fetch.assert_called_once_with(
        'GET', 'a url', timeout=120, allow_redirects=False,
        headers={'Authorization': 'Bearer fake-token'})

  @mock.patch('requests.request')
  def test__dev(self, mock_fetch):
    """In Dev, we cannot access uma-export."""
    actual = fetchmetrics._FetchMetrics('a url')

    self.assertIsNone(actual)
    mock_fetch.assert_not_called()


class UmaQueryTest(testing_config.CustomTestCase):

  def setUp(self):
    self.uma_query = fetchmetrics.UmaQuery(
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
      capstone.key.delete()

    self.assertTrue(actual)

  @mock.patch('internals.fetchmetrics._FetchMetrics')
  def test_FetchData__ready(self, mock_fetch_metrics):
    """When the uma-export data is ready, we parse and return it."""
    r = {'123': {'rate': 0.001},
         '234': {'rate': 0.002}}
    XSSI_PROTECTION = ')]}\' // XSSI prefix (go/xssi).'
    response_content = '\n'.join([XSSI_PROTECTION, json.dumps({'r': r})])
    mock_fetch_metrics.return_value = testing_config.Blank(
        status_code=200, content=response_content.encode())
    query_date = datetime.date.fromisoformat('2021-12-02')

    actual_r, actual_status = self.uma_query._FetchData(query_date)

    self.assertEqual(r, actual_r)
    self.assertEqual(200, actual_status)

  @mock.patch('internals.fetchmetrics._FetchMetrics')
  def test_FetchData__empty(self, mock_fetch_metrics):
    """When the uma-export data is empty, we treat that as not ready."""
    r = {}
    XSSI_PROTECTION = ')]}\' // XSSI prefix (go/xssi).'
    response_content = '\n'.join([XSSI_PROTECTION, json.dumps({'r': r})])
    mock_fetch_metrics.return_value = testing_config.Blank(
        status_code=200, content=response_content.encode())
    query_date = datetime.date.fromisoformat('2021-12-02')

    actual_r, actual_status = self.uma_query._FetchData(query_date)

    self.assertEqual(None, actual_r)
    self.assertEqual(404, actual_status)

  @mock.patch('logging.error')
  @mock.patch('internals.fetchmetrics._FetchMetrics')
  def test_FetchData__error_msg(self, mock_fetch_metrics, mock_logging_error):
    """When uma-export gives any error message, we treat that as not ready."""
    r = {'123': 'anything'}
    e = 'mock uma error message'
    XSSI_PROTECTION = ')]}\' // XSSI prefix (go/xssi).'
    response_content = '\n'.join([XSSI_PROTECTION, json.dumps({'r': r, 'e': e})])
    mock_fetch_metrics.return_value = testing_config.Blank(
        status_code=200, content=response_content.encode())
    query_date = datetime.date.fromisoformat('2021-12-02')

    actual_r, actual_status = self.uma_query._FetchData(query_date)

    self.assertEqual(None, actual_r)
    self.assertEqual(404, actual_status)

  @mock.patch('logging.error')
  @mock.patch('internals.fetchmetrics._FetchMetrics')
  def test_FetchData__error_status(self, mock_fetch_metrics, mock_logging_error):
    """When uma-export gives a non-200, we treat that as not ready."""
    response_content = 'Error!!!!1'
    mock_fetch_metrics.return_value = testing_config.Blank(
        status_code=500, content=response_content.encode())
    query_date = datetime.date.fromisoformat('2021-12-02')

    actual_r, actual_status = self.uma_query._FetchData(query_date)

    self.assertEqual(None, actual_r)
    self.assertEqual(500, actual_status)


class YesterdayHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.request_path = '/cron/metrics'
    self.handler = fetchmetrics.YesterdayHandler()

  @mock.patch('internals.fetchmetrics.UmaQuery.FetchAndSaveData')
  def test_get__normal(self, mock_FetchAndSaveData):
    """When requested with no date, we check the previous 5 days."""
    mock_FetchAndSaveData.return_value = 200
    today = datetime.date(2021, 1, 20)

    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.get_template_data(today=today)

    self.assertEqual('Success', actual_response)
    expected_calls = [
        mock.call(datetime.date(2021, 1, day))
        for day in [19, 18, 17, 16, 15]
        for unused_query in fetchmetrics.UMA_QUERIES]
    mock_FetchAndSaveData.assert_has_calls(expected_calls)

  @mock.patch('internals.fetchmetrics.UmaQuery.FetchAndSaveData')
  def test_get__debugging(self, mock_FetchAndSaveData):
    """We can request that the app get metrics for one specific day."""
    mock_FetchAndSaveData.return_value = 200
    today = datetime.date(2021, 1, 20)

    with test_app.test_request_context(
        self.request_path, query_string={'date': '20210120'}):
      actual_response = self.handler.get_template_data(today=today)

    self.assertEqual('Success', actual_response)
    expected_calls = [
        mock.call(datetime.date(2021, 1, 20))
        for unused_query in fetchmetrics.UMA_QUERIES]
    mock_FetchAndSaveData.assert_has_calls(expected_calls)


class HistogramsHandlerTest(testing_config.CustomTestCase):

  ENUMS_TEXT = '''
     <histogram-configuration>

     <!-- Enum types -->

     <enums>

     <enum name="FeatureObserver">
       <!-- Generated from third_party/blink/public/mojom/...
            Called by update_use_counter_feature_enum.py.-->

       <int value="0" label="OBSOLETE_PageDestruction"/>
       <int value="1" label="LegacyNotifications"/>
       <int value="2" label="MultipartMainResource"/>
       <int value="3" label="PrefixedIndexedDB"/>
       <int value="4" label="WorkerStart"/>
     </enum>

     <enum name="MappedCSSProperties">

       <!-- Generated from third_party/blink/public/...
            Called by update_use_counter_css.py.-->

       <int value="1" label="Total Pages Measured"/>
       <int value="2" label="color"/>
       <int value="3" label="direction"/>
       <int value="4" label="display"/>
     </enum>

     </enums>
     </histogram-configuration>
     '''

  def setUp(self):
    self.request_path = '/cron/histograms'
    self.handler = fetchmetrics.HistogramsHandler()

  @mock.patch('requests.get')
  @mock.patch('internals.fetchmetrics.HistogramsHandler._SaveData')
  def test_get_template_data__normal(self, mock_save_data, mock_requests_get):
    """We can fetch and parse XML for metrics."""
    mock_requests_get.return_value = testing_config.Blank(
        status_code=200,
        content=base64.b64encode(self.ENUMS_TEXT.encode()))
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.get_template_data()

    self.assertEqual('Success', actual_response)
    self.assertEqual(9, mock_save_data.call_count)
