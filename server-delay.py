# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc.
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

import time
import webapp2

from google.appengine.api import urlfetch

import common
import settings


class DelayHandler(common.ContentHandler):

  def get(self):
    delay = self.request.get('seconds') or 0
    url = self.request.get('url')

    if url is None:
      return self.response.write('No URL')

    time.sleep(int(delay))

    result = urlfetch.fetch(url)
    if result.status_code == 200:
      if url.endswith('.js'):
        self.response.headers.add_header('Content-Type', 'application/json')
      elif url.endswith('.css'):
        self.response.headers.add_header('Content-Type', 'text/css')
      self.response.write(result.content)
    else:
      self.abort('500')

routes = [('/delay', DelayHandler)]

app = webapp2.WSGIApplication(routes, debug=settings.DEBUG)

app.error_handlers[404] = common.handle_404

if settings.PROD and not settings.DEBUG:
  app.error_handlers[500] = common.handle_500
