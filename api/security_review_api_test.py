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
        owner_emails=['owner@example.com'], continuity_id=123)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.ot_stage_1 = Stage(
        feature_id=self.feature_1_id, stage_type=150,
        origin_trial_id='-1234567890')
    self.ot_stage_1.put()

    self.ot_gate_1 = Gate(feature_id=self.feature_1_id,
        stage_id=self.ot_stage_1.key.integer_id(),
        gate_type=3, state=Vote.APPROVED)
    self.ot_gate_1.put()
    self.request_path = (
        f'/api/v0/{self.feature_1_id}/{self.ot_stage_1.key.integer_id()}'
        '/create-security-review-issue')

    self.handler = security_review_api.SecurityReviewAPI()

  def test_do_post__feature_id_missing(self):
    """Give a 400 if the feature ID is not provided."""
    testing_config.sign_in('owner@example.com', 1234567890)
    json_body = {'gate_id': self.ot_gate_1.key.integer_id()}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
       self.handler.do_post()

  def test_do_post__feature_not_found(self):
    """Give a 404 if the no such feature exists."""
    testing_config.sign_in('owner@example.com', 1234567890)
    json_body = {'feature_id': 999, 'gate_id': self.ot_gate_1.key.integer_id()}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.NotFound):
       self.handler.do_post()

  def test_do_post__gate_id_missing(self):
    """Give a 400 if the no such stage exists."""
    testing_config.sign_in('owner@example.com', 1234567890)
    json_body = {'feature_id': self.feature_1_id}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
       self.handler.do_post()

  def test_do_post__gate_not_found(self):
    testing_config.sign_in('owner@example.com', 1234567890)
    """Give a 404 if the no such stage exists."""
    json_body = {'feature_id': self.feature_1_id, 'gate_id': 999}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.NotFound):
       self.handler.do_post()

  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_post__no_continuity_id(self, mock_create):
    """Request is still processed if no continuity ID exists."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create.return_value = (456, None)

    json_body = {
        'feature_id': self.feature_1_id,
        'gate_id': self.ot_gate_1.key.integer_id()}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      self.handler.do_post()
      mock_create.assert_called_once()
      self.assertEqual(456, self.feature_1.launch_issue_id)

  def test_do_post__anon(self):
    """Anon users cannot request origin trials."""
    testing_config.sign_out()
    json_body = {
        'feature_id': self.feature_1_id,
        'gate_id': self.ot_gate_1.key.integer_id()}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()
  
  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_post__valid(self, mock_create):
    """A valid request is processed successfully."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create.return_value = (456, None)

    json_body = {
        'feature_id': self.feature_1_id,
        'gate_id': self.ot_gate_1.key.integer_id()}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      self.handler.do_post()
      mock_create.assert_called_once()
      self.assertEqual(123, self.feature_1.continuity_id)
      self.assertEqual(456, self.feature_1.launch_issue_id)

  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_post__failed(self, mock_create):
    """A RequestException from the OT API is handled correctly."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create.side_effect = werkzeug.exceptions.InternalServerError

    json_body = {
        'feature_id': self.feature_1_id,
        'gate_id': self.ot_gate_1.key.integer_id()}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.InternalServerError):
        self.handler.do_post()
      mock_create.assert_called_once()
      self.assertEqual(None, self.feature_1.launch_issue_id)

  @mock.patch('framework.origin_trials_client.create_launch_issue')
  def test_do_patch__failed_with_reason(self, mock_create):
    """A response from the OT API containing a failed_reason is handled."""
    testing_config.sign_in('owner@example.com', 1234567890)
    mock_create.return_value = (456, 'Failed to create issue.')

    json_body = {
        'feature_id': self.feature_1_id,
        'gate_id': self.ot_gate_1.key.integer_id()}
    with test_app.test_request_context(
        self.request_path, method='POST', json=json_body):
      with self.assertRaises(werkzeug.exceptions.InternalServerError):
        self.handler.do_post()
      mock_create.assert_called_once()
      # launch_issue_id should be set if one is returned, regardless of failure.
      self.assertEqual(456, self.feature_1.launch_issue_id)