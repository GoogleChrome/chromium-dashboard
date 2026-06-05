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

"""Tests for releasenotes_l10n_helpers.py."""

import logging
from unittest import mock

import flask
import requests

import testing_config  # isort: split

from api import features_api
from framework import rediscache
from internals import releasenotes_l10n_helpers

test_app = flask.Flask(__name__)


class ReleaseNotesServingTest(testing_config.CustomTestCase):
    """Tests for localized release notes serving."""

    def setUp(self):
        """Set up test features and endpoints."""
        logging.disable(logging.CRITICAL)
        self.handler = features_api.FeaturesAPI()
        self.request_path = '/api/v0/features'

    def tearDown(self):
        """Clean up test environment."""
        logging.disable(logging.NOTSET)
        rediscache.flushall()

    def test_murmur3_hash_correctness(self):
        """Verify the Python murmur3 hash matches Java's outputs exactly."""
        # Test Case 1: Simple string
        text_1 = 'WebUSB API Support'
        hash_1 = releasenotes_l10n_helpers.murmur3_x64_128_h1(text_1)
        self.assertEqual('7851a20bf8f14d0a', hash_1)

        # Test Case 2: Long description
        text_2 = (
            'This feature allows web applications to communicate directly with '
            'USB devices, improving hardware integrations.'
        )
        hash_2 = releasenotes_l10n_helpers.murmur3_x64_128_h1(text_2)
        self.assertEqual('8914204e909276d9', hash_2)

        # Test Case 3: Very long description with markdown formatting, links, and newlines
        text_3 = (
            '**PreferSlowKEXAlgorithms** and **PreferSlowCiphers** are two new, experimental enterprise policies that configure Chrome to order its preferred key agreement algorithms (supported groups) and encryption cipher algorithms, in [TLS 1.3](https://datatracker.ietf.org/doc/html/rfc8446), to reflect a preference for algorithms that have been approved by a specific compliance regime. \n'
            'Currently, the only compliance regime is [CNSA2](https://datatracker.ietf.org/doc/draft-becker-cnsa2-ssh-profile/). This does not guarantee that any specific algorithms will be negotiated. It allows server operators who want to support clients with and without compliance requirements to differentiate between clients, and only use certain non-default algorithms with increased cryptographic strength for those explicitly configured to prefer them. This policy is not required for security. The default cryptography used by Chrome is strong enough to withstand a brute force attack using the [entire power of the sun](https://www.schneier.com/blog/archives/2009/09/the_doghouse_cr.html#:~:text=the%20second%20law%20of%20thermodynamics%20is%20that%20a%20certain%20amount%20of%20energy%20is%20necessary%20to%20represent%20information). Setting this policy will cause Chrome to be slower when accessing websites. This policy only affects TLS 1.3 and [QUIC](https://datatracker.ietf.org/doc/rfc9000/), it does not affect earlier versions of TLS.\n\n'
            'These policies are temporarily available as a single combined flag, `chrome://#cryptography-compliance-cnsa`.'
        )
        hash_3 = releasenotes_l10n_helpers.murmur3_x64_128_h1(text_3)
        self.assertEqual('728b2ea253f2aa05', hash_3)

    @mock.patch('requests.get')
    def test_fetch_translation_dict_caching(self, mock_get):
        """Verify fetch_translation_dict caches results in Redis."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'key1': {'text': 'translation1'}}
        mock_get.return_value = mock_response

        # First fetch: should call requests.get
        dict_1 = releasenotes_l10n_helpers.fetch_translation_dict('fr')
        self.assertEqual({'key1': {'text': 'translation1'}}, dict_1)
        mock_get.assert_called_once_with(
            'https://chromeenterprise.google/static/json/release_notes_fr.json',
            timeout=releasenotes_l10n_helpers.L10N_FETCH_TIMEOUT_SEC,
        )

        # Second fetch: should serve from cache (mock_get not called again)
        mock_get.reset_mock()
        dict_2 = releasenotes_l10n_helpers.fetch_translation_dict('fr')
        self.assertEqual({'key1': {'text': 'translation1'}}, dict_2)
        mock_get.assert_not_called()

    @mock.patch('requests.get')
    def test_fetch_translation_dict_stale_fallback(self, mock_get):
        """Verify fetch_translation_dict falls back to stale cache on fetch error."""
        # Populate the cache manually
        cache_key = 'l10n_release_notes_fr'
        rediscache.set(
            cache_key,
            {
                'data': {'key1': {'text': 'stale_translation'}},
                'fetched_at': 0,  # Expired
            },
        )

        # Mock requests.get to fail (e.g. timeout)
        mock_get.side_effect = requests.exceptions.Timeout(
            'Connection timed out'
        )

        # Fetch should fall back and return the stale dict
        dict_val = releasenotes_l10n_helpers.fetch_translation_dict('fr')
        self.assertEqual({'key1': {'text': 'stale_translation'}}, dict_val)

        # If cache is missing and fetch fails, should return empty dict
        rediscache.delete(cache_key)
        dict_val_empty = releasenotes_l10n_helpers.fetch_translation_dict('fr')
        self.assertEqual({}, dict_val_empty)

    @mock.patch('requests.get')
    def test_fetch_translation_dict_non_200_fallback(self, mock_get):
        """Verify fetch_translation_dict falls back to stale cache on HTTP error status (non-200)."""
        # Populate the cache manually
        cache_key = 'l10n_release_notes_fr'
        rediscache.set(
            cache_key,
            {
                'data': {'key1': {'text': 'stale_translation'}},
                'fetched_at': 0,  # Expired
            },
        )

        # Mock requests.get to return HTTP 500
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Fetch should fall back and return the stale dict
        dict_val = releasenotes_l10n_helpers.fetch_translation_dict('fr')
        self.assertEqual({'key1': {'text': 'stale_translation'}}, dict_val)

        # If cache is missing and fetch returns 500, should return empty dict
        rediscache.delete(cache_key)
        dict_val_empty = releasenotes_l10n_helpers.fetch_translation_dict('fr')
        self.assertEqual({}, dict_val_empty)

    @mock.patch('internals.releasenotes_l10n_helpers.fetch_translation_dict')
    def test_merge_translations(self, mock_fetch):
        """Verify merge_translations correctly merges values and falls back on mismatch."""
        mock_fetch.return_value = {
            'feature_123_name_7851a20bf8f14d0a': {'text': 'Translated Name'},
            'feature_123_summary_8914204e909276d9': {
                'text': 'Translated Summary'
            },
            'feature_123_stage_456_rolloutDetails_7851a20bf8f14d0a': {
                'text': 'Translated Rollout'
            },
        }

        features = [
            {
                'id': 123,
                'name': 'WebUSB API Support',
                'summary': (
                    'This feature allows web applications to communicate directly with '
                    'USB devices, improving hardware integrations.'
                ),
                'stages': [
                    {
                        'id': 456,
                        'rollout_details': 'WebUSB API Support',
                    }
                ],
            }
        ]

        merged = releasenotes_l10n_helpers.merge_translations(features, 'fr')
        self.assertEqual('Translated Name', merged[0]['name'])
        self.assertEqual('Translated Summary', merged[0]['summary'])
        self.assertEqual(
            'Translated Rollout', merged[0]['stages'][0]['rollout_details']
        )

        # Mismatch test: Change the summary so its hash doesn't match the dictionary
        features_modified = [
            {
                'id': 123,
                'name': 'WebUSB API Support',
                'summary': 'Modified English Summary',
                'stages': [],
            }
        ]
        merged_modified = releasenotes_l10n_helpers.merge_translations(
            features_modified, 'fr'
        )
        # Should keep original English summary since hash didn't match
        self.assertEqual(
            'Modified English Summary', merged_modified[0]['summary']
        )
        # Name should still be translated
        self.assertEqual('Translated Name', merged_modified[0]['name'])

    @mock.patch('internals.feature_helpers.get_features_in_release_notes')
    @mock.patch('internals.releasenotes_l10n_helpers.fetch_translation_dict')
    def test_features_api_integration(self, mock_fetch, mock_get_features):
        """Verify the feature API endpoint handles the lang parameter and translates features."""
        mock_get_features.side_effect = lambda *args, **kwargs: [
            {
                'id': 123,
                'name': 'WebUSB API Support',
                'summary': 'English Summary',
                'stages': [],
            }
        ]
        mock_fetch.return_value = {
            'feature_123_name_7851a20bf8f14d0a': {'text': 'Translated Name'},
        }

        # Request with lang=fr
        path = self.request_path + '?releaseNotesMilestone=138&lang=fr'
        with test_app.test_request_context(path):
            actual = self.handler.do_get()
        self.assertEqual('Translated Name', actual['features'][0]['name'])

        # Request with mixed case and whitespace (e.g. lang=" FR ")
        mock_fetch.reset_mock()
        path_normalize = (
            self.request_path + '?releaseNotesMilestone=138&lang=%20FR%20'
        )
        with test_app.test_request_context(path_normalize):
            actual_normalize = self.handler.do_get()
        self.assertEqual(
            'Translated Name', actual_normalize['features'][0]['name']
        )

        # Request without lang parameter (should default to English)
        mock_fetch.reset_mock()
        path_no_lang = self.request_path + '?releaseNotesMilestone=138'
        with test_app.test_request_context(path_no_lang):
            actual_no_lang = self.handler.do_get()
        mock_fetch.assert_not_called()
        self.assertEqual(
            'WebUSB API Support', actual_no_lang['features'][0]['name']
        )

        # Request with unsupported language (e.g. lang=it)
        mock_fetch.reset_mock()
        path_unsupported = (
            self.request_path + '?releaseNotesMilestone=138&lang=it'
        )
        with test_app.test_request_context(path_unsupported):
            actual_unsupported = self.handler.do_get()
        mock_fetch.assert_not_called()
        self.assertEqual(
            'WebUSB API Support', actual_unsupported['features'][0]['name']
        )

        # Request with invalid lang code (SSRF/Traversal guard)
        mock_fetch.reset_mock()
        path_invalid = (
            self.request_path + '?releaseNotesMilestone=138&lang=../../bad'
        )
        with test_app.test_request_context(path_invalid):
            actual_invalid = self.handler.do_get()
        # Should not fetch translations and keep English
        mock_fetch.assert_not_called()
        self.assertEqual(
            'WebUSB API Support', actual_invalid['features'][0]['name']
        )
