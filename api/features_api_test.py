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

from datetime import datetime
import testing_config  # Must be imported before the module under test.

import flask
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import features_api
from internals import core_enums
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate
from internals import user_models
from framework import rediscache

test_app = flask.Flask(__name__)


CHANNEL_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

def _datetime_to_str(dt):
  return datetime.strftime(dt, CHANNEL_DATETIME_FORMAT)

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
    self.ship_stage_1_id = self.ship_stage_1.key.integer_id()

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
    for kind in [FeatureEntry, Gate, Stage, user_models.AppUser]:
      for entity in kind.query():
        entity.key.delete()

    testing_config.sign_out()
    rediscache.delete_keys_with_prefix('features')
    rediscache.delete_keys_with_prefix('FeatureEntries')
    rediscache.delete_keys_with_prefix('FeatureNames')

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

  def test_get__all_listed_feature_names(self):
    """Get all feature names that are listed."""
    url = self.request_path + '?name_only=true'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()

    # Comparing only the total number of features and names,
    # as it only returns feature names.
    self.assertEqual(2, len(actual['features']))
    self.assertEqual(2, actual['total_count'])
    self.assertEqual(2, len(actual['features'][0]))
    self.assertEqual('feature two', actual['features'][0]['name'])
    self.assertEqual(2, len(actual['features'][1]))
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

    # User wants only 1 result, starting at index 0
    url = self.request_path + '?num=1&name_only=true'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(1, len(actual['features']))
    self.assertEqual(2, actual['total_count'])
    self.assertEqual('feature two', actual['features'][0]['name'])

    # User wants only 1 result, starting at index 1
    url = self.request_path + '?num=1&start=1&name_only=true'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(1, len(actual['features']))
    self.assertEqual(2, actual['total_count'])
    self.assertEqual('feature one', actual['features'][0]['name'])

    # User wants only 1 result, starting at index 2, but there are no more.
    url = self.request_path + '?num=1&start=2&name_only=true'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(0, len(actual['features']))
    self.assertEqual(2, actual['total_count'])

    # User wants only more results that we have
    url = self.request_path + '?num=999&name_only=true'
    with test_app.test_request_context(url):
      actual = self.handler.do_get()
    self.assertEqual(2, len(actual['features']))
    self.assertEqual(2, actual['total_count'])
    self.assertEqual('feature two', actual['features'][0]['name'])
    self.assertEqual('feature one', actual['features'][1]['name'])

    # User wants only the result count, zero actual results.
    url = self.request_path + '?num=0&name_only=true'
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
    """We give 404 if the requested feature was not found."""
    request_path = self.request_path + '/999'
    with test_app.test_request_context(request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_get(feature_id=999)

  def test_get__specific_id__deleted(self):
    """We give 404 if the requested feature was deleted, unless can dit."""
    self.feature_1.deleted = True
    self.feature_1.put()

    testing_config.sign_out()
    request_path = self.request_path + '/' + str(self.feature_1_id)
    with test_app.test_request_context(request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_get(feature_id=999)

    # Signed-in user with permissions
    testing_config.sign_in('admin@example.com', 123567890)
    with test_app.test_request_context(request_path):
      actual = self.handler.do_get(feature_id=self.feature_1_id)
    self.assertEqual('feature one', actual['name'])

  def test_patch__valid(self):
    """PATCH request successful with valid input from user with permissions."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    new_summary = 'a different summary'
    new_devtrial_instructions = 'https://example.com/instructions'
    doc_links = 'https://example.com/docs1\nhttps://example.com/docs2'
    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'summary': new_summary,  # str
        'owner_emails': 'test@example.com', # emails
        'search_tags': 'tag1,tag2,tag3',  # split_str
        'devtrial_instructions': new_devtrial_instructions,  # link
        'doc_links': doc_links,
        'category': '1',  # int
        'privacy_review_status': '',  # empty int
        'prefixed': 'true',  # bool
      },
      'stages': [],
    }

    expected_changes = [
      ('summary', new_summary),
      ('owner_emails', ['test@example.com']),
      ('search_tags', ['tag1', 'tag2', 'tag3']),
      ('devtrial_instructions', new_devtrial_instructions),
      ('doc_links', ['https://example.com/docs1', 'https://example.com/docs2']),
      ('category', 1),
      ('privacy_review_status', None),
      ('prefixed', True),
    ]
    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()
    # Success response should be returned.
    self.assertEqual({'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    for field, expected_value in expected_changes:
      self.assertEqual(getattr(self.feature_1, field), expected_value)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')

  def test_patch__stage_changes(self):
    """Valid PATCH updates stage entities."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    new_intent_url = 'https://example.com/intent'
    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
      },
      'stages': [
        {
          'id': self.ship_stage_1_id,
          'intent_thread_url': {
            'form_field_name': 'shipped_milestone',
            'value': new_intent_url,
          },
        },
      ],
    }
    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()

    # Success response should be returned.
    self.assertEqual(
        {'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertEqual(self.ship_stage_1.intent_thread_url, new_intent_url)
    # Updater email field should be changed even with only stage changes.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')

  def test_patch__milestone_changes(self):
    """Valid PATCH updates milestone fields on stage entities."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    new_desktop_first = 100
    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
      },
      'stages': [
        {
          'id': self.ship_stage_1_id,
          'desktop_first': {
            'form_field_name': 'desktop_first',
            'value': new_desktop_first,
          },
        },
      ],
    }
    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()

    # Success response should be returned.
    self.assertEqual(
        {'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertIsNotNone(self.ship_stage_1.milestones)
    self.assertEqual(
        self.ship_stage_1.milestones.desktop_first, new_desktop_first)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')

  def test_patch__milestone_changes_null(self):
    """Valid PATCH updates milestone fields when milestones object is null."""
    self.ship_stage_1.milestones = None
    self.ship_stage_1.put()

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    new_desktop_first = 100
    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
      },
      'stages': [
        {
          'id': self.ship_stage_1_id,
          'desktop_first': {
            'form_field_name': 'desktop_first',
            'value': new_desktop_first,
          },
        },
      ],
    }
    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()

    # Success response should be returned.
    self.assertEqual(
        {'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertIsNotNone(self.ship_stage_1.milestones)
    self.assertEqual(
        self.ship_stage_1.milestones.desktop_first, new_desktop_first)
    # Updater email field should be changed even with only stage changes.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')

  def test_patch__no_permissions(self):
    """We give 403 if the user does not have feature edit access."""
    testing_config.sign_in('someuser@example.com', 123567890)
    request_body = {
          'feature_changes': {
            'id': self.feature_1_id,
          },
          'stages': [],
        }
    request_path = f'{self.request_path}/{self.feature_1_id}'
    with test_app.test_request_context(request_path, json=request_body):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_patch(feature_id=self.feature_1_id)

  def test_patch__invalid_fields(self):
    """PATCH request does not attempt to update invalid fields."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    bad_param = 'Not a real field'
    invalid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'bad_param': bad_param,
      },
      'stages': [
        {
          'id': self.ship_stage_1_id,
          'bad_param': {
            'form_field_name': 'bad_param',
            'value': bad_param,
          },
        },
      ],
    }
    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=invalid_request_body):
      self.handler.do_patch(feature_id=self.feature_1_id)
    # Updater email field should NOT be changed. No changes were made.
    self.assertIsNone(self.feature_1.updater_email)

  def test_patch__accurate_as_of(self):
    """Updates accurate_as_of for accuracy verification request."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    # Add some outstanding notifications beforehand.
    self.feature_1.outstanding_notifications = 2
    old_accuracy_date = datetime(2020, 1, 1)
    self.feature_1.accurate_as_of = old_accuracy_date
    self.feature_1.put()

    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'accurate_as_of': True,
      },
      'stages': [
        {
          'id': self.ship_stage_1_id,
          'desktop_first': {
            'form_field_name': 'shipped_milestone',
            'value': 115,
          }
        },
      ],
    }
    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      self.handler.do_patch(feature_id=self.feature_1_id)
    # Assert that changes were made.
    self.assertIsNotNone(self.feature_1.accurate_as_of)
    self.assertTrue(self.feature_1.accurate_as_of > old_accuracy_date)
    self.assertEqual(self.feature_1.outstanding_notifications, 0)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')


  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_patch__enterprise_first_notice_wrong_non_enterprise_feature(self, mock_call):
    """PATCH request successful with no changes to first_enterprise_notification_milestone."""
    stable_date = _datetime_to_str(datetime.now().replace(year=datetime.now().year + 1, day=1))
    mock_call.return_value = { 100: { 'version': 100, 'stable_date': stable_date } }

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'first_enterprise_notification_milestone': 100,  # str
      },
      'stages': [],
    }

    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()
    # Success response should be returned.
    self.assertEqual({'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertEqual(getattr(self.feature_1, 'first_enterprise_notification_milestone'), None)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertIsNone(self.feature_1.updater_email)


  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_patch__enterprise_first_notice_enterprise_feature(self, mock_call):
    """PATCH request successful with provided first_enterprise_notification_milestone."""
    stable_date = _datetime_to_str(datetime.now().replace(year=datetime.now().year + 1, day=1))
    mock_call.return_value = { 100: { 'version': 100, 'stable_date': stable_date } }

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)
    self.feature_1.feature_type = 4
    self.feature_1.put()

    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'first_enterprise_notification_milestone': 100,  # str
      },
      'stages': [],
    }

    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()
    # Success response should be returned.
    self.assertEqual({'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertEqual(getattr(self.feature_1, 'first_enterprise_notification_milestone'), 100)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')



  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_patch__enterprise_first_notice_newly_breaking_feature(self, mock_call):
    """PATCH request successful with provided first_enterprise_notification_milestone."""
    stable_date = _datetime_to_str(datetime.now().replace(year=datetime.now().year + 1, day=1))
    mock_call.return_value = { 100: { 'version': 100, 'stable_date': stable_date } }

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'first_enterprise_notification_milestone': 100,  # str
        'enterprise_impact': core_enums.ENTERPRISE_IMPACT_LOW
      },
      'stages': [],
    }

    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()
    # Success response should be returned.
    self.assertEqual({'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertEqual(getattr(self.feature_1, 'first_enterprise_notification_milestone'), 100)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')

  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_patch__enterprise_first_notice_becomes_not_breaking_feature(self, mock_call):
    """PATCH request successful with first_enterprise_notification_milestone deleted."""
    stable_date = _datetime_to_str(datetime.now().replace(year=datetime.now().year + 1, day=1))
    mock_call.return_value = { 100: { 'version': 100, 'stable_date': stable_date } }

    self.feature_1.enterprise_impact = core_enums.ENTERPRISE_IMPACT_MEDIUM
    self.feature_1.first_enterprise_notification_milestone = 100
    self.feature_1.put()

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'enterprise_impact': core_enums.ENTERPRISE_IMPACT_NONE
      },
      'stages': [],
    }

    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()
    # Success response should be returned.
    self.assertEqual({'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertEqual(getattr(self.feature_1, 'first_enterprise_notification_milestone'), None)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')

  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_patch__first_notice_becomes_not_breaking_feature_already_published(self, mock_call):
    """PATCH request successful with first_enterprise_notification_milestone not deleted."""
    stable_date = _datetime_to_str(datetime.now().replace(year=datetime.now().year - 1, day=1))
    mock_call.return_value = { 100: { 'version': 100, 'stable_date': stable_date } }

    self.feature_1.enterprise_impact = core_enums.ENTERPRISE_IMPACT_MEDIUM
    self.feature_1.first_enterprise_notification_milestone = 100
    self.feature_1.put()

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'enterprise_impact': core_enums.ENTERPRISE_IMPACT_NONE
      },
      'stages': [],
    }

    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()
    # Success response should be returned.
    self.assertEqual({'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertEqual(getattr(self.feature_1, 'first_enterprise_notification_milestone'), 100)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')


  @mock.patch('api.channels_api.construct_chrome_channels_details')
  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_patch__enterprise_first_notice_in_the_past(self, specified_mock, chrome_mock):
    """PATCH request successful with newer default first_enterprise_notification_milestone."""
    stable_date = _datetime_to_str(datetime.now().replace(year=datetime.now().year - 2, day=1))
    specified_mock.return_value = { 100: { 'version': 100, 'stable_date': stable_date } }
    chrome_mock.return_value = { 'beta': { 'version': 420 } }

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)
    self.feature_1.feature_type = 4
    self.feature_1.put()

    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'first_enterprise_notification_milestone': 100,  # str
      },
      'stages': [],
    }

    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()
    # Success response should be returned.
    self.assertEqual({'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertEqual(getattr(self.feature_1, 'first_enterprise_notification_milestone'), 420)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertEqual(self.feature_1.updater_email, 'admin@example.com')


  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_patch__enterprise_first_notice_already_published(self, mock_call):
    """PATCH request successful with no changes to first_enterprise_notification_milestone."""
    now = datetime.now()
    mock_call.return_value =  {
        100: {
          'version': 100,
          'stable_date': _datetime_to_str(now.replace(year=now.year - 1, day=1))
        },
        101: {
          'version': 101,
          'stable_date': _datetime_to_str(now.replace(year=now.year + 1, day=1))
        },
    }

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)
    self.feature_1.feature_type = 4
    self.feature_1.first_enterprise_notification_milestone = 100
    self.feature_1.put()
    valid_request_body = {
      'feature_changes': {
        'id': self.feature_1_id,
        'first_enterprise_notification_milestone': 101,  # str
      },
      'stages': [],
    }

    request_path = f'{self.request_path}/update'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_patch()
    # Success response should be returned.
    self.assertEqual({'message': f'Feature {self.feature_1_id} updated.'}, response)
    # Assert that changes were made.
    self.assertEqual(getattr(self.feature_1, 'first_enterprise_notification_milestone'), 100)
    # Updater email field should be changed.
    self.assertIsNotNone(self.feature_1.updated)
    self.assertIsNone(self.feature_1.updater_email)

  def test_post__valid(self):
    """POST request successful with valid input from user with permissions."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    valid_request_body = {
      'name': 'A name',
      'summary': 'A summary',
      'owner_emails': 'user@example.com,user2@example.com',
      'category': 2,
      'feature_type': 1,
      'impl_status_chrome': 3,
      'standard_maturity': 2,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
      'wpt': True,
    }

    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_post()
    # A new feature ID should be returned.
    self.assertIsNotNone(response['feature_id'])
    self.assertTrue(type(response['feature_id']) == int)
    # New feature should exist.
    new_feature: FeatureEntry | None = (
        FeatureEntry.get_by_id(response['feature_id']))
    self.assertIsNotNone(new_feature)

    # New feature's values should match fields in JSON body.
    for field, value in valid_request_body.items():
      if field == 'owner_emails':
        # list field types should convert the string into a list.
        self.assertEqual(new_feature.owner_emails, ['user@example.com', 'user2@example.com'])
      else:
        self.assertEqual(getattr(new_feature, field), value)
    # User's email should match creator_email field.
    self.assertEqual(new_feature.creator_email, 'admin@example.com')

  def test_post__valid_stage_and_gate_creation(self):
    """POST request successful with valid input from user with permissions."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    valid_request_body = {
      'name': 'A name',
      'summary': 'A summary',
      'owner_emails': 'user@example.com,user2@example.com',
      'category': 2,
      'feature_type': 0,
      'impl_status_chrome': 3,
      'standard_maturity': 2,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
    }

    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_post()
    # A new feature ID should be returned.
    self.assertIsNotNone(response['feature_id'])
    self.assertTrue(type(response['feature_id']) == int)
    # New feature should exist.
    new_feature: FeatureEntry | None = (
        FeatureEntry.get_by_id(response['feature_id']))
    self.assertIsNotNone(new_feature)

    # Ensure Stage and Gate entities were created.
    stages = Stage.query(
        Stage.feature_id == new_feature.key.integer_id()).fetch()
    gates = Gate.query(Gate.feature_id == new_feature.key.integer_id()).fetch()
    self.assertEqual(len(stages), 6)
    self.assertEqual(len(gates), 11)

  def test_post__no_permissions(self):
    """403 Forbidden if the user does not have feature create access."""
    testing_config.sign_in('someuser@example.com', 123567890)

    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json={}):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

  def test_post__invalid_fields(self):
    """POST request fails with 400 when supplying invalid fields."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    request_body = {
      'bad_param': 'Not a real field',  # Bad field.

      'name': 'A name',
      'summary': 'A summary',
      'owner_emails': 'user@example.com,user2@example.com',
      'category': 1,
      'feature_type': 1,
      'impl_status_chrome': 1,
      'standard_maturity': 1,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
    }
    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=request_body):
      response = self.handler.do_post()
    # A new feature ID should be returned.
    self.assertIsNotNone(response['feature_id'])
    self.assertTrue(type(response['feature_id']) == int)
    # New feature should exist.
    new_feature: FeatureEntry | None = (
        FeatureEntry.get_by_id(response['feature_id']))
    self.assertIsNotNone(new_feature)

    # New feature's values should match fields in JSON body (except bad param).
    for field, value in request_body.items():
      # Invalid fields are ignored and not updated.
      if field == 'bad_param':
        continue
      if field == 'owner_emails':
        # list field types should convert the string into a list.
        self.assertEqual(new_feature.owner_emails, ['user@example.com', 'user2@example.com'])
      else:
        self.assertEqual(getattr(new_feature, field), value)

  def test_post__immutable_fields(self):
    """POST request fails with 400 when immutable field is provided."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    request_body = {
      'creator_email': 'differentuser@example.com',  # Immutable.

      'name': 'A name',
      'summary': 'A summary',
      'owner_emails': 'user@example.com,user2@example.com',
      'category': 1,
      'feature_type': 1,
      'impl_status_chrome': 1,
      'standard_maturity': 1,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
    }
    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=request_body):
      response = self.handler.do_post()
    # A new feature ID should be returned.
    self.assertIsNotNone(response['feature_id'])
    self.assertTrue(type(response['feature_id']) == int)
    # New feature should exist.
    new_feature: FeatureEntry | None = (
        FeatureEntry.get_by_id(response['feature_id']))
    self.assertIsNotNone(new_feature)

    # New feature's values should match fields in JSON body
    # (except immutable field).
    for field, value in request_body.items():
      if field == 'creator_email':
        # User's email should match creator_email field.
        # The given creator_email should be ignored.
        self.assertEqual(new_feature.creator_email, 'admin@example.com')
      elif field == 'owner_emails':
        # list field types should convert the string into a list.
        self.assertEqual(new_feature.owner_emails,
                         ['user@example.com', 'user2@example.com'])
      else:
        self.assertEqual(getattr(new_feature, field), value)

  def test_post__bad_data_type_int(self):
    """POST request fails with 400 when a bad int data type is provided."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    invalid_request_body = {
      'name': 'A name',
      'summary': 'A summary',
      'owner_emails': 'user@example.com,user2@example.com',
      'category': 'THIS SHOULD BE AN INTEGER',  # Bad data type.
      'feature_type': 1,
      'impl_status_chrome': 1,
      'standard_maturity': 1,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
    }
    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=invalid_request_body):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__bad_data_type_list(self):
    """POST request fails with 400 when a bad list data type is provided."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    invalid_request_body = {
      'name': 'A name',
      'summary': 'A summary',
      'owner_emails': 12345, # Bad data type.
      'category': 1,
      'feature_type': 1,
      'impl_status_chrome': 1,
      'standard_maturity': 1,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
    }
    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=invalid_request_body):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__missing_required_field(self):
    """POST request fails with 400 when missing required fields."""
    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    invalid_request_body = {
      # No 'name' field.
      'summary': 'A summary',
      'owner_emails': 'owner1@example.com,owner2@example.com',
      'category': 1,
      'feature_type': 1,
      'impl_status_chrome': 1,
      'standard_maturity': 1,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
    }
    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=invalid_request_body):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  @mock.patch('api.channels_api.construct_chrome_channels_details')
  def test_post__first_enterprise_notification_milestone_missing_enterprise(self, mock_call):
    """POST request successful with default first_enterprise_notification_milestone."""

    expected =  {
        'beta': { 'version': 420 }
    }
    mock_call.return_value = expected

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    valid_request_body = {
      'name': 'A name',
      'summary': 'A summary',
      'owner_emails': 'user@example.com,user2@example.com',
      'category': 2,
      'feature_type': 4,
      'impl_status_chrome': 3,
      'standard_maturity': 2,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
      'wpt': True,
    }

    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_post()

    # New feature should exist.
    new_feature: FeatureEntry | None = (
        FeatureEntry.get_by_id(response['feature_id']))
    self.assertIsNotNone(new_feature)

    # New feature's values should match fields in JSON body.
    for field, value in valid_request_body.items():
      if field == 'owner_emails':
        # list field types should convert the string into a list.
        self.assertEqual(new_feature.owner_emails, ['user@example.com', 'user2@example.com'])
      else:
        self.assertEqual(getattr(new_feature, field), value)

    # Enterprise first notice should be created.
    self.assertEqual(new_feature.first_enterprise_notification_milestone, 420)


  @mock.patch('api.channels_api.construct_chrome_channels_details')
  def test_post__first_enterprise_notification_milestone_missing_impact_enterprise(self, mock_call):
    """POST request successful with default first_enterprise_notification_milestone."""

    expected =  {
        'beta': { 'version': 420 }
    }
    mock_call.return_value = expected

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    valid_request_body = {
      'name': 'A name',
      'summary': 'A summary',
      'owner_emails': 'user@example.com,user2@example.com',
      'category': 2,
      'feature_type': 1,
      'impl_status_chrome': 3,
      'standard_maturity': 2,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
      'enterprise_impact': core_enums.ENTERPRISE_IMPACT_LOW,
      'wpt': True,
    }

    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_post()

    # New feature should exist.
    new_feature: FeatureEntry | None = (
        FeatureEntry.get_by_id(response['feature_id']))
    self.assertIsNotNone(new_feature)

    # New feature's values should match fields in JSON body.
    for field, value in valid_request_body.items():
      if field == 'owner_emails':
        # list field types should convert the string into a list.
        self.assertEqual(new_feature.owner_emails, ['user@example.com', 'user2@example.com'])
      else:
        self.assertEqual(getattr(new_feature, field), value)

    # Enterprise first notice should be created.
    self.assertEqual(new_feature.first_enterprise_notification_milestone, 420)


  @mock.patch('api.channels_api.construct_chrome_channels_details')
  def test_post__first_enterprise_notification_milestone_set(self, mock_call):
    """POST request successful with provided first_enterprise_notification_milestone."""

    expected =  {
        'beta': { 'version': 420 }
    }
    mock_call.return_value = expected

    # Signed-in user with permissions.
    testing_config.sign_in('admin@example.com', 123567890)

    valid_request_body = {
      'name': 'A name',
      'summary': 'A summary',
      'owner_emails': 'user@example.com,user2@example.com',
      'category': 2,
      'feature_type': 4,
      'enterprise_impact': core_enums.ENTERPRISE_IMPACT_HIGH,
      'impl_status_chrome': 3,
      'standard_maturity': 2,
      'ff_views': 1,
      'safari_views': 1,
      'web_dev_views': 1,
      'first_enterprise_notification_milestone': 123,
      'wpt': True,
    }

    request_path = f'{self.request_path}/create'
    with test_app.test_request_context(request_path, json=valid_request_body):
      response = self.handler.do_post()

    # New feature should exist.
    new_feature: FeatureEntry | None = (
        FeatureEntry.get_by_id(response['feature_id']))
    self.assertIsNotNone(new_feature)

    # New feature's values should match fields in JSON body.
    for field, value in valid_request_body.items():
      if field == 'owner_emails':
        # list field types should convert the string into a list.
        self.assertEqual(new_feature.owner_emails, ['user@example.com', 'user2@example.com'])
      else:
        self.assertEqual(getattr(new_feature, field), value)

    # Enterprise first notice should be created.
    self.assertEqual(new_feature.first_enterprise_notification_milestone, 123)
