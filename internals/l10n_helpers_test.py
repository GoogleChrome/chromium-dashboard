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

"""Unit tests for core localization framework, universal parity validator, and helpers."""

import json
import os
import shutil
import tempfile
import unittest
from enum import StrEnum
from typing import TypeVar

from internals import l10n_helpers, l10n_models

E = TypeVar('E', bound=StrEnum)


class MockPageKey(StrEnum):
    """Sample string keys for testing the generic L10n framework."""

    HEADER_TITLE = 'header_title'
    WELCOME_MESSAGE = 'welcome_message'
    ITEM_COUNT_DESC = 'item_count_desc'
    ACTION_BUTTON = 'action_button'


def assert_page_locale_parity(
    locales_dir: str,
    key_enum: type[E],
    placeholders: dict[E, set[str]] | None = None,
) -> None:
    """Universal CI validator that verifies 100% key and placeholder parity for any domain."""
    expected_keys = {e.value for e in key_enum}
    expected_placeholders = {
        (k.value if isinstance(k, StrEnum) else str(k)): v
        for k, v in (placeholders or {}).items()
    }

    en_file = os.path.join(
        locales_dir, f'{l10n_models.DEFAULT_LANGUAGE.value}.json'
    )
    if not os.path.exists(en_file):
        raise l10n_models.LocaleValidationError(
            f'Canonical English locale ({l10n_models.DEFAULT_LANGUAGE.value}.json) not found in {locales_dir}'
        )

    for lang in l10n_models.SupportedLanguage:
        file_path = os.path.join(locales_dir, f'{lang.value}.json')
        if not os.path.exists(file_path):
            raise l10n_models.LocaleValidationError(
                f"Missing expected locale file for language '{lang.value}': {file_path}"
            )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            raise l10n_models.LocaleValidationError(
                f'Failed to parse locale JSON file {file_path}: {e}'
            ) from e

        actual_keys = set(data.keys())

        # 1. Check for missing keys
        missing_keys = expected_keys - actual_keys
        if missing_keys:
            raise l10n_models.LocaleValidationError(
                f"Locale '{lang.value}.json' is missing required keys: {missing_keys}"
            )

        # 2. Check for extra/orphaned keys
        extra_keys = actual_keys - expected_keys
        if extra_keys:
            raise l10n_models.LocaleValidationError(
                f"Locale '{lang.value}.json' contains unrecognized/orphaned keys: {extra_keys}"
            )

        # 3. Check placeholder token parity
        for key_name, tokens in expected_placeholders.items():
            actual_tokens = l10n_models.extract_placeholders(
                data.get(key_name, '')
            )
            if actual_tokens != tokens:
                raise l10n_models.LocaleValidationError(
                    f"Locale '{lang.value}.json' key '{key_name}' placeholder mismatch: "
                    f'expected {tokens}, got {actual_tokens}'
                )


class L10nCoreFrameworkTest(unittest.TestCase):
    """Test suite for core L10n models, universal validator, and helper functions."""

    def setUp(self):
        """Initializes a temporary directory with valid mock catalogs for all languages."""
        self.temp_dir = tempfile.mkdtemp()
        self.valid_mock_placeholders = {
            MockPageKey.WELCOME_MESSAGE: {'username'},
            MockPageKey.ITEM_COUNT_DESC: {'count', 'item_type'},
        }

        # Seed valid mock catalogs for all 10 languages
        for lang in l10n_models.SupportedLanguage:
            mock_data = {
                MockPageKey.HEADER_TITLE.value: f'Title in {lang.value}',
                MockPageKey.WELCOME_MESSAGE.value: f'Hello {{username}} in {lang.value}',
                MockPageKey.ITEM_COUNT_DESC.value: f'You have {{count}} {{item_type}} in {lang.value}',
                MockPageKey.ACTION_BUTTON.value: f'Submit in {lang.value}',
            }
            with open(
                os.path.join(self.temp_dir, f'{lang.value}.json'),
                'w',
                encoding='utf-8',
            ) as f:
                json.dump(mock_data, f)

    def tearDown(self):
        """Cleans up the temporary directory after test execution."""
        shutil.rmtree(self.temp_dir)

    def test_assert_page_locale_parity__success_on_valid_catalogs(self):
        """It passes without error when all catalogs have exact key and placeholder parity."""
        assert_page_locale_parity(
            locales_dir=self.temp_dir,
            key_enum=MockPageKey,
            placeholders=self.valid_mock_placeholders,
        )

    def test_assert_page_locale_parity__detects_missing_key(self):
        """It raises LocaleValidationError when a translation file is missing a required key."""
        ja_file = os.path.join(self.temp_dir, 'ja.json')
        with open(ja_file, 'r', encoding='utf-8') as f:
            ja_data = json.load(f)
        del ja_data[MockPageKey.ACTION_BUTTON.value]
        with open(ja_file, 'w', encoding='utf-8') as f:
            json.dump(ja_data, f)

        with self.assertRaises(l10n_models.LocaleValidationError) as ctx:
            assert_page_locale_parity(
                locales_dir=self.temp_dir,
                key_enum=MockPageKey,
                placeholders=self.valid_mock_placeholders,
            )
        self.assertIn('missing required keys', str(ctx.exception))
        self.assertIn('action_button', str(ctx.exception))

    def test_assert_page_locale_parity__detects_orphaned_extra_key(self):
        """It raises LocaleValidationError when a translation file has leftover orphaned keys."""
        es_file = os.path.join(self.temp_dir, 'es.json')
        with open(es_file, 'r', encoding='utf-8') as f:
            es_data = json.load(f)
        es_data['obsolete_legacy_key'] = 'Old unused string'
        with open(es_file, 'w', encoding='utf-8') as f:
            json.dump(es_data, f)

        with self.assertRaises(l10n_models.LocaleValidationError) as ctx:
            assert_page_locale_parity(
                locales_dir=self.temp_dir,
                key_enum=MockPageKey,
                placeholders=self.valid_mock_placeholders,
            )
        self.assertIn('contains unrecognized/orphaned keys', str(ctx.exception))
        self.assertIn('obsolete_legacy_key', str(ctx.exception))

    def test_assert_page_locale_parity__detects_placeholder_token_mismatch(
        self,
    ):
        """It raises LocaleValidationError when a placeholder token is corrupted or typo'd."""
        de_file = os.path.join(self.temp_dir, 'de.json')
        with open(de_file, 'r', encoding='utf-8') as f:
            de_data = json.load(f)
        # Typo {username} as {user}
        de_data[MockPageKey.WELCOME_MESSAGE.value] = 'Hallo {user} auf Deutsch'
        with open(de_file, 'w', encoding='utf-8') as f:
            json.dump(de_data, f)

        with self.assertRaises(l10n_models.LocaleValidationError) as ctx:
            assert_page_locale_parity(
                locales_dir=self.temp_dir,
                key_enum=MockPageKey,
                placeholders=self.valid_mock_placeholders,
            )
        self.assertIn('placeholder mismatch', str(ctx.exception))
        self.assertIn('welcome_message', str(ctx.exception))

    def test_load_flat_page_strings(self):
        """It loads all flat string JSON files into memory by language enum."""
        loaded = l10n_helpers.load_flat_page_strings(
            domain_name='mock',
            locales_dir=self.temp_dir,
        )
        self.assertEqual(len(loaded), len(l10n_models.SupportedLanguage))
        self.assertIn(l10n_models.SupportedLanguage.EN, loaded)
        self.assertIn(l10n_models.SupportedLanguage.JA, loaded)
        self.assertEqual(
            loaded[l10n_models.SupportedLanguage.JA][
                MockPageKey.HEADER_TITLE.value
            ],
            'Title in ja',
        )

    def test_get_supported_languages__filters_to_available_translations(self):
        """It only includes LanguageOptions for languages that actually exist in the map."""
        partial_map = {
            l10n_models.SupportedLanguage.EN: {'k': 'v'},
            l10n_models.SupportedLanguage.JA: {'k': 'v'},
            l10n_models.SupportedLanguage.ES: {'k': 'v'},
        }
        opts = l10n_helpers.get_supported_languages(partial_map)
        self.assertEqual(len(opts), 3)
        self.assertEqual(opts[0].code, 'en')
        codes = [o.code for o in opts]
        self.assertEqual(codes, ['en', 'es', 'ja'])

    def test_resolve_supported_language(self):
        """It resolves string tags and Enum instances to SupportedLanguage with safe fallback."""
        self.assertEqual(
            l10n_helpers.resolve_supported_language('ja'),
            l10n_models.SupportedLanguage.JA,
        )
        self.assertEqual(
            l10n_helpers.resolve_supported_language('ES'),
            l10n_models.SupportedLanguage.ES,
        )
        self.assertEqual(
            l10n_helpers.resolve_supported_language('pt-BR'),
            l10n_models.SupportedLanguage.PT_BR,
        )
        self.assertEqual(
            l10n_helpers.resolve_supported_language(
                l10n_models.SupportedLanguage.JA
            ),
            l10n_models.SupportedLanguage.JA,
        )
        self.assertEqual(
            l10n_helpers.resolve_supported_language(None),
            l10n_models.SupportedLanguage.EN,
        )
        self.assertEqual(
            l10n_helpers.resolve_supported_language(''),
            l10n_models.SupportedLanguage.EN,
        )
        self.assertEqual(
            l10n_helpers.resolve_supported_language('unknown-lang'),
            l10n_models.SupportedLanguage.EN,
        )
