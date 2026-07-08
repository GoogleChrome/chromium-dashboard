# Copyright 2026 Google Inc.
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

"""Tests for pages/featuredetail.py."""

import testing_config  # isort: skip

from unittest import mock

import flask

import settings
from pages import featuredetail

test_app = flask.Flask(
    __name__, template_folder=settings.get_flask_template_path()
)


class FeatureDetailHandlerTest(testing_config.CustomTestCase):
    """Tests for FeatureDetailHandler."""

    def setUp(self):
        """Set up the test handler."""
        self.handler = featuredetail.FeatureDetailHandler()

    def test_get_crawler_data__no_feature_id(self):
        """It handles missing feature_id gracefully."""
        with test_app.test_request_context('/feature'):
            defaults = {}
            crawler_data = self.handler.get_crawler_data(defaults)
            self.assertEqual({}, crawler_data)

    @mock.patch('internals.feature_helpers.get_by_ids')
    def test_get_crawler_data__feature_not_found(self, mock_get_by_ids):
        """It handles feature not found gracefully."""
        mock_get_by_ids.return_value = []
        with test_app.test_request_context('/feature/123'):
            defaults = {'feature_id': 123}
            crawler_data = self.handler.get_crawler_data(defaults)
            self.assertEqual({}, crawler_data)
            mock_get_by_ids.assert_called_once_with([123])

    @mock.patch('internals.feature_helpers.get_by_ids')
    @mock.patch('framework.permissions.can_view_feature_formatted')
    @mock.patch('framework.users.get_current_user')
    def test_get_crawler_data__no_permission(
        self,
        mock_get_current_user,
        mock_can_view_feature_formatted,
        mock_get_by_ids,
    ):
        """It returns empty crawler data if user has no permission."""
        mock_user = mock.Mock()
        mock_get_current_user.return_value = mock_user

        fake_feature_dict = {'id': 123, 'name': 'Fake Feature'}
        mock_get_by_ids.return_value = [fake_feature_dict]

        mock_can_view_feature_formatted.return_value = False

        with test_app.test_request_context('/feature/123'):
            defaults = {'feature_id': 123}
            crawler_data = self.handler.get_crawler_data(defaults)
            self.assertEqual({}, crawler_data)
            mock_get_by_ids.assert_called_once_with([123])
            mock_can_view_feature_formatted.assert_called_once_with(
                mock_user, fake_feature_dict
            )

    @mock.patch('internals.feature_helpers.get_by_ids')
    @mock.patch('framework.permissions.can_view_feature_formatted')
    @mock.patch('framework.users.get_current_user')
    def test_get_crawler_data__has_permission(
        self,
        mock_get_current_user,
        mock_can_view_feature_formatted,
        mock_get_by_ids,
    ):
        """It returns crawler data when user has permission."""
        mock_user = mock.Mock()
        mock_get_current_user.return_value = mock_user

        fake_feature_dict = {
            'id': 123,
            'name': 'Fake Feature',
            'summary': 'Fake Summary',
            'stages': [
                {'intent_stage': 1, 'display_name': 'Stage One'},
                {'intent_stage': 2, 'display_name': 'Stage Two'},
            ],
        }
        mock_get_by_ids.return_value = [fake_feature_dict]

        mock_can_view_feature_formatted.return_value = True

        with test_app.test_request_context('/feature/123'):
            defaults = {'feature_id': 123}
            crawler_data = self.handler.get_crawler_data(defaults)

            mock_get_by_ids.assert_called_once_with([123])
            mock_can_view_feature_formatted.assert_called_once_with(
                mock_user, fake_feature_dict
            )

            self.assertEqual(
                {'title': 'Feature entry: Fake Feature'},
                crawler_data.get('heading'),
            )

            sections = crawler_data.get('sections')
            self.assertEqual(3, len(sections))  # 1 metadata + 2 stages

            # Verify metadata section
            self.assertEqual('Metadata', sections[0]['summary'])
            self.assertEqual('Fake Feature', sections[0]['fields']['name'])
            self.assertEqual('Fake Summary', sections[0]['fields']['summary'])
            self.assertNotIn('stages', sections[0]['fields'])

            # Verify stage sections
            self.assertEqual(
                'Stage: Start prototyping Stage One', sections[1]['summary']
            )
            self.assertEqual(
                {'intent_stage': 1, 'display_name': 'Stage One'},
                sections[1]['fields'],
            )

            self.assertEqual(
                'Stage: Dev trials Stage Two', sections[2]['summary']
            )
            self.assertEqual(
                {'intent_stage': 2, 'display_name': 'Stage Two'},
                sections[2]['fields'],
            )
