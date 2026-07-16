# -*- coding: utf-8 -*-
# Copyright 2026 Google LLC
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

"""Tests for the sitemap module."""

import flask

import testing_config
from internals.core_models import FeatureEntry
from pages import sitemap

test_app = flask.Flask(__name__)
test_app.secret_key = 'test_session_secret'


class SitemapHandlerTest(testing_config.CustomTestCase):
    """Tests for the SitemapHandler using real Datastore queries."""

    def setUp(self):
        """Set up the test."""
        self.handler = sitemap.SitemapHandler()
        self.request_path = '/sitemap.txt'

        self.fe1 = FeatureEntry(
            name='Listed 1',
            summary='summary',
            category=1,
            deleted=False,
            unlisted=False,
            confidential=False,
        )
        self.fe1.put()
        self.fe1_id = self.fe1.key.integer_id()

        self.fe2 = FeatureEntry(
            name='Unlisted',
            summary='summary',
            category=1,
            deleted=False,
            unlisted=True,
            confidential=False,
        )
        self.fe2.put()

        self.fe3 = FeatureEntry(
            name='Confidential',
            summary='summary',
            category=1,
            deleted=False,
            unlisted=False,
            confidential=True,
        )
        self.fe3.put()

        self.fe4 = FeatureEntry(
            name='Deleted',
            summary='summary',
            category=1,
            deleted=True,
            unlisted=False,
            confidential=False,
        )
        self.fe4.put()

        self.fe5 = FeatureEntry(
            name='Listed 2',
            summary='summary',
            category=1,
            deleted=False,
            unlisted=False,
            confidential=False,
        )
        self.fe5.put()
        self.fe5_id = self.fe5.key.integer_id()

    def tearDown(self):
        """Clean up the test environment by deleting created FeatureEntries."""
        for entry in FeatureEntry.query():
            entry.key.delete()

    def test_get_sitemap(self):
        """We can retrieve the sitemap.txt content with actual Datastore queries."""
        with test_app.test_request_context(self.request_path):
            actual_response = self.handler.get()

        # Actual response should be a tuple: (content, headers)
        self.assertIsInstance(actual_response, tuple)
        self.assertEqual(2, len(actual_response))

        content, headers = actual_response

        # Sort the IDs so we know the expected URL order
        expected_ids = sorted([self.fe1_id, self.fe5_id])
        expected_content = (
            f'https://chromestatus.com/feature/{expected_ids[0]}\n'
            f'https://chromestatus.com/feature/{expected_ids[1]}\n'
        )
        self.assertEqual(expected_content, content)
        self.assertEqual('text/plain', headers['Content-Type'])
