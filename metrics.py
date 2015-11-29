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

from datetime import timedelta
from google.appengine.api import memcache

import common
import models
import settings


CACHE_AGE = 86400 # 24hrs


class TimelineHandler(common.JSONHandler):

  def get(self):
    try:
      bucket_id = int(self.request.get('bucket_id'))
    except:
      return super(self.MODEL_CLASS, self).get([])

    KEY = '%s|%s' % (self.MEMCACHE_KEY, bucket_id)

    data = memcache.get(KEY)
    if data is None:
      query = self.MODEL_CLASS.all()
      query.filter('bucket_id =', bucket_id)
      query.order('date')
      data = query.fetch(None) # All matching results.

      # Remove outliers if percentage is not between 0-1.
      data = filter(lambda x: 0 <= x.day_percentage <= 1, data)

      # Remove one time peaks where delta is more than 10%.
      threshold = 0.1
      last_percentage = None
      for x in list(data):
        if last_percentage and (abs(x.day_percentage - last_percentage) > threshold):
          data.remove(x)
        last_percentage = x.day_percentage

      memcache.set(KEY, data, time=CACHE_AGE)

    data = self._clean_data(data)
    super(TimelineHandler, self).get(data)


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

  def get(self):
    properties = memcache.get(self.MEMCACHE_KEY)

    if properties is None:
      # Find last date data was fetched by pulling one entry.
      result = self.MODEL_CLASS.all().order('-date').get()

      properties = []

      if result:
        query = self.MODEL_CLASS.all()
        query.filter('date =', result.date)
        query.order('-day_percentage')
        properties = query.fetch(None) # All matching results.

        # Go another day back if if data looks invalid.
        if (properties[0].day_percentage < 0 or
            properties[0].day_percentage > 1):
          query = self.MODEL_CLASS.all()
          query.filter('date =', result.date - timedelta(days=1))
          query.order('-day_percentage')
          properties = query.fetch(None)

        memcache.set(self.MEMCACHE_KEY, properties, time=CACHE_AGE)

    properties = self._clean_data(properties)
    super(FeatureHandler, self).get(properties)


class CSSPopularityHandler(FeatureHandler):

  MEMCACHE_KEY = 'css_popularity'
  MODEL_CLASS = models.StableInstance

  def get(self):
    super(CSSPopularityHandler, self).get()


class CSSAnimatedHandler(FeatureHandler):

  MEMCACHE_KEY = 'css_animated'
  MODEL_CLASS = models.AnimatedProperty

  def get(self):
    super(CSSAnimatedHandler, self).get()


class FeatureObserverPopularityHandler(FeatureHandler):

  MEMCACHE_KEY = 'featureob_popularity'
  MODEL_CLASS = models.FeatureObserver

  def get(self):
    super(FeatureObserverPopularityHandler, self).get()


app = webapp2.WSGIApplication([
  ('/data/timeline/cssanimated', AnimatedTimelineHandler),
  ('/data/timeline/csspopularity', PopularityTimelineHandler),
  ('/data/timeline/featurepopularity', FeatureObserverTimelineHandler),
  ('/data/csspopularity', CSSPopularityHandler),
  ('/data/cssanimated', CSSAnimatedHandler),
  ('/data/featurepopularity', FeatureObserverPopularityHandler),
], debug=settings.DEBUG)
