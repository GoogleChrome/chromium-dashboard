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
    self.prop_5 = metrics_models.WebDXFeatureObserver(
        bucket_id=5, property_name='Popover')
    self.prop_5.put()
    self.prop_6 = metrics_models.WebDXFeatureObserver(
        bucket_id=6, property_name='HTTP/3')
    self.prop_6.put()

  def tearDown(self):
    self.prop_1.key.delete()
    self.prop_2.key.delete()
    self.prop_3.key.delete()
    self.prop_4.key.delete()
    self.prop_5.key.delete()
    self.prop_6.key.delete()

  def test_get_template_data__css(self):
    with test_app.test_request_context('/data/blink/cssprops'):
      actual_buckets = self.handler.get_template_data(prop_type='cssprops')
    self.assertEqual(
        [(2, 'a prop'), (1, 'b prop')],
        actual_buckets)

  def test_get_template_data__js(self):
    with test_app.test_request_context('/data/blink/features'):
      actual_buckets = self.handler.get_template_data(prop_type='featureprops')
    self.assertEqual(
        [(4, 'a feat'), (3, 'b feat')],
        actual_buckets)

  def test_get_template_data__webfeatures(self):
    with test_app.test_request_context('/data/blink/features'):
      actual_buckets = self.handler.get_template_data(
          prop_type='webfeatureprops')
    self.assertEqual(
        [(6, 'HTTP/3'), (5, 'Popover')],
        actual_buckets)


class WebFeatureTimelineHandlerTests(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = metricsdata.WebFeatureTimelineHandler()
    
    self.webdx_datapoint = metrics_models.WebDXFeature(
        day_percentage=0.0123456789, 
        date=datetime.date(2024, 8, 1),
        bucket_id=100, 
        property_name='TestWebDXFeature')
    self.webdx_datapoint.put()
    
    self.classic_datapoint = metrics_models.FeatureObserver(
        day_percentage=0.0987654321,
        date=datetime.date(2024, 5, 1),
        bucket_id=100,
        property_name='TestClassicFeature')
    self.classic_datapoint.put()

  def tearDown(self):
    self.webdx_datapoint.key.delete()
    self.classic_datapoint.key.delete()
    
    for webdx_entity in metrics_models.WebDXFeature.query().fetch():
      if webdx_entity.bucket_id in [100, 200]:
        webdx_entity.key.delete()
    
    for classic_entity in metrics_models.FeatureObserver.query().fetch():
      if classic_entity.bucket_id in [100, 200]:
        classic_entity.key.delete()

  def test_get_template_data__webdx_sufficient(self):
    """Test that WebDX data is returned when sufficient recent data exists."""
    # Create additional WebDX datapoints to meet the threshold of 5
    extra_datapoints = []
    for i in range(4):  # We already have 1, need 4 more
      dp = metrics_models.WebDXFeature(
          day_percentage=0.01 + i * 0.001,
          date=datetime.date(2024, 7, 1 + i),
          bucket_id=100,
          property_name=f'TestWebDXFeature{i}')
      dp.put()
      extra_datapoints.append(dp)
    
    try:
      url = '/data/timeline/webfeaturepopularity?bucket_id=100'
      
      with test_app.test_request_context(url):
        actual_datapoints = self.handler.get_template_data()
      
      # Should get 5 WebDX datapoints (no fallback needed)
      self.assertEqual(5, len(actual_datapoints))
      
      # Check that we have the original datapoint
      original_found = any(dp['property_name'] == 'TestWebDXFeature' and 
                          dp['date'] == '2024-08-01' 
                          for dp in actual_datapoints)
      self.assertTrue(original_found, 'Original WebDX datapoint should be present')
    
    finally:
      for dp in extra_datapoints:
        dp.key.delete()

  def test_get_template_data__no_bucket_id(self):
    """Test that empty list is returned when no bucket_id provided."""
    url = '/data/timeline/webfeaturepopularity'
    
    with test_app.test_request_context(url):
      actual_datapoints = self.handler.get_template_data()
    
    self.assertEqual([], actual_datapoints)

  def test_mapping_logic(self):
    """Test WebDX to Classic bucket_id mapping."""
    webdx_observer = metrics_models.WebDXFeatureObserver(
        bucket_id=150,
        property_name='MappingTestFeature'
    )
    webdx_observer.put()
    
    classic_observer = metrics_models.FeatureObserverHistogram(
        bucket_id=250,
        property_name='MappingTestFeature'  # Same feature name
    )
    classic_observer.put()
    
    try:
      # Test the mapping function
      mapped_bucket = self.handler._map_webdx_to_classic_bucket(150)
      self.assertEqual(250, mapped_bucket, 
                      'Should map WebDX bucket_id=150 to Classic bucket_id=250')
      
      # Test reverse lookup
      enum_result = metrics_models.WebDXFeatureObserver.get_enum_by_web_feature('MappingTestFeature')
      self.assertEqual('150', enum_result,
                      'Should find WebDX bucket_id for feature name')
      
    finally:
      webdx_observer.key.delete()
      classic_observer.key.delete()

  def test_performance_with_large_dataset(self):
    """Test performance with realistic data volume."""
    import time
    
    # Create 100 WebDX entries (realistic daily data for 3+ months)
    webdx_entries = []
    for i in range(100):
      entry = metrics_models.WebDXFeature(
          bucket_id=300,
          property_name=f'PerfTestFeature_{i}',
          date=datetime.date(2024, 6, 1) + datetime.timedelta(days=i),
          day_percentage=0.01 + i * 0.0001
      )
      entry.put()
      webdx_entries.append(entry)
    
    try:
      url = '/data/timeline/webfeaturepopularity?bucket_id=300'
      
      # Test response time
      start_time = time.time()
      
      with test_app.test_request_context(url):
        result = self.handler.get_template_data()
      
      response_time = time.time() - start_time
      
      self.assertLess(response_time, 2.0, 'Response should be under 2 seconds')
      self.assertEqual(100, len(result), 'Should return all 100 entries')
      
      start_time = time.time()
      
      with test_app.test_request_context(url):
        result2 = self.handler.get_template_data()
        
      cached_response_time = time.time() - start_time
      
      self.assertLess(cached_response_time, response_time, 
                     'Cached response should be faster')
      
    finally:
      for entry in webdx_entries:
        entry.key.delete()

  def test_get_template_data__fallback_to_classic(self):
    """Test fallback to classic data when WebDX data is insufficient."""
    webdx_observer = metrics_models.WebDXFeatureObserver(
        bucket_id=200,
        property_name='TestFallbackFeature')
    webdx_observer.put()
    
    classic_observer = metrics_models.FeatureObserverHistogram(
        bucket_id=250,  # Different bucket_id for classic
        property_name='TestFallbackFeature')  # Same property name
    classic_observer.put()
    
    old_webdx_datapoint = metrics_models.WebDXFeature(
        day_percentage=0.0555555555, 
        date=datetime.date(2024, 3, 1),  # Before June 2024
        bucket_id=200, 
        property_name='TestFallbackFeature')
    old_webdx_datapoint.put()
    
    # Create classic data for fallback
    classic_fallback_datapoint = metrics_models.FeatureObserver(
        day_percentage=0.0777777777,
        date=datetime.date(2024, 7, 1),  # After June 2024
        bucket_id=250,  # Classic bucket_id
        property_name='TestFallbackFeature')
    classic_fallback_datapoint.put()
    
    try:
      url = '/data/timeline/webfeaturepopularity?bucket_id=200'
      
      with test_app.test_request_context(url):
        actual_datapoints = self.handler.get_template_data()
      
      # Should get classic fallback data since WebDX data is insufficient
      # Plus metadata marker about fallback usage
      self.assertEqual(2, len(actual_datapoints))
      
      # First entry should be the actual classic fallback data
      self.assertEqual(250, actual_datapoints[0]['bucket_id'])  # Classic bucket_id
      self.assertEqual('TestFallbackFeature', actual_datapoints[0]['property_name'])
      self.assertEqual('2024-07-01', actual_datapoints[0]['date'])
      
      # Second entry should be the metadata marker
      self.assertEqual(-999, actual_datapoints[1]['bucket_id'])
      self.assertEqual('__DATA_SOURCE_INFO__', actual_datapoints[1]['property_name'])
      self.assertEqual('classic_fallback', actual_datapoints[1]['source_type'])
      self.assertIn('classic usecounter as fallback', actual_datapoints[1]['message'])
    
    finally:
      webdx_observer.key.delete()
      classic_observer.key.delete()
      old_webdx_datapoint.key.delete()
      classic_fallback_datapoint.key.delete()
