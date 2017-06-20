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

import json
import logging
import os
import webapp2

# Appengine imports.
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import users

import common
import models
import settings
import util


class BlinkHandler(common.ContentHandler):

  @common.require_whitelisted_user
  @common.strip_trailing_slash
  def get(self, path):
    # components = models.BlinkComponent.fetch_all_components()
    # for f in features:
      # milesstone = f.get('meta').get('milestone_str')
    #  print f.get('impl_status_chrome')

    components = models.BlinkComponent.all().fetch(None)
    owners = models.FeatureOwner.all().fetch(None)

    owners = [x.format_for_template() for x in sorted(owners, key=lambda o: o.name)]

    data = {
      #'components': components #json.dumps(components),json.dumps(components),
      'owners': owners,
      'components': sorted(components, key=lambda c: c.name)
    }

    self.render(data, template_path=os.path.join('admin/blink.html'))


app = webapp2.WSGIApplication([
  ('(.*)', BlinkHandler),
], debug=settings.DEBUG)

