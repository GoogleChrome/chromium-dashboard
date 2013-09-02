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

from google.appengine.api import memcache

import common
import models
import settings


class StableInstances(common.JSONHandler):

  def get(self):
    try:
      bucket_id = int(self.request.get('bucket_id'))
    except:
      return super(StableInstances, self).get([])

    query = models.StableInstance.all()
    query.filter('bucket_id =', bucket_id)
    query.order('date')

    # All matching results.
    data = query.fetch(None)

    super(StableInstances, self).get(data)


class QueryStackRank(common.JSONHandler):

  MEMCACHE_KEY = 'css_popularity'

  def get(self):
    css_popularity = memcache.get(self.MEMCACHE_KEY)
    if css_popularity is None:
      # Find last date data was fetched by pulling one entry.
      result = models.StableInstance.all().order('-date').get()

      css_popularity = []

      if result:
        query = models.StableInstance.all()
        query.filter('date =', result.date)
        query.order('-day_percentage')
        css_popularity = query.fetch(None) # All matching results.
      
        memcache.set(self.MEMCACHE_KEY, css_popularity, time=86400) # cache for 24hrs.

    super(QueryStackRank, self).get(css_popularity)


app = webapp2.WSGIApplication([
  ('/data/querystableinstances', StableInstances),
  ('/data/querystackrank', QueryStackRank)
], debug=settings.DEBUG)
