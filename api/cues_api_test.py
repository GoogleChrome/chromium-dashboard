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

import testing_config  # Must be imported before the module under test.

import flask
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import cues_api
from internals import models

test_app = flask.Flask(__name__)


class CuesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.user_pref_1 = models.UserPref(
        email='one@example.com',
        notify_as_starrer=False)
    self.user_pref_1.put()

    self.user_pref_2 = models.UserPref(
        email='two@example.com',
        notify_as_starrer=False,
        dismissed_cues=['progress-checkmarks'])
    self.user_pref_2.put()

    self.request_path = '/api/v0/currentuser/cues'
    self.handler = cues_api.CuesAPI()

  def tearDown(self):
    self.user_pref_1.key.delete()
    self.user_pref_2.key.delete()
    testing_config.sign_out()

  def test_post__valid(self):
    """User wants to dismiss a valid cue card ID."""
    testing_config.sign_in('one@example.com', 123567890)

    with test_app.test_request_context(
        '/cues/dismiss', json={"cue": "progress-checkmarks"}):
      actual_json = self.handler.do_post()
    self.assertEqual({'message': 'Done'}, actual_json)

    revised_user_pref = models.UserPref.get_signed_in_user_pref()
    self.assertEqual(['progress-checkmarks'], revised_user_pref.dismissed_cues)

  def test_post__invalid(self):
    """User wants to dismiss an invalid cue card ID."""
    testing_config.sign_in('one@example.com', 123567890)

    with test_app.test_request_context(
        '/cues/dismiss', json={"cue": "xyz"}):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    # The invalid string should not be added.
    revised_user_pref = models.UserPref.get_signed_in_user_pref()
    self.assertEqual([], revised_user_pref.dismissed_cues)

  def test_get__anon(self):
    """Anon should always have an empty list of dismissed cues."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    self.assertEqual([], actual_response)

  def test_get__signed_in(self):
    """Signed-in user has dismissed a cue."""
    testing_config.sign_in('two@example.com', 123567890)
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    self.assertEqual(['progress-checkmarks'], actual_response)
    