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
    """Unit test suite for l10n helpers, catalog loading, and validation."""

    def test_all_registered_locales_have_exact_schema_and_placeholder_parity(
        self,
    ):
        """Asserts that all real production JSON files in locales/ pass strict parity checks."""
        catalogs = l10n_helpers.load_and_validate_catalogs()
        self.assertIn('en', catalogs)
        self.assertIn('ja', catalogs)
        self.assertIn('es', catalogs)
        self.assertIn('de', catalogs)
        self.assertIn('fr', catalogs)
        self.assertIn('id', catalogs)
        self.assertIn('ko', catalogs)
        self.assertIn('nl', catalogs)
        self.assertIn('pt-br', catalogs)
        self.assertIn('zh-cn', catalogs)

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
        langs = l10n_helpers.get_supported_languages_for_page('release_notes')
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
        ui = l10n_helpers.build_release_notes_ui_strings(
            lang='en',
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
        ui = l10n_helpers.build_release_notes_ui_strings(
            lang='ja',
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
        ui = l10n_helpers.build_release_notes_ui_strings(
            lang='unsupported-lang',
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
                json.dump(l10n_helpers._CATALOGS_REGISTRY['en'], f)

            # Create invalid de.json with missing key
            de_data = {
                'meta': {},
                'release_notes': {'page_title': 'Chrome {milestone}'},
            }
            with open(
                os.path.join(temp_dir, 'de.json'), 'w', encoding='utf-8'
            ) as f:
                json.dump(de_data, f)

            with self.assertRaises(l10n_models.LocaleValidationError) as ctx:
                l10n_helpers.load_and_validate_catalogs(temp_dir)
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
                json.dump(l10n_helpers._CATALOGS_REGISTRY['en'], f)

            # Copy en.json to es.json but corrupt a placeholder name
            es_data = dict(l10n_helpers._CATALOGS_REGISTRY['en'])
            es_data['release_notes'] = dict(es_data['release_notes'])
            # Mistype {milestone} as {m}
            es_data['release_notes']['page_title'] = 'Chrome {m} Notas'
            with open(
                os.path.join(temp_dir, 'es.json'), 'w', encoding='utf-8'
            ) as f:
                json.dump(es_data, f)

            with self.assertRaises(l10n_models.LocaleValidationError) as ctx:
                l10n_helpers.load_and_validate_catalogs(temp_dir)
            self.assertIn('placeholder mismatch', str(ctx.exception))
        finally:
            shutil.rmtree(temp_dir)
