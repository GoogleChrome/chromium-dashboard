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


#import datetime
import json
import logging
import os

# App Engine imports.
from google.appengine.api import users
from google.appengine.ext import db

import flask

import common
import models
import settings


class UserListHandler(common.FlaskContentHandler):

  @common.strip_trailing_slash
  def get_template_data(self, path):
    users = models.AppUser.all().fetch(None) # TODO(ericbidelman): ramcache this.

    user_list = [user.format_for_template() for user in users]

    template_data = {
      'users': json.dumps(user_list)
    }
    return template_data


class UserAPI(common.FlaskContentHandler):

  def process_post_data(self, path, user_id=None):
    if user_id:
      self._delete(user_id)
      return {'deleted': user_id}

    email = flask.request.get('email')

    # Don't add a duplicate email address.
    user = models.AppUser.all(keys_only=True).filter('email = ', email).get()
    if not user:
      user = models.AppUser(email=db.Email(email))
      user.put()

      response_json = user.format_for_template()
      response_json['message'] = 'Created user'
    else:
      response_json = {
          'message': 'User already exists',
          'id': user.id()}

    return response_json

  def _delete(self, user_id):
    if user_id:
      found_user = models.AppUser.get_by_id(long(user_id))
      if found_user:
        found_user.delete()


class SettingsHandler(common.FlaskContentHandler):

  TEMPLATE_PATH = 'settings.html'

  def get_template_data(self):
    user_pref = models.UserPref.get_signed_in_user_pref()
    if not user_pref:
      return flask.redirect(users.create_login_url(self.request.uri))

    template_data = {
        'user_pref': user_pref,
        'user_pref_form': models.UserPrefForm(user_pref.to_dict()),
    }
    return template_data

  def process_post_data(self):
    user_pref = models.UserPref.get_signed_in_user_pref()
    if not user_pref:
      flask.abort(403)

    new_notify = flask.request.get('notify_as_starrer')
    logging.info('setting notify_as_starrer for %r to %r',
                 user_pref.email, new_notify)
    user_pref.notify_as_starrer = bool(new_notify)
    user_pref.put()
    return flask.redirect(flask.request.path)


app = common.FlaskApplication([
  ('/settings', SettingsHandler),
  ('/(.*)/([0-9]*)', UserHandler),
  ('/(.*)', UserHandler),
], debug=settings.DEBUG)
