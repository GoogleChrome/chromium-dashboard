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
from datetime import datetime

from internals.core_enums import *
from internals.enterprise_helpers import *
from internals.core_models import FeatureEntry
from unittest import mock

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

class EnterpriseHelpersTest(testing_config.CustomTestCase):

  def setUp(self):
    self.no_feature = None
    self.enterprise_feature = FeatureEntry(
        name='feature b', summary='sum',
        owner_emails=['feature_owner@example.com'], category=1,
        updated=datetime(2020, 4, 1), feature_type=4)
    self.enterprise_feature.put()

    self.breaking_feature = FeatureEntry(
        name='feature a', summary='sum', impl_status_chrome=3,
        owner_emails=['feature_owner@example.com'], category=1,
        updated=datetime(2020, 3, 1), feature_type=1, enterprise_impact=ENTERPRISE_IMPACT_LOW)
    self.breaking_feature.put()

    self.normal_feature = FeatureEntry(
        name='feature c', summary='sum', category=1, impl_status_chrome=2,
        owner_emails=['feature_owner@example.com'],
        updated=datetime(2020, 1, 1), feature_type=2)
    self.normal_feature.put()
    self.now = datetime.now()

  def tearDown(self):
    self.enterprise_feature.key.delete()
    self.breaking_feature.key.delete()
    self.normal_feature.key.delete()

  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test__needs_default_first_notification_milestone__new_feature(self, mock_specified_milestones):
    mock_specified_milestones.return_value = {
        99: { 
          'version': 99, 
          'stable_date': self.now.replace(year=self.now.year - 1, day=1).strftime(DATETIME_FORMAT)
        },
        100: { 
          'version': 100, 
          'stable_date': self.now.replace(year=self.now.year + 1, day=1).strftime(DATETIME_FORMAT)
        },
    }
    # Enterprise feature missing the milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 4}))
    # Enterprise feature with invalid milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 4, 'first_enterprise_notification_milestone': 1}))
    # Enterprise feature with older milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 4, 'first_enterprise_notification_milestone': 99}))
    # Enterprise feature with valid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 4, 'first_enterprise_notification_milestone': 100}))

    # Breaking change missing the milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 1,  'enterprise_impact': ENTERPRISE_IMPACT_LOW}))
    # Breaking change with invalid milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.no_feature,
      {'feature_type': 1,  'enterprise_impact': ENTERPRISE_IMPACT_LOW, 'first_enterprise_notification_milestone': 1}))
    # Breaking change with older milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.no_feature,
      {'feature_type': 1,  'enterprise_impact': ENTERPRISE_IMPACT_LOW, 'first_enterprise_notification_milestone': 99}))
    # Breaking change with valid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature,
      {'feature_type': 1, 'enterprise_impact': ENTERPRISE_IMPACT_LOW, 'first_enterprise_notification_milestone': 100}))

    # Normal feature missing the milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 1}))
    # Normal feature with invalid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 1, 'first_enterprise_notification_milestone': 1}))
    # Normal feature with older milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 1, 'first_enterprise_notification_milestone': 99}))
    # Normal feature with valid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 1, 'first_enterprise_notification_milestone': 100}))

    # Non-breaking Normal feature missing the milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature, {'feature_type': 1,  'enterprise_impact': ENTERPRISE_IMPACT_NONE}))
    # Non-breaking Normal feature with invalid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature,
      {'feature_type': 1,  'enterprise_impact': ENTERPRISE_IMPACT_NONE, 'first_enterprise_notification_milestone': 1}))
    # Non-breaking Normal feature with older milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature,
      {'feature_type': 1,  'enterprise_impact': ENTERPRISE_IMPACT_NONE, 'first_enterprise_notification_milestone': 99}))
    # Non-breaking Normal feature with valid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.no_feature,
      {'feature_type': 1,  'enterprise_impact': ENTERPRISE_IMPACT_NONE,
       'first_enterprise_notification_milestone': 100}))


  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test__needs_default_first_notification_milestone__update(self, mock_specified_milestones):
    
    mock_specified_milestones.return_value =  {
        99: {
          'version': 99,
          'stable_date': self.now.replace(year=self.now.year - 1, day=1).strftime(DATETIME_FORMAT)
        },
        100: {
          'version': 100,
          'stable_date': self.now.replace(year=self.now.year + 1, day=1).strftime(DATETIME_FORMAT)
        },
    }
    # Enterprise feature missing the milestone
    self.assertTrue(needs_default_first_notification_milestone(self.enterprise_feature, {}))
    # Enterprise feature with invalid milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 1}))
    # Enterprise feature with older milestone
    self.assertTrue( needs_default_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 99}))
    # Enterprise feature with valid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 100}))

    # Breaking change missing the milestone
    self.assertTrue( needs_default_first_notification_milestone(self.breaking_feature, {}))
    # Breaking change with invalid milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.breaking_feature, {'first_enterprise_notification_milestone': 1}))
    # Breaking change with older milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.breaking_feature, {'first_enterprise_notification_milestone': 99}))
    # Breaking change with valid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.breaking_feature, {'first_enterprise_notification_milestone': 100}))

    # Normal feature missing the milestone
    self.assertFalse(needs_default_first_notification_milestone(self.normal_feature, {}))
    # Normal feature with invalid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.normal_feature, {'first_enterprise_notification_milestone': 1}))
    # Normal feature with older milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.normal_feature, {'first_enterprise_notification_milestone': 99}))
    # Normal feature with valid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.normal_feature,
      {'first_enterprise_notification_milestone': 100}))

    # Normal feature becoming breaking missing the milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.normal_feature, { 'enterprise_impact': ENTERPRISE_IMPACT_LOW}))
    # Normal feature becoming breaking with invalid milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.normal_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_LOW,'first_enterprise_notification_milestone': 1}))
    # Normal feature becoming breaking with older milestone
    self.assertTrue(needs_default_first_notification_milestone(
      self.normal_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_LOW, 'first_enterprise_notification_milestone': 99}))
    # Normal feature becoming breaking with valid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.normal_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_LOW, 'first_enterprise_notification_milestone': 100}))
  
    # Breaking feature becoming normal feature missing the milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.breaking_feature, { 'enterprise_impact': ENTERPRISE_IMPACT_NONE}))
    # Breaking feature becoming normal feature with invalid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.breaking_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_NONE,'first_enterprise_notification_milestone': 1}))
    # Breaking feature becoming normal feature with older milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.breaking_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_NONE,'first_enterprise_notification_milestone': 99}))
    # Breaking feature becoming normal feature with valid milestone
    self.assertFalse(needs_default_first_notification_milestone(
      self.breaking_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_NONE,'first_enterprise_notification_milestone': 100}))

    #Feature already has a milestone
    self.breaking_feature.first_enterprise_notification_milestone = 100
    self.breaking_feature.put()
    self.assertFalse(needs_default_first_notification_milestone(self.breaking_feature))
    self.enterprise_feature.first_enterprise_notification_milestone = 100
    self.enterprise_feature.put()
    self.assertFalse(needs_default_first_notification_milestone(self.enterprise_feature))


  @mock.patch('api.channels_api.construct_chrome_channels_details')
  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test__is_update_first_notification_milestone(self,
                                                    mock_specified_milestones,
                                                    mock_channel_details):
    mock_specified_milestones.return_value =  {
        99: {
          'version': 99,
          'stable_date': self.now.replace(year=self.now.year - 1, day=1).strftime(DATETIME_FORMAT)
        },
        100: {
          'version': 100,
          'stable_date': self.now.replace(year=self.now.year + 1, day=1).strftime(DATETIME_FORMAT)
        },
        101: {
          'version': 101,
          'stable_date': self.now.replace(year=self.now.year + 2, day=1).strftime(DATETIME_FORMAT)
        },
    }
    mock_channel_details.return_value = {
      'beta': {
        'version': 100,
        'stable_date': self.now.replace(year=self.now.year + 1, day=1).strftime(DATETIME_FORMAT)
      }
    }

    # Enterprise feature missing the milestone
    self.assertFalse(is_update_first_notification_milestone(self.enterprise_feature, {}))
    # Enterprise feature with invalid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 1}))
    # Enterprise feature with older milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 99}))
    # Enterprise feature with valid milestone
    self.assertTrue(is_update_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 100}))

    # Breaking change missing the milestone
    self.assertFalse(is_update_first_notification_milestone(self.breaking_feature, {}))
    # Breaking change with invalid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.breaking_feature, {'first_enterprise_notification_milestone': 1}))
    # Breaking change with older milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.breaking_feature, {'first_enterprise_notification_milestone': 99}))
    # Breaking change with valid milestone
    self.assertTrue(is_update_first_notification_milestone(
      self.breaking_feature, {'first_enterprise_notification_milestone': 100}))

    # Normal feature missing the milestone
    self.assertFalse(is_update_first_notification_milestone(self.normal_feature, {}))
    # Normal feature with invalid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.normal_feature, {'first_enterprise_notification_milestone': 1}))
    # Normal feature with older milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.normal_feature, {'first_enterprise_notification_milestone': 99}))
    # Normal feature with valid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.normal_feature, {'first_enterprise_notification_milestone': 100}))

    # Normal feature becoming breaking missing the milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.normal_feature, { 'enterprise_impact': ENTERPRISE_IMPACT_LOW}))
    # Normal feature becoming breaking with invalid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.normal_feature, { 'enterprise_impact': ENTERPRISE_IMPACT_LOW, 'first_enterprise_notification_milestone': 1}))
    # Normal feature becoming breaking with older milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.normal_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_LOW, 'first_enterprise_notification_milestone': 99}))
    # Normal feature becoming breaking with valid milestone
    self.assertTrue(is_update_first_notification_milestone(
      self.normal_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_LOW, 'first_enterprise_notification_milestone': 100}))
  
    # Breaking feature becoming normal feature missing the milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.breaking_feature, { 'enterprise_impact': ENTERPRISE_IMPACT_NONE}))
    # Breaking feature becoming normal feature with invalid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.breaking_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_NONE, 'first_enterprise_notification_milestone': 1}))
    # Breaking feature becoming normal feature with older milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.breaking_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_NONE, 'first_enterprise_notification_milestone': 99}))
    # Breaking feature becoming normal feature with valid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.breaking_feature,
      { 'enterprise_impact': ENTERPRISE_IMPACT_NONE, 'first_enterprise_notification_milestone': 100}))

    #Feature already has a milestone that was already released
    self.breaking_feature.first_enterprise_notification_milestone = 99
    self.breaking_feature.put()
    # Breaking feature becoming normal feature missing the milestone
    self.assertFalse(is_update_first_notification_milestone(self.breaking_feature, {}))
    # Breaking feature becoming normal feature with invalid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.breaking_feature, {'first_enterprise_notification_milestone': 1}))
    # Breaking feature becoming normal feature with older milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.breaking_feature, {'first_enterprise_notification_milestone': 99}))
    # Breaking feature becoming normal feature with valid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.breaking_feature, {'first_enterprise_notification_milestone': 100}))

    #Feature already has a milestone, but it is in the future
    self.enterprise_feature.first_enterprise_notification_milestone = 100
    self.enterprise_feature.put()
    # Enterprise feature missing the milestone
    self.assertFalse(is_update_first_notification_milestone(self.enterprise_feature, {}))
    # Enterprise feature with invalid milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 1}))
    # Enterprise feature with older milestone
    self.assertFalse(is_update_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 99}))
    # Enterprise feature with valid milestone
    self.assertTrue(is_update_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 100}))
    self.assertTrue(is_update_first_notification_milestone(
      self.enterprise_feature, {'first_enterprise_notification_milestone': 101}))


  @mock.patch('api.channels_api.construct_chrome_channels_details')
  def test__get_default_first_notice_milestone_for_feature(self, mock_channel_details):
    now = datetime.now()
    mock_channel_details.return_value = {
      'beta': {
        'version': 120,
        'stable_date': now.replace(year=now.year + 1, day=2).strftime(DATETIME_FORMAT)
      }
    }
    self.assertEqual(get_default_first_notice_milestone_for_feature(), 120)


  @mock.patch('api.channels_api.construct_specified_milestones_details')
  def test__should_remove_first_notice_milestone(self, mock_specified_milestones):
    now = datetime.now()
    mock_specified_milestones.return_value =  {
        99: {
          'version': 99,
          'stable_date': now.replace(year=now.year - 1, day=1).strftime(DATETIME_FORMAT)
        },
        100: {
          'version': 100,
          'stable_date': now.replace(year=now.year + 1, day=1).strftime(DATETIME_FORMAT)
        },
        101: {
          'version': 101,
          'stable_date': now.replace(year=now.year + 2, day=1).strftime(DATETIME_FORMAT)
        },
    }
    
    # Enterprise feature with no changes and no existing milestone
    self.assertFalse(should_remove_first_notice_milestone(self.enterprise_feature, {}))

    # Enterprise feature with no changes and existing milestone
    self.enterprise_feature.first_enterprise_notification_milestone = 100
    self.enterprise_feature.put()
    self.assertFalse(should_remove_first_notice_milestone(self.enterprise_feature, {}))

    # Breaking change with no changes and no existing milestone
    self.assertFalse(should_remove_first_notice_milestone(self.breaking_feature, {}))

    # Breaking change with no changes and existing milestone
    self.breaking_feature.first_enterprise_notification_milestone = 100
    self.breaking_feature.put()
    self.assertFalse(should_remove_first_notice_milestone(self.breaking_feature, {}))

    # Breaking change becoming non-breaking and existing milestone
    self.breaking_feature.first_enterprise_notification_milestone = 100
    self.breaking_feature.put()
    self.assertTrue(should_remove_first_notice_milestone(
      self.breaking_feature, { 'enterprise_impact': ENTERPRISE_IMPACT_NONE}))

    # Breaking change becoming non-breaking and existing milestone already released
    self.breaking_feature.first_enterprise_notification_milestone = 99
    self.breaking_feature.put()
    self.assertFalse(should_remove_first_notice_milestone(
      self.breaking_feature, { 'enterprise_impact': ENTERPRISE_IMPACT_NONE}))
