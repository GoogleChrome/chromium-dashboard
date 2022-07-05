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
import werkzeug.exceptions

from api import settings_api
from internals import models

test_app = flask.Flask(__name__)


class SettingsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.user_pref_1 = models.UserPref(
        email='one@example.com',
        notify_as_starrer=False,
        dismissed_cues=['progress-checkmarks'])
    self.user_pref_1.put()

    self.request_path = '/api/v0/currentuser/settings'
    self.handler = settings_api.SettingsAPI()

  def tearDown(self):
    self.user_pref_1.key.delete()
    testing_config.sign_out()

  def test_post__valid(self):
    """User wants to set a valid setting."""
    testing_config.sign_in('one@example.com', 123567890)

    with test_app.test_request_context(
        '/notify', json={"notify": True}):
      actual_json = self.handler.do_post()
    self.assertEqual({'message': 'Done'}, actual_json)

    revised_user_pref = models.UserPref.get_signed_in_user_pref()
    self.assertEqual(True, revised_user_pref.notify_as_starrer)

  def test_post__invalid(self):
    """User wants to set an invalid setting."""
    testing_config.sign_in('one@example.com', 123567890)

    with test_app.test_request_context(
        '/notify', json={"notify": "xyz"}):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    # The invalid string should not be added.
    revised_user_pref = models.UserPref.get_signed_in_user_pref()
    self.assertEqual(False, revised_user_pref.notify_as_starrer)

  def test_get__anon(self):
    """We give 404 if the user preference was not found."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_get()

  def test_get__signed_in(self):
    """Signed-in user has a notify_as_starrer=False setting."""
    testing_config.sign_in('one@example.com', 123567890)
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get()
    self.assertEqual({'notify_as_starrer': False}, actual)
