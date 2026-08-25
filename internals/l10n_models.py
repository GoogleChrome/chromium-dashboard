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
from typing import Any, ClassVar, Generic, TypeVar

from internals import core_enums


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


@dataclasses.dataclass(frozen=True)
class LocaleMeta:
    """Represents the metadata header in a locale catalog file."""

    language_code: str
    display_name: str
    english_name: str


T = TypeVar('T')


@dataclasses.dataclass(frozen=True)
class TranslationBundle(Generic[T]):
    """Generic envelope containing locale metadata and typed translations for a domain."""

    meta: LocaleMeta
    translations: T


@dataclasses.dataclass(frozen=True)
class ReleaseNotesUiStrings:
    """Type-safe, pre-formatted UI strings for the Release Notes page."""

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


@dataclasses.dataclass(frozen=True)
class ReleaseNotesTranslations:
    """Full domain translation model for Release Notes including UI strings, categories, and links."""

    REQUIRED_LINK_PLACEHOLDERS: ClassVar[dict[str, set[str]]] = {
        'tracking_bug': {'bug_id'},
        'chromestatus': set(),
        'spec': set(),
        'origin_trial': set(),
        'doc': set(),
        'explainer': set(),
        'demo': set(),
        'other': set(),
    }

    ui: dict[str, str]
    categories: dict[str, str]
    links: dict[str, str]

    def get_category(self, category_name: str | None) -> str:
        """Returns the localized category display name, defaulting to MISC if None or empty."""
        target = (
            category_name
            if category_name
            else core_enums.FEATURE_CATEGORIES[core_enums.MISC]
        )
        return self.categories.get(target, target)

    def localize_links(
        self, links: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Translates the titles of release note links according to the target language."""
        if not links:
            return []
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
                    link_copy['title'] = self.links.get(
                        'tracking_bug', 'Tracking bug #{bug_id}'
                    ).format(bug_id=match.group(0))
            else:
                key = link_type_str.lower()
                if key in self.links:
                    link_copy['title'] = self.links[key]

            localized.append(link_copy)
        return localized

    def build_ui_strings(
        self,
        milestone: int,
        prev_milestone: int | None = None,
        next_milestone: int | None = None,
    ) -> ReleaseNotesUiStrings:
        """Constructs pre-formatted, type-safe UI strings for the Release Notes page."""
        context = {
            'milestone': milestone,
            'prev_milestone': (
                prev_milestone if prev_milestone is not None else milestone
            ),
            'next_milestone': (
                next_milestone if next_milestone is not None else milestone
            ),
        }
        formatted: dict[str, Any] = {}
        for key, val in self.ui.items():
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

    @classmethod
    def validate_locale_data(
        cls,
        lang_code: str,
        translations_dict: dict[str, Any],
        en_translations_dict: dict[str, Any],
    ) -> None:
        """Validates key parity and placeholder contracts for this bundle against English baseline."""
        for section in ('ui', 'categories', 'links'):
            if section not in translations_dict:
                raise LocaleValidationError(
                    f"Locale '{lang_code}' is missing required section '{section}' in 'translations'"
                )

        # 1. Validate UI strings
        ui_dict = translations_dict['ui']
        en_ui_dict = en_translations_dict['ui']
        missing_ui = set(en_ui_dict.keys()) - set(ui_dict.keys())
        if missing_ui:
            raise LocaleValidationError(
                f"Locale '{lang_code}' namespace 'ui' is missing required keys: {missing_ui}"
            )
        extra_ui = set(ui_dict.keys()) - set(en_ui_dict.keys())
        if extra_ui:
            raise LocaleValidationError(
                f"Locale '{lang_code}' namespace 'ui' contains unrecognized keys: {extra_ui}"
            )
        for (
            field_name,
            expected_tokens,
        ) in ReleaseNotesUiStrings.REQUIRED_PLACEHOLDERS.items():
            if field_name not in ui_dict:
                raise LocaleValidationError(
                    f"Locale '{lang_code}' is missing schema field '{field_name}' in 'ui'"
                )
            actual_tokens = extract_placeholders(ui_dict[field_name])
            if actual_tokens != expected_tokens:
                raise LocaleValidationError(
                    f"Locale '{lang_code}' namespace 'ui' field '{field_name}' placeholder mismatch: "
                    f'expected {expected_tokens}, got {actual_tokens}'
                )

        # 2. Validate Categories
        cat_dict = translations_dict['categories']
        en_cat_dict = en_translations_dict['categories']
        missing_cats = set(en_cat_dict.keys()) - set(cat_dict.keys())
        if missing_cats:
            raise LocaleValidationError(
                f"Locale '{lang_code}' namespace 'categories' is missing required keys: {missing_cats}"
            )
        extra_cats = set(cat_dict.keys()) - set(en_cat_dict.keys())
        if extra_cats:
            raise LocaleValidationError(
                f"Locale '{lang_code}' namespace 'categories' contains unrecognized keys: {extra_cats}"
            )

        # 3. Validate Links
        link_dict = translations_dict['links']
        en_link_dict = en_translations_dict['links']
        missing_links = set(en_link_dict.keys()) - set(link_dict.keys())
        if missing_links:
            raise LocaleValidationError(
                f"Locale '{lang_code}' namespace 'links' is missing required keys: {missing_links}"
            )
        extra_links = set(link_dict.keys()) - set(en_link_dict.keys())
        if extra_links:
            raise LocaleValidationError(
                f"Locale '{lang_code}' namespace 'links' contains unrecognized keys: {extra_links}"
            )
        for (
            field_name,
            expected_tokens,
        ) in cls.REQUIRED_LINK_PLACEHOLDERS.items():
            actual_tokens = extract_placeholders(link_dict.get(field_name, ''))
            if actual_tokens != expected_tokens:
                raise LocaleValidationError(
                    f"Locale '{lang_code}' namespace 'links' field '{field_name}' placeholder mismatch: "
                    f'expected {expected_tokens}, got {actual_tokens}'
                )
