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
      return self.redirect('/' + path.rstrip('/'))

    template_data = {}

    user = users.get_current_user()
    if user:
      template_data['login'] = ('Logout',
                                users.create_logout_url(dest_url=path))
      template_data['user'] = {
        'is_admin': users.is_current_user_admin(),
        'nickname': user.nickname(),
        'email': user.email(),
      }
    else:
      template_data['user'] = None
      template_data['login'] = ('Login', users.create_login_url(dest_url=path))

    if path == 'features':
      # TODO(ericbidelman): memcache the crap out of this.
      # All matching results.
      features = models.Feature.all().fetch(None)

      feature_list = []
      for f in features:
        d = models.Feature.format_for_template(f)
        feature_list.append(d)

      template_data['features'] = json.dumps(feature_list)

      #http://omahaproxy.appspot.com/all.json

    elif path == 'metrics/featurelevel':
      template_data['CSS_PROPERTY_BUCKETS'] = uma.CSS_PROPERTY_BUCKETS

    template_file = path + '.html'

    self.render(data=template_data, template_path=os.path.join(template_file))


# Main URL routes.
routes = [
  ('/(.*)', MainHandler),
]

app = webapp2.WSGIApplication(routes, debug=settings.DEBUG)
app.error_handlers[404] = common.handle_404
if settings.PROD and not settings.DEBUG:
  app.error_handlers[500] = common.handle_500
