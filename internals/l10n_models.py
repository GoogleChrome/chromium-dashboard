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

"""Data models, constants, and schema contracts for ChromeStatus localization (L10n)."""

import dataclasses
import re
from enum import StrEnum
from typing import Any, ClassVar


class LocaleValidationError(Exception):
    """Raised when a localization JSON catalog fails schema or placeholder validation."""


def extract_placeholders(text: str) -> set[str]:
    """Extracts named format tokens like '{milestone}' from a string."""
    return set(re.findall(r'\{([a-zA-Z0-9_]+)\}', text))


class SupportedLanguage(StrEnum):
    """Supported BCP-47 language codes for ChromeStatus localization."""

    EN = 'en'
    DE = 'de'
    ES = 'es'
    FR = 'fr'
    ID = 'id'
    JA = 'ja'
    KO = 'ko'
    NL = 'nl'
    PT_BR = 'pt-br'
    ZH_CN = 'zh-cn'


DEFAULT_LANGUAGE = SupportedLanguage.EN

# Canonical deterministic ordering for language selectors in the UI.
# Format: (language_code, native_display_name, english_name)
ORDERED_LANGUAGES: list[tuple[SupportedLanguage, str, str]] = [
    (SupportedLanguage.EN, 'English', 'English'),
    (SupportedLanguage.DE, 'Deutsch', 'German'),
    (SupportedLanguage.ES, 'Español', 'Spanish'),
    (SupportedLanguage.FR, 'Français', 'French'),
    (SupportedLanguage.ID, 'Bahasa Indonesia', 'Indonesian'),
    (SupportedLanguage.JA, '日本語', 'Japanese'),
    (SupportedLanguage.KO, '한국어', 'Korean'),
    (SupportedLanguage.NL, 'Nederlands', 'Dutch'),
    (SupportedLanguage.PT_BR, 'Português (Brasil)', 'Portuguese (Brazil)'),
    (SupportedLanguage.ZH_CN, '中文 (简体)', 'Chinese (Simplified)'),
]


@dataclasses.dataclass(frozen=True)
class LanguageOption:
    """Represents a language option for UI selectors."""

    code: str
    display_name: str
    english_name: str


class BasePageUiStrings:
    """Base contract for localized page UI models with co-located schema validation."""

    PAGE_NAMESPACE: ClassVar[str]
    REQUIRED_PLACEHOLDERS: ClassVar[dict[str, set[str]]]

    @classmethod
    def validate_page_catalog(
        cls,
        lang_code: str,
        page_dict: dict[str, str],
        en_page_dict: dict[str, str],
    ) -> None:
        """Validates key parity and placeholder contracts for this page in a specific locale."""
        en_keys = set(en_page_dict.keys())
        target_keys = set(page_dict.keys())

        missing_keys = en_keys - target_keys
        if missing_keys:
            raise LocaleValidationError(
                f"Locale '{lang_code}' namespace '{cls.PAGE_NAMESPACE}' is missing required keys: {missing_keys}"
            )

        extra_keys = target_keys - en_keys
        if extra_keys:
            raise LocaleValidationError(
                f"Locale '{lang_code}' namespace '{cls.PAGE_NAMESPACE}' contains unrecognized keys: {extra_keys}"
            )

        for field_name, expected_tokens in cls.REQUIRED_PLACEHOLDERS.items():
            if field_name not in page_dict:
                raise LocaleValidationError(
                    f"Locale '{lang_code}' namespace '{cls.PAGE_NAMESPACE}' is missing schema field '{field_name}'"
                )
            field_text = page_dict[field_name]
            actual_tokens = extract_placeholders(field_text)
            if actual_tokens != expected_tokens:
                raise LocaleValidationError(
                    f"Locale '{lang_code}' namespace '{cls.PAGE_NAMESPACE}' field '{field_name}' placeholder mismatch: "
                    f'expected {expected_tokens}, got {actual_tokens}'
                )

    @classmethod
    def validate_all_locales(
        cls, loaded_catalogs: dict[str, dict[str, Any]]
    ) -> None:
        """Validates all loaded locale catalogs against this page schema contract."""
        if DEFAULT_LANGUAGE.value not in loaded_catalogs:
            raise LocaleValidationError(
                f'Canonical English locale ({DEFAULT_LANGUAGE.value}.json) not found'
            )

        en_catalog = loaded_catalogs[DEFAULT_LANGUAGE.value]
        en_page_dict = en_catalog.get(cls.PAGE_NAMESPACE, {})

        # 1. Validate canonical English baseline against schema contract
        for field_name, expected_tokens in cls.REQUIRED_PLACEHOLDERS.items():
            if field_name not in en_page_dict:
                raise LocaleValidationError(
                    f"Canonical English locale is missing required field '{field_name}' in namespace '{cls.PAGE_NAMESPACE}'"
                )
            actual_tokens = extract_placeholders(en_page_dict[field_name])
            if actual_tokens != expected_tokens:
                raise LocaleValidationError(
                    f"Canonical English namespace '{cls.PAGE_NAMESPACE}' field '{field_name}' placeholder mismatch: "
                    f'expected {expected_tokens}, got {actual_tokens}'
                )

        # 2. Validate all other locales providing this namespace
        for lang_code, catalog in loaded_catalogs.items():
            if lang_code == DEFAULT_LANGUAGE.value:
                continue
            if cls.PAGE_NAMESPACE in catalog:
                cls.validate_page_catalog(
                    lang_code,
                    catalog[cls.PAGE_NAMESPACE],
                    en_page_dict,
                )


@dataclasses.dataclass(frozen=True)
class ReleaseNotesUiStrings(BasePageUiStrings):
    """Type-safe, pre-formatted UI strings for the Release Notes page."""

    PAGE_NAMESPACE: ClassVar[str] = 'release_notes'

    # Schema contract co-located directly on the dataclass definition
    REQUIRED_PLACEHOLDERS: ClassVar[dict[str, set[str]]] = {
        'page_title': {'milestone'},
        'jump_placeholder': set(),
        'jump_aria': set(),
        'prev_milestone_aria': {'milestone'},
        'next_milestone_aria': {'milestone'},
        'archival_banner': set(),
        'browse_archive_btn': set(),
        'origin_trials_heading': set(),
        'deprecations_heading': set(),
        'link_copied_tooltip': set(),
        'copy_link_aria': {'feature_name'},
        'empty_state_heading': {'milestone'},
        'empty_state_desc': {'milestone'},
        'view_roadmap_btn': set(),
        'search_features_btn': set(),
        'external_window_sr': set(),
        'language_selector_aria': set(),
    }

    # Typed fields
    page_title: str
    jump_placeholder: str
    jump_aria: str
    prev_milestone_aria: str
    next_milestone_aria: str
    archival_banner: str
    browse_archive_btn: str
    origin_trials_heading: str
    deprecations_heading: str
    link_copied_tooltip: str
    empty_state_heading: str
    empty_state_desc: str
    view_roadmap_btn: str
    search_features_btn: str
    external_window_sr: str
    language_selector_aria: str
    _copy_link_template: str

    def copy_link_aria(self, feature_name: str) -> str:
        """Formats accessible copy-link tooltip for a specific feature card."""
        return self._copy_link_template.format(feature_name=feature_name)


# Extensible central registry of all localized page schemas
REGISTERED_PAGE_SCHEMAS: dict[str, type[BasePageUiStrings]] = {
    ReleaseNotesUiStrings.PAGE_NAMESPACE: ReleaseNotesUiStrings,
}
