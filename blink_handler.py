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

  def __update_owners_list(self, add=True, user_id=None, blink_component=None):
    if not user_id or not blink_component:
      return False

    owner = models.FeatureOwner.get_by_id(long(user_id))
    if not owner:
      return True

    if add:
      owner.add_as_component_owner(blink_component)
    else:
      owner.remove_from_component_owners(blink_component)

    return True

  @common.require_whitelisted_user
  @common.strip_trailing_slash
  def get(self, path):
    components = models.BlinkComponent.all().order('name').fetch(None)
    owners = models.FeatureOwner.all().order('name').fetch(None)

    # Format for django template
    owners = [x.format_for_template() for x in owners]

    data = {
      'owners': owners,
      'components': components
    }

    self.render(data, template_path=os.path.join('admin/blink.html'))

  def put(self, path):
    params = json.loads(self.request.body)
    self.__update_owners_list(False, user_id=params.get('userId'),
                              blink_component=params.get('componentName'))
    self.response.set_status(200, message='User removed from owners')
    return self.response.write(json.dumps({'done': True}))

  def post(self, path):
    params = json.loads(self.request.body)
    self.__update_owners_list(True, user_id=params.get('userId'),
                              blink_component=params.get('componentName'))
    self.response.set_status(200, message='User added to owners')
    return self.response.write(json.dumps(params))


app = webapp2.WSGIApplication([
  ('(.*)', BlinkHandler),
], debug=settings.DEBUG)

