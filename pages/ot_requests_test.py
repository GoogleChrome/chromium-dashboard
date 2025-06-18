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

import testing_config  # Must be imported before the module under test.

import flask
import werkzeug
from unittest import mock

from pages import ot_requests
from internals import core_enums
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Gate, Vote
from internals.user_models import AppUser
import settings


test_app = flask.Flask(__name__,
  template_folder=settings.get_flask_template_path())


class OriginTrialsRequestsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(name='feature one', summary='sum', category=1)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    # 1. Stage with an action requested (will go into creation_stages)
    self.creation_request_stage = Stage(
        feature_id=self.feature_id, stage_type=150,
        ot_action_requested=True)
    self.creation_request_stage.put()

    # 2. Stage ready for creation (will go into creation_stages)
    self.ready_for_creation_stage = Stage(
        feature_id=self.feature_id, stage_type=150,
        ot_setup_status=core_enums.OT_READY_FOR_CREATION)
    self.ready_for_creation_stage.put()

    # 3. An extension stage request needs an original OT stage and a valid Gate.
    self.ot_stage_for_extension = Stage(
        feature_id=self.feature_id, stage_type=150)
    self.ot_stage_for_extension.put()
    # The extension stage itself (will go into extension_stages).
    self.extension_stage = Stage(
        feature_id=self.feature_id,
        stage_type=core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
        ot_action_requested=True,
        ot_stage_id=self.ot_stage_for_extension.key.integer_id())
    self.extension_stage.put()
    # Add the required Gate for the extension stage.
    self.extension_gate = Gate(
        feature_id=self.feature_id,
        stage_id=self.extension_stage.key.integer_id(),
        gate_type=core_enums.GATE_API_EXTEND_ORIGIN_TRIAL,
        state=Vote.APPROVED)
    self.extension_gate.put()


    # 4. Stage awaiting activation (will go into activation_pending_stages)
    self.awaiting_activation_stage = Stage(
        feature_id=self.feature_id, stage_type=150,
        ot_setup_status=core_enums.OT_CREATED)
    self.awaiting_activation_stage.put()

    # 5. Stage with activation failure (will go into failed_stages)
    self.activation_failed_stage = Stage(
        feature_id=self.feature_id, stage_type=150,
        ot_setup_status=core_enums.OT_ACTIVATION_FAILED)
    self.activation_failed_stage.put()

    # 6. Stage with creation failure (will go into failed_stages)
    self.creation_failed_stage = Stage(
        feature_id=self.feature_id, stage_type=150,
        ot_setup_status=core_enums.OT_CREATION_FAILED)
    self.creation_failed_stage.put()

    self.handler = ot_requests.OriginTrialsRequests()
    self.request_path = '/admin/features/ot_requests'

    self.app_admin = AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

  def tearDown(self):
    for kind in [AppUser, FeatureEntry, Stage, Gate]:
      for entity in kind.query():
        entity.key.delete()
    testing_config.sign_out()

  def test_get__anon(self):
    """Anon user is redirected to the login page."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      response = self.handler.get()
    self.assertEqual(302, response.status_code)

  def test_get__non_admin(self):
    """A non-admin user receives a 403 Forbidden error."""
    testing_config.sign_in('user@example.com', 111)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.get()

  def test_get_template_data__no_stages(self):
    """Admin user sees empty lists when no stages match the queries."""
    # Remove all stages created in setUp.
    for kind in [Stage, Gate]:
      for entity in kind.query():
        entity.key.delete()

    testing_config.sign_in('admin@example.com', 222)
    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data()

    self.assertEqual([], template_data['creation_stages'])
    self.assertEqual([], template_data['extension_stages'])
    self.assertEqual([], template_data['activation_pending_stages'])
    self.assertEqual([], template_data['failed_stages'])

  def test_get_template_data__all_stages(self):
    """Admin user sees all relevant stages, correctly categorized."""
    testing_config.sign_in('admin@example.com', 222)
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data()

    # Test that the extension stage (with an approved gate) is present.
    self.assertEqual(1, len(actual_data['extension_stages']))
    self.assertEqual(
        self.extension_stage.key.integer_id(),
        actual_data['extension_stages'][0]['extension_stage']['id'])

    # Test that all other stage categories are also correctly populated.
    self.assertEqual(2, len(actual_data['creation_stages']))
    self.assertEqual(1, len(actual_data['activation_pending_stages']))
    self.assertEqual(2, len(actual_data['failed_stages']))

  def test_get_template_data__non_approved_extension_is_ignored(self):
    """An extension stage with a denied gate is not included."""
    self.extension_gate.state = Vote.DENIED
    self.extension_gate.put()

    testing_config.sign_in('admin@example.com', 222)
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data()

    self.assertEqual([], actual_data['extension_stages'])

  def test_get_template_data__extension_with_na_gate_is_included(self):
    """An extension stage with a gate state of N/A is included."""
    self.extension_gate.state = Vote.NA
    self.extension_gate.put()

    testing_config.sign_in('admin@example.com', 222)
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data()

    self.assertEqual(1, len(actual_data['extension_stages']))
    self.assertEqual(
        self.extension_stage.key.integer_id(),
        actual_data['extension_stages'][0]['extension_stage']['id'])

  @mock.patch('logging.warning')
  def test_get_template_data__extension_with_bad_ot_stage_id(
      self, mock_logging_warning):
    """An extension stage with a bad ot_stage_id is skipped and logs a warning."""
    # Set the ot_stage_id to a non-existent ID
    self.extension_stage.ot_stage_id = 99999
    self.extension_stage.put()

    testing_config.sign_in('admin@example.com', 222)
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data()

    # The malformed extension request should not be included.
    self.assertEqual([], actual_data['extension_stages'])
    # A warning should have been logged.
    mock_logging_warning.assert_called_once()
    self.assertIn('found with invalid OT stage ID 99999',
                  mock_logging_warning.call_args[0][0])
