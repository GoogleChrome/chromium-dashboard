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

import json
import logging
import os
import webapp2

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import users

import common
import models
import settings


def normalized_name(val):
  return val.lower().replace(' ', '').replace('/', '')

def first_of_milestone(feature_list, milestone, start=0):
  for i in xrange(start, len(feature_list)):
    f = feature_list[i]
    if (str(f['shipped_milestone']) == str(milestone) or
        f['impl_status_chrome'] == str(milestone)):
      return i
  return -1

  
class MainHandler(common.ContentHandler, common.JSONHandler):

  def __get_omaha_data(self):
    omaha_data = memcache.get('omaha_data')
    if omaha_data is None:
      result = urlfetch.fetch('https://omahaproxy.appspot.com/all.json')
      if result.status_code == 200:
        omaha_data = json.loads(result.content)
        memcache.set('omaha_data', omaha_data, time=86400) # cache for 24hrs.

    return omaha_data

  def __annotate_first_of_milestones(self, feature_list):
    try:
      omaha_data = self.__get_omaha_data()

      win_versions = omaha_data[0]['versions']
      for v in win_versions:
        s = v.get('version') or v.get('prev_version')
        LATEST_VERSION = int(s.split('.')[0])
        break

      # TODO(ericbidelman) - memcache this calculation as part of models.py
      milestones = range(1, LATEST_VERSION + 1)
      milestones.reverse()
      versions = [
        models.IMPLEMENTATION_STATUS[models.NO_ACTIVE_DEV],
        models.IMPLEMENTATION_STATUS[models.PROPOSED],
        models.IMPLEMENTATION_STATUS[models.IN_DEVELOPMENT],
        ]
      versions.extend(milestones)
      versions.append(models.IMPLEMENTATION_STATUS[models.NO_LONGER_PURSUING])

      last_good_idx = 0
      for i, version in enumerate(versions):
        idx = first_of_milestone(feature_list, version, start=last_good_idx)
        if idx != -1:
          feature_list[idx]['first_of_milestone'] = True
          last_good_idx = idx
    except Exception as e:
      logging.error(e)

  def __get_feature_list(self):
    feature_list = models.Feature.get_chronological() # Memcached
    self.__annotate_first_of_milestones(feature_list)
    return feature_list

  def get(self, path, feature_id=None):
    # Default to features page.
    # TODO: remove later when we want an index.html
    if not path:
      return self.redirect('/features')

    # Default /metrics to CSS ranking.
    # TODO: remove later when we want /metrics/index.html
    if path == 'metrics' or path == 'metrics/css':
      return self.redirect('/metrics/css/popularity')

    # Remove trailing slash from URL and redirect. e.g. /metrics/ -> /metrics
    if feature_id == '':
      return self.redirect(self.request.path.rstrip('/'))

    template_data = {}

    if path.startswith('features'):
      if path.endswith('.json'): # JSON request.
        feature_list = self.__get_feature_list()
        return common.JSONHandler.get(self, feature_list, formatted=True)
      elif path.endswith('.xml'): # Atom feed request.
        filterby = None

        category = self.request.get('category', None)

        # Support setting larger-than-default Atom feed sizes so that web
        # crawlers can treat use this as a full site feed.
        try:
          max_items = int(self.request.get('max-items',
                                           settings.RSS_FEED_LIMIT))
        except TypeError:
          max_items = settings.RSS_FEED_LIMIT

        if category is not None:
          for k,v in models.FEATURE_CATEGORIES.iteritems():
            normalized = normalized_name(v)
            if category == normalized:
              filterby = ('category =', k)
              break

        feature_list = models.Feature.get_all( # Memcached
            limit=max_items,
            filterby=filterby,
            order='-updated')

        return self.render_atom_feed('Features', feature_list)
      else:
        # if settings.PROD: 
        #   feature_list = self.__get_feature_list()
        # else:
        #   result = urlfetch.fetch(
        #     self.request.scheme + '://' + self.request.host +
        #     '/static/js/mockdata.json')
        #   feature_list = json.loads(result.content)

        # template_data['features'] = json.dumps(
        #     feature_list, separators=(',',':'))

        template_data['categories'] = [
          (v, normalized_name(v)) for k,v in
          models.FEATURE_CATEGORIES.iteritems()]
        template_data['IMPLEMENTATION_STATUSES'] = [
          {'key': k, 'val': v} for k,v in
          models.IMPLEMENTATION_STATUS.iteritems()]
        template_data['VENDOR_VIEWS'] = [
          {'key': k, 'val': v} for k,v in
          models.VENDOR_VIEWS.iteritems()]
        template_data['WEB_DEV_VIEWS'] = [
          {'key': k, 'val': v} for k,v in
          models.WEB_DEV_VIEWS.iteritems()]
        template_data['STANDARDS_VALS'] = [
          {'key': k, 'val': v} for k,v in
          models.STANDARDIZATION.iteritems()]
    elif path.startswith('feature'):
      feature = None
      try:
        feature = models.Feature.get_feature(int(feature_id))
      except TypeError:
        pass
      if feature is None:
        self.abort(404)

      template_data['feature'] = feature
    elif path.startswith('metrics/css/timeline'):
      properties = sorted(models.CssPropertyHistogram.get_all().iteritems(), key=lambda x:x[1])
      template_data['CSS_PROPERTY_BUCKETS'] = json.dumps(
          properties, separators=(',',':'))
    elif path.startswith('metrics/feature/timeline'):
      properties = sorted(models.FeatureObserverHistogram.get_all().iteritems(), key=lambda x:x[1])
      template_data['FEATUREOBSERVER_BUCKETS'] = json.dumps(
          properties, separators=(',',':'))

    self.render(data=template_data, template_path=os.path.join(path + '.html'))


# Main URL routes.
routes = [
  ('/(.*)/([0-9]*)', MainHandler),
  ('/(.*)', MainHandler),
]

app = webapp2.WSGIApplication(routes, debug=settings.DEBUG)
app.error_handlers[404] = common.handle_404
if settings.PROD and not settings.DEBUG:
  app.error_handlers[500] = common.handle_500
