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

from datetime import datetime
from unittest import mock

import testing_config  # Must be imported before the module under test.
from internals.core_enums import *  # noqa: F403
from internals.core_models import FeatureEntry
from internals.enterprise_helpers import *  # noqa: F403

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class EnterpriseHelpersTest(testing_config.CustomTestCase):
    """Tests for enterprise helpers."""
    def setUp(self):
        self.no_feature = None
        self.enterprise_feature = FeatureEntry(
            name='feature b',
            summary='sum',
            owner_emails=['feature_owner@example.com'],
            category=1,
            updated=datetime(2020, 4, 1),
            feature_type=4,
        )
        self.enterprise_feature.put()

        self.breaking_feature = FeatureEntry(
            name='feature a',
            summary='sum',
            impl_status_chrome=3,
            owner_emails=['feature_owner@example.com'],
            category=1,
            updated=datetime(2020, 3, 1),
            feature_type=1,
            enterprise_impact=ENTERPRISE_IMPACT_LOW,
        )  # noqa: E501, F405
        self.breaking_feature.put()

        self.normal_feature = FeatureEntry(
            name='feature c',
            summary='sum',
            category=1,
            impl_status_chrome=2,
            owner_emails=['feature_owner@example.com'],
            updated=datetime(2020, 1, 1),
            feature_type=2,
        )
        self.normal_feature.put()
        self.now = datetime.now()

    @mock.patch('api.channels_api.construct_specified_milestones_details')
    def test__needs_default_first_notification_milestone__new_feature(
        self, mock_specified_milestones
    ):  # noqa: E501
        mock_specified_milestones.return_value = {
            99: {
                'version': 99,
                'stable_date': self.now.replace(
                    year=self.now.year - 1, day=1
                ).strftime(DATETIME_FORMAT),  # noqa: E501
            },
            100: {
                'version': 100,
                'stable_date': self.now.replace(
                    year=self.now.year + 1, day=1
                ).strftime(DATETIME_FORMAT),  # noqa: E501
            },
        }
        # Enterprise feature missing the milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature, {'feature_type': 4}
            )
        )
        # Enterprise feature with invalid milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 4,
                    'first_enterprise_notification_milestone': 1,
                },
            )
        )  # noqa: E501
        # Enterprise feature with older milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 4,
                    'first_enterprise_notification_milestone': 99,
                },
            )
        )  # noqa: E501
        # Enterprise feature with valid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 4,
                    'first_enterprise_notification_milestone': 100,
                },
            )
        )  # noqa: E501

        # Breaking change missing the milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {'feature_type': 1, 'enterprise_impact': ENTERPRISE_IMPACT_LOW},
            )
        )  # noqa: E501, F405
        # Breaking change with invalid milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'enterprise_impact': ENTERPRISE_IMPACT_LOW,
                    'first_enterprise_notification_milestone': 1,
                },
            )
        )  # noqa: E501, F405
        # Breaking change with older milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'enterprise_impact': ENTERPRISE_IMPACT_LOW,
                    'first_enterprise_notification_milestone': 99,
                },
            )
        )  # noqa: E501, F405
        # Breaking change with valid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'enterprise_impact': ENTERPRISE_IMPACT_LOW,
                    'first_enterprise_notification_milestone': 100,
                },
            )
        )  # noqa: E501, F405

        # Normal feature missing the milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature, {'feature_type': 1}
            )
        )
        # Normal feature with invalid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'first_enterprise_notification_milestone': 1,
                },
            )
        )  # noqa: E501
        # Normal feature with older milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'first_enterprise_notification_milestone': 99,
                },
            )
        )  # noqa: E501
        # Normal feature with valid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'first_enterprise_notification_milestone': 100,
                },
            )
        )  # noqa: E501

        # Non-breaking Normal feature missing the milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,
                },
            )
        )  # noqa: E501, F405
        # Non-breaking Normal feature with invalid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,
                    'first_enterprise_notification_milestone': 1,
                },
            )
        )  # noqa: E501, F405
        # Non-breaking Normal feature with older milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,
                    'first_enterprise_notification_milestone': 99,
                },
            )
        )  # noqa: E501, F405
        # Non-breaking Normal feature with valid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.no_feature,
                {
                    'feature_type': 1,
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,  # noqa: F405
                    'first_enterprise_notification_milestone': 100,
                },
            )
        )

    @mock.patch('api.channels_api.construct_specified_milestones_details')
    def test__needs_default_first_notification_milestone__update(
        self, mock_specified_milestones
    ):  # noqa: E501

        mock_specified_milestones.return_value = {
            99: {
                'version': 99,
                'stable_date': self.now.replace(
                    year=self.now.year - 1, day=1
                ).strftime(DATETIME_FORMAT),  # noqa: E501
            },
            100: {
                'version': 100,
                'stable_date': self.now.replace(
                    year=self.now.year + 1, day=1
                ).strftime(DATETIME_FORMAT),  # noqa: E501
            },
        }
        # Enterprise feature missing the milestone
        self.assertTrue(
            needs_default_first_notification_milestone(
                self.enterprise_feature, {}
            )
        )  # noqa: E501, F405
        # Enterprise feature with invalid milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 1},
            )
        )
        # Enterprise feature with older milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 99},
            )
        )
        # Enterprise feature with valid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 100},
            )
        )  # noqa: E501

        # Breaking change missing the milestone
        self.assertTrue(
            needs_default_first_notification_milestone(
                self.breaking_feature, {}
            )
        )  # noqa: E501, F405
        # Breaking change with invalid milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'first_enterprise_notification_milestone': 1},
            )
        )
        # Breaking change with older milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'first_enterprise_notification_milestone': 99},
            )
        )
        # Breaking change with valid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'first_enterprise_notification_milestone': 100},
            )
        )

        # Normal feature missing the milestone
        self.assertFalse(
            needs_default_first_notification_milestone(self.normal_feature, {})
        )  # noqa: E501, F405
        # Normal feature with invalid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {'first_enterprise_notification_milestone': 1},
            )
        )
        # Normal feature with older milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {'first_enterprise_notification_milestone': 99},
            )
        )
        # Normal feature with valid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {'first_enterprise_notification_milestone': 100},
            )
        )

        # Normal feature becoming breaking missing the milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {'enterprise_impact': ENTERPRISE_IMPACT_LOW},
            )
        )  # noqa: F405
        # Normal feature becoming breaking with invalid milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_LOW,
                    'first_enterprise_notification_milestone': 1,
                },
            )
        )  # noqa: E501, F405
        # Normal feature becoming breaking with older milestone
        self.assertTrue(
            needs_default_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_LOW,
                    'first_enterprise_notification_milestone': 99,
                },
            )
        )  # noqa: E501, F405
        # Normal feature becoming breaking with valid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_LOW,
                    'first_enterprise_notification_milestone': 100,
                },
            )
        )  # noqa: E501, F405

        # Breaking feature becoming normal feature missing the milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'enterprise_impact': ENTERPRISE_IMPACT_NONE},
            )
        )  # noqa: F405
        # Breaking feature becoming normal feature with invalid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,
                    'first_enterprise_notification_milestone': 1,
                },
            )
        )  # noqa: E501, F405
        # Breaking feature becoming normal feature with older milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,
                    'first_enterprise_notification_milestone': 99,
                },
            )
        )  # noqa: E501, F405
        # Breaking feature becoming normal feature with valid milestone
        self.assertFalse(
            needs_default_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,
                    'first_enterprise_notification_milestone': 100,
                },
            )
        )  # noqa: E501, F405

        # Feature already has a milestone
        self.breaking_feature.first_enterprise_notification_milestone = 100
        self.breaking_feature.put()
        self.assertFalse(
            needs_default_first_notification_milestone(self.breaking_feature)
        )  # noqa: F405
        self.enterprise_feature.first_enterprise_notification_milestone = 100
        self.enterprise_feature.put()
        self.assertFalse(
            needs_default_first_notification_milestone(self.enterprise_feature)
        )  # noqa: F405

    @mock.patch('api.channels_api.construct_chrome_channels_details')
    @mock.patch('api.channels_api.construct_specified_milestones_details')
    def test__is_update_first_notification_milestone(
        self, mock_specified_milestones, mock_channel_details
    ):
        mock_specified_milestones.return_value = {
            99: {
                'version': 99,
                'stable_date': self.now.replace(
                    year=self.now.year - 1, day=1
                ).strftime(DATETIME_FORMAT),  # noqa: E501
            },
            100: {  # Current milestone on stable channel
                'version': 100,
                'stable_date': self.now.replace(
                    year=self.now.year, day=1
                ).strftime(DATETIME_FORMAT),  # noqa: E501
            },
            101: {
                'version': 101,
                'stable_date': self.now.replace(
                    year=self.now.year + 1, day=1
                ).strftime(DATETIME_FORMAT),  # noqa: E501
            },
            102: {
                'version': 102,
                'stable_date': self.now.replace(
                    year=self.now.year + 2, day=1
                ).strftime(DATETIME_FORMAT),  # noqa: E501
            },
        }
        mock_channel_details.return_value = {
            'beta': {
                'version': 100,
                'stable_date': self.now.replace(
                    year=self.now.year, day=1
                ).strftime(DATETIME_FORMAT),  # noqa: E501
            }
        }

        # Enterprise feature missing the milestone
        self.assertFalse(
            is_update_first_notification_milestone(self.enterprise_feature, {})
        )  # noqa: E501, F405
        # Enterprise feature with invalid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 1},
            )
        )
        # Enterprise feature with older milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 99},
            )
        )
        # Enterprise feature with valid milestone
        self.assertTrue(
            is_update_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 100},
            )
        )  # noqa: E501

        # Breaking change missing the milestone
        self.assertFalse(
            is_update_first_notification_milestone(self.breaking_feature, {})
        )  # noqa: E501, F405
        # Breaking change with invalid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'first_enterprise_notification_milestone': 1},
            )
        )
        # Breaking change with older milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'first_enterprise_notification_milestone': 99},
            )
        )
        # Breaking change with valid milestone
        self.assertTrue(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'first_enterprise_notification_milestone': 100},
            )
        )

        # Normal feature missing the milestone
        self.assertFalse(
            is_update_first_notification_milestone(self.normal_feature, {})
        )  # noqa: E501, F405
        # Normal feature with invalid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {'first_enterprise_notification_milestone': 1},
            )
        )
        # Normal feature with older milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {'first_enterprise_notification_milestone': 99},
            )
        )
        # Normal feature with valid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {'first_enterprise_notification_milestone': 100},
            )
        )

        # Normal feature becoming breaking missing the milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {'enterprise_impact': ENTERPRISE_IMPACT_LOW},
            )
        )  # noqa: F405
        # Normal feature becoming breaking with invalid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_LOW,
                    'first_enterprise_notification_milestone': 1,
                },
            )
        )  # noqa: E501, F405
        # Normal feature becoming breaking with older milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_LOW,
                    'first_enterprise_notification_milestone': 99,
                },
            )
        )  # noqa: E501, F405
        # Normal feature becoming breaking with valid milestone
        self.assertTrue(
            is_update_first_notification_milestone(  # noqa: F405
                self.normal_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_LOW,
                    'first_enterprise_notification_milestone': 100,
                },
            )
        )  # noqa: E501, F405

        # Breaking feature becoming normal feature missing the milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'enterprise_impact': ENTERPRISE_IMPACT_NONE},
            )
        )  # noqa: F405
        # Breaking feature becoming normal feature with invalid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,
                    'first_enterprise_notification_milestone': 1,
                },
            )
        )  # noqa: E501, F405
        # Breaking feature becoming normal feature with older milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,
                    'first_enterprise_notification_milestone': 99,
                },
            )
        )  # noqa: E501, F405
        # Breaking feature becoming normal feature with valid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {
                    'enterprise_impact': ENTERPRISE_IMPACT_NONE,
                    'first_enterprise_notification_milestone': 100,
                },
            )
        )  # noqa: E501, F405

        # Feature already has a milestone that was already released
        self.breaking_feature.first_enterprise_notification_milestone = 99
        self.breaking_feature.put()
        # Breaking feature becoming normal feature missing the milestone
        self.assertFalse(
            is_update_first_notification_milestone(self.breaking_feature, {})
        )  # noqa: E501, F405
        # Breaking feature becoming normal feature with invalid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'first_enterprise_notification_milestone': 1},
            )
        )
        # Breaking feature becoming normal feature with older milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'first_enterprise_notification_milestone': 99},
            )
        )
        # Breaking feature becoming normal feature with valid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.breaking_feature,
                {'first_enterprise_notification_milestone': 100},
            )
        )

        # Feature already has a milestone, but it is in the future
        self.enterprise_feature.first_enterprise_notification_milestone = 100
        self.enterprise_feature.put()
        # Enterprise feature missing the milestone
        self.assertFalse(
            is_update_first_notification_milestone(self.enterprise_feature, {})
        )  # noqa: E501, F405
        # Enterprise feature with invalid milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 1},
            )
        )
        # Enterprise feature with older milestone
        self.assertFalse(
            is_update_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 99},
            )
        )
        # Enterprise feature with valid milestone
        self.assertTrue(
            is_update_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 100},
            )
        )  # noqa: E501
        self.assertTrue(
            is_update_first_notification_milestone(  # noqa: F405
                self.enterprise_feature,
                {'first_enterprise_notification_milestone': 101},
            )
        )  # noqa: E501

    @mock.patch('api.channels_api.construct_chrome_channels_details')
    def test__get_default_first_notice_milestone_for_feature(
        self, mock_channel_details
    ):  # noqa: E501
        now = datetime.now()
        mock_channel_details.return_value = {
            'beta': {
                'version': 120,
                'stable_date': now.replace(year=now.year + 1, day=2).strftime(
                    DATETIME_FORMAT
                ),  # noqa: E501
            }
        }
        self.assertEqual(get_default_first_notice_milestone_for_feature(), 120)  # noqa: F405

    @mock.patch('api.channels_api.construct_specified_milestones_details')
    def test__should_remove_first_notice_milestone(
        self, mock_specified_milestones
    ):  # noqa: E501
        now = datetime.now()
        mock_specified_milestones.return_value = {
            99: {
                'version': 99,
                'stable_date': now.replace(year=now.year - 1, day=1).strftime(
                    DATETIME_FORMAT
                ),  # noqa: E501
            },
            100: {
                'version': 100,
                'stable_date': now.replace(year=now.year + 1, day=1).strftime(
                    DATETIME_FORMAT
                ),  # noqa: E501
            },
            101: {
                'version': 101,
                'stable_date': now.replace(year=now.year + 2, day=1).strftime(
                    DATETIME_FORMAT
                ),  # noqa: E501
            },
        }

        # Enterprise feature with no changes and no existing milestone
        self.assertFalse(
            should_remove_first_notice_milestone(self.enterprise_feature, {})
        )  # noqa: E501, F405

        # Enterprise feature with no changes and existing milestone
        self.enterprise_feature.first_enterprise_notification_milestone = 100
        self.enterprise_feature.put()
        self.assertFalse(
            should_remove_first_notice_milestone(self.enterprise_feature, {})
        )  # noqa: E501, F405

        # Breaking change with no changes and no existing milestone
        self.assertFalse(
            should_remove_first_notice_milestone(self.breaking_feature, {})
        )  # noqa: E501, F405

        # Breaking change with no changes and existing milestone
        self.breaking_feature.first_enterprise_notification_milestone = 100
        self.breaking_feature.put()
        self.assertFalse(
            should_remove_first_notice_milestone(self.breaking_feature, {})
        )  # noqa: E501, F405

        # Breaking change becoming non-breaking and existing milestone
        self.breaking_feature.first_enterprise_notification_milestone = 100
        self.breaking_feature.put()
        self.assertTrue(
            should_remove_first_notice_milestone(  # noqa: F405
                self.breaking_feature,
                {'enterprise_impact': ENTERPRISE_IMPACT_NONE},
            )
        )  # noqa: F405

        # Breaking change becoming non-breaking and existing milestone already released  # noqa: E501
        self.breaking_feature.first_enterprise_notification_milestone = 99
        self.breaking_feature.put()
        self.assertFalse(
            should_remove_first_notice_milestone(  # noqa: F405
                self.breaking_feature,
                {'enterprise_impact': ENTERPRISE_IMPACT_NONE},
            )
        )  # noqa: F405
