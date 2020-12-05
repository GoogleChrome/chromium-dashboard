from __future__ import division
from __future__ import print_function

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

import webapp2
import datetime
import json
import logging
import ramcache

import common
import models
import settings

CACHE_AGE = 86400 # 24hrs


class TimelineHandler(common.JSONHandler):

  def make_query(self, bucket_id):
    query = self.MODEL_CLASS.all()
    query.filter('bucket_id =', bucket_id)
    # The switch to new UMA data changed the semantics of the CSS animated
    # properties. Since showing the historical data alongside the new data
    # does not make sense, filter out everything before the 2017-10-26 switch.
    # See https://github.com/GoogleChrome/chromium-dashboard/issues/414
    if self.MODEL_CLASS == models.AnimatedProperty:
      query.filter('date >=', datetime.datetime(2017, 10, 26))
    return query

  def get(self):
    ramcache.check_for_distributed_invalidation()
    try:
      bucket_id = int(self.request.get('bucket_id'))
    except:
      return super(self.MODEL_CLASS, self).get([])

    KEY = '%s|%s' % (self.MEMCACHE_KEY, bucket_id)

    keys = models.get_chunk_memcache_keys(self.make_query(bucket_id), KEY)
    chunk_dict = ramcache.get_multi(keys)

    if chunk_dict and len(chunk_dict) == len(keys):
      datapoints = models.combine_memcache_chunks(chunk_dict)
    else:
      query = self.make_query(bucket_id)
      query.order('date')
      datapoints = query.fetch(None) # All matching results.

      # Remove outliers if percentage is not between 0-1.
      #datapoints = filter(lambda x: 0 <= x.day_percentage <= 1, datapoints)

      chunk_dict = models.set_chunk_memcache_keys(KEY, datapoints)
      ramcache.set_multi(chunk_dict, time=CACHE_AGE)

    datapoints = self._clean_data(datapoints)
    # Metrics json shouldn't be cached by intermediary caches because users
    # see different data when logged in. Set Cache-Control: private.
    super(TimelineHandler, self).get(datapoints, public=False)


class PopularityTimelineHandler(TimelineHandler):

  MEMCACHE_KEY = 'css_pop_timeline'
  MODEL_CLASS = models.StableInstance

  def get(self):
    super(PopularityTimelineHandler, self).get()


class AnimatedTimelineHandler(TimelineHandler):

  MEMCACHE_KEY = 'css_animated_timeline'
  MODEL_CLASS = models.AnimatedProperty

  def get(self):
    super(AnimatedTimelineHandler, self).get()


class FeatureObserverTimelineHandler(TimelineHandler):

  MEMCACHE_KEY = 'featureob_timeline'
  MODEL_CLASS = models.FeatureObserver

  def get(self):
    super(FeatureObserverTimelineHandler, self).get()


class FeatureHandler(common.JSONHandler):

  def __query_metrics_for_properties(self):
    datapoints = []

    # First, grab a bunch of recent datapoints in a batch.
    # That operation is fast and makes most of the iterations
    # of the main loop become in-RAM operations.
    batch_datapoints_query = self.MODEL_CLASS.all()
    batch_datapoints_query.order('-date')
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
    buckets = self.PROPERTY_CLASS.all().fetch(None)
    for b in buckets:
      if b.bucket_id in batch_datapoints_dict:
        datapoints.append(batch_datapoints_dict[b.bucket_id])
      else:
        query = self.MODEL_CLASS.all()
        query.filter('bucket_id =', b.bucket_id)
        query.order('-date')
        last_result = query.get()
        if last_result:
          datapoints.append(last_result)

    # Sort list by percentage. Highest first.
    datapoints.sort(key=lambda x: x.day_percentage, reverse=True)
    return datapoints

  def get(self):
    ramcache.check_for_distributed_invalidation()
    # TODO(jrobbins): chunking is unneeded with ramcache, so we can
    # simplify this code.
    # Memcache doesn't support saving values > 1MB. Break up features into chunks
    # and save those to memcache.
    if self.MODEL_CLASS == models.FeatureObserver:
      keys = models.get_chunk_memcache_keys(
          self.PROPERTY_CLASS.all(), self.MEMCACHE_KEY)
      logging.info('looking for keys %r' % keys)
      properties = ramcache.get_multi(keys)
      logging.info('found chunk keys %r' % (properties and properties.keys()))

      # TODO(jrobbins): We are at risk of displaying a partial result if
      # memcache loses some but not all chunks.  We can't estimate the number of
      # expected cached items efficiently.  To counter that, we refresh
      # every 30 minutes via a cron.
      if not properties or self.request.get('refresh'):
        properties = self.__query_metrics_for_properties()

        # Memcache doesn't support saving values > 1MB. Break up list into chunks.
        chunk_keys = models.set_chunk_memcache_keys(self.MEMCACHE_KEY, properties)
        logging.info('about to store chunks keys %r' % chunk_keys.keys())
        ramcache.set_multi(chunk_keys, time=CACHE_AGE)
      else:
        properties = models.combine_memcache_chunks(properties)
    else:
      properties = ramcache.get(self.MEMCACHE_KEY)
      if properties is None:
        properties = self.__query_metrics_for_properties()
        ramcache.set(self.MEMCACHE_KEY, properties, time=CACHE_AGE)

    properties = self._clean_data(properties)
    # Metrics json shouldn't be cached by intermediary caches because users
    # see different data when logged in. Set Cache-Control: private.
    super(FeatureHandler, self).get(properties, public=False)


class CSSPopularityHandler(FeatureHandler):

  MEMCACHE_KEY = 'css_popularity'
  MODEL_CLASS = models.StableInstance
  PROPERTY_CLASS = models.CssPropertyHistogram

  def get(self):
    super(CSSPopularityHandler, self).get()


class CSSAnimatedHandler(FeatureHandler):

  MEMCACHE_KEY = 'css_animated'
  MODEL_CLASS = models.AnimatedProperty
  PROPERTY_CLASS = models.CssPropertyHistogram

  def get(self):
    super(CSSAnimatedHandler, self).get()


class FeatureObserverPopularityHandler(FeatureHandler):

  MEMCACHE_KEY = 'featureob_popularity'
  MODEL_CLASS = models.FeatureObserver
  PROPERTY_CLASS = models.FeatureObserverHistogram

  def get(self):
    super(FeatureObserverPopularityHandler, self).get()


class FeatureBucketsHandler(common.BaseHandler):

  def get(self, type):
    if type == 'cssprops':
      properties = sorted(
          models.CssPropertyHistogram.get_all().iteritems(), key=lambda x:x[1])
    else:
      properties = sorted(
          models.FeatureObserverHistogram.get_all().iteritems(), key=lambda x:x[1])

    self.response.headers['Content-Type'] = 'application/json;charset=utf-8'
    return self.response.write(json.dumps(properties, separators=(',',':')))


app = webapp2.WSGIApplication([
  ('/data/timeline/cssanimated', AnimatedTimelineHandler),
  ('/data/timeline/csspopularity', PopularityTimelineHandler),
  ('/data/timeline/featurepopularity', FeatureObserverTimelineHandler),
  ('/data/csspopularity', CSSPopularityHandler),
  ('/data/cssanimated', CSSAnimatedHandler),
  ('/data/featurepopularity', FeatureObserverPopularityHandler),
  ('/data/blink/(.*)', FeatureBucketsHandler),
], debug=settings.DEBUG)
