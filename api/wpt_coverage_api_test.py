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
import werkzeug.exceptions
from unittest import mock
from datetime import datetime

import testing_config
from api import wpt_coverage_api
from internals import core_enums
from internals.core_models import FeatureEntry

test_app = flask.Flask(__name__)


class WPTCoverageAPITest(testing_config.CustomTestCase):

  def setUp(self):
    """Set up test data for the API handler."""
    self.handler = wpt_coverage_api.WPTCoverageAPI()

    # Create a feature to test against.
    self.feature_1 = FeatureEntry(
        id=123456,
        name='Test Feature 1',
        summary='Summary for testing',
        category=1,
        owner_emails=['owner@example.com'],
    )
    self.feature_1.put()

  def tearDown(self):
    """Tear down test data."""
    for entity in FeatureEntry.query():
      entity.key.delete()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  @mock.patch('framework.permissions.can_edit_feature')
  def test_do_post__success(self, mock_can_edit, mock_enqueue):
    """Ensure valid requests update the feature and enqueue a task."""
    mock_can_edit.return_value = True
    # Track the time before the operation to verify the timestamp update.
    before_call = datetime.now()

    params = {'feature_id': 123456}
    with test_app.test_request_context('/api/v0/generate-wpt-coverage-analysis',
                                       method='POST', json=params):
      response = self.handler.do_post()

    self.assertEqual(response, {'message': 'Task enqueued'})

    mock_can_edit.assert_called_once()

    # Verify Cloud Task was enqueued with correct parameters.
    mock_enqueue.assert_called_once_with(
        '/tasks/generate-wpt-coverage-analysis',
        {'feature_id': 123456}
    )

    updated_feature = FeatureEntry.get_by_id(123456)
    self.assertEqual(
        updated_feature.ai_test_eval_run_status,
        core_enums.AITestEvaluationStatus.IN_PROGRESS.value
    )
    self.assertIsNotNone(updated_feature.ai_test_eval_status_timestamp)
    self.assertGreaterEqual(updated_feature.ai_test_eval_status_timestamp,
                            before_call)

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  @mock.patch('framework.permissions.can_edit_feature')
  def test_do_post__forbidden(self, mock_can_edit, mock_enqueue):
    """Ensure requests without edit permissions abort with 403."""
    mock_can_edit.return_value = False

    params = {'feature_id': 123456}
    with test_app.test_request_context('/api/v0/generate-wpt-coverage-analysis',
                                       method='POST', json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

    # Verify no task was enqueued.
    mock_enqueue.assert_not_called()

    # Verify FeatureEntry was NOT updated.
    unchanged_feature = FeatureEntry.get_by_id(123456)
    self.assertIsNone(unchanged_feature.ai_test_eval_run_status)
    self.assertIsNone(unchanged_feature.ai_test_eval_status_timestamp)

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  def test_do_post__not_found(self, mock_enqueue):
    """Ensure requests for non-existent features abort with 404."""
    params = {'feature_id': 999999}  # ID that does not exist.
    with test_app.test_request_context('/api/v0/generate-wpt-coverage-analysis',
                                       method='POST', json=params):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post(feature_id=999999)

    mock_enqueue.assert_not_called()

  def test_do_post__missing_param(self):
    """Ensure requests missing required parameters abort appropriately."""
    # Missing 'feature_id'
    with test_app.test_request_context('/api/v0/generate-wpt-coverage-analysis',
                                       method='POST', json={}):
      # basehandlers usually raise BadRequest (400) if a required int param is missing
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  @mock.patch('framework.permissions.can_edit_feature')
  def test_do_post__already_in_progress(self, mock_can_edit, mock_enqueue):
    """Ensure requests abort with 409 if an analysis is already running."""
    mock_can_edit.return_value = True

    self.feature_1.ai_test_eval_run_status = (
        core_enums.AITestEvaluationStatus.IN_PROGRESS.value)
    self.feature_1.ai_test_eval_status_timestamp = datetime.now()
    self.feature_1.put()

    params = {'feature_id': self.feature_1.key.integer_id()}
    with test_app.test_request_context('/api/v0/generate-wpt-coverage-analysis',
                                       method='POST', json=params):
      with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
        self.handler.do_post()

      # Verify the status code inside the exception.
      self.assertEqual(cm.exception.response.status_code, 409)

      # Verify the Retry-After header is present and is an integer.
      self.assertIn('Retry-After', cm.exception.response.headers)
      retry_after = cm.exception.response.headers['Retry-After']
      self.assertTrue(str(retry_after).isdigit())

    # Verify we did not enqueue a duplicate task.
    mock_enqueue.assert_not_called()

  @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
  @mock.patch('framework.permissions.can_edit_feature')
  def test_do_post__confidential_feature(self, mock_can_edit, mock_enqueue):
    """Ensure requests for confidential features abort with 400."""
    mock_can_edit.return_value = True

    # Set the feature to confidential.
    self.feature_1.confidential = True
    self.feature_1.put()

    params = {'feature_id': self.feature_1.key.integer_id()}
    with test_app.test_request_context('/api/v0/generate-wpt-coverage-analysis',
                                       method='POST', json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
        self.handler.do_post()

      # Verify the specific error message matches your logic.
      self.assertEqual(
        cm.exception.description,
        ('Confidential feature information cannot be used to '
         'generate WTP coverage reports.')
      )

    # Verify no task was enqueued.
    mock_enqueue.assert_not_called()
