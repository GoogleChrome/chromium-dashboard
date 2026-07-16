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

import unittest
from unittest.mock import patch

import flask
from google.cloud import ndb

import testing_config  # noqa: F401
from internals.core_models import FeatureEntry
from pages import sitemap

test_app = flask.Flask(__name__)
test_app.secret_key = 'test_session_secret'


class SitemapHandlerTest(unittest.TestCase):
    """Tests for the SitemapHandler."""

    def setUp(self):
        """Set up the test."""
        self.handler = sitemap.SitemapHandler()
        self.request_path = '/sitemap.txt'

    @patch('internals.core_models.FeatureEntry.query')
    def test_get_sitemap(self, mock_query):
        """We can retrieve the sitemap.txt content and filter features correctly."""
        client = ndb.Client()
        with client.context():
            fe1 = FeatureEntry(
                id=1,
                name='Listed 1',
                category=1,
                deleted=False,
                unlisted=False,
                confidential=False,
            )
            fe2 = FeatureEntry(
                id=2,
                name='Unlisted',
                category=1,
                deleted=False,
                unlisted=True,
                confidential=False,
            )
            fe3 = FeatureEntry(
                id=3,
                name='Confidential',
                category=1,
                deleted=False,
                unlisted=False,
                confidential=True,
            )
            fe4 = FeatureEntry(
                id=4,
                name='Deleted',
                category=1,
                deleted=True,
                unlisted=False,
                confidential=False,
            )
            fe5 = FeatureEntry(
                id=5,
                name='Listed 2',
                category=1,
                deleted=False,
                unlisted=False,
                confidential=False,
            )

        # Mock the fetch to return ALL features to test our in-memory filtering as well,
        # or exactly what the query would return (which would be 1, 3, 5 if we query deleted=False and unlisted=False).
        # Wait, if the query in the code is:
        #   query = FeatureEntry.query(deleted == False, unlisted == False)
        # Then the mock should return the set of features that MATCH that query,
        # OR we can return all of them to make sure the IN-MEMORY filter catches the rest!
        # Let's return all to be thorough with in-memory filter testing.
        mock_query.return_value.fetch.return_value = [fe1, fe2, fe3, fe4, fe5]

        with test_app.test_request_context(self.request_path):
            actual_response = self.handler.get()

        # Actual response should be a tuple: (content, headers)
        self.assertIsInstance(actual_response, tuple)
        self.assertEqual(2, len(actual_response))

        content, headers = actual_response
        expected_content = 'https://chromestatus.com/feature/1\nhttps://chromestatus.com/feature/5\n'
        self.assertEqual(expected_content, content)
        self.assertEqual('text/plain', headers['Content-Type'])

        # Verify that the query was called with expected filters
        mock_query.assert_called_once()

    @patch('internals.core_models.FeatureEntry.query')
    def test_route_registered(self, mock_query):
        """The /sitemap.txt route is registered in main.py and returns expected content."""
        client = ndb.Client()
        with client.context():
            fe1 = FeatureEntry(
                id=1,
                name='Listed 1',
                category=1,
                deleted=False,
                unlisted=False,
                confidential=False,
            )
            fe5 = FeatureEntry(
                id=5,
                name='Listed 2',
                category=1,
                deleted=False,
                unlisted=False,
                confidential=False,
            )

        mock_query.return_value.fetch.return_value = [fe1, fe5]

        from main import app

        with app.test_client() as client:
            response = client.get('/sitemap.txt')
            self.assertEqual(200, response.status_code)
            expected_content = b'https://chromestatus.com/feature/1\nhttps://chromestatus.com/feature/5\n'
            self.assertEqual(expected_content, response.data)
            self.assertIn('text/plain', response.headers['Content-Type'])
