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

#from google.appengine.api import urlfetch
from google.appengine.api import users

import common
import models
import settings
import uma


def normalized_name(val):
  return val.lower().replace(' ', '').replace('/', '')


class MainHandler(common.ContentHandler, common.JSONHandler):

  def get(self, path):
    # Default to features page.
    # TODO: remove later when we want an index.html
    if not path:
      return self.redirect('/features')

    # Remove trailing slash from URL and redirect. e.g. /metrics/ -> /metrics
    if path[-1] == '/':
      return self.redirect(self.request.path.rstrip('/'))

    template_data = {}

    if path.startswith('features'):
      if path.endswith('.json'): # JSON request.
        feature_list = models.Feature.get_all() # Memcached
        return common.JSONHandler.get(self, feature_list, formatted=True)
      elif path.endswith('.xml'): # Atom feed request.
        filterby = None

        category = self.request.get('category', None)
        if category is not None:
          for k,v in models.FEATURE_CATEGORIES.iteritems():
            normalized = normalized_name(v)
            if category == normalized:
              filterby = ('category =', k)
              break

        feature_list = models.Feature.get_all( # Memcached
            limit=settings.RSS_FEED_LIMIT,
            filterby=filterby)

        return self.render_atom_feed('Features', feature_list)
      else:
        feature_list = models.Feature.get_all() # Memcached
        template_data['features'] = json.dumps(feature_list)
        template_data['categories'] = [
          (v, normalized_name(v)) for k,v in
          models.FEATURE_CATEGORIES.iteritems()]

    elif path == 'metrics/featurelevel':
      template_data['CSS_PROPERTY_BUCKETS'] = uma.CSS_PROPERTY_BUCKETS

    self.render(data=template_data, template_path=os.path.join(path + '.html'))


# Main URL routes.
routes = [
  ('/(.*)', MainHandler),
]

app = webapp2.WSGIApplication(routes, debug=settings.DEBUG)
app.error_handlers[404] = common.handle_404
if settings.PROD and not settings.DEBUG:
  app.error_handlers[500] = common.handle_500
