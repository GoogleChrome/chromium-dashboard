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

"""Unit tests for localization helpers and schema validation."""

import json
import os
import shutil
import tempfile
import unittest

from internals import l10n_helpers, l10n_models


class L10nHelpersTest(unittest.TestCase):
    """Unit test suite for l10n helpers, bundle loading, and validation."""

    def test_all_registered_locales_have_exact_schema_and_placeholder_parity(
        self,
    ):
        """Asserts that all real production JSON files in locales/ pass strict parity checks."""
        bundles = l10n_helpers.load_and_validate_bundles()
        self.assertIn('en', bundles)
        self.assertIn('ja', bundles)
        self.assertIn('es', bundles)
        self.assertIn('de', bundles)
        self.assertIn('fr', bundles)
        self.assertIn('id', bundles)
        self.assertIn('ko', bundles)
        self.assertIn('nl', bundles)
        self.assertIn('pt-br', bundles)
        self.assertIn('zh-cn', bundles)

    def test_resolve_supported_language(self):
        """It correctly parses case-insensitive and hyphenated language tags."""
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
        # Pass-through for Enum
        self.assertEqual(
            l10n_helpers.resolve_supported_language(
                l10n_models.SupportedLanguage.JA
            ),
            l10n_models.SupportedLanguage.JA,
        )
        # Fallbacks for unknown, empty, or None
        self.assertEqual(
            l10n_helpers.resolve_supported_language(None),
            l10n_models.SupportedLanguage.EN,
        )
        self.assertEqual(
            l10n_helpers.resolve_supported_language(''),
            l10n_models.SupportedLanguage.EN,
        )
        self.assertEqual(
            l10n_helpers.resolve_supported_language('xx-unknown'),
            l10n_models.SupportedLanguage.EN,
        )

    def test_get_supported_languages_for_page(self):
        """It returns supported language options in canonical order with English first."""
        langs = l10n_helpers.get_supported_languages_for_page()
        self.assertTrue(len(langs) >= 10)
        # First language MUST be English
        self.assertEqual(langs[0].code, 'en')
        self.assertEqual(langs[0].display_name, 'English')
        codes = [opt.code for opt in langs]
        self.assertIn('ja', codes)
        self.assertIn('es', codes)
        self.assertIn('de', codes)

    def test_build_release_notes_ui_strings__english(self):
        """It formats English release notes UI strings with milestone tokens."""
        bundle = l10n_helpers.get_release_notes_bundle('en')
        ui = bundle.translations.build_ui_strings(
            milestone=151,
            prev_milestone=150,
            next_milestone=152,
        )
        self.assertEqual(ui.page_title, 'Chrome 151 Release Notes')
        self.assertEqual(
            ui.prev_milestone_aria, 'Previous milestone: Chrome 150'
        )
        self.assertEqual(ui.next_milestone_aria, 'Next milestone: Chrome 152')
        self.assertEqual(ui.origin_trials_heading, 'New origin trials')
        self.assertEqual(ui.copy_link_aria('CSS Grid'), 'Copy link to CSS Grid')

    def test_build_release_notes_ui_strings__japanese(self):
        """It formats Japanese release notes UI strings with milestone tokens."""
        bundle = l10n_helpers.get_release_notes_bundle('ja')
        ui = bundle.translations.build_ui_strings(
            milestone=151,
            prev_milestone=150,
            next_milestone=152,
        )
        self.assertEqual(ui.page_title, 'Chrome 151 リリースノート')
        self.assertEqual(
            ui.prev_milestone_aria, '前のマイルストーン: Chrome 150'
        )
        self.assertEqual(
            ui.next_milestone_aria, '次のマイルストーン: Chrome 152'
        )
        self.assertEqual(ui.origin_trials_heading, '新しいオリジントライアル')
        self.assertEqual(
            ui.copy_link_aria('CSS Grid'), 'CSS Grid へのリンクをコピー'
        )

    def test_build_release_notes_ui_strings__fallback_on_unsupported_lang(self):
        """It falls back to English when an unsupported language is requested."""
        bundle = l10n_helpers.get_release_notes_bundle('unsupported-lang')
        ui = bundle.translations.build_ui_strings(
            milestone=151,
            prev_milestone=150,
            next_milestone=152,
        )
        # Should cleanly return English strings
        self.assertEqual(ui.page_title, 'Chrome 151 Release Notes')
        self.assertEqual(ui.origin_trials_heading, 'New origin trials')

    def test_validator_detects_missing_keys(self):
        """It raises LocaleValidationError when required keys are missing in a translation."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create valid en.json
            with open(
                os.path.join(temp_dir, 'en.json'), 'w', encoding='utf-8'
            ) as f:
                with open(
                    'locales/release_notes/en.json', 'r', encoding='utf-8'
                ) as src:
                    f.write(src.read())

            # Create invalid de.json with missing key
            de_data = {
                'meta': {
                    'language_code': 'de',
                    'display_name': 'Deutsch',
                    'english_name': 'German',
                },
                'translations': {
                    'ui': {'page_title': 'Chrome {milestone}'},
                    'categories': {},
                    'links': {},
                },
            }
            with open(
                os.path.join(temp_dir, 'de.json'), 'w', encoding='utf-8'
            ) as f:
                json.dump(de_data, f)

            with self.assertRaises(l10n_models.LocaleValidationError) as ctx:
                l10n_helpers.load_and_validate_bundles(temp_dir)
            self.assertIn('missing required keys', str(ctx.exception))
        finally:
            shutil.rmtree(temp_dir)

    def test_validator_detects_placeholder_mismatch(self):
        """It raises LocaleValidationError when placeholder tokens do not match schema contract."""
        temp_dir = tempfile.mkdtemp()
        try:
            with open(
                os.path.join(temp_dir, 'en.json'), 'w', encoding='utf-8'
            ) as f:
                with open(
                    'locales/release_notes/en.json', 'r', encoding='utf-8'
                ) as src:
                    en_content = src.read()
                    f.write(en_content)

            # Copy en.json to es.json but corrupt a placeholder name
            es_data = json.loads(en_content)
            # Mistype {milestone} as {m}
            es_data['translations']['ui']['page_title'] = 'Chrome {m} Notas'
            with open(
                os.path.join(temp_dir, 'es.json'), 'w', encoding='utf-8'
            ) as f:
                json.dump(es_data, f)

            with self.assertRaises(l10n_models.LocaleValidationError) as ctx:
                l10n_helpers.load_and_validate_bundles(temp_dir)
            self.assertIn('placeholder mismatch', str(ctx.exception))
        finally:
            shutil.rmtree(temp_dir)

    def test_get_category_translations_and_fallbacks(self):
        """It translates category names into the target language and encapsulates defaults."""
        ja_bundle = l10n_helpers.get_release_notes_bundle('ja')
        # Japanese translations
        self.assertEqual(
            ja_bundle.translations.get_category('Miscellaneous'),
            'その他',
        )
        # Automatic fallback for None and empty string
        self.assertEqual(
            ja_bundle.translations.get_category(None),
            'その他',
        )
        self.assertEqual(
            ja_bundle.translations.get_category(''),
            'その他',
        )
        self.assertEqual(
            ja_bundle.translations.get_category('Security'),
            'セキュリティ',
        )
        self.assertEqual(
            ja_bundle.translations.get_category('CSS'),
            'CSS',
        )

        # Spanish translations
        es_bundle = l10n_helpers.get_release_notes_bundle('es')
        self.assertEqual(
            es_bundle.translations.get_category('Miscellaneous'),
            'Varios',
        )
        self.assertEqual(
            es_bundle.translations.get_category(None),
            'Varios',
        )
        self.assertEqual(
            es_bundle.translations.get_category('Performance'),
            'Rendimiento',
        )

        # German translations
        de_bundle = l10n_helpers.get_release_notes_bundle('de')
        self.assertEqual(
            de_bundle.translations.get_category('Miscellaneous'),
            'Sonstiges',
        )

        # English (identity)
        en_bundle = l10n_helpers.get_release_notes_bundle('en')
        self.assertEqual(
            en_bundle.translations.get_category('Miscellaneous'),
            'Miscellaneous',
        )
        self.assertEqual(
            en_bundle.translations.get_category(None),
            'Miscellaneous',
        )

        # Unknown / non-standard category fallback
        self.assertEqual(
            ja_bundle.translations.get_category('Custom Cat'),
            'Custom Cat',
        )

    def test_localize_release_note_links(self):
        """It translates link titles and extracts tracking bug numbers."""
        test_links = [
            {
                'type': 'BUG',
                'url': 'https://issues.chromium.org/issues/12345',
                'title': 'Tracking bug #12345',
            },
            {
                'type': 'SPEC',
                'url': 'https://w3c.github.io/spec',
                'title': 'Spec',
            },
            {
                'type': 'DOC',
                'url': 'https://developer.mozilla.org/docs',
                'title': 'Docs',
            },
            {
                'type': 'ORIGIN_TRIAL',
                'url': '/origintrials#/view_trial/1',
                'title': 'Origin trial',
            },
        ]

        # Japanese localization
        ja_bundle = l10n_helpers.get_release_notes_bundle('ja')
        ja_links = ja_bundle.translations.localize_links(test_links)
        self.assertEqual(ja_links[0]['title'], 'トラッキング バグ #12345')
        self.assertEqual(ja_links[1]['title'], '仕様')
        self.assertEqual(ja_links[2]['title'], 'ドキュメント')
        self.assertEqual(ja_links[3]['title'], 'オリジントライアル')

        # Spanish localization
        es_bundle = l10n_helpers.get_release_notes_bundle('es')
        es_links = es_bundle.translations.localize_links(test_links)
        self.assertEqual(es_links[0]['title'], 'Error de seguimiento n.º 12345')
        self.assertEqual(es_links[1]['title'], 'Especificación')
        self.assertEqual(es_links[2]['title'], 'Documentación')
        self.assertEqual(es_links[3]['title'], 'Prueba de origen')

        # English (identity)
        en_bundle = l10n_helpers.get_release_notes_bundle('en')
        en_links = en_bundle.translations.localize_links(test_links)
        self.assertEqual(en_links[0]['title'], 'Tracking bug #12345')
        self.assertEqual(en_links[1]['title'], 'Spec')
