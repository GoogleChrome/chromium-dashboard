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

from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.legacy_models import Feature
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
      owner_emails=['owner_1@example.com', 'owner_2@example.com'],
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

    self.old_feature_template = Feature(id=123,
        name='feature one', summary='sum', owner=['feature_owner@example.com'],
        category=1, feature_type=0, ot_milestone_desktop_start=100)
    self.feature_template = FeatureEntry(id=123,
      name='feature one', summary='sum',
      owner_emails=['feature_owner@example.com'],
      category=1, feature_type=0)
    stages = [110, 120, 130, 140, 150, 151, 160]
    for stage_type in stages:
      stage = Stage(feature_id=123, stage_type=stage_type)
      if stage_type == 150:
        stage.milestones = MilestoneSet(desktop_first=100)
      stage.put()
    
    self.old_feature_template.put()
    self.feature_template.put()

    self.maxDiff = None
  
  def tearDown(self) -> None:
    kinds: list[ndb.Model] = [Feature, FeatureEntry, Stage]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_build_email_tasks_feature_accuracy(self):
    with test_app.app_context():
      actual = reminders.build_email_tasks(
          [(self.feature_template, 100)], '[Action requested] Update %s',
          reminders.FeatureAccuracyHandler.EMAIL_TEMPLATE_PATH,
          self.current_milestone_info)
    self.assertEqual(1, len(actual))
    task = actual[0]
    self.assertEqual('feature_owner@example.com', task['to'])
    self.assertEqual('[Action requested] Update feature one', task['subject'])
    self.assertEqual(None, task['reply_to'])
    # TESTDATA.make_golden(task['html'], 'test_build_email_tasks_feature_accuracy.html')
    self.assertMultiLineEqual(
      TESTDATA['test_build_email_tasks_feature_accuracy.html'], task['html'])

  def test_build_email_tasks_prepublication(self):
    with test_app.app_context():
      actual = reminders.build_email_tasks(
          [(self.feature_template, 100)], '[Action requested] Update %s',
          reminders.PrepublicationHandler.EMAIL_TEMPLATE_PATH,
          self.current_milestone_info)
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
    expected = {'message': '1 email(s) sent or logged.'}
    self.assertEqual(result, expected)

  @mock.patch('requests.get')
  def test_determine_features_to_notify__multiple_owners(self, mock_get):
    mock_return = MockResponse(
        text=('{"mstones":[{"mstone": "148", '
              '"earliest_beta": "2024-02-03T01:23:45"}]}'))
    mock_get.return_value = mock_return
    with test_app.app_context():
      result = self.handler.get_template_data()
    expected = {'message': '2 email(s) sent or logged.'}
    self.assertEqual(result, expected)


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
