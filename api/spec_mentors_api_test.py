# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testing_config  # isort: split

import json
import os.path
from datetime import datetime

import flask
from werkzeug.exceptions import HTTPException

from api import features_api, spec_mentors_api
from framework import rediscache
from internals import user_models
from internals.core_models import FeatureEntry

test_app = flask.Flask(__name__)

BASE_FEATURE_CREATE_BODY = {
  'name': 'A name',
  'summary': 'A summary',
  'owner_emails': 'user@example.com',
  'category': 2,
  'feature_type': 1,
  'impl_status_chrome': 3,
  'standard_maturity': 2,
  'ff_views': 1,
  'safari_views': 1,
  'web_dev_views': 1,
}


class SpecMentorsAPITest(testing_config.CustomTestCase):
  def setUp(self):
    self.api_base = '/api/v0'
    self.request_path = f'{self.api_base}/spec_mentors'
    self.spec_mentors_handler = spec_mentors_api.SpecMentorsAPI()

    self.feature_handler = features_api.FeaturesAPI()

    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

    self.created_features = []

  def tearDown(self):
    for feature in self.created_features:
      feature.key.delete()
    self.app_admin.key.delete()
    testing_config.sign_out()

    rediscache.delete_keys_with_prefix('features')
    rediscache.delete_keys_with_prefix('FeatureEntries')

  def createFeature(self, params) -> FeatureEntry:
    with test_app.test_request_context(
      f'{self.api_base}/features/create', json=BASE_FEATURE_CREATE_BODY | params
    ):
      response = self.feature_handler.do_post()
    feature = FeatureEntry.get_by_id(response['feature_id'])
    self.created_features.append(feature)
    return feature

  def test_finds_one_mentored_feature(self):
    """Returns the single feature that exists, which has a mentor."""
    # Create a feature using the admin user.
    testing_config.sign_in(self.app_admin.email, 123567890)

    feature = self.createFeature({'name': 'The feature'})
    feature.spec_mentor_emails = ['mentor@example.org']
    feature.put()
    testing_config.sign_out()

    with test_app.test_request_context(self.request_path):
      response = self.spec_mentors_handler.do_get()

    self.assertEqual(
      response,
      [
        {
          'email': 'mentor@example.org',
          'mentored_features': [{'id': feature.key.id(), 'name': 'The feature'}],
        }
      ],
    )

  def test_omits_unlisted_feature(self):
    """Does not return an unlisted feature that has a mentor."""
    # Create a feature using the admin user.
    testing_config.sign_in(self.app_admin.email, 123567890)

    feature = self.createFeature({'name': 'The feature'})
    feature.spec_mentor_emails = ['mentor@example.org']
    feature.unlisted = True
    feature.put()
    testing_config.sign_out()

    with test_app.test_request_context(self.request_path):
      response = self.spec_mentors_handler.do_get()

    self.assertEqual(response, [])

  def test_obeys_after_param(self):
    """The ?after URL parameter filters features."""
    # Create a feature using the admin user.
    testing_config.sign_in(self.app_admin.email, 123567890)

    feature = self.createFeature({'name': 'The feature'})
    feature.spec_mentor_emails = ['mentor@example.org']
    feature.updated = datetime.fromisoformat('2024-01-14')
    feature.put()
    testing_config.sign_out()

    with test_app.test_request_context(f'{self.request_path}?after=2024-01-15'):
      response = self.spec_mentors_handler.do_get()

    self.assertEqual(response, [])

    # Now the feature was last updated after the 'after' param.
    feature.updated = datetime.fromisoformat('2024-01-16')
    feature.put()

    with test_app.test_request_context(f'{self.request_path}?after=2024-01-15'):
      response = self.spec_mentors_handler.do_get()
    self.assertEqual(
      response,
      [
        {
          'email': 'mentor@example.org',
          'mentored_features': [{'id': feature.key.id(), 'name': 'The feature'}],
        }
      ],
    )

  def test_fails_on_malformed_after_param(self):
    """An ?after value that isn't a date returns a 400 error."""
    with test_app.test_request_context(f'{self.request_path}?after=arglebargle'):
      with self.assertRaises(HTTPException) as cm:
        self.spec_mentors_handler.do_get()
      self.assertEqual(cm.exception.code, 400)

  def test_sorts_mentors_alphabetically(self):
    # Create a feature using the admin user.
    testing_config.sign_in(self.app_admin.email, 123567890)

    feature = self.createFeature({'name': 'The feature'})
    feature.spec_mentor_emails = ['bmentor@example.org', 'amentor@example.org']
    feature.put()
    testing_config.sign_out()

    with test_app.test_request_context(self.request_path):
      response = self.spec_mentors_handler.do_get()

    self.assertEqual(
      response,
      [
        {
          'email': 'amentor@example.org',
          'mentored_features': [{'id': feature.key.id(), 'name': 'The feature'}],
        },
        {
          'email': 'bmentor@example.org',
          'mentored_features': [{'id': feature.key.id(), 'name': 'The feature'}],
        },
      ],
    )

  def test_sorts_features_by_updated_date_recent_first(self):
    # Create a feature using the admin user.
    testing_config.sign_in(self.app_admin.email, 123567890)

    feature1 = self.createFeature({'name': 'First feature'})
    feature1.spec_mentor_emails = ['mentor@example.org']
    feature1.put()

    feature2 = self.createFeature({'name': 'Second feature'})
    feature2.spec_mentor_emails = ['mentor@example.org']
    feature2.put()
    testing_config.sign_out()

    with test_app.test_request_context(self.request_path):
      response = self.spec_mentors_handler.do_get()
    self.assertEqual(
      response,
      [
        {
          'email': 'mentor@example.org',
          'mentored_features': [
            # The later-created feature is listed first.
            {'id': feature2.key.id(), 'name': 'Second feature'},
            {'id': feature1.key.id(), 'name': 'First feature'},
          ],
        }
      ],
    )

    # Make the first feature more-recently updated.
    feature1.updated = datetime.now()
    feature1.put()

    with test_app.test_request_context(self.request_path):
      response = self.spec_mentors_handler.do_get()
    self.assertEqual(
      response,
      [
        {
          'email': 'mentor@example.org',
          'mentored_features': [
            # And the order switches.
            {'id': feature1.key.id(), 'name': 'First feature'},
            {'id': feature2.key.id(), 'name': 'Second feature'},
          ],
        }
      ],
    )

  def test_organizes_features_by_mentor(self):
    # Create a feature using the admin user.
    testing_config.sign_in(self.app_admin.email, 123567890)

    feature1 = self.createFeature({'name': 'First feature'})
    feature1.spec_mentor_emails = ['mentor@example.org', 'expert@example.com']
    feature1.put()

    feature2 = self.createFeature({'name': 'Second feature'})
    feature2.spec_mentor_emails = ['mentor@example.org']
    feature2.put()
    testing_config.sign_out()

    with test_app.test_request_context(self.request_path):
      response = self.spec_mentors_handler.do_get()

    # Unlike the other test expectations in this file, this one is saved to a JSON file so the
    # Playwright tests can use it as a mock API response. Because the real feature IDs are
    # dynamically generated, we have to slot them into the right places here.
    with open(
      os.path.join(
        os.path.dirname(__file__),
        '../packages/playwright/tests/spec_mentor_api_result.json',
      )
    ) as f:
      expected_response = json.load(f)
    expected_response[0]['mentored_features'][0]['id'] = feature1.key.id()
    expected_response[1]['mentored_features'][0]['id'] = feature2.key.id()
    expected_response[1]['mentored_features'][1]['id'] = feature1.key.id()

    self.assertEqual(response, expected_response)
