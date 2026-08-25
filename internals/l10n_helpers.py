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

"""Core loader, language resolver, and helper functions for localization (L10n)."""

import json
import logging
import os
from typing import Any

from internals.l10n_models import (
    ALL_LANGUAGE_OPTIONS,
    DEFAULT_LANGUAGE,
    LanguageOption,
    LocaleValidationError,
    SupportedLanguage,
)

# Base directory where localization domain folders reside.
LOCALES_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'locales',
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


def load_flat_page_strings(
    domain_name: str,
    locales_dir: str | None = None,
) -> dict[SupportedLanguage, dict[str, str]]:
    """Loads all flat string catalogs from disk for a given page domain."""
    target_dir = locales_dir or os.path.join(LOCALES_BASE_DIR, domain_name)
    if not os.path.isdir(target_dir):
        logging.warning('Locales directory not found at %s', target_dir)
        return {}

    loaded_translations: dict[SupportedLanguage, dict[str, str]] = {}
    for filename in os.listdir(target_dir):
        if not filename.endswith('.json'):
            continue
        file_path = os.path.join(target_dir, filename)
        lang_code = filename[:-5].lower()
        try:
            lang_enum = SupportedLanguage(lang_code)
        except ValueError:
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                loaded_translations[lang_enum] = {
                    str(k): str(v) for k, v in data.items()
                }
        except Exception as e:
            raise LocaleValidationError(
                f'Failed to parse locale JSON file {file_path}: {e}'
            ) from e

    return loaded_translations


def get_supported_languages(
    translations_map: dict[SupportedLanguage, Any],
) -> list[LanguageOption]:
    """Returns ordered list of LanguageOptions that actually exist in the translations map."""
    return [
        opt
        for opt in ALL_LANGUAGE_OPTIONS
        if SupportedLanguage(opt.code) in translations_map
    ]


def get_page_translations(
    domain_name: str,
    lang: SupportedLanguage | str | None = None,
    locales_dir: str | None = None,
    **context: Any,
) -> dict[str, Any]:
    """Retrieves and pre-formats translations for any page domain with English fallback."""
    resolved_lang = resolve_supported_language(lang)
    loaded = load_flat_page_strings(domain_name, locales_dir=locales_dir)
    if not loaded:
        return {}

    raw = loaded.get(resolved_lang, loaded.get(DEFAULT_LANGUAGE, {}))
    formatted: dict[str, Any] = {}
    for key, text in raw.items():
        if '{' in text and any(f'{{{k}}}' in text for k in context):
            try:
                formatted[key] = text.format(**context)
            except (KeyError, IndexError):
                formatted[key] = text
        elif '{' in text:
            formatted[key] = lambda name=text, **kw: name.format(**kw)
        else:
            formatted[key] = text
    return formatted


def format_localized_path(
    path: str,
    lang: SupportedLanguage | str | None = None,
) -> str:
    """Formats a canonical URL path, appending ?hl= for non-default languages."""
    resolved = resolve_supported_language(lang)
    if resolved == DEFAULT_LANGUAGE:
        return path
    return f'{path}?hl={resolved.value}'
