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

import http2push.http2push as http2push


def normalized_name(val):
  return val.lower().replace(' ', '').replace('/', '')

def first_of_milestone(feature_list, milestone, start=0):
  for i in xrange(start, len(feature_list)):
    f = feature_list[i]
    if (str(f['shipped_milestone']) == str(milestone) or
        f['impl_status_chrome'] == str(milestone)):
      return i
    elif (f['shipped_milestone'] == None and
          str(f['shipped_android_milestone']) == str(milestone)):
      return i

  return -1

def first_of_milestone_v2(feature_list, milestone, start=0):
  for i in xrange(start, len(feature_list)):
    f = feature_list[i]
    desktop_milestone = f['browsers']['chrome'].get('desktop', None)
    android_milestone = f['browsers']['chrome'].get('android', None)
    status = f['browsers']['chrome']['status'].get('text', None)

    if (str(desktop_milestone) == str(milestone) or status == str(milestone)):
      return i
    elif (desktop_milestone == None and str(android_milestone) == str(milestone)):
      return i

  return -1

def get_omaha_data():
  omaha_data = memcache.get('omaha_data')
  if omaha_data is None:
    result = urlfetch.fetch('https://omahaproxy.appspot.com/all.json')
    if result.status_code == 200:
      omaha_data = json.loads(result.content)
      memcache.set('omaha_data', omaha_data, time=86400) # cache for 24hrs.

  return omaha_data

def annotate_first_of_milestones(feature_list, version=None):
  try:
    omaha_data = get_omaha_data()

    win_versions = omaha_data[0]['versions']

    # Find the latest canary major version from the list of windows versions.
    canary_versions = [x for x in win_versions if x.get('channel') and x.get('channel').startswith('canary')]
    LATEST_VERSION = int(canary_versions[0].get('version').split('.')[0])

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

    first_of_milestone_func = first_of_milestone
    if version == 2:
      first_of_milestone_func = first_of_milestone_v2

    last_good_idx = 0
    for i, ver in enumerate(versions):
      idx = first_of_milestone_func(feature_list, ver, start=last_good_idx)
      if idx != -1:
        feature_list[idx]['first_of_milestone'] = True
        last_good_idx = idx
  except Exception as e:
    logging.error(e)


class MainHandler(http2push.PushHandler, common.ContentHandler, common.JSONHandler):

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
    push_urls = [] # URLs to push in this response.

    template_data['embed'] = self.request.get('embed', None) is not None

    if path.startswith('features'):
      if path.endswith('.xml'): # Atom feed request.
        status = self.request.get('status', None)
        if status:
          feature_list = models.Feature.get_all_with_statuses(status.split(','))
        else:
          filterby = None
          category = self.request.get('category', None)

          # Support setting larger-than-default Atom feed sizes so that web
          # crawlers can use this as a full site feed.
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
        template_data['categories'] = [
          (v, normalized_name(v)) for k,v in
          models.FEATURE_CATEGORIES.iteritems()]
        template_data['IMPLEMENTATION_STATUSES'] = json.dumps([
          {'key': k, 'val': v} for k,v in
          models.IMPLEMENTATION_STATUS.iteritems()])
        template_data['VENDOR_VIEWS'] = json.dumps([
          {'key': k, 'val': v} for k,v in
          models.VENDOR_VIEWS.iteritems()])
        template_data['WEB_DEV_VIEWS'] = json.dumps([
          {'key': k, 'val': v} for k,v in
          models.WEB_DEV_VIEWS.iteritems()])
        template_data['STANDARDS_VALS'] = json.dumps([
          {'key': k, 'val': v} for k,v in
          models.STANDARDIZATION.iteritems()])
        template_data['TEMPLATE_CACHE_TIME'] = settings.TEMPLATE_CACHE_TIME

        push_urls = http2push.use_push_manifest('push_manifest_features.json')

    elif path.startswith('feature'):
      feature = None
      try:
        feature = models.Feature.get_feature(int(feature_id))
      except TypeError:
        pass
      if feature is None:
        self.abort(404)

      was_updated = False
      if self.request.referer:
        was_updated = (self.request.referer.endswith('/admin/features/new') or
                       '/admin/features/edit' in self.request.referer)

      template_data['feature'] = feature
      template_data['was_updated'] = was_updated

    elif path.startswith('metrics/css/timeline'):
      properties = sorted(
          models.CssPropertyHistogram.get_all().iteritems(), key=lambda x:x[1])
      template_data['CSS_PROPERTY_BUCKETS'] = json.dumps(
          properties, separators=(',',':'))
    elif path.startswith('metrics/feature/timeline'):
      properties = sorted(
          models.FeatureObserverHistogram.get_all().iteritems(), key=lambda x:x[1])
      template_data['FEATUREOBSERVER_BUCKETS'] = json.dumps(
          properties, separators=(',',':'))
    elif path.startswith('omaha_data'):
      omaha_data = get_omaha_data()
      return common.JSONHandler.get(self, omaha_data, formatted=True)
    elif path.startswith('samples'):
      feature_list = models.Feature.get_shipping_samples() # Memcached

      if path.endswith('.json'): # JSON request.
        return common.JSONHandler.get(self, feature_list, formatted=True)
      elif path.endswith('.xml'): # Atom feed request.
        # Support setting larger-than-default Atom feed sizes so that web
        # crawlers can use this as a full site feed.
        try:
          max_items = int(self.request.get('max-items',
                                           settings.RSS_FEED_LIMIT))
        except TypeError:
          max_items = settings.RSS_FEED_LIMIT

        return self.render_atom_feed('Samples', feature_list)
      else:
        template_data['FEATURES'] = json.dumps(feature_list, separators=(',',':'))
        template_data['CATEGORIES'] = [
          (v, normalized_name(v)) for k,v in
          models.FEATURE_CATEGORIES.iteritems()]
        template_data['categories'] = dict([
          (v, normalized_name(v)) for k,v in
          models.FEATURE_CATEGORIES.iteritems()])

    if path.startswith('metrics/'):
      push_urls = http2push.use_push_manifest('push_manifest_metrics.json')

    # Add Link rel=preload header for h2 push on .html file requests.
    if push_urls:
      self.response.headers.add_header(
          'Link', self._generate_link_preload_headers(push_urls))

    self.render(data=template_data, template_path=os.path.join(path + '.html'))


class FeaturesAPIHandler(common.JSONHandler):

  def __get_feature_list(self, version=None):
    feature_list = models.Feature.get_chronological(version=version) # Memcached
    annotate_first_of_milestones(feature_list, version=version)
    return feature_list

  def get(self, version=None):
    if version is None:
      version = 1
    else:
      version = int(version)

    KEY = '%s|v%s|all' % (models.Feature.DEFAULT_MEMCACHE_KEY, version)
    feature_list = memcache.get(KEY)
    if feature_list is None:
      feature_list = self.__get_feature_list(version)
      memcache.set(KEY, feature_list)
    return common.JSONHandler.get(self, feature_list, formatted=True)


# Main URL routes.
routes = [
  (r'/features(?:_v(\d+))?.json', FeaturesAPIHandler),
  ('/(.*)/([0-9]*)', MainHandler),
  ('/(.*)', MainHandler),
]

app = webapp2.WSGIApplication(routes, debug=settings.DEBUG)

app.error_handlers[404] = common.handle_404

if settings.PROD and not settings.DEBUG:
  app.error_handlers[500] = common.handle_500
