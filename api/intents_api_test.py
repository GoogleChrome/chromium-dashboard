# Copyright 2024 Google Inc.
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
import werkzeug.exceptions

import flask
from unittest import mock

from api import intents_api
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote
from internals.user_models import AppUser
import settings

test_app = flask.Flask(__name__,
  template_folder=settings.get_flask_template_path())


class IntentsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        feature_type=1, name='feature one', summary='sum', category=1,
        owner_emails=['owner@example.com'])
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.ot_stage_1 = Stage(
        feature_id=self.feature_1_id, stage_type=150,
        origin_trial_id='-1234567890')
    self.ot_stage_1.put()
    self.ot_gate_1 = Gate(feature_id=self.feature_1_id,
                stage_id=self.ot_stage_1.key.integer_id(),
                gate_type=2, state=Vote.APPROVED)
    self.ot_gate_1.put()
    self.extension_stage_1 = Stage(
        feature_id=self.feature_1_id, stage_type=151,
        ot_stage_id=self.ot_stage_1.key.integer_id(),
        milestones=MilestoneSet(desktop_last=153),
        intent_thread_url='https://example.com/intent')
    self.extension_stage_1.put()
    self.extension_gate_1 = Gate(feature_id=self.feature_1_id,
                stage_id=self.extension_stage_1.key.integer_id(),
                gate_type=3, state=Vote.APPROVED)
    self.extension_gate_1.put()

    self.devtrial_stage = Stage(feature_id=self.feature_1_id, stage_type=130)
    self.devtrial_stage.put()

    self.owner = AppUser(email='owner@example.com')
    self.owner.put()

    self.handler = intents_api.IntentsAPI()

  def tearDown(self):
    for kind in [AppUser, FeatureEntry, Gate, Stage]:
      for entity in kind.query():
        entity.key.delete()

  def test_get__valid(self):
    """A valid request returns intent draft info."""
    testing_config.sign_in('owner@example.com', 1234567890)
    request_path = (f'features/{self.feature_1_id}/'
                    f'{self.extension_stage_1.key.integer_id()}/intent')
    with test_app.test_request_context(request_path, method='GET'):
      response = self.handler.do_get(
          feature_id=self.feature_1_id,
          stage_id=self.extension_stage_1.key.integer_id())
    self.assertEqual('Intent to Extend Experiment: feature one',
                     response['subject'])
    # The contents of email body are already tested in intentpreview_test.
    self.assertTrue('email_body' in response)

  def test_get__no_edit_access(self):
    """403 returned when user does not have edit access to feature."""
    testing_config.sign_in('some_other_user@example.com', 1234567890)
    request_path = (f'features/{self.feature_1_id}/'
                    f'{self.ot_stage_1.key.integer_id()}/intent')
    with test_app.test_request_context(request_path, method='GET'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_get(feature_id=self.feature_1_id,
                            stage_id=self.ot_stage_1.key.integer_id())

  def test_get__bad_feature_id(self):
    """404 returned when feature is not found."""
    testing_config.sign_in('owner@example.com', 1234567890)
    request_path = f'features/-1/{self.ot_stage_1.key.integer_id()}/intent'
    with test_app.test_request_context(request_path, method='GET'):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(feature_id=-1,
                            stage_id=self.ot_stage_1.key.integer_id())

  def test_get__bad_stage_id(self):
    """404 returned when stage is not found."""
    testing_config.sign_in('owner@example.com', 1234567890)
    request_path = f'features/{self.feature_1_id}/-1/intent'
    with test_app.test_request_context(request_path, method='GET'):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(feature_id=self.feature_1_id,
                            stage_id=-1)

  @mock.patch("framework.cloud_tasks_helpers.enqueue_task")
  def test_post__valid(self, mock_enqueue_cloud_task):
    """A valid POST request will create a new notification task."""
    testing_config.sign_in('owner@example.com', 1234567890)

    body = {
      'gate_id': self.extension_gate_1.key.integer_id(),
      'intent_cc_emails': ['cc1@example.com', 'owner@example.com']
    }
    request_path = (f'features/{self.feature_1_id}/'
                    f'{self.extension_stage_1.key.integer_id()}/intent')
    with test_app.test_request_context(request_path, json=body):
      response = self.handler.do_post(
          feature_id=self.feature_1_id,
          stage_id=self.extension_stage_1.key.integer_id())
    self.assertEqual(response,
                     {'message': 'Email task submitted successfully.'})
    expected_task_params: intents_api.IntentGenerationOptions = {
      'subject': 'Intent to Extend Experiment: feature one',
      'feature_id': self.feature_1_id,
      'sections_to_show': ['i2p_thread', 'experiment', 'extension_reason'],
      'intent_stage': 11,
      'default_url': (f'http://localhost/feature/{self.feature_1_id}'
                      f'?gate={self.extension_gate_1.key.integer_id()}'),
      'intent_cc_emails': ['cc1@example.com', 'owner@example.com'],
    }
    mock_enqueue_cloud_task.assert_called_once_with(
        '/tasks/email-intent-to-blink-dev', expected_task_params)

  @mock.patch("framework.cloud_tasks_helpers.enqueue_task")
  def test_post__valid_ot(self, mock_enqueue_cloud_task):
    """A valid POST request will create a new notification task for OT
    stages."""
    testing_config.sign_in('owner@example.com', 1234567890)

    body = {
      'gate_id': self.ot_gate_1.key.integer_id(),
      'intent_cc_emails': ['cc33@example.com', 'owner@example.com']
    }
    request_path = (f'features/{self.feature_1_id}/'
                    f'{self.ot_stage_1.key.integer_id()}/intent')
    with test_app.test_request_context(request_path, json=body):
      response = self.handler.do_post(
          feature_id=self.feature_1_id,
          stage_id=self.ot_stage_1.key.integer_id())
    self.assertEqual(response,
                     {'message': 'Email task submitted successfully.'})
    expected_task_params: intents_api.IntentGenerationOptions = {
      'subject': 'Intent to Experiment: feature one',
      'feature_id': self.feature_1_id,
      'sections_to_show': ['i2p_thread', 'experiment', 'extension_reason'],
      'intent_stage': 3,
      'default_url': (f'http://localhost/feature/{self.feature_1_id}'
                      f'?gate={self.ot_gate_1.key.integer_id()}'),
      'intent_cc_emails': ['cc33@example.com', 'owner@example.com'],
    }
    mock_enqueue_cloud_task.assert_called_once_with(
        '/tasks/email-intent-to-blink-dev', expected_task_params)

  @mock.patch("framework.cloud_tasks_helpers.enqueue_task")
  def test_post__valid_no_gate_id(self, mock_enqueue_cloud_task):
    """A request with no gate_id will still show intent draft for devtrial."""
    testing_config.sign_in('owner@example.com', 1234567890)

    body = {
      'gate_id': None,
      'intent_cc_emails': ['cc1@example.com', 'owner@example.com']
    }
    request_path = (f'features/{self.feature_1_id}/'
                    f'{self.devtrial_stage.key.integer_id()}/intent')
    with test_app.test_request_context(request_path, json=body):
      response = self.handler.do_post(
          feature_id=self.feature_1_id,
          stage_id=self.devtrial_stage.key.integer_id())
    self.assertEqual(response,
                     {'message': 'Email task submitted successfully.'})
    expected_task_params: intents_api.IntentGenerationOptions = {
      'subject': 'Ready for Developer Testing: feature one',
      'feature_id': self.feature_1_id,
      'sections_to_show': ['i2p_thread', 'experiment'],
      'intent_stage': 2,
      'default_url': f'http://localhost/feature/{self.feature_1_id}',
      'intent_cc_emails': ['cc1@example.com', 'owner@example.com'],
    }
    mock_enqueue_cloud_task.assert_called_once_with(
        '/tasks/email-intent-to-blink-dev', expected_task_params)

  def test_post__anon(self):
    """403 returned when user is not signed in."""
    testing_config.sign_out()
    request_path = (f'features/{self.feature_1_id}/'
                    f'{self.ot_stage_1.key.integer_id()}/intent')
    with test_app.test_request_context(request_path, method='POST', json={}):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(feature_id=self.feature_1_id,
                            stage_id=self.ot_stage_1.key.integer_id())

  def test_post__no_edit_access(self):
    """403 returned when user does not have edit access to feature."""
    testing_config.sign_in('some_other_user@example.com', 1234567890)
    request_path = (f'features/{self.feature_1_id}/'
                    f'{self.ot_stage_1.key.integer_id()}/intent')
    with test_app.test_request_context(request_path, method='POST', json={}):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(feature_id=self.feature_1_id,
                            stage_id=self.ot_stage_1.key.integer_id())

  def test_post__bad_feature_id(self):
    """404 returned when feature is not found."""
    testing_config.sign_in('owner@example.com', 1234567890)
    request_path = f'features/-1/{self.ot_stage_1.key.integer_id()}/intent'
    with test_app.test_request_context(request_path, method='POST', json={}):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(feature_id=-1,
                            stage_id=self.ot_stage_1.key.integer_id())

  def test_post__bad_stage_id(self):
    """404 returned when stage is not found."""
    testing_config.sign_in('owner@example.com', 1234567890)
    request_path = f'features/{self.feature_1_id}/-1/intent'
    with test_app.test_request_context(request_path, method='POST', json={}):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(feature_id=self.feature_1_id,
                            stage_id=-1)
