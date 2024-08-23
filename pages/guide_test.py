# Copyright 2020 Google Inc.
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
import flask
from unittest import mock
import werkzeug
from google.cloud import ndb  # type: ignore

from framework import rediscache
from internals import core_enums
from internals import stage_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate
from pages import guide

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

test_app = flask.Flask(__name__)


class TestWithFeature(testing_config.CustomTestCase):

  REQUEST_PATH_FORMAT = 'subclasses fill this in'
  HANDLER_CLASS = 'subclasses fill this in'

  def setUp(self):
    self.request_path = self.REQUEST_PATH_FORMAT
    self.handler = self.HANDLER_CLASS()
    self.now = datetime.now()

  def tearDown(self):
    rediscache.flushall()


class FeatureCreateTest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = guide.FeatureCreateHandler()
    self.now = datetime.now()

  def tearDown(self) -> None:
    kinds: list[ndb.Model] = [FeatureEntry, Stage, Gate]
    for kind in kinds:
      entities = kind.query().fetch()
      for entity in entities:
        entity.key.delete()

  def test_post__anon(self):
    """Anon cannot create features, gets a 403."""
    testing_config.sign_out()
    with test_app.test_request_context('/guide/new', method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.process_post_data()

  def test_post__non_allowed(self):
    """Non-allowed cannot create features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with test_app.test_request_context('/guide/new', method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.post()

  @mock.patch('internals.notifier_helpers.notify_subscribers_and_save_amendments')
  def test_post__normal_valid(self, mock_notify):
    """Allowed user can create a feature."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        '/guide/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
            'feature_type': '0'
        }, method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/feature/'))
    new_feature_id = int(location.split('/')[-1])

    # Ensure FeatureEntry entity was created.
    feature_entry = FeatureEntry.get_by_id(new_feature_id)
    self.assertEqual(1, feature_entry.category)
    self.assertEqual('Feature name', feature_entry.name)
    self.assertEqual('Feature summary', feature_entry.summary)
    self.assertEqual('user1@google.com', feature_entry.creator_email)
    self.assertEqual(['devrel-chromestatus-all@google.com'],
                     feature_entry.devrel_emails)
    self.assertEqual(None, feature_entry.first_enterprise_notification_milestone)

    # Ensure Stage and Gate entities were created.
    stages = Stage.query().fetch()
    gates = Gate.query().fetch()
    self.assertEqual(len(stages), 6)
    self.assertEqual(len(gates), 11)

    # Ensure notifications are sent.
    mock_notify.assert_called_once()

  @mock.patch('api.channels_api.construct_chrome_channels_details')
  def test_post__feature_impact_missing_first_notice(self, mock_channel_details):
    """Create a feature, first_enterprise_notification_milestone not added."""
    stable_date = self.now.replace(year=self.now.year + 1, day=1).strftime(DATE_FORMAT)
    mock_channel_details.return_value = {'beta': { 'version': 120, 'stable_date': stable_date } }

    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        '/guide/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
            'feature_type': '1',
            'enterprise_impact': '2'
        },
        method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/feature/'))
    new_feature_id = int(location.split('/')[-1])

    # Ensure FeatureEntry entity was created.
    feature_entry = FeatureEntry.get_by_id(new_feature_id)
    self.assertEqual(1, feature_entry.category)
    self.assertEqual(1, feature_entry.feature_type)
    self.assertEqual('Feature name', feature_entry.name)
    self.assertEqual('Feature summary', feature_entry.summary)
    self.assertEqual('user1@google.com', feature_entry.creator_email)
    self.assertEqual(120, feature_entry.first_enterprise_notification_milestone)

  @mock.patch('api.channels_api.construct_chrome_channels_details')
  def test_post__enterprise_impact_missing_first_notice(self, mock_channel_details):
    """Create a feature, first_enterprise_notification_milestone not added."""
    stable_date = self.now.replace(year=self.now.year + 1, day=1).strftime(DATE_FORMAT)
    mock_channel_details.return_value = {'beta': { 'version': 120, 'stable_date': stable_date } }

    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        '/guide/enterprise/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
            'feature_type': '1',
            'enterprise_impact': '2'
        },
        method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/feature/'))
    new_feature_id = int(location.split('/')[-1])

    # Ensure FeatureEntry entity was created.
    feature_entry = FeatureEntry.get_by_id(new_feature_id)
    self.assertEqual(1, feature_entry.category)
    self.assertEqual(1, feature_entry.feature_type)
    self.assertEqual('Feature name', feature_entry.name)
    self.assertEqual('Feature summary', feature_entry.summary)
    self.assertEqual('user1@google.com', feature_entry.creator_email)
    self.assertEqual(120, feature_entry.first_enterprise_notification_milestone)


  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_post__enterprise_impact_with_first_notice(self, mock_specified_milestones):
    """Create a feature, first_enterprise_notification_milestone set to provided value."""
    mock_specified_milestones.return_value =  {
        99: {
          'version': 99,
          'stable_date': self.now.replace(year=self.now.year - 1, day=1).strftime(DATE_FORMAT)
        },
        100: {
          'version': 100,
          'stable_date': self.now.replace(year=self.now.year + 1, day=1).strftime(DATE_FORMAT)
        },
    }

    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        '/guide/enterprise/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
            'feature_type': '1',
            'enterprise_impact': '2',
            'first_enterprise_notification_milestone': '100'
        }, method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/feature/'))
    new_feature_id = int(location.split('/')[-1])

    # Ensure FeatureEntry entity was created.
    feature_entry = FeatureEntry.get_by_id(new_feature_id)
    self.assertEqual(1, feature_entry.category)
    self.assertEqual(1, feature_entry.feature_type)
    self.assertEqual('Feature name', feature_entry.name)
    self.assertEqual('Feature summary', feature_entry.summary)
    self.assertEqual('user1@google.com', feature_entry.creator_email)
    self.assertEqual(100, feature_entry.first_enterprise_notification_milestone)


  @mock.patch('api.channels_api.construct_chrome_channels_details')
  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_post__enterprise_impact_with_old_first_notice(self, mock_specified_milestones, mock_channel_details):
    """Create a feature, first_enterprise_notification_milestone set to default newer value."""
    mock_specified_milestones.return_value =  {
        99: {
          'version': 99,
          'stable_date': self.now.replace(year=self.now.year - 1, day=1).strftime(DATE_FORMAT)
        },
        100: {
          'version': 100,
          'stable_date': self.now.replace(year=self.now.year + 1, day=1).strftime(DATE_FORMAT)
        },
    }
    mock_channel_details.return_value = {
      'beta': {
        'version': 101,
        'stable_date': self.now.replace(year=self.now.year + 1, day=2).strftime(DATE_FORMAT)
      }
    }

    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        '/guide/enterprise/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
            'feature_type': '1',
            'enterprise_impact': '2',
            'first_enterprise_notification_milestone': '99'
        }, method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    new_feature_id = int(location.split('/')[-1])

    # Ensure FeatureEntry entity was created.
    feature_entry = FeatureEntry.get_by_id(new_feature_id)
    self.assertEqual(1, feature_entry.category)
    self.assertEqual(1, feature_entry.feature_type)
    self.assertEqual('Feature name', feature_entry.name)
    self.assertEqual('Feature summary', feature_entry.summary)
    self.assertEqual('user1@google.com', feature_entry.creator_email)
    self.assertEqual(101, feature_entry.first_enterprise_notification_milestone)


  @mock.patch('api.channels_api.construct_chrome_channels_details')
  def test_post__enterprise_missing_first_notice(self, mock_channel_details):
    """Create a feature, first_enterprise_notification_milestone set to default value."""
    self.handler = guide.EnterpriseFeatureCreateHandler()
    stable_date = self.now.replace(year=self.now.year + 1, day=2).strftime(DATE_FORMAT)
    mock_channel_details.return_value = { 'beta': { 'version': 120, 'stable_date': stable_date } }

    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        '/guide/enterprise/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
            'feature_type': '4'
        }, method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/guide/editall'))
    new_feature_id = int(location.split('/')[-1].split('#')[0])

    # Ensure FeatureEntry entity was created.
    feature_entry = FeatureEntry.get_by_id(new_feature_id)
    self.assertEqual(2, feature_entry.category)
    self.assertEqual(4, feature_entry.feature_type)
    self.assertEqual('Feature name', feature_entry.name)
    self.assertEqual('Feature summary', feature_entry.summary)
    self.assertEqual('user1@google.com', feature_entry.creator_email)
    self.assertEqual(120, feature_entry.first_enterprise_notification_milestone)


  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_post__enterprise_with_first_notice(self, mock_specified_milestones):
    """Create a feature, first_enterprise_notification_milestone set to provided value."""
    self.handler = guide.EnterpriseFeatureCreateHandler()
    mock_specified_milestones.return_value =  {
        99: {
          'version': 99,
          'stable_date': self.now.replace(year=self.now.year - 1, day=1).strftime(DATE_FORMAT)
        },
        100: {
          'version': 100,
          'stable_date': self.now.replace(year=self.now.year + 1, day=1).strftime(DATE_FORMAT)
        },
    }

    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        '/guide/enterprise/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
            'feature_type': '4',
            'first_enterprise_notification_milestone': '100'
        }, method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/guide/editall'))
    new_feature_id = int(location.split('/')[-1].split('#')[0])

    # Ensure FeatureEntry entity was created.
    feature_entry = FeatureEntry.get_by_id(new_feature_id)
    self.assertEqual(2, feature_entry.category)
    self.assertEqual(4, feature_entry.feature_type)
    self.assertEqual('Feature name', feature_entry.name)
    self.assertEqual('Feature summary', feature_entry.summary)
    self.assertEqual('user1@google.com', feature_entry.creator_email)
    self.assertEqual(100, feature_entry.first_enterprise_notification_milestone)


  @mock.patch('api.channels_api.construct_chrome_channels_details')
  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test_post__enterprise_with_old_first_notice(self, mock_specified_milestones, mock_channel_details):
    """Create a feature, first_enterprise_notification_milestone set to default newer value."""
    self.handler = guide.EnterpriseFeatureCreateHandler()
    mock_specified_milestones.return_value =  {
        99: {
          'version': 99,
          'stable_date': self.now.replace(year=self.now.year - 1, day=1).strftime(DATE_FORMAT)
        },
        100: {
          'version': 100,
          'stable_date': self.now.replace(year=self.now.year + 1, day=1).strftime(DATE_FORMAT)
        },
    }
    mock_channel_details.return_value = {
      'beta': {
        'version': 101,
        'stable_date': self.now.replace(year=self.now.year + 1, day=2).strftime(DATE_FORMAT)
      }
    }

    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        '/guide/enterprise/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
            'feature_type': '4',
            'first_enterprise_notification_milestone': '99'
        }, method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/guide/editall'))
    new_feature_id = int(location.split('/')[-1].split('#')[0])

    # Ensure FeatureEntry entity was created.
    feature_entry = FeatureEntry.get_by_id(new_feature_id)
    self.assertEqual(2, feature_entry.category)
    self.assertEqual(4, feature_entry.feature_type)
    self.assertEqual('Feature name', feature_entry.name)
    self.assertEqual('Feature summary', feature_entry.summary)
    self.assertEqual('user1@google.com', feature_entry.creator_email)
    self.assertEqual(101, feature_entry.first_enterprise_notification_milestone)
