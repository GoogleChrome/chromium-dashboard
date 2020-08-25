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

import unittest
import testing_config  # Must be imported before the module under test.

import mock
import webapp2
from webob import exc

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import users

import cues
import models
import settings


class DismissCueHandlerTest(unittest.TestCase):

  def setUp(self):
    self.user_pref_1 = models.UserPref(
        email='one@example.com',
        notify_as_starrer=False)
    self.user_pref_1.put()
    self.handler = cues.DismissCueHandler()
    self.handler.request = webapp2.Request.blank('/features/star/set')
    self.handler.response = webapp2.Response()

  def tearDown(self):
    self.user_pref_1.delete()

  def test_post__valid(self):
    """User wants to dismiss a valid cue card ID."""
    testing_config.sign_in('one@example.com', 123567890)

    self.handler.request.body = '{"cue": "progress-checkmarks"}'
    self.handler.post()

    revised_user_pref = models.UserPref.get_signed_in_user_pref()
    self.assertEqual(['progress-checkmarks'], revised_user_pref.dismissed_cues)

  def test_post__invalid(self):
    """User wants to dismiss an invalid cue card ID."""
    testing_config.sign_in('one@example.com', 123567890)

    self.handler.request.body = '{"cue": "xyz"}'
    with self.assertRaises(exc.HTTPClientError):
        self.handler.post()

    # The invalid string should not be added.
    revised_user_pref = models.UserPref.get_signed_in_user_pref()
    self.assertEqual([], revised_user_pref.dismissed_cues)
