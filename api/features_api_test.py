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

from __future__ import division
from __future__ import print_function

import unittest
import testing_config  # Must be imported before the module under test.

import flask
import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import features_api
from api import register
from internals import models


class FeaturesAPITest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=models.INTENT_IMPLEMENT)
    self.feature_1.put()
    self.feature_id = self.feature_1.key().id()

    self.request_path = '/api/v0/features/%d' % self.feature_id
    self.handler = features_api.FeaturesAPI()

  def tearDown(self):
    self.feature_1.delete()

  def test_delete__valid(self):
    """Admin wants to soft-delete a feature."""
    testing_config.sign_in('admin@example.com', 123567890, is_admin=True)

    with register.app.test_request_context(self.request_path):
      actual_json = self.handler.do_delete(self.feature_id)
    self.assertEqual({'message': 'Done'}, actual_json)

    revised_feature = models.Feature.get_by_id(self.feature_id)
    self.assertTrue(revised_feature.deleted)

  def test_delete__forbidden(self):
    """Regular user cannot soft-delete a feature."""
    testing_config.sign_in('one@example.com', 123567890)

    with register.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_delete(self.feature_id)

    revised_feature = models.Feature.get_by_id(self.feature_id)
    self.assertFalse(revised_feature.deleted)

  def test_delete__invalid(self):
    """We cannot soft-delete a feature without a feature_id."""
    testing_config.sign_in('admin@example.com', 123567890, is_admin=True)

    with register.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_delete(None)

    revised_feature = models.Feature.get_by_id(self.feature_id)
    self.assertFalse(revised_feature.deleted)

  def test_delete__not_found(self):
    """We cannot soft-delete a feature with the wrong feature_id."""
    testing_config.sign_in('admin@example.com', 123567890, is_admin=True)

    with register.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_delete(self.feature_id + 1)

    revised_feature = models.Feature.get_by_id(self.feature_id)
    self.assertFalse(revised_feature.deleted)
