# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc.
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

__author__ = 'ericbidelman@chromium.org (Eric Bidelman)'

import datetime
import json
import logging

from framework import users
from framework import basehandlers
from internals import metrics_models
from framework import rediscache
import settings

CACHE_AGE = 86400 # 24hrs
ROUNDING = 8  # 8 decimal places because all percents are < 1.0.

# WebDX fallback mechanism constants
WEBDX_DATA_CUTOFF_DATE = datetime.date(2024, 6, 1)  # After this date, WebDX data should be sufficient
MIN_RECENT_DATAPOINTS = 5  # Minimum recent data points to consider WebDX data sufficient
DATA_SOURCE_INFO_MARKER = '__DATA_SOURCE_INFO__'  # Special property name for metadata
FALLBACK_METADATA_BUCKET_ID = -999  # Special bucket_id for metadata entries


def _is_googler(user):
  return user and user.email().endswith('@google.com')


def _datapoints_to_json_dicts(datapoints):
  user = users.get_current_user()
  # Don't show raw percentages if user is not a googler.
  full_precision = _is_googler(user)

  json_dicts = [
      {'bucket_id': dp.bucket_id,
       'date': str(dp.date),  # YYYY-MM-DD
       'day_percentage':
         (dp.day_percentage if full_precision else
          round(dp.day_percentage, ROUNDING)),
       'property_name': dp.property_name,
      }
      for dp in datapoints]
  return json_dicts


class TimelineHandler(basehandlers.FlaskHandler):

  HTTP_CACHE_TYPE = 'private'
  JSONIFY = True
  CACHE_PREFIX = 'metrics|'

  def make_query(self, bucket_id):
    query = self.MODEL_CLASS.query()
    query = query.filter(self.MODEL_CLASS.bucket_id == bucket_id)
    # The switch to new UMA data changed the semantics of the CSS animated
    # properties. Since showing the historical data alongside the new data
    # does not make sense, filter out everything before the 2017-10-26 switch.
    # See https://github.com/GoogleChrome/chromium-dashboard/issues/414
    if self.MODEL_CLASS == metrics_models.AnimatedProperty:
      query = query.filter(
          self.MODEL_CLASS.date >= datetime.datetime(2017, 10, 26))
    return query

  def get_template_data(self, **kwargs):
    bucket_id = self.get_int_arg('bucket_id')
    if bucket_id is None:
      # TODO(jrobbins): Why return [] instead of 400?
      return []

    cache_key = '%s|%s' % (self.CACHE_KEY, bucket_id)

    datapoints = rediscache.get(cache_key)

    if not datapoints:
      query = self.make_query(bucket_id)
      query = query.order(self.MODEL_CLASS.date)
      datapoints = query.fetch(None) # All matching results.

      # Remove outliers if percentage is not between 0-1.
      #datapoints = filter(lambda x: 0 <= x.day_percentage <= 1, datapoints)
      rediscache.set(cache_key, datapoints, time=CACHE_AGE)

    return _datapoints_to_json_dicts(datapoints)


class PopularityTimelineHandler(TimelineHandler):

  CACHE_KEY = TimelineHandler.CACHE_PREFIX + 'css_pop_timeline'
  MODEL_CLASS = metrics_models.StableInstance

  def get_template_data(self, **kwargs):
    return super(PopularityTimelineHandler, self).get_template_data()


class AnimatedTimelineHandler(TimelineHandler):

  CACHE_KEY = TimelineHandler.CACHE_PREFIX + 'css_animated_timeline'
  MODEL_CLASS = metrics_models.AnimatedProperty

  def get_template_data(self, **kwargs):
    return super(AnimatedTimelineHandler, self).get_template_data()


class FeatureObserverTimelineHandler(TimelineHandler):

  CACHE_KEY = TimelineHandler.CACHE_PREFIX + 'featureob_timeline'
  MODEL_CLASS = metrics_models.FeatureObserver

  def get_template_data(self, **kwargs):
    return super(FeatureObserverTimelineHandler, self).get_template_data()


class WebFeatureTimelineHandler(TimelineHandler):

  CACHE_KEY = TimelineHandler.CACHE_PREFIX + 'webfeature_timeline'
  MODEL_CLASS = metrics_models.WebDXFeature

  def get_template_data(self, **kwargs):
    """Get WebDX timeline data with fallback to classic data if insufficient."""
    bucket_id = self.get_int_arg('bucket_id')
    if bucket_id is None:
      return []
    
    # Try WebDX data first
    webdx_data = self._get_webdx_data(bucket_id)
    
    if self._has_sufficient_webdx_data(webdx_data):
      return self._add_data_source_info(webdx_data, 'webdx')
    
    # Fallback to classic FeatureObserver data
    classic_data = self._get_classic_fallback_data(bucket_id)
    if classic_data:
      logging.info('Using classic fallback data for WebDX bucket_id %s', bucket_id)
      return self._add_data_source_info(classic_data, 'classic_fallback')
    
    # Last resort - return limited WebDX data with warning
    logging.warning(
        'No sufficient data found, returning limited WebDX data for bucket_id %s', 
        bucket_id)
    return self._add_data_source_info(webdx_data, 'webdx_limited')
  
  def _add_data_source_info(self, data, source_type):
    """Add metadata about data source for frontend notification."""
    if not data:
      return data
    
    metadata_messages = {
      'classic_fallback': 'Data after June 2024 uses classic usecounter as fallback for WebDX data',
      'webdx_limited': 'Limited WebDX data available after June 2024'
    }
    
    message = metadata_messages.get(source_type)
    if message:
      metadata_entry = {
        'bucket_id': FALLBACK_METADATA_BUCKET_ID,
        'date': str(WEBDX_DATA_CUTOFF_DATE),
        'day_percentage': 0,
        'property_name': DATA_SOURCE_INFO_MARKER,
        'source_type': source_type,
        'message': message
      }
      data.append(metadata_entry)
    
    return data
  
  def _get_webdx_data(self, bucket_id):
    """Get WebDX feature data using standard caching and query logic."""
    cache_key = f'{self.CACHE_KEY}|{bucket_id}'
    datapoints = rediscache.get(cache_key)
    
    if not datapoints:
      query = self.make_query(bucket_id)
      query = query.order(self.MODEL_CLASS.date)
      datapoints = query.fetch(None)
      rediscache.set(cache_key, datapoints, time=CACHE_AGE)
    
    return _datapoints_to_json_dicts(datapoints)
  
  def _has_sufficient_webdx_data(self, webdx_data):
    """Check if WebDX data has sufficient recent entries after the cutoff date."""
    if not webdx_data:
      return False
    
    recent_data = [
      dp for dp in webdx_data 
      if datetime.datetime.strptime(dp['date'], '%Y-%m-%d').date() >= WEBDX_DATA_CUTOFF_DATE
    ]
    
    return len(recent_data) >= MIN_RECENT_DATAPOINTS
  
  def _get_classic_fallback_data(self, webdx_bucket_id):
    """Get classic FeatureObserver data as fallback for WebDX data."""
    classic_bucket_id = self._map_webdx_to_classic_bucket(webdx_bucket_id)
    
    if not classic_bucket_id or classic_bucket_id == webdx_bucket_id:
      # No mapping found or mapping failed
      return []
    
    try:
      query = metrics_models.FeatureObserver.query()
      query = query.filter(metrics_models.FeatureObserver.bucket_id == classic_bucket_id)
      query = query.order(metrics_models.FeatureObserver.date)
      datapoints = query.fetch(None)
      
      return _datapoints_to_json_dicts(datapoints) if datapoints else []
    
    except Exception as e:
      logging.warning('Error fetching classic fallback data: %s', e)
      return []
  
  def _map_webdx_to_classic_bucket(self, webdx_bucket_id):
    """Map WebDX bucket_id to classic FeatureObserver bucket_id."""
    try:
      # Get WebDX feature name
      webdx_mapping = metrics_models.WebDXFeatureObserver.get_all()
      
      if webdx_bucket_id not in webdx_mapping:
        logging.info('No WebDXFeatureObserver found for bucket_id %s', webdx_bucket_id)
        return webdx_bucket_id
      
      web_feature_name = webdx_mapping[webdx_bucket_id]
      
      # Find classic bucket_id for same feature
      classic_mapping = metrics_models.FeatureObserverHistogram.get_all()
      
      for classic_bucket_id, property_name in classic_mapping.items():
        if property_name == web_feature_name:
          logging.info(
              'Mapped WebDX bucket %s (%s) -> Classic bucket %s',
              webdx_bucket_id, web_feature_name, classic_bucket_id)
          return classic_bucket_id
      
      logging.info(
          'No classic mapping found for WebDX feature "%s"', web_feature_name)
        
    except Exception as e:
      logging.warning('Error in bucket mapping: %s', e)
    
    return webdx_bucket_id  # Fallback to original bucket_id


class FeatureHandler(basehandlers.FlaskHandler):

  HTTP_CACHE_TYPE = 'private'
  JSONIFY = True
  CACHE_PREFIX = 'metrics|'

  def __query_metrics_for_properties(self):
    datapoints = []

    buckets_future = self.PROPERTY_CLASS.query().fetch_async(None)

    # First, grab a bunch of recent datapoints in a batch.
    # That operation is fast and makes most of the iterations
    # of the main loop become in-RAM operations.
    batch_datapoints_query = self.MODEL_CLASS.query()
    batch_datapoints_query = batch_datapoints_query.order(
        -self.MODEL_CLASS.date)
    batch_datapoints_list = batch_datapoints_query.fetch(5000)
    logging.info('batch query found %r recent datapoints',
                 len(batch_datapoints_list))
    batch_datapoints_dict = {}
    for dp in batch_datapoints_list:
      if dp.bucket_id not in batch_datapoints_dict:
        batch_datapoints_dict[dp.bucket_id] = dp
    logging.info('batch query found datapoints for %r buckets',
                 len(batch_datapoints_dict))

    # For every css property, fetch latest day_percentage.
    buckets = buckets_future.get_result()
    futures = []
    for b in buckets:
      if b.bucket_id in batch_datapoints_dict:
        datapoints.append(batch_datapoints_dict[b.bucket_id])
      else:
        query = self.MODEL_CLASS.query()
        query = query.filter(self.MODEL_CLASS.bucket_id == b.bucket_id)
        query = query.order(-self.MODEL_CLASS.date)
        futures.append(query.get_async())

    for f in futures:
      last_result = f.result()
      if last_result:
        datapoints.append(last_result)

    # Sort list by percentage. Highest first.
    datapoints.sort(key=lambda x: x.day_percentage, reverse=True)
    return datapoints

  def get_template_data(self, **kwargs):
    num = self.get_int_arg('num')
    if num and not self.should_refresh():
      feature_observer_key = self.get_top_num_cache_key(num)
      properties = rediscache.get(feature_observer_key)
      if properties is not None:
        return _datapoints_to_json_dicts(properties)

    # Get all datapoints in sorted order.
    properties = self.fetch_all_datapoints()

    if num:
      feature_observer_key = self.get_top_num_cache_key(num)
      # Cache top `num` properties.
      properties = properties[:num]
      rediscache.set(feature_observer_key, properties, time=CACHE_AGE)
    return _datapoints_to_json_dicts(properties)

  def get_top_num_cache_key(self, num):
    return self.CACHE_KEY + '_' + str(num)

  def fetch_all_datapoints(self):
    properties = rediscache.get(self.CACHE_KEY)
    logging.info(
        'looked at cache %r and found %s', self.CACHE_KEY,
        repr(properties)[:settings.MAX_LOG_LINE])

    if (properties is None) or self.should_refresh():
      logging.info('Loading properties from datastore')
      properties = self.__query_metrics_for_properties()
      rediscache.set(self.CACHE_KEY, properties, time=CACHE_AGE)

    logging.info('before filtering: %s',
                 repr(properties)[:settings.MAX_LOG_LINE])
    return properties

  def should_refresh(self):
    return (self.MODEL_CLASS == metrics_models.FeatureObserver and
        self.request.args.get('refresh'))


class CSSPopularityHandler(FeatureHandler):

  CACHE_KEY = FeatureHandler.CACHE_PREFIX + 'css_popularity'
  MODEL_CLASS = metrics_models.StableInstance
  PROPERTY_CLASS = metrics_models.CssPropertyHistogram

  def get_template_data(self, **kwargs):
    return super(CSSPopularityHandler, self).get_template_data()


class CSSAnimatedHandler(FeatureHandler):

  CACHE_KEY = FeatureHandler.CACHE_PREFIX + 'css_animated'
  MODEL_CLASS = metrics_models.AnimatedProperty
  PROPERTY_CLASS = metrics_models.CssPropertyHistogram

  def get_template_data(self, **kwargs):
    return super(CSSAnimatedHandler, self).get_template_data()


class FeatureObserverPopularityHandler(FeatureHandler):

  CACHE_KEY = FeatureHandler.CACHE_PREFIX + 'featureob_popularity'
  MODEL_CLASS = metrics_models.FeatureObserver
  PROPERTY_CLASS = metrics_models.FeatureObserverHistogram

  def get_template_data(self, **kwargs):
    return super(FeatureObserverPopularityHandler, self).get_template_data()


class WebFeaturePopularityHandler(FeatureHandler):

  CACHE_KEY = FeatureHandler.CACHE_PREFIX + 'webfeature_popularity'
  MODEL_CLASS = metrics_models.WebDXFeature
  PROPERTY_CLASS = metrics_models.WebDXFeatureObserver

  def get_template_data(self, **kwargs):
    return super(WebFeaturePopularityHandler, self).get_template_data()


class FeatureBucketsHandler(basehandlers.FlaskHandler):
  HTTP_CACHE_TYPE = 'private'
  JSONIFY = True

  TYPE_TO_HISTOGRAM_CLASS = {
      'cssprops': metrics_models.CssPropertyHistogram,
      'featureprops': metrics_models.FeatureObserverHistogram,
      'webfeatureprops': metrics_models.WebDXFeatureObserver,
      }

  def get_template_data(self, **kwargs):
    properties = []
    prop_type = kwargs.get('prop_type', None)
    histogram_class = self.TYPE_TO_HISTOGRAM_CLASS.get(prop_type)
    if histogram_class:
      properties = sorted(
          histogram_class.get_all().items(),
          key=lambda x:x[1])

    return properties
