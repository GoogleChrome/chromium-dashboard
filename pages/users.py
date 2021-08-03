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
import os

import flask

from framework import basehandlers
from framework import loggging
from framework import permissions
from internals import models
import settings

LOGIN_PAGE_URL = '/features?loginStatus=False'


class UserListHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'admin/users/new.html'

  @permissions.require_admin_site
  def get_template_data(self):
    users = models.AppUser.query().fetch(None) # TODO(ericbidelman): ramcache this.

    user_list = [user.format_for_template() for user in users]

    logging.info('user_list is %r', user_list)
    template_data = {
      'users': json.dumps(user_list)
    }
    return template_data


class SettingsHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'settings.html'

  def get_template_data(self):
    user_pref = models.UserPref.get_signed_in_user_pref()
    if not user_pref:
      return flask.redirect(LOGIN_PAGE_URL)

    template_data = {
        'user_pref': user_pref,
        'user_pref_form': models.UserPrefForm(user_pref.to_dict()),
    }
    return template_data

  def process_post_data(self):
    user_pref = models.UserPref.get_signed_in_user_pref()
    if not user_pref:
      self.abort(403, msg='User must be signed in')

    new_notify = flask.request.form.get('notify_as_starrer')
    logging.info('setting notify_as_starrer for %r to %r',
                 user_pref.email, new_notify)
    user_pref.notify_as_starrer = bool(new_notify)
    user_pref.put()
    return flask.redirect(flask.request.path)


app = basehandlers.FlaskApplication([
  ('/settings', SettingsHandler),
  ('/admin/users/new', UserListHandler),
], debug=settings.DEBUG)
