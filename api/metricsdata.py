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
    try:
      bucket_id = int(self.request.args.get('bucket_id'))
    except:
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
    num = self.request.args.get('num')
    if num:
      feature_observer_key = self.get_top_num_cache_key(num)
      properties = rediscache.get(feature_observer_key)
      if properties is not None:
        return _datapoints_to_json_dicts(properties)

    # Get all datapoints in sorted order.
    properties = self.fetch_all_datapoints()

    if num and not self.should_refresh():
      feature_observer_key = self.get_top_num_cache_key(num)
      # Cache top `num` properties.
      properties = properties[0: min(int(num), len(properties))]
      rediscache.set(feature_observer_key, properties, time=CACHE_AGE)
    return _datapoints_to_json_dicts(properties)

  def get_top_num_cache_key(self, num):
    return self.CACHE_KEY + '_' + num

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
    return (self.MODEL_CLASS == metrics_models.FeatureObserver) and self.request.args.get('refresh')


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


class FeatureBucketsHandler(basehandlers.FlaskHandler):
  HTTP_CACHE_TYPE = 'private'
  JSONIFY = True

  def get_template_data(self, **kwargs):
    prop_type = kwargs.get('prop_type', None)
    if prop_type == 'cssprops':
      properties = sorted(
          metrics_models.CssPropertyHistogram.get_all().items(),
          key=lambda x:x[1])
    else:
      properties = sorted(
          metrics_models.FeatureObserverHistogram.get_all().items(),
          key=lambda x:x[1])

    return properties
