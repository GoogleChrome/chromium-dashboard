
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

from typing import Optional
from framework.basehandlers import FlaskHandler
import testing_config  # Must be imported first

import os
import flask
import werkzeug
import html5lib
import settings

from internals import core_enums
from internals.core_models import FeatureEntry
from internals import user_models
from pages import featurelist
from framework import rediscache

test_app = flask.Flask(__name__,
  template_folder=settings.get_flask_template_path())

# Load testdata to be used across all of the CustomTestCases
TESTDATA = testing_config.Testdata(__file__)

class TestWithFeature(testing_config.CustomTestCase):

  REQUEST_PATH_FORMAT: Optional[str] = None
  HANDLER_CLASS: Optional[object] = None

  def setUp(self):
    self.app_user = user_models.AppUser(email='registered@example.com')
    self.app_user.put()

    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

    self.fe_1 = FeatureEntry(
        name='feature one', summary='detailed sum',
        owner_emails=['owner@example.com'],
        category=1, intent_stage=core_enums.INTENT_IMPLEMENT)
    self.fe_1.put()
    self.feature_id = self.fe_1.key.integer_id()

    self.request_path = (self.REQUEST_PATH_FORMAT %
        {'feature_id': self.feature_id} if self.REQUEST_PATH_FORMAT else '')
    if self.HANDLER_CLASS:
      self.handler = self.HANDLER_CLASS()

  def tearDown(self):
    self.fe_1.key.delete()
    self.app_user.delete()
    self.app_admin.delete()
    rediscache.flushall()


class FeaturesJsonHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/features.json'
  HANDLER_CLASS = featurelist.FeaturesJsonHandler

  def test_get_template_data(self):
    """User can get a JSON feed of all features."""
    testing_config.sign_in('user@example.com', 111)
    with test_app.test_request_context(self.request_path):
      json_data = self.handler.get_template_data()

    self.assertEqual(1, len(json_data))
    self.assertEqual('feature one', json_data[0]['name'])

  def test_get_template_data__unlisted_no_perms(self):
    """JSON feed does not include unlisted features for users who can't edit."""
    self.fe_1.unlisted = True
    self.fe_1.put()

    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      json_data = self.handler.get_template_data()
    self.assertEqual(0, len(json_data))

    testing_config.sign_in('user@example.com', 111)
    with test_app.test_request_context(self.request_path):
      json_data = self.handler.get_template_data()
    self.assertEqual(0, len(json_data))

  def test_get_template_data__unlisted_can_edit(self):
    """JSON feed includes unlisted features for site editors and admins."""

    testing_config.sign_in('admin@example.com', 111)
    with test_app.test_request_context(self.request_path):
      json_data = self.handler.get_template_data()
    self.assertEqual(1, len(json_data))
    self.assertEqual('feature one', json_data[0]['name'])


class FeatureListHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/features'
  HANDLER_CLASS = featurelist.FeatureListHandler

  def test_get_template_data(self):
    """User can get a feature list page."""
    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data()

    self.assertIn('IMPLEMENTATION_STATUSES', template_data)


class FeatureListTemplateTest(TestWithFeature):

  REQUEST_PATH_FORMAT = None
  HANDLER_CLASS = featurelist.FeatureListHandler

  def setUp(self):
    super(FeatureListTemplateTest, self).setUp()
    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data(
          feature_id=self.feature_id)

      testing_config.sign_in('admin@example.com', 111)

      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      self.template_data['xsrf_token'] = ''
      self.template_data['xsrf_token_expires'] = 0
      template_path = self.handler.get_template_path(self.template_data)
      self.full_template_path = os.path.join(template_path)
      self.maxDiff = None

    def tearDown(self):
      testing_config.sign_out()

  def test_html_rendering(self):
    """We can render the template with valid html."""
    with test_app.app_context():
      template_text = self.handler.render(
          self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)
    # TESTDATA.make_golden(template_text, 'test_html_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['test_html_rendering.html'], template_text)
