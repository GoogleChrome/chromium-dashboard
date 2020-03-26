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

  @common.strip_trailing_slash
  def get(self, path):
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


class SettingsHandler(common.ContentHandler):

  def load_user_pref(self):
    """Return a UserPref for the signed in user or None if anon."""
    signed_in_user = users.get_current_user()
    if not signed_in_user:
      return None

    user_pref_list = models.UserPref.all().filter(
        'email =', signed_in_user.email()).fetch(1)
    if user_pref_list:
      user_pref = user_pref_list[0]
    else:
      user_pref = models.UserPref(email=signed_in_user.email())
    return user_pref

  def get(self):
    user_pref = self.load_user_pref()
    if not user_pref:
      return self.redirect(users.create_login_url(self.request.uri))

    template_data = {
        'user_pref': user_pref,
        'user_pref_form': models.UserPrefForm(user_pref.to_dict()),
    }

    self.render(data=template_data, template_path=os.path.join('settings.html'))

  def post(self):
    user_pref = self.load_user_pref()
    if not user_pref:
      self.abort(403)

    new_notify = self.request.get('notify_as_starrer')
    logging.info('setting notify_as_starrer for %r to %r',
                 user_pref.email, new_notify)
    user_pref.notify_as_starrer = bool(new_notify)
    user_pref.put()
    return self.redirect(self.request.uri)


app = webapp2.WSGIApplication([
  ('/settings', SettingsHandler),
  ('/(.*)/([0-9]*)', UserHandler),
  ('/(.*)', UserHandler),
], debug=settings.DEBUG)
