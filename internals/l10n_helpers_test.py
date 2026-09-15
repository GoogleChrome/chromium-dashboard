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

"""Unit tests for localization framework, universal parity validator, and release notes translations."""

import dataclasses
import json
import os
import shutil
import tempfile
import unittest
from enum import StrEnum
from typing import TypeVar

from internals import core_enums, l10n_helpers, l10n_models

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

    def test_format_localized_path(self):
        """It formats canonical URL paths with ?hl= for non-default languages only."""
        self.assertEqual(
            l10n_helpers.format_localized_path('/release-notes/152', 'en'),
            '/release-notes/152',
        )
        self.assertEqual(
            l10n_helpers.format_localized_path(
                '/release-notes/152', l10n_models.SupportedLanguage.EN
            ),
            '/release-notes/152',
        )
        self.assertEqual(
            l10n_helpers.format_localized_path('/release-notes/152', 'ja'),
            '/release-notes/152?hl=ja',
        )
        self.assertEqual(
            l10n_helpers.format_localized_path(
                '/release-notes/152', l10n_models.SupportedLanguage.ES
            ),
            '/release-notes/152?hl=es',
        )
        self.assertEqual(
            l10n_helpers.format_localized_path('/roadmap', 'unknown-lang'),
            '/roadmap',
        )

    def test_get_page_translations__static_and_context_formatting(self):
        """It formats context placeholders and provides callables for dynamic placeholders."""
        ja_ui = l10n_helpers.get_page_translations(
            domain_name='mock',
            lang='ja',
            locales_dir=self.temp_dir,
            username='Alice',
        )
        self.assertEqual(ja_ui['header_title'], 'Title in ja')
        self.assertEqual(ja_ui['welcome_message'], 'Hello Alice in ja')
        self.assertEqual(ja_ui['action_button'], 'Submit in ja')
        self.assertEqual(
            ja_ui['item_count_desc'](count=5, item_type='features'),
            'You have 5 features in ja',
        )

    def test_get_page_translations__safe_fallback_on_unknown_lang(self):
        """It safely falls back to English when an unknown language code is requested."""
        fallback_ui = l10n_helpers.get_page_translations(
            domain_name='mock',
            lang='invalid-locale',
            locales_dir=self.temp_dir,
            username='Bob',
        )
        self.assertEqual(fallback_ui['header_title'], 'Title in en')
        self.assertEqual(fallback_ui['welcome_message'], 'Hello Bob in en')


class ReleaseNotesL10nTest(unittest.TestCase):
    """Exhaustive tests for the Release Notes localization catalogs and models."""

    def test_production_release_notes_locales_have_exact_schema_parity(self):
        """Asserts that all 10 real production JSON files in locales/release_notes pass parity checks."""
        assert_page_locale_parity(
            locales_dir='locales/release_notes',
            key_enum=l10n_models.ReleaseNotesKey,
            placeholders=l10n_models.RELEASE_NOTES_PLACEHOLDERS,
        )

    def test_dataclass_fields_match_enum(self):
        """Guarantees that ReleaseNotesTranslations dataclass fields match ReleaseNotesKey exactly."""
        dataclass_fields = {
            f.name
            for f in dataclasses.fields(l10n_models.ReleaseNotesTranslations)
        }
        enum_fields = {k.value for k in l10n_models.ReleaseNotesKey}
        self.assertEqual(dataclass_fields, enum_fields)

    def test_all_core_enums_categories_have_l10n_parity(self):
        """Guarantees that all categories in core_enums.FEATURE_CATEGORIES resolve cleanly in L10n."""
        en_trans = l10n_helpers.get_release_notes_translations('en')
        ja_trans = l10n_helpers.get_release_notes_translations('ja')
        for category_id in core_enums.FEATURE_CATEGORIES.keys():
            en_cat = en_trans.get_category(category_id)
            ja_cat = ja_trans.get_category(category_id)
            self.assertTrue(len(en_cat) > 0)
            self.assertTrue(len(ja_cat) > 0)

    def test_get_release_notes_translations__returns_loaded_translations(self):
        """It retrieves the typed translations for a language with English fallback."""
        ja_trans = l10n_helpers.get_release_notes_translations('ja')
        self.assertEqual(ja_trans.category_css, 'CSS')

        fallback_trans = l10n_helpers.get_release_notes_translations(
            'unknown-lang'
        )
        self.assertEqual(
            fallback_trans.page_title,
            'Chrome {milestone} Release Notes',
        )

    def test_category_localization_and_fallback(self):
        """It translates category integer IDs into target languages and encapsulates defaults."""
        ja_trans = l10n_helpers.get_release_notes_translations('ja')
        self.assertEqual(ja_trans.get_category(core_enums.MISC), 'その他')
        self.assertEqual(ja_trans.get_category(None), 'その他')
        self.assertEqual(
            ja_trans.get_category(core_enums.SECURITY), 'セキュリティ'
        )
        self.assertEqual(ja_trans.get_category(core_enums.CSS), 'CSS')
        self.assertEqual(ja_trans.get_category(99999), 'その他')

        es_trans = l10n_helpers.get_release_notes_translations('es')
        self.assertEqual(es_trans.get_category(core_enums.MISC), 'Varios')
        self.assertEqual(es_trans.get_category(None), 'Varios')
        self.assertEqual(
            es_trans.get_category(core_enums.PERFORMANCE), 'Rendimiento'
        )

        de_trans = l10n_helpers.get_release_notes_translations('de')
        self.assertEqual(de_trans.get_category(core_enums.MISC), 'Sonstiges')

        en_trans = l10n_helpers.get_release_notes_translations('en')
        self.assertEqual(
            en_trans.get_category(core_enums.MISC), 'Miscellaneous'
        )
        self.assertEqual(en_trans.get_category(None), 'Miscellaneous')

    def test_link_localization(self):
        """It translates link titles and extracts tracking bug numbers."""
        test_links = [
            l10n_models.ReleaseNoteLinkItem(
                type=core_enums.ReleaseNoteLinkType.BUG,
                url='https://issues.chromium.org/issues/12345',
                title='Tracking bug #12345',
            ),
            l10n_models.ReleaseNoteLinkItem(
                type=core_enums.ReleaseNoteLinkType.SPEC,
                url='https://w3c.github.io/spec',
                title='Spec',
            ),
            l10n_models.ReleaseNoteLinkItem(
                type=core_enums.ReleaseNoteLinkType.DOC,
                url='https://developer.mozilla.org/docs',
                title='Docs',
            ),
            l10n_models.ReleaseNoteLinkItem(
                type=core_enums.ReleaseNoteLinkType.ORIGIN_TRIAL,
                url='/origintrials#/view_trial/1',
                title='Origin trial',
            ),
            l10n_models.ReleaseNoteLinkItem(
                type=core_enums.ReleaseNoteLinkType.BUG,
                url='https://issues.chromium.org/new',
                title=None,
            ),
        ]

        ja_trans = l10n_helpers.get_release_notes_translations('ja')
        ja_links = ja_trans.localize_links(test_links)
        self.assertEqual(ja_links[0].title, 'トラッキング バグ #12345')
        self.assertEqual(ja_links[1].title, '仕様')
        self.assertEqual(ja_links[2].title, 'ドキュメント')
        self.assertEqual(ja_links[3].title, 'オリジントライアル')
        self.assertEqual(ja_links[4].title, 'トラッキング バグ')

        es_trans = l10n_helpers.get_release_notes_translations('es')
        es_links = es_trans.localize_links(test_links)
        self.assertEqual(es_links[0].title, 'Error de seguimiento #12345')
        self.assertEqual(es_links[1].title, 'Especificación')
        self.assertEqual(es_links[2].title, 'Documentación')
        self.assertEqual(es_links[3].title, 'Prueba de origen')
        self.assertEqual(es_links[4].title, 'Error de seguimiento')

    def test_format_ui__english_and_japanese(self):
        """It constructs pre-formatted type-safe UI strings for release notes."""
        en_trans = l10n_helpers.get_release_notes_translations('en')
        en_ui = en_trans.format_ui(
            milestone=151, prev_milestone=150, next_milestone=152
        )
        self.assertEqual(en_ui['page_title'], 'Chrome 151 Release Notes')
        self.assertEqual(
            en_ui['prev_milestone_aria'], 'Previous milestone: Chrome 150'
        )
        self.assertEqual(
            en_ui['next_milestone_aria'], 'Next milestone: Chrome 152'
        )
        self.assertEqual(en_ui['origin_trials_heading'], 'New origin trials')
        self.assertEqual(
            en_ui['copy_link_aria']('CSS Grid'), 'Copy link to CSS Grid'
        )

        ja_trans = l10n_helpers.get_release_notes_translations('ja')
        ja_ui = ja_trans.format_ui(
            milestone=151, prev_milestone=150, next_milestone=152
        )
        self.assertEqual(ja_ui['page_title'], 'Chrome 151 リリースノート')
        self.assertEqual(
            ja_ui['prev_milestone_aria'], '前のマイルストーン: Chrome 150'
        )
        self.assertEqual(
            ja_ui['next_milestone_aria'], '次のマイルストーン: Chrome 152'
        )
        self.assertEqual(
            ja_ui['origin_trials_heading'], '新しいオリジントライアル'
        )
        self.assertEqual(
            ja_ui['copy_link_aria']('CSS Grid'), 'CSS Grid へのリンクをコピー'
        )
