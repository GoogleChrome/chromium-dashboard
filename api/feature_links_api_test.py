# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
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

"""Tests for FeatureLinksAPI, FeatureLinksSummaryAPI, and FeatureLinksSamplesAPI."""

import datetime
from unittest import mock

import flask
import werkzeug.exceptions

import testing_config  # isort: skip  # Must be imported before the module under test.
from chromestatus_openapi.models import (
    FeatureLinksResponse,
    FeatureLinksSummaryResponse,
)

from api import feature_links_api
from internals.core_models import FeatureEntry
from internals.feature_links import FeatureLinks
from internals.user_models import AppUser

test_app = flask.Flask(__name__)


class FeatureLinksAPITest(testing_config.CustomTestCase):
    """Tests for FeatureLinksAPI."""

    def setUp(self):
        """Set up the test environment."""
        self.feature_1 = FeatureEntry(
            name='feature one',
            summary='sum Z',
            category=1,
            owner_emails=['owner@example.com'],
            confidential=False,
        )
        self.feature_1.put()
        self.feature_id = self.feature_1.key.integer_id()

        self.confidential_feature = FeatureEntry(
            name='confidential feature',
            summary='secret',
            category=1,
            confidential=True,
        )
        self.confidential_feature.put()
        self.cf_id = self.confidential_feature.key.integer_id()

        # Insert some feature links.
        self.link_1 = FeatureLinks(
            url='https://example.com/spec',
            type='spec',
            feature_ids=[self.feature_id],
            information={'title': 'Example Spec'},
            is_error=False,
            http_error_code=None,
        )
        self.link_1.put()

        self.link_2 = FeatureLinks(
            url='https://example.org/web',
            type='web',
            feature_ids=[self.feature_id, self.cf_id],
            information=None,
            is_error=True,
            http_error_code=404,
        )
        self.link_2.put()

        self.handler = feature_links_api.FeatureLinksAPI()
        self.request_path = f'/api/v0/feature_links?feature_id={self.feature_id}'

    def tearDown(self):
        """Clean up the test environment."""
        self.link_1.key.delete()
        self.link_2.key.delete()
        self.feature_1.key.delete()
        self.confidential_feature.key.delete()
        for user in AppUser.query().fetch(None):
            user.key.delete()

    @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
    def test_get_feature_links__success(self, mock_enqueue):
        """We can retrieve feature links for a public feature using get_feature_links."""
        with test_app.test_request_context(self.request_path):
            data, has_stale_links = self.handler.get_feature_links(
                feature_id=self.feature_id, update_stale_links=False
            )

        self.assertEqual(2, len(data))
        self.assertEqual('https://example.com/spec', data[0]['url'])
        self.assertEqual('spec', data[0]['type'])
        self.assertEqual({'title': 'Example Spec'}, data[0]['information'])
        self.assertIsNone(data[0]['http_error_code'])

        self.assertEqual('https://example.org/web', data[1]['url'])
        self.assertEqual('web', data[1]['type'])
        self.assertIsNone(data[1]['information'])
        self.assertEqual(404, data[1]['http_error_code'])

        self.assertFalse(has_stale_links)
        mock_enqueue.assert_not_called()

    @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
    @mock.patch('internals.feature_links.datetime')
    def test_get_feature_links__trigger_update_stale(
        self, mock_datetime, mock_enqueue
    ):
        """If update_stale_links is True, stale links trigger background cloud task update."""
        # Make datetime.datetime.now() return a time 1 hour in the future,
        # making existing links stale.
        future_now = datetime.datetime.now(
            tz=datetime.timezone.utc
        ) + datetime.timedelta(hours=1)
        mock_datetime.datetime.now.return_value = future_now
        mock_datetime.timedelta = datetime.timedelta
        mock_datetime.timezone = datetime.timezone

        with test_app.test_request_context(self.request_path):
            data, has_stale_links = self.handler.get_feature_links(
                feature_id=self.feature_id, update_stale_links=True
            )

        self.assertEqual(2, len(data))
        self.assertTrue(has_stale_links)

        # It should trigger enqueue_task for both link_1 and link_2 since both are stale
        # (created/updated defaults to the old timestamp in test setup or is behind LINK_STALE_MINUTES).
        mock_enqueue.assert_called_once()
        args, kwargs = mock_enqueue.call_args
        self.assertEqual('/tasks/update-feature-links', args[0])
        self.assertIn('feature_link_ids', args[1])
        self.assertEqual(2, len(args[1]['feature_link_ids']))

    def test_get_feature_links__forbidden(self):
        """Regular users cannot view links for a confidential feature."""
        testing_config.sign_out()
        testing_config.sign_in('regular_user@example.com', 123)
        path = f'/api/v0/feature_links?feature_id={self.cf_id}'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.get_feature_links(
                    feature_id=self.cf_id, update_stale_links=False
                )
        testing_config.sign_out()

    def test_get_feature_links__admin_can_view_confidential(self):
        """Admin users CAN view links for a confidential feature."""
        admin_user = AppUser(email='admin@example.com', is_admin=True)
        admin_user.put()

        testing_config.sign_out()
        testing_config.sign_in('admin@example.com', 123)
        path = f'/api/v0/feature_links?feature_id={self.cf_id}'
        with test_app.test_request_context(path):
            data, has_stale_links = self.handler.get_feature_links(
                feature_id=self.cf_id, update_stale_links=False
            )
        testing_config.sign_out()

        self.assertEqual(1, len(data))
        self.assertEqual('https://example.org/web', data[0]['url'])

    def test_get_feature_links__not_found(self):
        """We get a 404 if the feature does not exist."""
        bad_path = '/api/v0/feature_links?feature_id=99999'
        with test_app.test_request_context(bad_path):
            with self.assertRaises(werkzeug.exceptions.NotFound):
                self.handler.get_feature_links(
                    feature_id=99999, update_stale_links=False
                )

    @mock.patch('framework.cloud_tasks_helpers.enqueue_task')
    def test_do_get__success(self, mock_enqueue):
        """We can retrieve feature links via the do_get API endpoint."""
        with test_app.test_request_context(
            f'/api/v0/feature_links?feature_id={self.feature_id}&update_stale_links=false'
        ):
            actual_response = self.handler.do_get()

        self.assertIsInstance(actual_response, FeatureLinksResponse)
        actual_dict = actual_response.to_dict()

        self.assertIn('data', actual_dict)
        self.assertIn('has_stale_links', actual_dict)
        self.assertFalse(actual_dict['has_stale_links'])

        data = actual_dict['data']
        self.assertEqual(2, len(data))
        self.assertEqual('https://example.com/spec', data[0]['url'])
        self.assertEqual('spec', data[0]['type'])
        self.assertEqual({'title': 'Example Spec'}, data[0]['information'])
        self.assertIsNone(data[0]['http_error_code'])

        self.assertEqual('https://example.org/web', data[1]['url'])
        self.assertEqual('web', data[1]['type'])
        self.assertIsNone(data[1]['information'])
        self.assertEqual(404, data[1]['http_error_code'])
        mock_enqueue.assert_not_called()

    def test_do_get__missing_feature_id(self):
        """We get a 400 if feature_id is omitted."""
        with test_app.test_request_context('/api/v0/feature_links'):
            with self.assertRaises(werkzeug.exceptions.BadRequest):
                self.handler.do_get()

    def test_do_get__invalid_feature_id(self):
        """We get a 400 if feature_id is not an integer."""
        with test_app.test_request_context('/api/v0/feature_links?feature_id=abc'):
            with self.assertRaises(werkzeug.exceptions.BadRequest):
                self.handler.do_get()


class FeatureLinksSummaryAPITest(testing_config.CustomTestCase):
    """Tests for FeatureLinksSummaryAPI."""

    def setUp(self):
        """Set up the test environment."""
        self.feature_1 = FeatureEntry(
            name='feature one', summary='sum Z', category=1
        )
        self.feature_1.put()
        self.feature_id = self.feature_1.key.integer_id()

        self.link_1 = FeatureLinks(
            url='https://example.com/spec',
            type='spec',
            feature_ids=[self.feature_id],
            information={'title': 'Example Spec'},
            is_error=False,
            http_error_code=None,
        )
        self.link_1.put()

        self.link_2 = FeatureLinks(
            url='https://example.org/web',
            type='web',
            feature_ids=[self.feature_id],
            information=None,
            is_error=True,
            http_error_code=404,
        )
        self.link_2.put()

        self.handler = feature_links_api.FeatureLinksSummaryAPI()
        self.request_path = '/api/v0/feature_links_summary'

    def tearDown(self):
        """Clean up the test environment."""
        self.link_1.key.delete()
        self.link_2.key.delete()
        self.feature_1.key.delete()
        for user in AppUser.query().fetch(None):
            user.key.delete()

    def test_do_get__admin_success(self):
        """Admin users can retrieve the feature links summary."""
        admin_user = AppUser(email='admin@example.com', is_admin=True)
        admin_user.put()

        testing_config.sign_out()
        testing_config.sign_in('admin@example.com', 123)
        with test_app.test_request_context(self.request_path):
            actual_response = self.handler.do_get()
        testing_config.sign_out()

        self.assertIsInstance(
            actual_response, FeatureLinksSummaryResponse
        )
        actual_dict = actual_response.to_dict()

        self.assertEqual(2, actual_dict['total_count'])
        self.assertEqual(1, actual_dict['covered_count'])
        self.assertEqual(1, actual_dict['uncovered_count'])
        self.assertEqual(1, actual_dict['error_count'])
        self.assertEqual(1, actual_dict['http_error_count'])

        # Verify counters.
        self.assertIn({'key': 'spec', 'count': 1}, actual_dict['link_types'])
        self.assertIn({'key': 'web', 'count': 1}, actual_dict['link_types'])
        self.assertIn(
            {'key': 'https://example.org', 'count': 1},
            actual_dict['uncovered_link_domains'],
        )
        self.assertIn(
            {'key': 'https://example.org', 'count': 1},
            actual_dict['error_link_domains'],
        )

    def test_do_get__forbidden(self):
        """Regular users cannot retrieve the feature links summary."""
        testing_config.sign_out()
        testing_config.sign_in('regular_user@example.com', 123)
        with test_app.test_request_context(self.request_path):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_get()
        testing_config.sign_out()


class FeatureLinksSamplesAPITest(testing_config.CustomTestCase):
    """Tests for FeatureLinksSamplesAPI."""

    def setUp(self):
        """Set up the test environment."""
        self.feature_1 = FeatureEntry(
            name='feature one', summary='sum Z', category=1
        )
        self.feature_1.put()
        self.feature_id = self.feature_1.key.integer_id()

        self.link_1 = FeatureLinks(
            url='https://example.com/spec',
            type='spec',
            feature_ids=[self.feature_id],
            information={'title': 'Example Spec'},
            is_error=False,
            http_error_code=None,
        )
        self.link_1.put()

        self.link_2 = FeatureLinks(
            url='https://example.org/web',
            type='web',
            feature_ids=[self.feature_id],
            information=None,
            is_error=True,
            http_error_code=404,
        )
        self.link_2.put()

        self.handler = feature_links_api.FeatureLinksSamplesAPI()

    def tearDown(self):
        """Clean up the test environment."""
        self.link_1.key.delete()
        self.link_2.key.delete()
        self.feature_1.key.delete()
        for user in AppUser.query().fetch(None):
            user.key.delete()

    def test_do_get__admin_success(self):
        """Admin users can retrieve sample feature links for a domain."""
        admin_user = AppUser(email='admin@example.com', is_admin=True)
        admin_user.put()

        testing_config.sign_out()
        testing_config.sign_in('admin@example.com', 123)
        
        path = '/api/v0/feature_links_samples?domain=https://example.org'
        with test_app.test_request_context(path):
            actual_response = self.handler.do_get()
        testing_config.sign_out()

        self.assertIsInstance(actual_response, list)
        self.assertEqual(1, len(actual_response))
        sample = actual_response[0]
        self.assertEqual('https://example.org/web', sample['url'])
        self.assertEqual('web', sample['type'])
        self.assertEqual(self.feature_id, sample['feature_ids'])
        self.assertTrue(sample['is_error'])
        self.assertEqual(404, sample['http_error_code'])

    def test_do_get__forbidden(self):
        """Regular users cannot retrieve sample feature links."""
        testing_config.sign_out()
        testing_config.sign_in('regular_user@example.com', 123)
        with test_app.test_request_context('/api/v0/feature_links_samples?domain=https://example.org'):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_get()
        testing_config.sign_out()
