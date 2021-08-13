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

import testing_config  # Must be imported before the module under test.

import flask
import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import features_api
from api import register
from internals import models
from framework import ramcache


class FeaturesAPITestDelete(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=models.INTENT_IMPLEMENT)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.request_path = '/api/v0/features/%d' % self.feature_id
    self.handler = features_api.FeaturesAPI()

    self.app_admin = models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

  def tearDown(self):
    self.feature_1.key.delete()
    self.app_admin.key.delete()
    testing_config.sign_out()
    ramcache.flush_all()
    ramcache.check_for_distributed_invalidation()

  def test_delete__valid(self):
    """Admin wants to soft-delete a feature."""
    testing_config.sign_in('admin@example.com', 123567890)

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
    testing_config.sign_in('admin@example.com', 123567890)

    with register.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_delete(None)

    revised_feature = models.Feature.get_by_id(self.feature_id)
    self.assertFalse(revised_feature.deleted)

  def test_delete__not_found(self):
    """We cannot soft-delete a feature with the wrong feature_id."""
    testing_config.sign_in('admin@example.com', 123567890)

    with register.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_delete(self.feature_id + 1)

    revised_feature = models.Feature.get_by_id(self.feature_id)
    self.assertFalse(revised_feature.deleted)
  

class FeaturesAPITestGet(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=5,
        intent_stage=models.INTENT_IMPLEMENT, shipped_milestone=1)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.request_path = '/api/v0/features'
    self.handler = features_api.FeaturesAPI()

    self.app_admin = models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

  def tearDown(self):
    self.feature_1.key.delete()
    self.app_admin.key.delete()
    testing_config.sign_out()
    ramcache.flush_all()
    ramcache.check_for_distributed_invalidation()

  def test_get__all_listed(self):
    """Get all features that are listed."""
    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()

    # Comparing only the total number of features and name of the feature 
    # as certain fields like `updated` cannot be compared 
    self.assertEqual(1, len(actual_response))
    self.assertEqual('feature one', actual_response[0]['name'])

  def test_get__all_unlisted_no_perms(self):
    """JSON feed does not include unlisted features for users who can't edit."""
    self.feature_1.unlisted = True
    self.feature_1.put()

    # No signed-in user
    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get() 
    self.assertEqual(0, len(actual_response))

    # Signed-in user with no permissions
    testing_config.sign_in('one@example.com', 123567890)
    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    self.assertEqual(0, len(actual_response))

  def test_get__all_unlisted_can_edit(self):
    """JSON feed includes unlisted features for users who may edit."""
    self.feature_1.unlisted = True
    self.feature_1.put()

    # Signed-in user with permissions
    testing_config.sign_in('admin@example.com', 123567890)
    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    self.assertEqual(1, len(actual_response))
    self.assertEqual('feature one', actual_response[0]['name'])

  def test_get__in_milestone_listed(self):
    """Get all features in a specific milestone that are listed."""
    # Atleast one feature is present in milestone
    with register.app.test_request_context(self.request_path+'?milestone=1'):
      actual_response = self.handler.do_get()
    self.assertEqual(6, len(actual_response))
    self.assertEqual(1, len(actual_response['Enabled by default']))

    # No Feature is present in milestone
    with register.app.test_request_context(self.request_path+'?milestone=2'):
      actual_response = self.handler.do_get()
    self.assertEqual(6, len(actual_response))
    self.assertEqual(0, len(actual_response['Enabled by default']))

  def test_get__in_milestone_unlisted_no_perms(self):
    """JSON feed does not include unlisted features for users who can't edit."""
    self.feature_1.unlisted = True
    self.feature_1.put()

    # No signed-in user
    with register.app.test_request_context(self.request_path+'?milestone=1'):
      actual_response = self.handler.do_get()
    self.assertEqual(6, len(actual_response))
    self.assertEqual(0, len(actual_response['Enabled by default']))

    # Signed-in user with no permissions
    testing_config.sign_in('one@example.com', 123567890)
    with register.app.test_request_context(self.request_path+'?milestone=1'):
      actual_response = self.handler.do_get()
    self.assertEqual(6, len(actual_response))
    self.assertEqual(0, len(actual_response['Enabled by default']))

  def test_get__in_milestone_unlisted_can_edit(self):
    """JSON feed includes unlisted features for users who may edit."""
    self.feature_1.unlisted = True
    self.feature_1.put()

    # Signed-in user with permissions
    testing_config.sign_in('admin@example.com', 123567890)

    # Feature is present in milestone
    with register.app.test_request_context(self.request_path+'?milestone=1'):
      actual_response = self.handler.do_get()
    self.assertEqual(6, len(actual_response))
    self.assertEqual(1, len(actual_response['Enabled by default']))

    # Feature is not present in milestone
    with register.app.test_request_context(self.request_path+'?milestone=2'):
      actual_response = self.handler.do_get()
    self.assertEqual(6, len(actual_response))
    self.assertEqual(0, len(actual_response['Enabled by default']))

  @mock.patch('flask.abort')
  def test_get__in_milestone_invalid_query(self, mock_abort):
    """Invalid value of milestone should not be processed."""

    # Feature is present in milestone
    with register.app.test_request_context(self.request_path+'?milestone=chromium'):
      actual_response = self.handler.do_get()
    mock_abort.assert_called_once_with(400, description='Invalid  Milestone')