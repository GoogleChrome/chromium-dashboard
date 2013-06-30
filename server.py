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


class MainHandler(common.ContentHandler):

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
      # Request was for an Atom feed.
      if path.endswith('.xml'):
        feature_list = models.Feature.get_all(
          limit=settings.RSS_FEED_LIMIT) # Memcached
        return self.render_atom_feed('Features', feature_list)
      else:
        feature_list = models.Feature.get_all() # Memcached
        template_data['features'] = json.dumps(feature_list)

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
