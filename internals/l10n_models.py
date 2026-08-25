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

"""Data models and constants for ChromeStatus localization (L10n)."""

import dataclasses
import re
from enum import StrEnum
from typing import Any

from internals import core_enums


class LocaleValidationError(Exception):
    """Raised when a localization catalog fails schema or placeholder validation."""


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


@dataclasses.dataclass(frozen=True)
class LanguageOption:
    """Represents a language option for UI selectors."""

    code: str
    display_name: str
    english_name: str


# Canonical deterministic list of all languages supported across the application.
ALL_LANGUAGE_OPTIONS: list[LanguageOption] = [
    LanguageOption(
        code=SupportedLanguage.EN.value,
        display_name='English',
        english_name='English',
    ),
    LanguageOption(
        code=SupportedLanguage.DE.value,
        display_name='Deutsch',
        english_name='German',
    ),
    LanguageOption(
        code=SupportedLanguage.ES.value,
        display_name='Español',
        english_name='Spanish',
    ),
    LanguageOption(
        code=SupportedLanguage.FR.value,
        display_name='Français',
        english_name='French',
    ),
    LanguageOption(
        code=SupportedLanguage.ID.value,
        display_name='Bahasa Indonesia',
        english_name='Indonesian',
    ),
    LanguageOption(
        code=SupportedLanguage.JA.value,
        display_name='日本語',
        english_name='Japanese',
    ),
    LanguageOption(
        code=SupportedLanguage.KO.value,
        display_name='한국어',
        english_name='Korean',
    ),
    LanguageOption(
        code=SupportedLanguage.NL.value,
        display_name='Nederlands',
        english_name='Dutch',
    ),
    LanguageOption(
        code=SupportedLanguage.PT_BR.value,
        display_name='Português (Brasil)',
        english_name='Portuguese (Brazil)',
    ),
    LanguageOption(
        code=SupportedLanguage.ZH_CN.value,
        display_name='中文 (简体)',
        english_name='Chinese (Simplified)',
    ),
]


class ReleaseNotesKey(StrEnum):
    """Exhaustive list of all translation keys for the Release Notes page."""

    # UI Strings
    PAGE_TITLE = 'page_title'
    JUMP_PLACEHOLDER = 'jump_placeholder'
    JUMP_ARIA = 'jump_aria'
    PREV_MILESTONE_ARIA = 'prev_milestone_aria'
    NEXT_MILESTONE_ARIA = 'next_milestone_aria'
    ARCHIVAL_BANNER = 'archival_banner'
    BROWSE_ARCHIVE_BTN = 'browse_archive_btn'
    ORIGIN_TRIALS_HEADING = 'origin_trials_heading'
    DEPRECATIONS_HEADING = 'deprecations_heading'
    LINK_COPIED_TOOLTIP = 'link_copied_tooltip'
    COPY_LINK_ARIA = 'copy_link_aria'
    EMPTY_STATE_HEADING = 'empty_state_heading'
    EMPTY_STATE_DESC = 'empty_state_desc'
    VIEW_ROADMAP_BTN = 'view_roadmap_btn'
    SEARCH_FEATURES_BTN = 'search_features_btn'
    EXTERNAL_WINDOW_SR = 'external_window_sr'
    LANGUAGE_SELECTOR_ARIA = 'language_selector_aria'

    # Categories
    CATEGORY_CSS = 'category_css'
    CATEGORY_DOM = 'category_dom'
    CATEGORY_JAVASCRIPT = 'category_javascript'
    CATEGORY_WEB_COMPONENTS = 'category_web_components'
    CATEGORY_SECURITY = 'category_security'
    CATEGORY_MULTIMEDIA = 'category_multimedia'
    CATEGORY_FILE_APIS = 'category_file_apis'
    CATEGORY_OFFLINE_STORAGE = 'category_offline_storage'
    CATEGORY_DEVICE = 'category_device'
    CATEGORY_REALTIME_COMMUNICATION = 'category_realtime_communication'
    CATEGORY_NETWORK_CONNECTIVITY = 'category_network_connectivity'
    CATEGORY_USER_INPUT = 'category_user_input'
    CATEGORY_PERFORMANCE = 'category_performance'
    CATEGORY_GRAPHICS = 'category_graphics'
    CATEGORY_HOUDINI = 'category_houdini'
    CATEGORY_SERVICE_WORKER = 'category_service_worker'
    CATEGORY_WEBRTC = 'category_webrtc'
    CATEGORY_LAYERED_APIS = 'category_layered_apis'
    CATEGORY_WEBASSEMBLY = 'category_webassembly'
    CATEGORY_CAPABILITIES_FUGU = 'category_capabilities_fugu'
    CATEGORY_ISOLATED_WEB_APPS = 'category_isolated_web_apps'
    CATEGORY_MISCELLANEOUS = 'category_miscellaneous'

    # Links
    LINK_TRACKING_BUG = 'link_tracking_bug'
    LINK_CHROMESTATUS = 'link_chromestatus'
    LINK_SPEC = 'link_spec'
    LINK_ORIGIN_TRIAL = 'link_origin_trial'
    LINK_DOC = 'link_doc'
    LINK_EXPLAINER = 'link_explainer'
    LINK_DEMO = 'link_demo'
    LINK_OTHER = 'link_other'


RELEASE_NOTES_PLACEHOLDERS: dict[ReleaseNotesKey, set[str]] = {
    ReleaseNotesKey.PAGE_TITLE: {'milestone'},
    ReleaseNotesKey.PREV_MILESTONE_ARIA: {'milestone'},
    ReleaseNotesKey.NEXT_MILESTONE_ARIA: {'milestone'},
    ReleaseNotesKey.EMPTY_STATE_HEADING: {'milestone'},
    ReleaseNotesKey.EMPTY_STATE_DESC: {'milestone'},
    ReleaseNotesKey.COPY_LINK_ARIA: {'feature_name'},
    ReleaseNotesKey.LINK_TRACKING_BUG: {'bug_id'},
}

CATEGORY_NAME_TO_KEY: dict[str, ReleaseNotesKey] = {
    'CSS': ReleaseNotesKey.CATEGORY_CSS,
    'Web Components': ReleaseNotesKey.CATEGORY_WEB_COMPONENTS,
    'Miscellaneous': ReleaseNotesKey.CATEGORY_MISCELLANEOUS,
    'Security': ReleaseNotesKey.CATEGORY_SECURITY,
    'Multimedia': ReleaseNotesKey.CATEGORY_MULTIMEDIA,
    'DOM': ReleaseNotesKey.CATEGORY_DOM,
    'File APIs': ReleaseNotesKey.CATEGORY_FILE_APIS,
    'Offline / Storage': ReleaseNotesKey.CATEGORY_OFFLINE_STORAGE,
    'Device': ReleaseNotesKey.CATEGORY_DEVICE,
    'Realtime / Communication': ReleaseNotesKey.CATEGORY_REALTIME_COMMUNICATION,
    'JavaScript': ReleaseNotesKey.CATEGORY_JAVASCRIPT,
    'Network / Connectivity': ReleaseNotesKey.CATEGORY_NETWORK_CONNECTIVITY,
    'User input': ReleaseNotesKey.CATEGORY_USER_INPUT,
    'Performance': ReleaseNotesKey.CATEGORY_PERFORMANCE,
    'Graphics': ReleaseNotesKey.CATEGORY_GRAPHICS,
    'Houdini': ReleaseNotesKey.CATEGORY_HOUDINI,
    'Service Worker': ReleaseNotesKey.CATEGORY_SERVICE_WORKER,
    'WebRTC': ReleaseNotesKey.CATEGORY_WEBRTC,
    'Layered APIs': ReleaseNotesKey.CATEGORY_LAYERED_APIS,
    'WebAssembly': ReleaseNotesKey.CATEGORY_WEBASSEMBLY,
    'Capabilities (Fugu)': ReleaseNotesKey.CATEGORY_CAPABILITIES_FUGU,
    'Isolated Web Apps': ReleaseNotesKey.CATEGORY_ISOLATED_WEB_APPS,
    'Isolated Web Apps-specific API': ReleaseNotesKey.CATEGORY_ISOLATED_WEB_APPS,
}

LINK_TYPE_TO_KEY: dict[str, ReleaseNotesKey] = {
    'BUG': ReleaseNotesKey.LINK_TRACKING_BUG,
    'CHROMESTATUS': ReleaseNotesKey.LINK_CHROMESTATUS,
    'SPEC': ReleaseNotesKey.LINK_SPEC,
    'ORIGIN_TRIAL': ReleaseNotesKey.LINK_ORIGIN_TRIAL,
    'DOC': ReleaseNotesKey.LINK_DOC,
    'EXPLAINER': ReleaseNotesKey.LINK_EXPLAINER,
    'DEMO': ReleaseNotesKey.LINK_DEMO,
    'OTHER': ReleaseNotesKey.LINK_OTHER,
}


@dataclasses.dataclass(frozen=True)
class ReleaseNotesUiStrings:
    """Pre-formatted, strongly-typed UI strings for release-notes.html."""

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
        """Formats the aria-label for copy link buttons with the feature name."""
        return self._copy_link_template.format(feature_name=feature_name)


@dataclasses.dataclass(frozen=True)
class ReleaseNotesTranslations:
    """Encapsulates flat string catalog access, category resolution, and link translation."""

    strings: dict[str, str]

    def get_category(self, category_name: str | None) -> str:
        """Returns the localized category display name, defaulting to Miscellaneous."""
        target = category_name or core_enums.FEATURE_CATEGORIES[core_enums.MISC]
        key = CATEGORY_NAME_TO_KEY.get(target)
        if key and key.value in self.strings:
            return self.strings[key.value]
        return target

    def localize_links(
        self, links: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Translates the titles of release note links in-place."""
        if not links:
            return []
        localized: list[dict[str, Any]] = []
        for link in links:
            link_copy = dict(link)
            raw_type = link_copy.get('type')
            link_type_str = str(
                getattr(raw_type, 'value', raw_type) or ''
            ).upper()
            title = str(link_copy.get('title') or '')

            if link_type_str == 'BUG':
                match = re.search(r'\d+', title) or re.search(
                    r'\d+', str(link_copy.get('url', ''))
                )
                if match:
                    template = self.strings.get(
                        ReleaseNotesKey.LINK_TRACKING_BUG.value,
                        'Tracking bug #{bug_id}',
                    )
                    link_copy['title'] = template.format(bug_id=match.group(0))
            else:
                key = LINK_TYPE_TO_KEY.get(link_type_str)
                if key and key.value in self.strings:
                    link_copy['title'] = self.strings[key.value]

            localized.append(link_copy)
        return localized

    def build_ui_strings(
        self,
        milestone: int,
        prev_milestone: int | None = None,
        next_milestone: int | None = None,
    ) -> ReleaseNotesUiStrings:
        """Constructs pre-formatted, type-safe UI strings for the release notes template."""
        prev_m = prev_milestone if prev_milestone is not None else milestone
        next_m = next_milestone if next_milestone is not None else milestone

        return ReleaseNotesUiStrings(
            page_title=self.strings[ReleaseNotesKey.PAGE_TITLE.value].format(
                milestone=milestone
            ),
            jump_placeholder=self.strings[
                ReleaseNotesKey.JUMP_PLACEHOLDER.value
            ],
            jump_aria=self.strings[ReleaseNotesKey.JUMP_ARIA.value],
            prev_milestone_aria=self.strings[
                ReleaseNotesKey.PREV_MILESTONE_ARIA.value
            ].format(milestone=prev_m),
            next_milestone_aria=self.strings[
                ReleaseNotesKey.NEXT_MILESTONE_ARIA.value
            ].format(milestone=next_m),
            archival_banner=self.strings[ReleaseNotesKey.ARCHIVAL_BANNER.value],
            browse_archive_btn=self.strings[
                ReleaseNotesKey.BROWSE_ARCHIVE_BTN.value
            ],
            origin_trials_heading=self.strings[
                ReleaseNotesKey.ORIGIN_TRIALS_HEADING.value
            ],
            deprecations_heading=self.strings[
                ReleaseNotesKey.DEPRECATIONS_HEADING.value
            ],
            link_copied_tooltip=self.strings[
                ReleaseNotesKey.LINK_COPIED_TOOLTIP.value
            ],
            empty_state_heading=self.strings[
                ReleaseNotesKey.EMPTY_STATE_HEADING.value
            ].format(milestone=milestone),
            empty_state_desc=self.strings[
                ReleaseNotesKey.EMPTY_STATE_DESC.value
            ].format(milestone=milestone),
            view_roadmap_btn=self.strings[
                ReleaseNotesKey.VIEW_ROADMAP_BTN.value
            ],
            search_features_btn=self.strings[
                ReleaseNotesKey.SEARCH_FEATURES_BTN.value
            ],
            external_window_sr=self.strings[
                ReleaseNotesKey.EXTERNAL_WINDOW_SR.value
            ],
            language_selector_aria=self.strings[
                ReleaseNotesKey.LANGUAGE_SELECTOR_ARIA.value
            ],
            _copy_link_template=self.strings[
                ReleaseNotesKey.COPY_LINK_ARIA.value
            ],
        )
