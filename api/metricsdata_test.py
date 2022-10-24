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

import testing_config  # Must be imported first

import datetime
from unittest import mock
import flask
import werkzeug.exceptions

# from google.appengine.api import users
from framework import users
from framework import rediscache

from api import metricsdata
from internals import metrics_models

test_app = flask.Flask(__name__)


class MetricsFunctionTests(testing_config.CustomTestCase):

  def setUp(self):
    self.datapoint = metrics_models.StableInstance(
        day_percentage=0.0123456789, date=datetime.date.today(),
        bucket_id=1, property_name='prop')

  def test_is_googler__anon(self):
    testing_config.sign_out()
    user = users.get_current_user()
    self.assertFalse(metricsdata._is_googler(user))

  def test_is_googler__nongoogler(self):
    testing_config.sign_in('test@example.com', 111)
    user = users.get_current_user()
    self.assertFalse(metricsdata._is_googler(user))

  def test_is_googler__googler(self):
    testing_config.sign_in('test@google.com', 111)
    user = users.get_current_user()
    self.assertTrue(metricsdata._is_googler(user))

  def test_datapoints_to_json_dicts__googler(self):
    testing_config.sign_in('test@google.com', 111)
    datapoints = [self.datapoint]
    actual = metricsdata._datapoints_to_json_dicts(datapoints)
    expected = [{
        'bucket_id': 1,
        'date': str(datetime.date.today()),
        'day_percentage': 0.0123456789,
        'property_name': 'prop',
        }]
    self.assertEqual(expected, actual)

  def test_datapoints_to_json_dicts__nongoogler(self):
    testing_config.sign_in('test@example.com', 222)
    datapoints = [self.datapoint]
    actual = metricsdata._datapoints_to_json_dicts(datapoints)
    expected = [{
        'bucket_id': 1,
        'date': str(datetime.date.today()),
        'day_percentage': 0.01234568,  # rounded
        'property_name': 'prop',
        }]
    self.assertEqual(expected, actual)


class PopularityTimelineHandlerTests(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = metricsdata.PopularityTimelineHandler()
    self.datapoint = metrics_models.StableInstance(
        day_percentage=0.0123456789, date=datetime.date.today(),
        bucket_id=1, property_name='prop')
    self.datapoint.put()

  def tearDown(self):
    self.datapoint.key.delete()

  def test_make_query(self):
    actual_query = self.handler.make_query(1)
    self.assertEqual(actual_query.kind, metrics_models.StableInstance._get_kind())

  @mock.patch('flask.abort')
  def test_get_template_data__bad_bucket(self, mock_abort):
    url = '/data/timeline/csspopularity?bucket_id=not-a-number'
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context(url):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        actual = self.handler.get_template_data()
      mock_abort.assert_called_once_with(
          400, description="Request parameter 'bucket_id' was not an int")

  def test_get_template_data__normal(self):
    testing_config.sign_out()
    url = '/data/timeline/csspopularity?bucket_id=1'
    with test_app.test_request_context(url):
      actual_datapoints = self.handler.get_template_data()
    self.assertEqual(1, len(actual_datapoints))
    self.assertEqual(0.01234568, actual_datapoints[0]['day_percentage'])


class CSSPopularityHandlerTests(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = metricsdata.CSSPopularityHandler()
    # Set up StableInstance data.
    self.datapoint = metrics_models.StableInstance(
        day_percentage=0.0123456789, date=datetime.date.today(),
        bucket_id=1, property_name='b prop')
    self.datapoint.put()
    # Set up CssPropertyHistogram data.
    self.prop_1 = metrics_models.CssPropertyHistogram(
        bucket_id=1, property_name='b prop')
    self.prop_1.put()
    self.prop_2 = metrics_models.CssPropertyHistogram(
        bucket_id=2, property_name='a prop')
    self.prop_2.put()
    self.prop_3 = metrics_models.FeatureObserverHistogram(
        bucket_id=3, property_name='b feat')
    self.prop_3.put()
    self.prop_4 = metrics_models.FeatureObserverHistogram(
        bucket_id=4, property_name='a feat')
    self.prop_4.put()

  def tearDown(self):
    self.datapoint.key.delete()
    self.prop_1.key.delete()
    self.prop_2.key.delete()
    self.prop_3.key.delete()
    self.prop_4.key.delete()
    rediscache.flushall()

  def test_get_top_num_cache_key(self):
    actual = self.handler.get_top_num_cache_key(30)
    self.assertEqual('metrics|css_popularity_30', actual)

  def test_get_template_data(self):
    url = '/data/csspopularity'
    with test_app.test_request_context(url):
      actual_datapoints = self.handler.get_template_data()
    self.assertEqual(1, len(actual_datapoints))
    self.assertEqual(0.01234568, actual_datapoints[0]['day_percentage'])

  def test_get_template_data_from_cache(self):
    url = '/data/csspopularity'
    with test_app.test_request_context(url):
      self.handler.get_template_data()

    actual_datapoints = rediscache.get('metrics|css_popularity')
    self.assertEqual(1, len(actual_datapoints))
    self.assertEqual(0.0123456789, actual_datapoints[0].day_percentage)

  def test_should_refresh(self):
    url = '/data/csspopularity?'
    with test_app.test_request_context(url):
      self.assertEqual(False, self.handler.should_refresh())

  def test_get_template_data_with_num(self):
    self.assertEqual(None, rediscache.get('metrics|css_popularity_30'))
    url = '/data/csspopularity?num=30'
    with test_app.test_request_context(url):
      self.handler.get_template_data()

    actual_datapoints = rediscache.get('metrics|css_popularity_30')
    self.assertEqual(1, len(actual_datapoints))
    self.assertEqual(0.0123456789, actual_datapoints[0].day_percentage)


class FeatureBucketsHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = metricsdata.FeatureBucketsHandler()
    self.prop_1 = metrics_models.CssPropertyHistogram(
        bucket_id=1, property_name='b prop')
    self.prop_1.put()
    self.prop_2 = metrics_models.CssPropertyHistogram(
        bucket_id=2, property_name='a prop')
    self.prop_2.put()
    self.prop_3 = metrics_models.FeatureObserverHistogram(
        bucket_id=3, property_name='b feat')
    self.prop_3.put()
    self.prop_4 = metrics_models.FeatureObserverHistogram(
        bucket_id=4, property_name='a feat')
    self.prop_4.put()

  def tearDown(self):
    self.prop_1.key.delete()
    self.prop_2.key.delete()
    self.prop_3.key.delete()
    self.prop_4.key.delete()

  def test_get_template_data__css(self):
    with test_app.test_request_context('/data/blink/cssprops'):
      actual_buckets = self.handler.get_template_data(prop_type='cssprops')
    self.assertEqual(
        [(2, 'a prop'), (1, 'b prop')],
        actual_buckets)

  def test_get_template_data__js(self):
    with test_app.test_request_context('/data/blink/features'):
      actual_buckets = self.handler.get_template_data(prop_type='features')
    self.assertEqual(
        [(4, 'a feat'), (3, 'b feat')],
        actual_buckets)
