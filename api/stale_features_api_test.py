# Copyright 2025 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import flask
from unittest import mock
from datetime import datetime

import testing_config
from api import stale_features_api
from internals.core_models import FeatureEntry

test_app = flask.Flask(__name__)


class StaleFeaturesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    """Set up test data for the API handler."""
    self.handler = stale_features_api.StaleFeaturesAPI()
    self.feature_1_date = datetime(2025, 10, 1, 12, 30, 0)
    self.feature_2_date = datetime(2025, 9, 15, 0, 0, 0)

    # Feature 1: A standard stale feature.
    self.feature_1 = FeatureEntry(
        id=1,
        name='Stale Feature 1',
        summary='summary',
        category=1,
        owner_emails=['owner1@example.com'],
        outstanding_notifications=1,
        accurate_as_of=self.feature_1_date
    )
    self.feature_1.put()

    # Feature 2: Another stale feature with different properties.
    self.feature_2 = FeatureEntry(
        id=2,
        name='Stale Feature 2',
        summary='summary',
        category=1,
        owner_emails=['owner2@example.com', 'owner3@example.com'],
        outstanding_notifications=3,
        accurate_as_of=self.feature_2_date
    )
    self.feature_2.put()

    # Data structure that the mocked get_stale_features should return.
    self.mock_return_value = [
        (self.feature_1, 120, 'shipped_milestone'),
        (self.feature_2, 121, 'shipped_android_milestone')
    ]

  def tearDown(self):
    """Tear down test data."""
    for entity in FeatureEntry.query():
      entity.key.delete()

  @mock.patch('internals.feature_helpers.get_stale_features')
  def test_do_get__success(self, mock_get_stale_features):
    """The API should return a formatted list of stale features."""
    mock_get_stale_features.return_value = self.mock_return_value

    with test_app.test_request_context('/api/v0/stalefeatures'):
      response = self.handler.do_get()

    mock_get_stale_features.assert_called_once()
    self.assertIn('stale_features', response)
    stale_features_info = response['stale_features']
    self.assertEqual(len(stale_features_info), 2)

    # Use a dictionary for easy, order-independent lookup and assertion.
    response_map = {f['id']: f for f in stale_features_info}

    # Assertions for Feature 1.
    self.assertIn(self.feature_1.key.integer_id(), response_map)
    feature_1_info = response_map[self.feature_1.key.integer_id()]
    self.assertEqual(feature_1_info['name'], self.feature_1.name)
    self.assertEqual(feature_1_info['owner_emails'], self.feature_1.owner_emails)
    self.assertEqual(feature_1_info['milestone'], 120)
    self.assertEqual(feature_1_info['milestone_field'], 'shipped_milestone')
    self.assertEqual(feature_1_info['outstanding_notifications'],
                     self.feature_1.outstanding_notifications)
    self.assertEqual(feature_1_info['accurate_as_of'], '2025-10-01T12:30:00')

    # Assertions for Feature 2.
    self.assertIn(self.feature_2.key.integer_id(), response_map)
    feature_2_info = response_map[self.feature_2.key.integer_id()]
    self.assertEqual(feature_2_info['name'], self.feature_2.name)
    self.assertEqual(feature_2_info['owner_emails'], self.feature_2.owner_emails)
    self.assertEqual(feature_2_info['milestone'], 121)
    self.assertEqual(feature_2_info['milestone_field'], 'shipped_android_milestone')
    self.assertEqual(feature_2_info['outstanding_notifications'],
                     self.feature_2.outstanding_notifications)
    self.assertEqual(feature_2_info['accurate_as_of'], '2025-09-15T00:00:00')

  @mock.patch('internals.feature_helpers.get_stale_features')
  def test_do_get__no_stale_features(self, mock_get_stale_features):
    """The API should return an empty list when no features are stale."""
    mock_get_stale_features.return_value = []

    with test_app.test_request_context('/api/v0/stalefeatures'):
      response = self.handler.do_get()

    mock_get_stale_features.assert_called_once()
    self.assertIn('stale_features', response)
    self.assertEqual(response['stale_features'], [])
