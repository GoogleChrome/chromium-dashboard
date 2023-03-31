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

from api import features_api
from internals import core_enums
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals import user_models
from framework import rediscache

test_app = flask.Flask(__name__)


class FeaturesAPITestDelete(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        name='feature one', summary='sum', category=1,
        intent_stage=core_enums.INTENT_IMPLEMENT)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.request_path = '/api/v0/features/%d' % self.feature_id
    self.handler = features_api.FeaturesAPI()

    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

    self.random_user = user_models.AppUser(email='someuser@example.com')
    self.random_user.put()

  def tearDown(self):
    cache_key = '%s|%s' % (
        FeatureEntry.DEFAULT_CACHE_KEY, self.feature_1.key.integer_id())
    self.feature_1.key.delete()
    self.app_admin.key.delete()
    testing_config.sign_out()
    rediscache.delete(cache_key)

  def test_delete__valid(self):
    """Admin wants to soft-delete a feature."""
    testing_config.sign_in('admin@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      actual_json = self.handler.do_delete(feature_id=self.feature_id)
    self.assertEqual({'message': 'Done'}, actual_json)

    revised_feature = FeatureEntry.get_by_id(self.feature_id)
    self.assertTrue(revised_feature.deleted)

  def test_delete__forbidden(self):
    """Regular user cannot soft-delete a feature."""
    testing_config.sign_in('one@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_delete(feature_id=self.feature_id)

    revised_feature = FeatureEntry.get_by_id(self.feature_id)
    self.assertFalse(revised_feature.deleted)

  def test_delete__invalid(self):
    """We cannot soft-delete a feature without a feature_id."""
    testing_config.sign_in('admin@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_delete()

    revised_feature = FeatureEntry.get_by_id(self.feature_id)
    self.assertFalse(revised_feature.deleted)

  def test_delete__not_found(self):
    """We cannot soft-delete a feature with the wrong feature_id."""
    testing_config.sign_in('admin@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_delete(feature_id=self.feature_id + 1)

    revised_feature = FeatureEntry.get_by_id(self.feature_id)
    self.assertFalse(revised_feature.deleted)


class FeaturesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        name='feature one', summary='sum Z', feature_type=0,
        owner_emails=['feature_owner@example.com'], category=1,
        intent_stage=core_enums.INTENT_IMPLEMENT)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.ship_stage_1 = Stage(feature_id=self.feature_1_id,
        stage_type=160, milestones=MilestoneSet(desktop_first=1))
    self.ship_stage_1.put()

    self.feature_2 = FeatureEntry(
        name='feature two', summary='sum K', feature_type=1,
        owner_emails=['other_owner@example.com'], category=1,
        intent_stage=core_enums.INTENT_IMPLEMENT)
    self.feature_2.put()
    self.feature_2_id = self.feature_2.key.integer_id()
    self.ship_stage_2 = Stage(feature_id=self.feature_2_id,
        stage_type=260, milestones=MilestoneSet(desktop_first=2))
    self.ship_stage_2.put()

    self.feature_3 = FeatureEntry(
        name='feature three', summary='sum A', feature_type=2,
        owner_emails=['other_owner@example.com'], category=1,
        intent_stage=core_enums.INTENT_IMPLEMENT,
        unlisted=True)
    self.feature_3.put()
    self.feature_3_id = self.feature_3.key.integer_id()
    self.ship_stage_3 = Stage(feature_id=self.feature_3_id,
        stage_type=360, milestones=MilestoneSet(desktop_first=2))
    self.ship_stage_3.put()

    self.request_path = '/api/v0/features'
    self.handler = features_api.FeaturesAPI()

    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

  def tearDown(self):
    for kind in [FeatureEntry, Stage, user_models.AppUser]:
      for entity in kind.query():
        entity.key.delete()

    testing_config.sign_out()
    rediscache.delete_keys_with_prefix('features|*')
    rediscache.delete_keys_with_prefix('FeatureEntries|*')

  def test_get__all_listed(self):
    """Get all features that are listed."""
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get()

    # Comparing only the total number of features and name of the feature
    # as certain fields like `updated` cannot be compared
    self.assertEqual(2, len(actual['features']))
    self.assertEqual(2, actual['total_count'])
    self.assertEqual('feature two', actual['features'][0]['name'])
    self.assertEqual('feature one', actual['features'][1]['name'])

  def test_get__all_listed__pagination(self):
    """Get a pagination page features that are listed."""
    # User wants only 1 result, starting at index 0
    url = self.request_path + '?num=1'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(1, len(actual['features']))
    self.assertEqual(2, actual['total_count'])
    self.assertEqual('feature two', actual['features'][0]['name'])

    # User wants only 1 result, starting at index 1
    url = self.request_path + '?num=1&start=1'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(1, len(actual['features']))
    self.assertEqual(2, actual['total_count'])
    self.assertEqual('feature one', actual['features'][0]['name'])

    # User wants only 1 result, starting at index 2, but there are no more.
    url = self.request_path + '?num=1&start=2'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(0, len(actual['features']))
    self.assertEqual(2, actual['total_count'])

    # User wants only more results that we have
    url = self.request_path + '?num=999'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(2, len(actual['features']))
    self.assertEqual(2, actual['total_count'])
    self.assertEqual('feature two', actual['features'][0]['name'])
    self.assertEqual('feature one', actual['features'][1]['name'])

    # User wants only the result count, zero actual results.
    url = self.request_path + '?num=0'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(0, len(actual['features']))
    self.assertEqual(2, actual['total_count'])

  def test_get__all_listed__bad_pagination(self):
    """Reject requests that have bad pagination params."""
    # Malformed start parameter
    url = self.request_path + '?start=bad'
    with test_app.test_request_context(url):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_get()

    # Malformed num parameter
    url = self.request_path + '?num=bad'
    with test_app.test_request_context(url):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_get()

    # User wants a negative number of results
    url = self.request_path + '?num=-1'
    with test_app.test_request_context(url):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_get()

    # User wants a negative offset
    url = self.request_path + '?start=-1'
    with test_app.test_request_context(url):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_get()

  def test_get__all_unlisted_no_perms(self):
    """JSON feed does not include unlisted features for users who can't edit."""
    self.feature_1.unlisted = True
    self.feature_1.put()

    # No signed-in user
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get()
    self.assertEqual(1, len(actual['features']))
    self.assertEqual(1, actual['total_count'])
    self.assertEqual('feature two', actual['features'][0]['name'])

    # Signed-in user with no permissions
    testing_config.sign_in('one@example.com', 123567890)
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get()
    self.assertEqual(1, len(actual['features']))
    self.assertEqual(1, actual['total_count'])
    self.assertEqual('feature two', actual['features'][0]['name'])

  def test_get__all_unlisted_can_edit(self):
    """JSON feed includes unlisted features for users who may edit."""
    self.feature_1.unlisted = True
    self.feature_1.put()

    # Signed-in user with permissions
    testing_config.sign_in('admin@example.com', 123567890)
    with test_app.test_request_context(self.request_path):
      actual = self.handler.do_get()
    self.assertEqual(3, len(actual['features']))
    self.assertEqual(3, actual['total_count'])
    self.assertEqual('feature three', actual['features'][0]['name'])
    self.assertEqual('feature two', actual['features'][1]['name'])
    self.assertEqual('feature one', actual['features'][2]['name'])

  def test_get__user_query_no_sort__signed_out(self):
    """Get all features with a specified owner, unlisted not shown."""
    url = self.request_path + '?q=owner=other_owner@example.com'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(1, len(actual['features']))
    self.assertEqual(1, actual['total_count'])
    self.assertEqual('feature two', actual['features'][0]['name'])

  def test_get__user_query_no_sort__with_perms(self):
    """Get all features with a specified owner."""
    testing_config.sign_in('admin@example.com', 123567890)
    url = self.request_path + '?q=owner=feature_owner@example.com'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(1, len(actual['features']))
    self.assertEqual(1, actual['total_count'])
    self.assertEqual('feature one', actual['features'][0]['name'])

  def test_get__user_query_with_sort__signed_out(self):
    """Get all features, sorted by summary DESC, unlisted not shown."""
    url = self.request_path + '?sort=-summary'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(2, len(actual['features']))
    self.assertEqual(2, actual['total_count'])
    self.assertEqual('sum Z', actual['features'][0]['summary'])
    self.assertEqual('sum K', actual['features'][1]['summary'])

  def test_get__user_query_with_sort__with_perms(self):
    """Get all features, sorted by summary descending."""
    testing_config.sign_in('admin@example.com', 123567890)
    url = self.request_path + '?sort=-summary'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(3, len(actual['features']))
    self.assertEqual(3, actual['total_count'])
    self.assertEqual('sum Z', actual['features'][0]['summary'])
    self.assertEqual('sum K', actual['features'][1]['summary'])
    self.assertEqual('sum A', actual['features'][2]['summary'])

  def test_get__in_milestone_listed(self):
    """Get all features in a specific milestone that are listed."""
    # Atleast one feature is present in milestone
    with test_app.test_request_context(self.request_path+'?milestone=1'):
      actual = self.handler.do_get()
    self.assertEqual(6, len(actual['features_by_type']))
    self.assertEqual(1, actual['total_count'])
    self.assertEqual(1, len(actual['features_by_type']['Enabled by default']))

    # No Feature is present in milestone
    with test_app.test_request_context(self.request_path+'?milestone=99'):
      actual = self.handler.do_get()
    self.assertEqual(6, len(actual['features_by_type']))
    self.assertEqual(0, actual['total_count'])
    self.assertEqual(0, len(actual['features_by_type']['Enabled by default']))

  def test_get__in_milestone_unlisted_no_perms(self):
    """JSON feed does not include unlisted features for users who can't edit."""
    self.feature_1.unlisted = True
    self.feature_1.put()

    # No signed-in user
    with test_app.test_request_context(self.request_path+'?milestone=1'):
      actual = self.handler.do_get()
    self.assertEqual(6, len(actual['features_by_type']))
    self.assertEqual(0, actual['total_count'])
    self.assertEqual(0, len(actual['features_by_type']['Enabled by default']))

    # Signed-in user with no permissions
    testing_config.sign_in('one@example.com', 123567890)
    with test_app.test_request_context(self.request_path+'?milestone=1'):
      actual = self.handler.do_get()
    self.assertEqual(6, len(actual['features_by_type']))
    self.assertEqual(0, actual['total_count'])
    self.assertEqual(0, len(actual['features_by_type']['Enabled by default']))

  def test_get__in_milestone_unlisted_can_edit(self):
    """JSON feed includes unlisted features for users who may edit."""
    self.feature_1.unlisted = True
    self.feature_1.put()

    # Signed-in user with permissions
    testing_config.sign_in('admin@example.com', 123567890)

    # Feature is present in milestone
    with test_app.test_request_context(self.request_path+'?milestone=1'):
      actual = self.handler.do_get()
    self.assertEqual(6, len(actual['features_by_type']))
    self.assertEqual(1, actual['total_count'])
    self.assertEqual(1, len(actual['features_by_type']['Enabled by default']))

    # Feature is not present in milestone
    with test_app.test_request_context(self.request_path+'?milestone=99'):
      actual = self.handler.do_get()
    self.assertEqual(6, len(actual['features_by_type']))
    self.assertEqual(0, actual['total_count'])
    self.assertEqual(0, len(actual['features_by_type']['Enabled by default']))

  def test_get__in_milestone_invalid_query(self):
    """Invalid value of milestone should not be processed."""
    with test_app.test_request_context(
        self.request_path+'?milestone=chromium'):
      with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
        self.handler.do_get()
      self.assertEqual(400, cm.exception.code)
      self.assertEqual(
          "Request parameter 'milestone' was not an int",
          cm.exception.description)

  def test_get__specific_id__found(self):
    """JSON feed has just the feature requested."""
    request_path = self.request_path + '/' + str(self.feature_1_id)
    with test_app.test_request_context(request_path):
      actual = self.handler.do_get(feature_id=self.feature_1_id)
    self.assertEqual('feature one', actual['name'])

  def test_get__specific_id__not_found(self):
    """We give 404 if the feature requested feature was not found."""
    request_path = self.request_path + '/999'
    with test_app.test_request_context(request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_get(feature_id=999)
  
  def test_patch__valid(self):
    """PATCH request successful with valid input from user with permissions."""
    # Signed-in user with permissions
    testing_config.sign_in('admin@example.com', 123567890)

    new_summary = 'a different summary'
    new_owner_emails = ['test@example.com']
    valid_request_body = {
      'update_fields': ['summary', 'owner_emails'],
      'summary': new_summary,
      'owner_emails': new_owner_emails,
    }
    request_path = f'{self.request_path}/{self.feature_1_id}'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch(feature_id=self.feature_1_id)
    # Success response should be returned
    self.assertEqual({'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertEqual(self.feature_1.summary, new_summary)
    self.assertEqual(self.feature_1.owner_emails, new_owner_emails)
    # Updater email field should be changed
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')

  def test_patch__no_permissions(self):
    """We give 403 if the user does not have feature edit access."""
    testing_config.sign_in('someuser@example.com', 123567890)

    request_path = f'{self.request_path}/{self.feature_1_id}'
    with test_app.test_request_context(request_path, json={}):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_patch(feature_id=self.feature_1_id)

  def test_patch__invalid_fields(self):
    """PATCH request fails with 400 when supplying invalid fields."""
    # Signed-in user with permissions
    testing_config.sign_in('admin@example.com', 123567890)

    bad_param = 'Not a real field'
    new_owner_emails = ['test@example.com']
    invalid_request_body = {
      'update_fields': ['bad_param', 'owner_emails'],
      'bad_param': bad_param,
      'owner_emails': new_owner_emails,
    }
    request_path = f'{self.request_path}/{self.feature_1_id}'
    with test_app.test_request_context(request_path, json=invalid_request_body):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_patch(feature_id=self.feature_1_id)
  
  def test_patch__immutable_fields(self):
    """PATCH request fails with 400 when immutable field change is attempted."""
    # Signed-in user with permissions
    testing_config.sign_in('admin@example.com', 123567890)

    new_creator = 'differentuser@example.com'
    invalid_request_body = {
      'update_fields': ['creator_email'],
      'creator_email': new_creator,
    }
    request_path = f'{self.request_path}/{self.feature_1_id}'
    with test_app.test_request_context(request_path, json=invalid_request_body):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_patch(feature_id=self.feature_1_id)
