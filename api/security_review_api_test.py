# Copyright 2025 Google Inc.
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

from unittest import mock

import flask
import requests
import werkzeug.exceptions  # Flask HTTP stuff.

import testing_config  # Must be imported before the module under test.
from api import security_review_api
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Gate, Vote

test_app = flask.Flask(__name__)


class SecurityReviewAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        feature_type=1, name='feature one', summary='sum', category=1,
        owner_emails=['owner@example.com'], security_continuity_id=123)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()

    self.stage_1 = Stage(
        feature_id=self.feature_1_id, stage_type=150,
        origin_trial_id='-1234567890')
    self.stage_1.put()

    self.gate_1 = Gate(feature_id=self.feature_1_id,
                          stage_id=self.stage_1.key.integer_id(),
                          gate_type=3, state=Vote.APPROVED)
    self.gate_1.put()
    self.gate_1_id = self.gate_1.key.integer_id()
    
    self.handler = security_review_api.SecurityReviewAPI()
    self.request_path = (f'/api/v0/{self.feature_1_id}/{self.stage_1.key.integer_id()}'
                         '/create-security-review-issue')
    self.valid_json_body = {
        'feature_id': self.feature_1_id,
        'gate_id': self.gate_1_id,
    }

  def tearDown(self):
    testing_config.sign_out()
    for kind in [FeatureEntry, Gate, Stage]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_post__success(self, mock_create_issue):
    """A valid request is processed successfully and the feature is updated."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create_issue.return_value = (456, None)

    with test_app.test_request_context(
        self.request_path, method='POST', json=self.valid_json_body):
      response = self.handler.do_post()

    self.assertEqual(response.message, 'Security review issue 456 created successfully.')
    mock_create_issue.assert_called_once_with(
        feature_id=self.feature_1_id,
        gate_id=self.gate_1_id,
        security_continuity_id=123
    )
    # The feature in datastore should be updated with the new issue ID.
    updated_feature = FeatureEntry.get_by_id(self.feature_1_id)
    self.assertEqual(updated_feature.security_launch_issue_id, 456)

  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_post__success_without_continuity_id(self, mock_create_issue):
    """A request for a feature without a continuity ID is still valid."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create_issue.return_value = (789, None)
    
    # Create a feature specifically without the continuity ID for this test.
    feature_2 = FeatureEntry(
        name='feature two', summary='sum2', category=1,
        owner_emails=['owner@example.com'])
    feature_2.put()
    body = {'feature_id': feature_2.key.integer_id(), 'gate_id': self.gate_1_id}

    with test_app.test_request_context(
        self.request_path, method='POST', json=body):
      self.handler.do_post()

    mock_create_issue.assert_called_once_with(
        feature_id=feature_2.key.integer_id(),
        gate_id=self.gate_1_id,
        security_continuity_id=None
    )
    updated_feature = FeatureEntry.get_by_id(feature_2.key.integer_id())
    self.assertEqual(updated_feature.security_launch_issue_id, 789)
    feature_2.key.delete()

  def test_do_post__missing_feature_id(self):
    """A 400 is returned if the feature_id is missing from the request."""
    testing_config.sign_in('owner@example.com', 1234567890)
    json_body = {'gate_id': self.gate_1_id}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_do_post__feature_not_found(self):
    """A 404 is returned if the feature does not exist."""
    testing_config.sign_in('owner@example.com', 1234567890)
    json_body = {'feature_id': 999, 'gate_id': self.gate_1_id}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post()
  
  def test_do_post__gate_not_found(self):
    """A 404 is returned if the gate does not exist."""
    testing_config.sign_in('owner@example.com', 1234567890)
    json_body = {'feature_id': self.feature_1_id, 'gate_id': 999}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post()

  def test_do_post__already_has_issue(self):
    """A 400 is returned if the feature already has a security review issue."""
    testing_config.sign_in('owner@example.com', 1234567890)
    self.feature_1.security_launch_issue_id = 98765
    self.feature_1.put()
    with test_app.test_request_context(
        self.request_path, method='POST', json=self.valid_json_body):
      with self.assertRaisesRegex(
        werkzeug.exceptions.BadRequest,
        'already has a security review issue'
      ):
        self.handler.do_post()

  def test_do_post__permission_denied_anon(self):
    """A 403 is returned for anonymous users."""
    testing_config.sign_out()
    with test_app.test_request_context(
        self.request_path, method='POST', json=self.valid_json_body):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()
        
  def test_do_post__permission_denied_non_owner(self):
    """A 403 is returned for signed-in users who do not have edit permission."""
    testing_config.sign_in('user@example.com', 9876543210)
    with test_app.test_request_context(
        self.request_path, method='POST', json=self.valid_json_body):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_post__api_request_exception(self, mock_create_issue):
    """A 500 is returned if the external API call fails with a request exception."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create_issue.side_effect = requests.exceptions.RequestException
    with test_app.test_request_context(
        self.request_path, method='POST', json=self.valid_json_body):
      with self.assertRaisesRegex(
        werkzeug.exceptions.InternalServerError,
        'Error communicating with the issue creation service.'
      ):
        self.handler.do_post()
    
    updated_feature = FeatureEntry.get_by_id(self.feature_1_id)
    self.assertIsNone(updated_feature.security_launch_issue_id)

  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_post__api_key_error(self, mock_create_issue):
    """A 500 is returned if the external API response is malformed."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create_issue.side_effect = KeyError
    with test_app.test_request_context(
        self.request_path, method='POST', json=self.valid_json_body):
      with self.assertRaisesRegex(
        werkzeug.exceptions.InternalServerError,
        'Malformed response from the issue creation service.'
      ):
        self.handler.do_post()

  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_post__api_unexpected_response(self, mock_create_issue):
    """A 500 is returned if the API gives an empty, non-error response."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create_issue.return_value = (None, None)
    with test_app.test_request_context(
        self.request_path, method='POST', json=self.valid_json_body):
      with self.assertRaisesRegex(
        werkzeug.exceptions.InternalServerError,
        'Issue creation failed for an unknown reason.'
      ):
        self.handler.do_post()

  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_post__api_call_failed_with_reason(self, mock_create_issue):
    """A 500 is returned if the API response contains a failure reason."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create_issue.return_value = (456, 'Failed to create issue.')

    with test_app.test_request_context(
        self.request_path, method='POST', json=self.valid_json_body):
      with self.assertRaisesRegex(
        werkzeug.exceptions.InternalServerError,
        'Failed to create issue.'
      ):
        self.handler.do_post()
    
    # The launch ID is saved even on failure.
    updated_feature = FeatureEntry.get_by_id(self.feature_1_id)
    self.assertEqual(updated_feature.security_launch_issue_id, 456)
