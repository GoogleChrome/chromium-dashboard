# Copyright 2022 Google Inc.
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

from unittest import mock

import flask
import werkzeug
import html5lib
import settings

from google.cloud import ndb  # type: ignore
from pages import blink_handler
from internals import user_models

test_app = flask.Flask(__name__,
  template_folder=settings.get_flask_template_path())

# Load testdata to be used across all of the CustomTestCases
TESTDATA = testing_config.Testdata(__file__)

class SubscribersTemplateTest(testing_config.CustomTestCase):

  HANDLER_CLASS = blink_handler.SubscribersHandler

  def setUp(self):
    # need to patch in setup because the details are retreived here.
    # unable to use method decorator for setUp.
    self.mock_chrome_details_patch = mock.patch(
      'pages.blink_handler.construct_chrome_channels_details')
    mock_chrome_details = self.mock_chrome_details_patch.start()
    mock_chrome_details.return_value = {
      "stable": {"mstone": 1},
      "beta": {"mstone": 2},
      "dev": {"mstone": 3},
      "canary": {"mstone": 4},
    }

    self.request_path = self.HANDLER_CLASS.TEMPLATE_PATH
    self.handler = self.HANDLER_CLASS()

    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

    testing_config.sign_in('admin@example.com', 123567890)

    self.component_1 = user_models.BlinkComponent(name='Blink')
    self.component_1.put()
    self.component_2 = user_models.BlinkComponent(name='Blink>Accessibility')
    self.component_2.put()
    self.component_owner_1 = user_models.FeatureOwner(
        name='owner_1', email='owner_1@example.com',
        primary_blink_components=[self.component_1.key, self.component_2.key])
    self.component_owner_1.key = ndb.Key('FeatureOwner', 111)
    self.component_owner_1.put()
    self.watcher_1 = user_models.FeatureOwner(
        name='watcher_1', email='watcher_1@example.com',
        watching_all_features=True)
    self.watcher_1.key = ndb.Key('FeatureOwner', 222)
    self.watcher_1.put()

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data()
      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      self.template_data['xsrf_token'] = ''
      self.template_data['xsrf_token_expires'] = 0
    self.full_template_path = self.handler.get_template_path(self.template_data)

    self.maxDiff = None

  def tearDown(self):
    self.mock_chrome_details_patch.stop()
    self.watcher_1.key.delete()
    self.component_owner_1.key.delete()
    self.component_1.key.delete()
    self.component_2.key.delete()
    testing_config.sign_out()
    self.app_admin.key.delete()

  def test_html_rendering(self):
    """We can render the template with valid html."""
    with test_app.app_context():
      template_text = self.handler.render(
          self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)
    # TESTDATA.make_golden(template_text, 'SubscribersTemplateTest_test_html_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['SubscribersTemplateTest_test_html_rendering.html'], template_text)
