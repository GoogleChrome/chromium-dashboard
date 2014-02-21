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


#import datetime
import json
import logging
import os
import webapp2

# App Engine imports.
from google.appengine.api import users
from google.appengine.ext import db

import common
import models
import settings


class UserHandler(common.ContentHandler):

  def get(self, path):
    # Remove trailing slash from URL and redirect. e.g. /users/ -> /users
    if path[-1] == '/':
      return self.redirect(self.request.path.rstrip('/'))

    users = models.AppUser.all().fetch(None) # TODO(ericbidelman): memcache this.

    user_list = [user.format_for_template() for user in users]

    template_data = {
      'users': json.dumps(user_list)
    }

    self.render(data=template_data, template_path=os.path.join(path + '.html'))

  def post(self, path, user_id=None):
    if user_id:
      self._delete(user_id)
      self.redirect('/admin/users/new')
      return

    email = self.request.get('email')

    # Don't add a duplicate email address.
    user = models.AppUser.all(keys_only=True).filter('email = ', email).get()
    if not user:
      user = models.AppUser(email=db.Email(email))
      user.put()

      self.response.set_status(201, message='Created user')
      self.response.headers['Content-Type'] = 'application/json;charset=utf-8'
      return self.response.write(json.dumps(user.format_for_template()))
    else:
      self.response.set_status(200, message='User already exists')
      self.response.write(json.dumps({'id': user.id()}))

  def _delete(self, user_id):
    if user_id:
      found_user = models.AppUser.get_by_id(long(user_id))
      if found_user:
        found_user.delete()


app = webapp2.WSGIApplication([
  ('/(.*)/([0-9]*)', UserHandler),
  ('/(.*)', UserHandler),
], debug=settings.DEBUG)

