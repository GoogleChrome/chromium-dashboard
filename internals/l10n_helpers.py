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
import re
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
                loaded_catalogs[filename[:-5].lower()] = json.load(f)
        except Exception as e:
            raise LocaleValidationError(
                f'Failed to parse locale JSON file {file_path}: {e}'
            ) from e

    # Generic validation across all registered page schemas
    for schema_cls in REGISTERED_PAGE_SCHEMAS.values():
        schema_cls.validate_all_locales(loaded_catalogs)

    return loaded_catalogs


# Load and validate all catalogs once on module import
_CATALOGS_REGISTRY: dict[str, dict[str, Any]] = load_and_validate_catalogs()


def resolve_supported_language(lang: str | None) -> SupportedLanguage:
    """Resolves a requested language code to a supported enum, falling back to English."""
    if not lang:
        return DEFAULT_LANGUAGE
    try:
        return SupportedLanguage(lang.strip().lower())
    except ValueError:
        return DEFAULT_LANGUAGE


def get_supported_languages_for_page(
    namespace: str = 'release_notes',
) -> list[LanguageOption]:
    """Returns an ordered list of supported LanguageOption items for a page namespace."""
    return [
        LanguageOption(
            code=lang_enum.value,
            display_name=native_name,
            english_name=en_name,
        )
        for lang_enum, native_name, en_name in ORDERED_LANGUAGES
        if lang_enum.value in _CATALOGS_REGISTRY
        and namespace in _CATALOGS_REGISTRY[lang_enum.value]
    ]


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
    catalog = _CATALOGS_REGISTRY.get(resolved_lang.value, {})
    raw = catalog.get(
        ReleaseNotesUiStrings.PAGE_NAMESPACE
    ) or _CATALOGS_REGISTRY.get(
        DEFAULT_LANGUAGE.value, {ReleaseNotesUiStrings.PAGE_NAMESPACE: {}}
    ).get(ReleaseNotesUiStrings.PAGE_NAMESPACE, {})

    context = {
        'milestone': milestone,
        'prev_milestone': (
            prev_milestone if prev_milestone is not None else milestone
        ),
        'next_milestone': (
            next_milestone if next_milestone is not None else milestone
        ),
    }

    # Format fields that require milestone tokens, pass others through directly
    formatted: dict[str, Any] = {}
    for key, val in raw.items():
        placeholders = ReleaseNotesUiStrings.REQUIRED_PLACEHOLDERS.get(
            key, set()
        )
        if 'milestone' in placeholders:
            token_key = 'milestone'
            if key == 'prev_milestone_aria':
                token_key = 'prev_milestone'
            elif key == 'next_milestone_aria':
                token_key = 'next_milestone'
            formatted[key] = val.format(milestone=context[token_key])
        elif key == 'copy_link_aria':
            formatted['_copy_link_template'] = val
        else:
            formatted[key] = val

    return ReleaseNotesUiStrings(**formatted)


def get_localized_category_name(
    category_name: str,
    lang: SupportedLanguage | str | None = None,
) -> str:
    """Returns the localized display name for a feature category."""
    if not category_name:
        return ''
    resolved_lang = (
        lang
        if isinstance(lang, SupportedLanguage)
        else resolve_supported_language(lang)
    )
    return (
        _CATALOGS_REGISTRY.get(resolved_lang.value, {})
        .get('categories', {})
        .get(category_name, category_name)
    )


def localize_release_note_links(
    links: list[dict[str, Any]],
    lang: SupportedLanguage | str | None = None,
) -> list[dict[str, Any]]:
    """Translates the titles of release note links according to the target language."""
    if not links:
        return []
    resolved_lang = (
        lang
        if isinstance(lang, SupportedLanguage)
        else resolve_supported_language(lang)
    )
    if resolved_lang == DEFAULT_LANGUAGE:
        return links

    link_catalog = _CATALOGS_REGISTRY.get(resolved_lang.value, {}).get(
        'links', {}
    )
    if not link_catalog:
        return links

    localized: list[dict[str, Any]] = []
    for link in links:
        link_copy = dict(link)
        raw_type = link_copy.get('type')
        link_type_str = str(getattr(raw_type, 'value', raw_type) or '')

        title = link_copy.get('title') or ''

        if link_type_str.upper() == 'BUG':
            match = re.search(r'\d+', title) or re.search(
                r'\d+', link_copy.get('url', '')
            )
            if match:
                link_copy['title'] = link_catalog.get(
                    'tracking_bug', 'Tracking bug #{bug_id}'
                ).format(bug_id=match.group(0))
        else:
            key = link_type_str.lower()
            if key in link_catalog:
                link_copy['title'] = link_catalog[key]

        localized.append(link_copy)

    return localized
