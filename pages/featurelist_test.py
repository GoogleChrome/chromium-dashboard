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

from __future__ import division
from __future__ import print_function

import testing_config  # Must be imported first
import unittest

import flask
import werkzeug

from framework import ramcache
from internals import models
from pages import featurelist
from google.cloud import ndb

client = ndb.Client()



class TestWithFeature(unittest.TestCase):

  REQUEST_PATH_FORMAT = 'subclasses fill this in'
  HANDLER_CLASS = 'subclasses fill this in'

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='detailed sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=models.INTENT_IMPLEMENT)
    with client.context():
      self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.request_path = self.REQUEST_PATH_FORMAT % {
        'feature_id': self.feature_id,
    }
    self.handler = self.HANDLER_CLASS()

  def tearDown(self):
    with client.context():
      self.feature_1.key.delete()
      ramcache.flush_all()
      ramcache.check_for_distributed_invalidation()


class FeaturesJsonHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/features.json'
  HANDLER_CLASS = featurelist.FeaturesJsonHandler

  def test_get_template_data(self):
    """User can get a JSON feed of all features."""
    with featurelist.app.test_request_context(self.request_path):
      with client.context():
        json_data = self.handler.get_template_data()

    self.assertEqual(1, len(json_data))
    self.assertEqual('feature one', json_data[0]['name'])

  def test_get_template_data__unlisted_no_perms(self):
    """JSON feed does not include unlisted features for users who can't edit."""
    self.feature_1.unlisted = True
    with client.context():
      self.feature_1.put()

    testing_config.sign_out()
    with featurelist.app.test_request_context(self.request_path):
      with client.context():
        json_data = self.handler.get_template_data()
    self.assertEqual(0, len(json_data))

    testing_config.sign_in('user@example.com', 111)
    with featurelist.app.test_request_context(self.request_path):
      with client.context():
        json_data = self.handler.get_template_data()
    self.assertEqual(0, len(json_data))

  def test_get_template_data__unlisted_can_edit(self):
    """JSON feed includes unlisted features for users who may edit."""
    self.feature_1.unlisted = True
    with client.context():
      self.feature_1.put()

    testing_config.sign_in('user@google.com', 111)
    with featurelist.app.test_request_context(self.request_path):
      with client.context():
        json_data = self.handler.get_template_data()
    self.assertEqual(1, len(json_data))
    self.assertEqual('feature one', json_data[0]['name'])


class FeatureListHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/features'
  HANDLER_CLASS = featurelist.FeatureListHandler

  def test_get_template_data(self):
    """User can get a feature list page."""
    with featurelist.app.test_request_context(self.request_path):
      with client.context():
        template_data = self.handler.get_template_data()

    self.assertIn('IMPLEMENTATION_STATUSES', template_data)


class FeatureListXMLHandlerTest(TestWithFeature):

  REQUEST_PATH_FORMAT = '/features.xml'
  HANDLER_CLASS = featurelist.FeatureListXMLHandler

  def test_get_template_data__no_filters(self):
    """User can get an XML feed of all features."""
    with featurelist.app.test_request_context(self.request_path):
      with client.context():
        actual_text, actual_headers = self.handler.get_template_data()

    self.assertTrue(actual_text.startswith('<?xml'))
    self.assertIn('feature one', actual_text)
    self.assertIn('detailed sum', actual_text)
    self.assertIn(str(self.feature_id), actual_text)

    self.assertIn('atom+xml', actual_headers['Content-Type'])

  def test_get_template_data__category(self):
    """User can get an XML feed of features by category."""
    request_path = self.request_path + '?category=web components'
    with featurelist.app.test_request_context(request_path):
      with client.context():
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
    with featurelist.app.test_request_context(request_path):
      with client.context():
        actual_text, actual_headers = self.handler.get_template_data()

    self.assertTrue(actual_text.startswith('<?xml'))
    self.assertNotIn('feature one', actual_text)
