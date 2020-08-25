# -*- coding: utf-8 -*-
# Copyright 2020 Google Inc.
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

import logging
import json
import webapp2

from google.appengine.ext import db
from google.appengine.api import users

from django.template.loader import render_to_string

import common
import models
import settings


# We only accept known cue name strings.
ALLOWED_CUES = ['progress-checkmarks']


class DismissCueHandler(webapp2.RequestHandler):
  """Handle JSON API requests to dismiss an on-page help cue card."""

  def post(self):
    """Dismisses a cue card for the signed in user."""
    json_body = json.loads(self.request.body)
    cue = json_body.get('cue')
    if cue not in ALLOWED_CUES:
      logging.info('Unexpected cue: %r', cue)
      self.abort(400)

    user = users.get_current_user()
    if not user:
      logging.info('User must be signed in before dismissing cues')
      self.abort(400)

    models.UserPref.dismiss_cue(cue)
    data = {}
    self.response.headers['Content-Type'] = 'application/json;charset=utf-8'
    result = self.response.write(json.dumps(data, separators=(',',':')))


app = webapp2.WSGIApplication([
  ('/cues/dismiss', DismissCueHandler),
], debug=settings.DEBUG)
