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
