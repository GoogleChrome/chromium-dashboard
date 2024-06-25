# Copyright 2022 Google Inc.
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
import settings
from datetime import datetime
from unittest import mock

from internals import approval_defs
from internals import core_enums
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote
from internals import reminders

from google.cloud import ndb  # type: ignore

test_app = flask.Flask(__name__,
  template_folder=settings.get_flask_template_path())

# Load testdata to be used across all of the CustomTestCases
TESTDATA = testing_config.Testdata(__file__)

class MockResponse:
  """Creates a fake response object for testing."""
  def __init__(self, status_code=200, text='{}'):
    self.status_code = status_code
    self.text = text


def make_test_features():
  feature_1 = FeatureEntry(
      name='feature one', summary='sum',
      owner_emails=['feature_owner@example.com'],
      category=1, feature_type=0)
  feature_1.put()
  stages = [110, 120, 130, 140, 150, 151, 160]
  for stage_type in stages:
    stage = Stage(feature_id=feature_1.key.integer_id(), stage_type=stage_type)
    # Add a starting milestone for the origin trial stage.
    if stage_type == 150:
      stage.milestones = MilestoneSet(desktop_first=100)
    stage.put()

  feature_2 = FeatureEntry(
      name='feature two', summary='sum',
      creator_email='owner_2@example.com',
      owner_emails=['owner_1@example.com', 'owner_2@example.com'],
      editor_emails=['feature_editor@example.com'],
      spec_mentor_emails=['mentor@example.com'],
      category=1, feature_type=1)
  feature_2.put()

  stages = [220, 230, 250, 251, 260]
  for stage_type in stages:
    stage = Stage(feature_id=feature_2.key.integer_id(), stage_type=stage_type)
    # Add a starting milestone for the shipping stage.
    if stage_type == 260:
      stage.milestones = MilestoneSet(desktop_first=150)
    stage.put()

  feature_3 = FeatureEntry(
      name='feature three', summary='sum', category=1, feature_type=2)
  feature_3.put()
  stages = [320, 330, 360]
  for stage_type in stages:
    stage = Stage(feature_id=feature_3.key.integer_id(), stage_type=stage_type)
    stage.put()

  return feature_1, feature_2, feature_3


class FunctionTest(testing_config.CustomTestCase):

  def setUp(self):
    self.current_milestone_info = {
        'earliest_beta': '2022-09-21T12:34:56',
    }
    self.feature_template = FeatureEntry(id=123,
      name='feature one', summary='sum',
      creator_email='creator@example.com',
      owner_emails=['feature_owner@example.com'],
      editor_emails=['feature_editor@example.com'],
      spec_mentor_emails=['mentor@example.com'],
      category=1, feature_type=0)
    stages = [110, 120, 130, 140, 150, 151, 160, 1061]
    for stage_type in stages:
      stage = Stage(feature_id=123, stage_type=stage_type)
      # OT stage.
      if stage_type == 150:
        stage.milestones = MilestoneSet(desktop_first=100, desktop_last=105)
      # OT extension stage.
      if stage_type == 151:
        stage.milestones = MilestoneSet(desktop_last=108)
      # Enterprise rollout stage.
      if stage_type == 1061:
        stage.rollout_milestone = 110
      stage.put()

    self.feature_template.put()

    self.maxDiff = None

  def tearDown(self) -> None:
    kinds: list[ndb.Model] = [FeatureEntry, Stage]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_choose_email_recipients__normal(self):
    """Normal reminders go to feature participants."""
    actual = reminders.choose_email_recipients(
        self.feature_template, False)
    expected = ['feature_owner@example.com',
                ]
    self.assertEqual(set(actual), set(expected))

  @mock.patch('settings.PROD', True)
  def test_choose_email_recipients__escalated(self):
    """Escalated reminders go to feature participants and lists."""
    actual = reminders.choose_email_recipients(
        self.feature_template, True)
    expected = ['creator@example.com',
                'feature_owner@example.com',
                'feature_editor@example.com',
                'mentor@example.com',
                'webstatus@google.com',
                'cbe-releasenotes@google.com',
                ]
    self.assertEqual(set(actual), set(expected))

  def test_build_email_tasks_feature_accuracy(self):
    with test_app.app_context():
      handler = reminders.FeatureAccuracyHandler()
      actual = reminders.build_email_tasks(
          [(self.feature_template, 100)],
          '[Action requested] Update %s',
          handler.EMAIL_TEMPLATE_PATH,
          self.current_milestone_info,
          handler.should_escalate_notification)

    self.assertEqual(1, len(actual))
    task = actual[0]
    self.assertEqual('feature_owner@example.com', task['to'])
    self.assertEqual('[Action requested] Update feature one', task['subject'])
    self.assertEqual(None, task['reply_to'])
    # TESTDATA.make_golden(task['html'], 'test_build_email_tasks_feature_accuracy.html')
    self.assertMultiLineEqual(
      TESTDATA['test_build_email_tasks_feature_accuracy.html'], task['html'])

  def test_build_email_tasks_feature_accuracy__enterprise(self):
    with test_app.app_context():
      handler = reminders.FeatureAccuracyHandler()
      actual = reminders.build_email_tasks(
          [(self.feature_template, 110)],
          '[Action requested] Update %s',
          handler.EMAIL_TEMPLATE_PATH,
          self.current_milestone_info,
          handler.should_escalate_notification)

    self.assertEqual(1, len(actual))
    task = actual[0]
    self.assertEqual('feature_owner@example.com', task['to'])
    self.assertEqual('[Action requested] Update feature one', task['subject'])
    self.assertEqual(None, task['reply_to'])
    TESTDATA.make_golden(task['html'], 'test_build_email_tasks_feature_accuracy_enterprise.html')
    self.assertMultiLineEqual(
        TESTDATA['test_build_email_tasks_feature_accuracy_enterprise.html'],
        task['html'])

  def test_build_email_tasks_feature_accuracy__escalated(self):
    # Set feature to have outstanding notifications to cause escalation.
    self.feature_template.outstanding_notifications = 2

    with test_app.app_context():
      handler = reminders.FeatureAccuracyHandler()
      actual = reminders.build_email_tasks(
          [(self.feature_template, 100)],
          '[Action requested] Update %s',
          handler.EMAIL_TEMPLATE_PATH,
          self.current_milestone_info,
          handler.should_escalate_notification)

    self.assertEqual(5, len(actual))
    task = actual[0]
    self.assertEqual(
        'ESCALATED: [Action requested] Update feature one', task['subject'])
    self.assertEqual(None, task['reply_to'])
    # TESTDATA.make_golden(task['html'], 'test_build_email_tasks_escalated_feature_accuracy.html')
    self.assertMultiLineEqual(
      TESTDATA['test_build_email_tasks_escalated_feature_accuracy.html'], task['html'])

  def test_build_email_tasks_prepublication(self):
    with test_app.app_context():
      handler = reminders.PrepublicationHandler()
      actual = reminders.build_email_tasks(
          [(self.feature_template, 100)], '[Action requested] Update %s',
          handler.EMAIL_TEMPLATE_PATH,
          self.current_milestone_info, handler.should_escalate_notification)
    self.assertEqual(1, len(actual))
    task = actual[0]
    self.assertEqual('feature_owner@example.com', task['to'])
    self.assertEqual('[Action requested] Update feature one', task['subject'])
    self.assertEqual(None, task['reply_to'])
    # TESTDATA.make_golden(task['html'], 'test_build_email_tasks_prepublication.html')
    self.assertMultiLineEqual(
      TESTDATA['test_build_email_tasks_prepublication.html'], task['html'])

class FeatureAccuracyHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1, self.feature_2, self.feature_3 = make_test_features()
    self.handler = reminders.FeatureAccuracyHandler()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()
    for stage in Stage.query():
      stage.key.delete()

  @mock.patch('requests.get')
  def test_determine_features_to_notify__no_features(self, mock_get):
    mock_return = MockResponse(
        text=('{"mstones":[{"mstone": "40", '
              '"earliest_beta": "2018-01-01T01:23:45"}]}'))
    mock_get.return_value = mock_return
    result = self.handler.get_template_data()
    expected = {'message': '0 email(s) sent or logged.'}
    self.assertEqual(result, expected)

  @mock.patch('requests.get')
  def test_determine_features_to_notify__valid_features(self, mock_get):
    mock_return = MockResponse(
        text=('{"mstones":[{"mstone": "100", '
              '"earliest_beta": "2022-08-01T01:23:45"}]}'))
    mock_get.return_value = mock_return
    with test_app.app_context():
      result = self.handler.get_template_data()
    expected_message = ('1 email(s) sent or logged.\n'
                        'Recipients:\n'
                        'feature_owner@example.com')
    expected = {'message': expected_message}
    self.assertEqual(result, expected)

  @mock.patch('requests.get')
  def test_determine_features_to_notify__multiple_owners(self, mock_get):
    mock_return = MockResponse(
        text=('{"mstones":[{"mstone": "148", '
              '"earliest_beta": "2024-02-03T01:23:45"}]}'))
    mock_get.return_value = mock_return
    with test_app.app_context():
      result = self.handler.get_template_data()
    expected_message = ('2 email(s) sent or logged.\n'
                        'Recipients:\n'
                        'owner_1@example.com\n'
                        'owner_2@example.com')
    expected = {'message': expected_message}
    self.assertEqual(result, expected)

  @mock.patch('requests.get')
  def test_determine_features_to_notify__escalated(self, mock_get):
    self.feature_1.outstanding_notifications = 1
    self.feature_2.outstanding_notifications = 2

    mock_return = MockResponse(
        text=('{"mstones":[{"mstone": "148", '
              '"earliest_beta": "2024-02-03T01:23:45"}]}'))
    mock_get.return_value = mock_return
    with test_app.app_context():
      result = self.handler.get_template_data()
    # More email tasks should be created to notify extended contributors.
    expected_message = ('5 email(s) sent or logged.\n'
                        'Recipients:\n'
                        'feature_editor@example.com\n'
                        'jrobbins-test@googlegroups.com\n'
                        'mentor@example.com\n'
                        'owner_1@example.com\n'
                        'owner_2@example.com')
    expected = {'message': expected_message}
    self.assertEqual(result, expected)

    # F1 outstanding should be unchanged and F2 should have one extra.
    self.assertEqual(self.feature_1.outstanding_notifications, 1)
    self.assertEqual(self.feature_2.outstanding_notifications, 3)

  @mock.patch('requests.get')
  def test_determine_features_to_notify__escalated_not_outstanding(
      self, mock_get):
    self.feature_1.outstanding_notifications = 2
    self.feature_2.outstanding_notifications = 1

    mock_return = MockResponse(
        text=('{"mstones":[{"mstone": "148", '
              '"earliest_beta": "2024-02-03T01:23:45"}]}'))
    mock_get.return_value = mock_return
    with test_app.app_context():
      result = self.handler.get_template_data()
    expected_message = ('2 email(s) sent or logged.\n'
                        'Recipients:\n'
                        'owner_1@example.com\n'
                        'owner_2@example.com')
    expected = {'message': expected_message}
    self.assertEqual(result, expected)

    # F1 outstanding should be unchanged and F2 should have one extra.
    self.assertEqual(self.feature_1.outstanding_notifications, 2)
    self.assertEqual(self.feature_2.outstanding_notifications, 2)


class PrepublicationHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.current_milestone_info = {
        'earliest_beta': '2022-09-21T12:34:56',
    }
    self.handler = reminders.PrepublicationHandler()

  def test_prefilter_features__off_week(self):
    """No reminders sent because the next beta is far future or past."""
    features = ['mock feature']

    mock_now = datetime(2022, 9, 1)  # Way before beta.
    actual = self.handler.prefilter_features(
        self.current_milestone_info, features, now=mock_now)
    self.assertEqual([], actual)

    mock_now = datetime(2022, 9, 18)  # After DevRel cut-off.
    actual = self.handler.prefilter_features(
        self.current_milestone_info, features, now=mock_now)
    self.assertEqual([], actual)

  def test_prefilter_features__on_week(self):
    """Reminders are sent because the next beta is coming up."""
    features = ['mock feature']
    mock_now = datetime(2022, 9, 12)
    actual = self.handler.prefilter_features(
        self.current_milestone_info, features, now=mock_now)
    self.assertEqual(['mock feature'], actual)


class SLOOverdueHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1, self.feature_2, self.feature_3 = make_test_features()
    self.gate_1 = Gate(
        feature_id=self.feature_1.key.integer_id(),
        stage_id=1111, gate_type=core_enums.GATE_ENTERPRISE_SHIP,
        state=Gate.PREPARING)
    self.gate_1.put()
    self.handler = reminders.SLOOverdueHandler()
    # Just a non-empty date, the value is ignored by mock_remaining_days
    self.request_date = datetime(2023, 6, 7, 12, 30, 0)

  def tearDown(self) -> None:
    kinds: list[ndb.Model] = [FeatureEntry, Stage, Gate]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_get_template_data__no_reviews_pending(self):
    with test_app.app_context():
      actual = self.handler.get_template_data()

    expected_message = ('0 email(s) sent or logged.')
    expected = {'message': expected_message}
    self.assertEqual(actual, expected)

  @mock.patch('internals.slo.remaining_days')
  def test_get_template_data__no_reviews_due(self, mock_remaining_days):
    self.gate_1.state = Vote.REVIEW_REQUESTED
    self.gate_1.put()
    mock_remaining_days.return_value = 1

    with test_app.app_context():
      actual = self.handler.get_template_data()

    expected_message = '0 email(s) sent or logged.'
    expected = {'message': expected_message}
    self.assertEqual(actual, expected)

  @mock.patch('internals.slo.remaining_days')
  def test_get_template_data__one_due_unassigned(self, mock_remaining_days):
    self.gate_1.state = Vote.REVIEW_REQUESTED
    self.gate_1.requested_on = self.request_date
    self.gate_1.put()
    mock_remaining_days.return_value = -1

    with test_app.app_context():
      actual = self.handler.get_template_data()

    expected_message = (f'4 email(s) sent or logged.\n'
                        'Recipients:\n'
                        'angelaweber@google.com\n'
                        'bheenan@google.com\n'
                        'davidayad@google.com\n'
                        'mhoste@google.com')
    expected = {'message': expected_message}
    self.assertEqual(actual, expected)

  @mock.patch('internals.slo.remaining_days')
  def test_get_template_data__one_due_assigned(self, mock_remaining_days):
    self.gate_1.state = Vote.REVIEW_REQUESTED
    self.gate_1.assignee_emails = [
        'b_assignee@example.com', 'a_assignee@example.com']
    self.gate_1.requested_on = self.request_date
    self.gate_1.put()
    mock_remaining_days.return_value = -1

    with test_app.app_context():
      actual = self.handler.get_template_data()

    expected_message = (f'2 email(s) sent or logged.\n'
                        'Recipients:\n'
                        'a_assignee@example.com\n'
                        'b_assignee@example.com')
    expected = {'message': expected_message}
    self.assertEqual(actual, expected)

  @mock.patch('internals.slo.remaining_days')
  def test_get_template_data__one_overdue_unassigned(self, mock_remaining_days):
    self.gate_1.state = Vote.REVIEW_REQUESTED
    self.gate_1.requested_on = self.request_date
    self.gate_1.put()
    mock_remaining_days.return_value = -approval_defs.DEFAULT_SLO_LIMIT

    with test_app.app_context():
      actual = self.handler.get_template_data()

    expected_message = (f'4 email(s) sent or logged.\n'
                        'Recipients:\n'
                        'angelaweber@google.com\n'
                        'bheenan@google.com\n'
                        'davidayad@google.com\n'
                        'mhoste@google.com')
    expected = {'message': expected_message}
    self.assertEqual(actual, expected)

  @mock.patch('internals.slo.remaining_days')
  def test_get_template_data__one_overdue_assigned(self, mock_remaining_days):
    self.gate_1.state = Vote.REVIEW_REQUESTED
    self.gate_1.assignee_emails = [
        'bheenan@google.com', 'a_assignee@example.com']
    self.gate_1.requested_on = self.request_date
    self.gate_1.put()
    mock_remaining_days.return_value = -approval_defs.DEFAULT_SLO_LIMIT

    with test_app.app_context():
      actual = self.handler.get_template_data()

    expected_message = (f'5 email(s) sent or logged.\n'
                        'Recipients:\n'
                        'a_assignee@example.com\n'
                        'angelaweber@google.com\n'
                        'bheenan@google.com\n'
                        'davidayad@google.com\n'
                        'mhoste@google.com')
    expected = {'message': expected_message}
    self.assertEqual(actual, expected)

  @mock.patch('internals.slo.remaining_days')
  def test_get_template_data__old_reviews(self, mock_remaining_days):
    self.gate_1.state = Vote.REVIEW_REQUESTED
    self.gate_1.put()
    mock_remaining_days.return_value = 99

    with test_app.app_context():
      actual = self.handler.get_template_data()

    expected_message = '0 email(s) sent or logged.'
    expected = {'message': expected_message}
    self.assertEqual(actual, expected)
