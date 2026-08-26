# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

"""Unit tests for translation_helpers module."""

import unittest
from unittest import mock

import testing_config  # noqa: F401
from framework import rediscache
from internals import translation_helpers


class TranslationHelpersTest(unittest.TestCase):
    """Unit tests for translation helpers, Redis caching, and error fallbacks."""

    def setUp(self):
        """Set up clean Redis test state."""
        rediscache.flushall()

    def tearDown(self):
        """Clean up Redis test state."""
        rediscache.flushall()

    def test_compute_summary_hash__deterministic(self):
        """It computes consistent 16-character SHA-256 fingerprints with whitespace normalization."""
        hash1 = translation_helpers.compute_summary_hash('Test summary text')
        hash2 = translation_helpers.compute_summary_hash(
            '  Test summary text  '
        )
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 16)

        hash3 = translation_helpers.compute_summary_hash('Different text')
        self.assertNotEqual(hash1, hash3)

    def test_build_summary_cache_key(self):
        """It constructs structured Redis cache keys with feature ID, language, and content hash."""
        key = translation_helpers.build_summary_cache_key(
            12345, 'ja', 'abc1234567890def'
        )
        self.assertEqual(key, 'l10n_feat_summary|12345|ja|abc1234567890def')

    def test_mask_code_elements_for_translation(self):
        """It adds translate='no' attributes to <code> tags without duplicating existing attributes."""
        html = '<p>Use <code>navigator.gpu</code> and <code translate="no">fetch()</code></p>'
        masked = translation_helpers.mask_code_elements_for_translation(html)
        self.assertEqual(
            masked,
            '<p>Use <code translate="no">navigator.gpu</code> and <code translate="no">fetch()</code></p>',
        )

    def test_localize_features_for_release_notes__english_returns_en_and_renders_markdown(
        self,
    ):
        """It renders markdown and assigns summary_lang='en' when English is requested."""
        features = [
            {'id': 1, 'summary': 'Summary with `code`'},
            {'id': 2, 'summary': 'Another summary'},
        ]
        result = translation_helpers.localize_features_for_release_notes(
            features, 'en'
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['summary_lang'], 'en')
        self.assertIn('<code>code</code>', result[0]['formatted_summary'])
        self.assertEqual(result[1]['summary_lang'], 'en')

    def test_localize_features_for_release_notes__translates_and_caches_in_redis(
        self,
    ):
        """It translates missing summaries, caches them in Redis, and serves from cache subsequently."""
        features = [
            {'id': 101, 'summary': 'First feature summary'},
            {'id': 102, 'summary': 'Second feature summary'},
        ]
        result = translation_helpers.localize_features_for_release_notes(
            features, 'ja'
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['summary_lang'], 'ja')
        self.assertTrue(
            result[0]['formatted_summary'].startswith('[Translated to ja]')
        )
        self.assertEqual(result[1]['summary_lang'], 'ja')

        # Verify cached in Redis
        hash101 = translation_helpers.compute_summary_hash(
            'First feature summary'
        )
        key101 = translation_helpers.build_summary_cache_key(101, 'ja', hash101)
        cached_val = rediscache.get(key101)
        self.assertEqual(cached_val, result[0]['formatted_summary'])

        # Subsequent call should hit Redis cache (mocking translate_html_batch to verify it's not called)
        with mock.patch(
            'internals.translation_helpers.translate_html_batch'
        ) as mock_translate:
            cached_result = (
                translation_helpers.localize_features_for_release_notes(
                    [{'id': 101, 'summary': 'First feature summary'}], 'ja'
                )
            )
            self.assertEqual(cached_result[0]['formatted_summary'], cached_val)
            mock_translate.assert_not_called()

    def test_localize_features_for_release_notes__invalidates_stale_cache_on_source_change(
        self,
    ):
        """It invalidates and re-translates when the English source summary is modified."""
        # Initial translation
        translation_helpers.localize_features_for_release_notes(
            [{'id': 201, 'summary': 'Original English Summary'}], 'es'
        )

        # Feature edited with new summary
        updated_features = [
            {'id': 201, 'summary': 'Updated English Summary with new details'}
        ]
        new_result = translation_helpers.localize_features_for_release_notes(
            updated_features, 'es'
        )
        self.assertEqual(new_result[0]['summary_lang'], 'es')
        self.assertIn(
            'Updated English Summary', new_result[0]['formatted_summary']
        )

    def test_localize_features_for_release_notes__fallback_on_translation_failure(
        self,
    ):
        """It gracefully falls back to English and does not cache failed attempts when API errors occur."""
        features = [{'id': 301, 'summary': 'Feature during API downtime'}]
        with mock.patch(
            'internals.translation_helpers.translate_html_batch',
            return_value=[None],
        ):
            result = translation_helpers.localize_features_for_release_notes(
                features, 'fr'
            )
            self.assertEqual(result[0]['summary_lang'], 'en')
            self.assertIn(
                'Feature during API downtime', result[0]['formatted_summary']
            )
            # Failed translation must not be cached in Redis
            hash301 = translation_helpers.compute_summary_hash(
                'Feature during API downtime'
            )
            key301 = translation_helpers.build_summary_cache_key(
                301, 'fr', hash301
            )
            self.assertIsNone(rediscache.get(key301))


if __name__ == '__main__':
    unittest.main()
