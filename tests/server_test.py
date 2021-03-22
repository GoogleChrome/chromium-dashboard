from __future__ import division
from __future__ import print_function

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

import flask
import werkzeug

import models
from framework import ramcache
import server


class ServerFunctionsTest(unittest.TestCase):

  def test_normalized_name(self):
    self.assertEqual('', server.normalized_name(''))
    self.assertEqual('abc', server.normalized_name('abc'))
    self.assertEqual('abc', server.normalized_name('Abc'))
    self.assertEqual('abc', server.normalized_name('ABC'))
    self.assertEqual('abc', server.normalized_name('A BC'))
    self.assertEqual('abc', server.normalized_name('A B/C'))
    self.assertEqual('abc', server.normalized_name(' /A B/C /'))


class TestWithFeature(unittest.TestCase):

  REQUEST_PATH_FORMAT = 'subclasses fill this in'
  HANDLER_CLASS = 'subclasses fill this in'

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='detailed sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=models.INTENT_IMPLEMENT)
    self.feature_1.put()
    self.feature_id = self.feature_1.key().id()

    self.request_path = self.REQUEST_PATH_FORMAT % {
        'feature_id': self.feature_id,
    }
    self.handler = self.HANDLER_CLASS()

  def tearDown(self):
    self.feature_1.delete()
    ramcache.flush_all()
    ramcache.check_for_distributed_invalidation()


class FeatureDetailHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/feature/{feature_id}'
  HANDLER_CLASS = server.FeatureDetailHandler

  def test_get_template_data__missing(self):
    """If a feature is not found, give a 404."""
    feature_id = 123456
    with server.app.test_request_context('/feature/123456'):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(feature_id=feature_id)

  def test_get_template_data__deleted(self):
    """If a feature was soft-deleted, give a 404."""
    # TODO(jrobbins): split this into admin vs. non-admin when
    # we implement undelete.
    self.feature_1.deleted = True
    self.feature_1.put()

    with server.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        template_data = self.handler.get_template_data(
            feature_id=self.feature_id)

  def test_get_template_data__normal(self):
    """We can prep to render the feature detail page."""
    with server.app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          feature_id=self.feature_id)

    self.assertEqual(self.feature_id, template_data['feature_id'])
    self.assertEqual('detailed sum', template_data['feature']['summary'])


class FeatureListXMLHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/features.xml'
  HANDLER_CLASS = server.FeatureListXMLHandler

  def test_get_template_data__no_filters(self):
    """User can get an XML feed of all features."""
    with server.app.test_request_context(self.request_path):
      actual_text, actual_headers = self.handler.get_template_data()

    self.assertTrue(actual_text.startswith('<?xml'))
    self.assertIn('feature one', actual_text)
    self.assertIn('detailed sum', actual_text)
    self.assertIn(str(self.feature_id), actual_text)

    self.assertIn('atom+xml', actual_headers['Content-Type'])

  def test_get_template_data__category(self):
    """User can get an XML feed of features by category."""
    request_path = self.request_path + '?category=web components'
    with server.app.test_request_context(request_path):
      actual_text, actual_headers = self.handler.get_template_data()

    # It is an XML feed
    self.assertTrue(actual_text.startswith('<?xml'))
    self.assertIn('atom+xml', actual_headers['Content-Type'])
    self.assertIn('Features', actual_text)

    # feature_1 is in the list
    self.assertIn('feature one', actual_text)
    self.assertIn('detailed sum', actual_text)
    self.assertIn(str(self.feature_id), actual_text)


    request_path = self.request_path + '?category=css'
    with server.app.test_request_context(request_path):
      actual_text, actual_headers = self.handler.get_template_data()

    self.assertTrue(actual_text.startswith('<?xml'))
    self.assertNotIn('feature one', actual_text)


class FeatureListHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/features'
  HANDLER_CLASS = server.FeatureListHandler

  def test_get_template_data(self):
    """User can get a feature list page."""
    with server.app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data()

    self.assertIn('IMPLEMENTATION_STATUSES', template_data)


class FeaturesAPIHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/features.json'
  HANDLER_CLASS = server.FeaturesAPIHandler

  def test_get_template_data(self):
    """User can get a JSON feed of all features."""
    with server.app.test_request_context(self.request_path):
      json_data = self.handler.get_template_data()

    self.assertEqual(1, len(json_data))
    self.assertEqual('feature one', json_data[0]['name'])


class SamplesHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/samples'
  HANDLER_CLASS = server.SamplesHandler

  def test_get_template_data(self):
    """User can get a page with all samples."""
    with server.app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data()

    self.assertIn('FEATURES', template_data)


class SamplesJSONHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/samples'
  HANDLER_CLASS = server.SamplesJSONHandler

  def test_get_template_data(self):
    """User can get a JSON feed of all samples."""
    with server.app.test_request_context(self.request_path):
      json_data = self.handler.get_template_data()

    self.assertEqual([], json_data)


class SamplesXMLHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/samples.xml'
  HANDLER_CLASS = server.SamplesXMLHandler

  def test_get_template_data(self):
    """User can get an XML feed of all samples."""
    with server.app.test_request_context(self.request_path):
      actual_text, actual_headers = self.handler.get_template_data()

    # It is an XML feed
    self.assertTrue(actual_text.startswith('<?xml'))
    self.assertIn('atom+xml', actual_headers['Content-Type'])
    self.assertIn('Samples', actual_text)

    # feature_1 is not in the list because it does not have a sample.
    self.assertNotIn('detailed sum', actual_text)
    self.assertNotIn(str(self.feature_id), actual_text)
