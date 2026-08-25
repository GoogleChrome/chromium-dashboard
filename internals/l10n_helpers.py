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

"""Core loader, schema validator, and bundle registry for localization (L10n)."""

import json
import logging
import os
from typing import Any

from internals.l10n_models import (
    DEFAULT_LANGUAGE,
    ORDERED_LANGUAGES,
    LanguageOption,
    LocaleMeta,
    LocaleValidationError,
    ReleaseNotesTranslations,
    SupportedLanguage,
    TranslationBundle,
)

# Base directory where localization JSON catalogs reside.
DEFAULT_LOCALES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'locales',
    'release_notes',
)


def load_and_validate_bundles(
    locales_dir: str | None = None,
) -> dict[str, TranslationBundle[ReleaseNotesTranslations]]:
    """Loads all localization files from disk and validates strict schema contracts.

    Runs on module import (server startup) so errors are caught before traffic is served.
    """
    target_dir = locales_dir or DEFAULT_LOCALES_DIR
    if not os.path.isdir(target_dir):
        logging.warning('Locales directory not found at %s', target_dir)
        return {}

    raw_catalogs: dict[str, dict[str, Any]] = {}
    for filename in os.listdir(target_dir):
        if not filename.endswith('.json'):
            continue
        file_path = os.path.join(target_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_catalogs[filename[:-5].lower()] = json.load(f)
        except Exception as e:
            raise LocaleValidationError(
                f'Failed to parse locale JSON file {file_path}: {e}'
            ) from e

    if DEFAULT_LANGUAGE.value not in raw_catalogs:
        raise LocaleValidationError(
            f'Canonical English locale ({DEFAULT_LANGUAGE.value}.json) not found'
        )

    en_raw = raw_catalogs[DEFAULT_LANGUAGE.value]
    if 'translations' not in en_raw or 'meta' not in en_raw:
        raise LocaleValidationError(
            "Canonical English locale must contain 'meta' and 'translations'"
        )

    # Validate English and all target locales against schema
    for lang_code, raw_doc in raw_catalogs.items():
        if 'meta' not in raw_doc or 'translations' not in raw_doc:
            raise LocaleValidationError(
                f"Locale '{lang_code}' must contain 'meta' and 'translations' high-level keys"
            )
        ReleaseNotesTranslations.validate_locale_data(
            lang_code, raw_doc['translations'], en_raw['translations']
        )

    # Instantiate typed bundles
    loaded_bundles: dict[str, TranslationBundle[ReleaseNotesTranslations]] = {}
    for lang_code, raw_doc in raw_catalogs.items():
        meta_dict = raw_doc['meta']
        trans_dict = raw_doc['translations']
        loaded_bundles[lang_code] = TranslationBundle(
            meta=LocaleMeta(
                language_code=meta_dict.get('language_code', lang_code),
                display_name=meta_dict.get('display_name', ''),
                english_name=meta_dict.get('english_name', ''),
            ),
            translations=ReleaseNotesTranslations(
                ui=trans_dict.get('ui', {}),
                categories=trans_dict.get('categories', {}),
                links=trans_dict.get('links', {}),
            ),
        )

    return loaded_bundles


# Load and validate all bundles once on module import
_BUNDLES_REGISTRY: dict[str, TranslationBundle[ReleaseNotesTranslations]] = (
    load_and_validate_bundles()
)


def resolve_supported_language(
    lang: str | SupportedLanguage | None,
) -> SupportedLanguage:
    """Resolves a requested language code to a supported enum, falling back to English."""
    if isinstance(lang, SupportedLanguage):
        return lang
    if not lang or not isinstance(lang, str):
        return DEFAULT_LANGUAGE
    try:
        return SupportedLanguage(lang.strip().lower())
    except ValueError:
        return DEFAULT_LANGUAGE


def get_release_notes_bundle(
    lang: SupportedLanguage | str | None = None,
) -> TranslationBundle[ReleaseNotesTranslations]:
    """Returns the typed translation bundle for the requested language, falling back to English."""
    resolved_lang = resolve_supported_language(lang)
    bundle = _BUNDLES_REGISTRY.get(resolved_lang.value)
    if bundle:
        return bundle
    return _BUNDLES_REGISTRY[DEFAULT_LANGUAGE.value]


def get_supported_languages_for_page() -> list[LanguageOption]:
    """Returns an ordered list of supported LanguageOption items."""
    return [
        LanguageOption(
            code=lang_enum.value,
            display_name=native_name,
            english_name=en_name,
        )
        for lang_enum, native_name, en_name in ORDERED_LANGUAGES
        if lang_enum.value in _BUNDLES_REGISTRY
    ]
