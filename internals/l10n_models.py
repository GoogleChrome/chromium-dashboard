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
    PREVIEW_BADGE = 'preview_badge'
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


@dataclasses.dataclass(frozen=True)
class ReleaseNoteLinkItem:
    """Represents a release note link."""

    url: str
    type: core_enums.ReleaseNoteLinkType | str
    title: str | None = None


@dataclasses.dataclass(frozen=True)
class ReleaseNotesTranslations:
    """Strongly-typed translations for the Release Notes page."""

    # UI Strings
    page_title: str
    preview_badge: str
    jump_placeholder: str
    jump_aria: str
    prev_milestone_aria: str
    next_milestone_aria: str
    archival_banner: str
    browse_archive_btn: str
    origin_trials_heading: str
    deprecations_heading: str
    link_copied_tooltip: str
    copy_link_aria: str
    empty_state_heading: str
    empty_state_desc: str
    view_roadmap_btn: str
    search_features_btn: str
    external_window_sr: str
    language_selector_aria: str

    # Categories
    category_css: str
    category_dom: str
    category_javascript: str
    category_web_components: str
    category_security: str
    category_multimedia: str
    category_file_apis: str
    category_offline_storage: str
    category_device: str
    category_realtime_communication: str
    category_network_connectivity: str
    category_user_input: str
    category_performance: str
    category_graphics: str
    category_houdini: str
    category_service_worker: str
    category_webrtc: str
    category_layered_apis: str
    category_webassembly: str
    category_capabilities_fugu: str
    category_isolated_web_apps: str
    category_miscellaneous: str

    # Links
    link_tracking_bug: str
    link_chromestatus: str
    link_spec: str
    link_origin_trial: str
    link_doc: str
    link_explainer: str
    link_demo: str
    link_other: str

    def get_category(self, category_id: int | None) -> str:
        """Returns localized category display name using direct attribute access."""
        match category_id:
            case core_enums.CSS:
                return self.category_css
            case core_enums.DOM:
                return self.category_dom
            case core_enums.JAVASCRIPT:
                return self.category_javascript
            case core_enums.WEBCOMPONENTS:
                return self.category_web_components
            case core_enums.SECURITY:
                return self.category_security
            case core_enums.MULTIMEDIA:
                return self.category_multimedia
            case core_enums.FILE:
                return self.category_file_apis
            case core_enums.OFFLINE:
                return self.category_offline_storage
            case core_enums.DEVICE:
                return self.category_device
            case core_enums.COMMUNICATION:
                return self.category_realtime_communication
            case core_enums.NETWORKING:
                return self.category_network_connectivity
            case core_enums.INPUT:
                return self.category_user_input
            case core_enums.PERFORMANCE:
                return self.category_performance
            case core_enums.GRAPHICS:
                return self.category_graphics
            case core_enums.HOUDINI:
                return self.category_houdini
            case core_enums.SERVICEWORKER:
                return self.category_service_worker
            case core_enums.WEBRTC:
                return self.category_webrtc
            case core_enums.LAYERED:
                return self.category_layered_apis
            case core_enums.WEBASSEMBLY:
                return self.category_webassembly
            case core_enums.CAPABILITIES:
                return self.category_capabilities_fugu
            case core_enums.IWA:
                return self.category_isolated_web_apps
            case _:
                return self.category_miscellaneous

    def localize_link_title(self, link: ReleaseNoteLinkItem) -> str:
        """Translates a single release note link's title into the target locale."""
        match link.type:
            case core_enums.ReleaseNoteLinkType.BUG:
                raw_text = f'{link.title or ""} {link.url}'
                match = re.search(r'\d+', raw_text)
                bug_suffix = f' #{match.group(0)}' if match else ''
                return self.link_tracking_bug.format(bug_id=bug_suffix)
            case core_enums.ReleaseNoteLinkType.SPEC:
                return self.link_spec
            case core_enums.ReleaseNoteLinkType.DOC:
                return self.link_doc
            case core_enums.ReleaseNoteLinkType.ORIGIN_TRIAL:
                return self.link_origin_trial
            case core_enums.ReleaseNoteLinkType.EXPLAINER:
                return self.link_explainer
            case core_enums.ReleaseNoteLinkType.DEMO:
                return self.link_demo
            case core_enums.ReleaseNoteLinkType.CHROMESTATUS:
                return self.link_chromestatus
            case core_enums.ReleaseNoteLinkType.OTHER:
                return self.link_other
            case _:
                return link.title or ''

    def localize_links(
        self, links: list[ReleaseNoteLinkItem]
    ) -> list[ReleaseNoteLinkItem]:
        """Translates a list of release note links."""
        return [
            ReleaseNoteLinkItem(
                url=link.url,
                type=link.type,
                title=self.localize_link_title(link),
            )
            for link in links
        ]

    def format_ui(
        self,
        milestone: int,
        prev_milestone: int | None = None,
        next_milestone: int | None = None,
    ) -> dict[str, Any]:
        """Pre-formats milestone tokens in UI strings for Jinja templates."""
        prev_m = prev_milestone if prev_milestone is not None else milestone
        next_m = next_milestone if next_milestone is not None else milestone

        return {
            'page_title': self.page_title.format(milestone=milestone),
            'preview_badge': self.preview_badge,
            'jump_placeholder': self.jump_placeholder,
            'jump_aria': self.jump_aria,
            'prev_milestone_aria': self.prev_milestone_aria.format(
                milestone=prev_m
            ),
            'next_milestone_aria': self.next_milestone_aria.format(
                milestone=next_m
            ),
            'archival_banner': self.archival_banner,
            'browse_archive_btn': self.browse_archive_btn,
            'origin_trials_heading': self.origin_trials_heading,
            'deprecations_heading': self.deprecations_heading,
            'link_copied_tooltip': self.link_copied_tooltip,
            'empty_state_heading': self.empty_state_heading.format(
                milestone=milestone
            ),
            'empty_state_desc': self.empty_state_desc.format(
                milestone=milestone
            ),
            'view_roadmap_btn': self.view_roadmap_btn,
            'search_features_btn': self.search_features_btn,
            'external_window_sr': self.external_window_sr,
            'language_selector_aria': self.language_selector_aria,
            'copy_link_aria': lambda feature_name: self.copy_link_aria.format(
                feature_name=feature_name
            ),
        }
