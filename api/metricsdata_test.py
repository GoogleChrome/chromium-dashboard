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

import testing_config  # Must be imported first
import unittest

import datetime
import mock
import flask

from google.appengine.api import users

from api import metricsdata
import models


class MetricsFunctionTests(unittest.TestCase):

  def setUp(self):
    self.datapoint = models.StableInstance(
        day_percentage=0.0123456789, date=datetime.date.today(),
        bucket_id=1, property_name='prop')

  def test_truncate_day_percentage(self):
    updated_datapoint = metricsdata._truncate_day_percentage(self.datapoint)
    self.assertEqual(0.01234568, updated_datapoint.day_percentage)

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

  def test_clean_data__no_op(self):
    testing_config.sign_in('test@google.com', 111)
    datapoints = [self.datapoint]
    updated_datapoints = metricsdata._clean_data(datapoints)
    self.assertEqual(0.0123456789, updated_datapoints[0].day_percentage)

  def test_clean_data__clean_datapoints(self):
    testing_config.sign_out()
    datapoints = [self.datapoint]
    updated_datapoints = metricsdata._clean_data(datapoints)
    self.assertEqual(0.01234568, updated_datapoints[0].day_percentage)


class PopularityTimelineHandlerTests(unittest.TestCase):

  def setUp(self):
    self.handler = metricsdata.PopularityTimelineHandler()
    self.datapoint = models.StableInstance(
        day_percentage=0.0123456789, date=datetime.date.today(),
        bucket_id=1, property_name='prop')
    self.datapoint.put()

  def tearDown(self):
    self.datapoint.delete()

  def test_make_query(self):
    actual_query = self.handler.make_query(1)
    self.assertEqual(actual_query._model_class, models.StableInstance)

  def test_get_template_data__bad_bucket(self):
    url = '/data/timeline/csspopularity?bucket_id=not-a-number'
    with metricsdata.app.test_request_context(url):
      actual = self.handler.get_template_data()
    self.assertEqual([], actual)

  def test_get_template_data__normal(self):
    testing_config.sign_out()
    url = '/data/timeline/csspopularity?bucket_id=1'
    with metricsdata.app.test_request_context(url):
      actual_datapoints = self.handler.get_template_data()
    self.assertEqual(1, len(actual_datapoints))
    self.assertEqual(0.01234568, actual_datapoints[0]['day_percentage'])


# TODO(jrobbins): Test for metricsdata.FeatureHandler.


class FeatureBucketsHandlerTest(unittest.TestCase):

  def setUp(self):
    self.handler = metricsdata.FeatureBucketsHandler()
    self.prop_1 = models.CssPropertyHistogram(
        bucket_id=1, property_name='b prop')
    self.prop_1.put()
    self.prop_2 = models.CssPropertyHistogram(
        bucket_id=2, property_name='a prop')
    self.prop_2.put()
    self.prop_3 = models.FeatureObserverHistogram(
        bucket_id=3, property_name='b feat')
    self.prop_3.put()
    self.prop_4 = models.FeatureObserverHistogram(
        bucket_id=4, property_name='a feat')
    self.prop_4.put()

  def tearDown(self):
    self.prop_1.delete()
    self.prop_2.delete()
    self.prop_3.delete()
    self.prop_4.delete()

  def test_get_template_data__css(self):
    with metricsdata.app.test_request_context('/data/blink/cssprops'):
      actual_buckets = self.handler.get_template_data('cssprops')
    self.assertEqual(
        [(2, 'a prop'), (1, 'b prop')],
        actual_buckets)

  def test_get_template_data__js(self):
    with metricsdata.app.test_request_context('/data/blink/features'):
      actual_buckets = self.handler.get_template_data('features')
    self.assertEqual(
        [(4, 'a feat'), (3, 'b feat')],
        actual_buckets)
