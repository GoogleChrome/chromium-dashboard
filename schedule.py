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


# import datetime
import json
import logging
import os
# import re
# import sys
import webapp2
# import xml.dom.minidom

# Appengine imports.
# import cloudstorage
# from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import users
# from google.appengine.ext import blobstore
# from google.appengine.ext import db
# from google.appengine.ext.webapp import blobstore_handlers

# File imports.
import common
# import models
import settings


def fetch_chrome_release_info(version):
  url = 'https://chromepmo.appspot.com/schedule/mstone/json?mstone=%s' % version
  result = urlfetch.fetch(url)
  if result.status_code == 200:
    return json.loads(result.content)['mstones']
  return None

def get_omaha_data(host):
  result = urlfetch.fetch('%s/omaha_data' % host)
  if result.status_code == 200:
    return json.loads(result.content)
  return None


class ScheduleHandler(common.ContentHandler):

  def get(self, path):
    user = users.get_current_user()
    if not self._is_user_whitelisted(user):
      common.handle_401(self.request, self.response, Exception)
      return

    data = {
      'versions': json.dumps(get_omaha_data(self.request.host_url)),
      'release': fetch_chrome_release_info(58)
    }

    self.render(data, template_path=os.path.join(path + '.html'))
    # self.response.out.write('here')


app = webapp2.WSGIApplication([
  ('/(.*)', ScheduleHandler),
], debug=settings.DEBUG)

