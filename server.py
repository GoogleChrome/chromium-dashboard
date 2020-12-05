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

import json
import logging
import os
import webapp2

import settings
import common
import guideforms
import models
import processes
import ramcache
import util

from google.appengine.api import users

import http2push.http2push as http2push


def normalized_name(val):
  return val.lower().replace(' ', '').replace('/', '')


class FeatureDetailHandler(common.ContentHandler):

  def get(self, feature_id):
    ramcache.check_for_distributed_invalidation()
    f = models.Feature.get_by_id(long(feature_id))
    if f is None:
      self.abort(404)

    feature_process = processes.ALL_PROCESSES.get(
        f.feature_type, processes.BLINK_LAUNCH_PROCESS)
    field_defs = guideforms.DISPLAY_FIELDS_IN_STAGES
    template_data = {
        'process_json': json.dumps(processes.process_to_dict(feature_process)),
        'field_defs_json': json.dumps(field_defs),
        'feature': f.format_for_template(),
        'feature_id': f.key().id,
        'feature_json': json.dumps(f.format_for_template()),
        'updated_display': f.updated.strftime("%Y-%m-%d"),
    }

    self._add_common_template_values(template_data)
    self.render(data=template_data, template_path='feature.html')


class MainHandler(http2push.PushHandler, common.ContentHandler, common.JSONHandler):

  def get(self, path, feature_id=None):
    ramcache.check_for_distributed_invalidation()
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
      omaha_data = util.get_omaha_data()
      return common.JSONHandler.get(self, omaha_data, formatted=True)

    if path.startswith('metrics/'):
      push_urls = http2push.use_push_manifest('push_manifest_metrics.json')

    # Add Link rel=preload header for h2 push on .html file requests.
    if push_urls:
      self.response.headers.add_header(
          'Link', self._generate_link_preload_headers(push_urls))

    self.render(data=template_data, template_path=os.path.join(path + '.html'))


class FeaturesAPIHandler(common.JSONHandler):

  def get(self, version=None):
    ramcache.check_for_distributed_invalidation()
    if version is None:
      version = 2
    else:
      version = int(version)

    user = users.get_current_user()
    feature_list = models.Feature.get_chronological(
        version=version, show_unlisted=self.user_can_edit(user))
    return common.JSONHandler.get(
        self, feature_list, formatted=True, public=False)


class SamplesHandler(common.ContentHandler, common.JSONHandler):

  def get(self, path=None):
    ramcache.check_for_distributed_invalidation()
    feature_list = models.Feature.get_shipping_samples() # Memcached

    if path == '/':
      return self.redirect(self.request.path.rstrip('/'))

    template_data = {}

    if path and path.endswith('.json'): # JSON request.
      return common.JSONHandler.get(self, feature_list, formatted=True)
    elif path and path.endswith('.xml'): # Atom feed request.
      # Support setting larger-than-default Atom feed sizes so that web
      # crawlers can use this as a full site feed.
      try:
        max_items = int(self.request.get('max-items',
                                          settings.RSS_FEED_LIMIT))
      except TypeError:
        max_items = settings.RSS_FEED_LIMIT

      return self.render_atom_feed('Samples', feature_list)

    template_data['FEATURES'] = json.dumps(feature_list, separators=(',',':'))
    template_data['CATEGORIES'] = [
      (v, normalized_name(v)) for k,v in
      models.FEATURE_CATEGORIES.iteritems()]
    template_data['categories'] = dict([
      (v, normalized_name(v)) for k,v in
      models.FEATURE_CATEGORIES.iteritems()])

    return self.render(data=template_data, template_path=os.path.join('samples.html'))


# Main URL routes.
routes = [
  (r'/features(?:_v(\d+))?.json', FeaturesAPIHandler),
  ('/samples(.*)', SamplesHandler),
  ('/feature/([0-9]*)', FeatureDetailHandler),
  ('/(.*)/([0-9]*)', MainHandler),
  ('/(.*)', MainHandler),
]

app = webapp2.WSGIApplication(routes, debug=settings.DEBUG)

app.error_handlers[404] = common.handle_404

if settings.PROD and not settings.DEBUG:
  app.error_handlers[500] = common.handle_500
