# Copyright 2021 Google Inc.
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

import flask
import werkzeug

from internals import models
from framework import ramcache
from pages import samples

test_app = flask.Flask(__name__)


class TestWithFeature(testing_config.CustomTestCase):

  REQUEST_PATH_FORMAT = 'subclasses fill this in'
  HANDLER_CLASS = 'subclasses fill this in'

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='detailed sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=models.INTENT_IMPLEMENT)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.request_path = self.REQUEST_PATH_FORMAT % {
        'feature_id': self.feature_id,
    }
    self.handler = self.HANDLER_CLASS()

  def tearDown(self):
    self.feature_1.key.delete()
    ramcache.flush_all()
    ramcache.check_for_distributed_invalidation()


class SamplesHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/samples'
  HANDLER_CLASS = samples.SamplesHandler

  def test_get_template_data(self):
    """User can get a page with all samples."""
    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data()

    self.assertIn('FEATURES', template_data)


class SamplesJSONHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/samples'
  HANDLER_CLASS = samples.SamplesJSONHandler

  def test_get_template_data(self):
    """User can get a JSON feed of all samples."""
    with test_app.test_request_context(self.request_path):
      json_data = self.handler.get_template_data()

    self.assertEqual([], json_data)


class SamplesXMLHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/samples.xml'
  HANDLER_CLASS = samples.SamplesXMLHandler

  def test_get_template_data(self):
    """User can get an XML feed of all samples."""
    with test_app.test_request_context(self.request_path):
      actual_text, actual_headers = self.handler.get_template_data()

    # It is an XML feed
    self.assertTrue(actual_text.startswith('<?xml'))
    self.assertIn('atom+xml', actual_headers['Content-Type'])
    self.assertIn('Samples', actual_text)

    # feature_1 is not in the list because it does not have a sample.
    self.assertNotIn('detailed sum', actual_text)
    self.assertNotIn('feature/' + str(self.feature_id), actual_text)
