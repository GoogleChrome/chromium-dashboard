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


import testing_config  # Must be imported first

import os
import flask
import werkzeug
import html5lib

from internals import core_enums
from internals import core_models
from pages import featuredetail

test_app = flask.Flask(__name__)


class TestWithFeature(testing_config.CustomTestCase):

  REQUEST_PATH_FORMAT = 'subclasses fill this in'
  HANDLER_CLASS = 'subclasses fill this in'

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature one', summary='detailed sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=core_enums.INTENT_IMPLEMENT)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.request_path = self.REQUEST_PATH_FORMAT % {
        'feature_id': self.feature_id,
    }
    self.handler = self.HANDLER_CLASS()

  def tearDown(self):
    self.feature_1.key.delete()


class FeatureDetailHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/feature/{feature_id}'
  HANDLER_CLASS = featuredetail.FeatureDetailHandler

  def test_get_template_data__missing(self):
    """If a feature is not found, give a 404."""
    feature_id = 123456
    with test_app.test_request_context('/feature/123456'):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(feature_id=feature_id)

  def test_get_template_data__deleted(self):
    """If a feature was soft-deleted, give a 404."""
    # TODO(jrobbins): split this into admin vs. non-admin when
    # we implement undelete.
    self.feature_1.deleted = True
    self.feature_1.put()

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        template_data = self.handler.get_template_data(
            feature_id=self.feature_id)

  def test_get_template_data__normal(self):
    """We can prep to render the feature detail page."""
    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          feature_id=self.feature_id)

    self.assertEqual(self.feature_id, template_data['feature_id'])
    self.assertEqual('feature one', template_data['feature']['name'])
    self.assertEqual('detailed sum', template_data['feature']['summary'])


class FeatureDetailTemplateTest(TestWithFeature):

  HANDLER_CLASS = featuredetail.FeatureDetailHandler

  def setUp(self):
    super(FeatureDetailTemplateTest, self).setUp()
    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data(
          feature_id=self.feature_id)

      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      template_path = self.handler.get_template_path(self.template_data)
      self.full_template_path = os.path.join(template_path)

  def test_basic_rendering(self):
    """We can render the template."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    self.assertIn('feature one', template_text) # still exists at the title section
    self.assertIn('detailed sum', template_text) # still exists at the meta section
