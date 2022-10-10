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
from datetime import datetime
from unittest import mock

from internals import core_models
from internals import reminders


class MockResponse:
  """Creates a fake response object for testing."""
  def __init__(self, status_code=200, text='{}'):
    self.status_code = status_code
    self.text = text


def make_test_features():
  feature_1 = core_models.Feature(
      name='feature one', summary='sum', owner=['feature_owner@example.com'],
      category=1, ot_milestone_desktop_start=100)
  feature_1.put()
  feature_2 = core_models.Feature(
      name='feature two', summary='sum',
      owner=['owner_1@example.com', 'owner_2@example.com'],
      category=1, shipped_milestone=150)
  feature_2.put()
  feature_3 = core_models.Feature(
      name='feature three', summary='sum', category=1)
  feature_3.put()
  return feature_1, feature_2, feature_3


class FunctionTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1, self.feature_2, self.feature_3 = make_test_features()
    self.current_milestone_info = {
        'earliest_beta': '2022-09-21T12:34:56',
    }

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()

  def test_build_email_tasks(self):
    actual = reminders.build_email_tasks(
        [(self.feature_1, 100)], '[Action requested] Update %s',
        reminders.FeatureAccuracyHandler.EMAIL_TEMPLATE_PATH,
        self.current_milestone_info)
    self.assertEqual(1, len(actual))
    task = actual[0]
    self.assertEqual('feature_owner@example.com', task['to'])
    self.assertEqual('[Action requested] Update feature one', task['subject'])
    self.assertEqual(None, task['reply_to'])
    self.assertIn('/guide/verify_accuracy/%d' % self.feature_1.key.integer_id(),
                  task['html'])


class FeatureAccuracyHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1, self.feature_2, self.feature_3 = make_test_features()
    self.handler = reminders.FeatureAccuracyHandler()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()

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
    result = self.handler.get_template_data()
    expected = {'message': '1 email(s) sent or logged.'}
    self.assertEqual(result, expected)

  @mock.patch('requests.get')
  def test_determine_features_to_notify__multiple_owners(self, mock_get):
    mock_return = MockResponse(
        text=('{"mstones":[{"mstone": "148", '
              '"earliest_beta": "2024-02-03T01:23:45"}]}'))
    mock_get.return_value = mock_return
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
