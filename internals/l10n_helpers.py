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

"""Core loader, schema validator, and UI string builder for localization (L10n)."""

import json
import logging
import os
from typing import Any

from internals.l10n_models import (
    DEFAULT_LANGUAGE,
    ORDERED_LANGUAGES,
    REGISTERED_PAGE_SCHEMAS,
    LanguageOption,
    LocaleValidationError,
    ReleaseNotesUiStrings,
    SupportedLanguage,
)

# Base directory where localization JSON catalogs reside.
DEFAULT_LOCALES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'locales',
    'release_notes',
)


def load_and_validate_catalogs(
    locales_dir: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Loads all localization catalogs from disk and validates strict schema contracts across registered pages.

    Runs on module import (server startup) so errors are caught before traffic is served.
    """
    target_dir = locales_dir or DEFAULT_LOCALES_DIR
    if not os.path.isdir(target_dir):
        logging.warning('Locales directory not found at %s', target_dir)
        return {}

    loaded_catalogs: dict[str, dict[str, Any]] = {}

    for filename in os.listdir(target_dir):
        if not filename.endswith('.json'):
            continue
        file_path = os.path.join(target_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            lang_code = filename[:-5].lower()
            loaded_catalogs[lang_code] = data
        except Exception as e:
            raise LocaleValidationError(
                f'Failed to parse locale JSON file {file_path}: {e}'
            ) from e

    # Completely generic validation across all registered page schemas
    for namespace, schema_cls in REGISTERED_PAGE_SCHEMAS.items():
        schema_cls.validate_all_locales(loaded_catalogs)

    return loaded_catalogs


# Load and validate all catalogs once on module import
_CATALOGS_REGISTRY: dict[str, dict[str, Any]] = load_and_validate_catalogs()


def resolve_supported_language(lang: str | None) -> SupportedLanguage:
    """Resolves a requested language code to a supported enum, falling back to English."""
    if not lang:
        return DEFAULT_LANGUAGE

    normalized = lang.strip().lower()
    try:
        return SupportedLanguage(normalized)
    except ValueError:
        # Fallback to English for any unsupported or malformed language tag
        return DEFAULT_LANGUAGE


def get_supported_languages_for_page(
    namespace: str = 'release_notes',
) -> list[LanguageOption]:
    """Returns an ordered list of supported LanguageOption items for a page namespace."""
    options: list[LanguageOption] = []
    for lang_enum, native_name, en_name in ORDERED_LANGUAGES:
        code = lang_enum.value
        # Only include if the catalog exists in registry and contains the requested namespace
        if code in _CATALOGS_REGISTRY and namespace in _CATALOGS_REGISTRY[code]:
            options.append(
                LanguageOption(
                    code=code,
                    display_name=native_name,
                    english_name=en_name,
                )
            )
    return options


def build_release_notes_ui_strings(
    lang: SupportedLanguage | str | None,
    milestone: int,
    prev_milestone: int | None = None,
    next_milestone: int | None = None,
) -> ReleaseNotesUiStrings:
    """Constructs pre-formatted, type-safe UI strings for the Release Notes page."""
    resolved_lang = (
        lang
        if isinstance(lang, SupportedLanguage)
        else resolve_supported_language(lang)
    )

    catalog = _CATALOGS_REGISTRY.get(resolved_lang.value)
    if not catalog or ReleaseNotesUiStrings.PAGE_NAMESPACE not in catalog:
        # Fallback to English catalog
        catalog = _CATALOGS_REGISTRY.get(
            DEFAULT_LANGUAGE.value, {ReleaseNotesUiStrings.PAGE_NAMESPACE: {}}
        )

    strings = catalog[ReleaseNotesUiStrings.PAGE_NAMESPACE]
    en_strings = _CATALOGS_REGISTRY.get(
        DEFAULT_LANGUAGE.value, {ReleaseNotesUiStrings.PAGE_NAMESPACE: {}}
    )[ReleaseNotesUiStrings.PAGE_NAMESPACE]

    def get_str(key: str) -> str:
        return strings.get(key, en_strings.get(key, ''))

    prev_m_val = prev_milestone if prev_milestone is not None else milestone
    next_m_val = next_milestone if next_milestone is not None else milestone

    return ReleaseNotesUiStrings(
        page_title=get_str('page_title').format(milestone=milestone),
        jump_placeholder=get_str('jump_placeholder'),
        jump_aria=get_str('jump_aria'),
        prev_milestone_aria=get_str('prev_milestone_aria').format(
            milestone=prev_m_val
        ),
        next_milestone_aria=get_str('next_milestone_aria').format(
            milestone=next_m_val
        ),
        archival_banner=get_str('archival_banner'),
        browse_archive_btn=get_str('browse_archive_btn'),
        origin_trials_heading=get_str('origin_trials_heading'),
        deprecations_heading=get_str('deprecations_heading'),
        link_copied_tooltip=get_str('link_copied_tooltip'),
        empty_state_heading=get_str('empty_state_heading').format(
            milestone=milestone
        ),
        empty_state_desc=get_str('empty_state_desc').format(
            milestone=milestone
        ),
        view_roadmap_btn=get_str('view_roadmap_btn'),
        search_features_btn=get_str('search_features_btn'),
        external_window_sr=get_str('external_window_sr'),
        language_selector_aria=get_str('language_selector_aria'),
        _copy_link_template=get_str('copy_link_aria'),
    )
