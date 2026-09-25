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

"""Dynamic content machine translation and Redis fingerprint caching engine.

Architectural Role:
    This module manages DYNAMIC machine translation of live database content (such as
    feature summaries and descriptions) using Google Cloud Translation API (or Gemini).
    Because feature descriptions can be edited by users at any time, this module handles
    content fingerprint hashing (SHA-256), distributed Redis cache storage, HTML code-tag
    protection (`translate="no"`), and upstream API failure fallback.

When to add to `translation_helpers.py`:
    - Adding or modifying machine translation API integrations (Cloud Translation / Gemini).
    - Content hashing algorithms and fingerprint-based cache key generation.
    - Redis caching strategies, TTL management, or invalidation for dynamic translations.
    - HTML/Markdown protection filters for machine translation.
    - Batch translation orchestration and graceful English fallback logic.

When to add to `l10n_helpers.py` instead:
    - Anything related to STATIC UI strings and catalogs in `locales/<page_name>/<lang>.json`.
    - Page schemas, placeholder validation, or strongly-typed UI translation models.
    - Path localization helpers or language selector option registries.
"""

import hashlib
import logging
import re
from typing import Any

import settings
from framework import rediscache
from internals import l10n_models, markdown_helpers

# Duration for which a cached translation is stored in Redis (30 days).
TRANSLATION_CACHE_TTL_SEC: int = 30 * 24 * 60 * 60

# Upstream Cloud Translation request timeout (in seconds).
TRANSLATION_TIMEOUT_SEC: float = 2.0


def compute_summary_hash(summary: str) -> str:
    """Computes a deterministic 16-character SHA-256 fingerprint of a summary string."""
    normalized = (summary or '').strip().encode('utf-8')
    return hashlib.sha256(normalized).hexdigest()[:16]


def build_summary_cache_key(
    feature_id: int, lang: str, source_hash: str
) -> str:
    """Builds a deterministic Redis cache key containing the feature ID, language, and content hash."""
    return f'l10n_feat_summary|{feature_id}|{lang}|{source_hash}'


def mask_code_elements_for_translation(html: str) -> str:
    """Ensures code elements and technical tokens have translate='no' attributes."""
    return re.sub(
        r'<code(?![^>]*\btranslate=[\'"]no[\'"])',
        '<code translate="no"',
        html,
        flags=re.IGNORECASE,
    )


def translate_html_batch(
    html_list: list[str], target_lang: str
) -> list[str | None]:
    """Translates a batch of HTML strings to target_lang using Cloud Translation or mock provider."""
    if not html_list:
        return []
    if target_lang == l10n_models.DEFAULT_LANGUAGE.value:
        return [h for h in html_list]

    # In local development, unit test mode, or playwright mode, return deterministic mock translations.
    if settings.DEV_MODE or settings.UNIT_TEST_MODE or settings.PLAYWRIGHT_MODE:
        return [f'[Translated to {target_lang}] {h}' for h in html_list]

    try:
        from google.cloud import translate_v3

        client = translate_v3.TranslationServiceClient()
        parent = f'projects/{settings.APP_ID}/locations/global'

        # Protect code tokens before sending to Cloud Translation
        masked_contents = [
            mask_code_elements_for_translation(h) for h in html_list
        ]

        response = client.translate_text(
            request={
                'parent': parent,
                'contents': masked_contents,
                'mime_type': 'text/html',
                'source_language_code': 'en',
                'target_language_code': target_lang,
            },
            timeout=TRANSLATION_TIMEOUT_SEC,
        )

        return [t.translated_text for t in response.translations]
    except Exception as e:
        logging.warning(
            'Failed to translate HTML batch to %s: %s', target_lang, e
        )
        return [None] * len(html_list)


def localize_features_for_release_notes(
    features: list[dict[str, Any]], target_lang: str
) -> list[dict[str, Any]]:
    """Applies localized summaries with Redis fingerprint caching and per-feature fallback."""
    if not features:
        return features

    # English requires no translation; render standard markdown
    if target_lang == l10n_models.DEFAULT_LANGUAGE.value:
        for f in features:
            f['formatted_summary'] = markdown_helpers.render_markdown(
                f.get('summary') or ''
            )
            f['summary_lang'] = l10n_models.DEFAULT_LANGUAGE.value
        return features

    # 1. Compute English rendered HTML and source hashes for all features
    prepared_features: list[tuple[dict[str, Any], str, str, str]] = []
    cache_keys: list[str] = []

    for f in features:
        raw_summary = f.get('summary') or ''
        rendered_html = markdown_helpers.render_markdown(raw_summary)
        source_hash = compute_summary_hash(raw_summary)
        feature_id = f.get('id', 0)
        cache_key = build_summary_cache_key(
            feature_id, target_lang, source_hash
        )
        prepared_features.append((f, rendered_html, source_hash, cache_key))
        cache_keys.append(cache_key)

    # 2. Batch lookup in Redis
    cached_map = rediscache.get_multi(cache_keys) or {}

    # 3. Identify cache misses
    missing_indices: list[int] = []
    missing_html_list: list[str] = []

    for idx, (f, rendered_html, _, cache_key) in enumerate(prepared_features):
        cached_val = cached_map.get(cache_key)
        if cached_val:
            f['formatted_summary'] = cached_val
            f['summary_lang'] = target_lang
        else:
            missing_indices.append(idx)
            missing_html_list.append(rendered_html)

    # 4. Batch translate missing items if any
    if missing_html_list:
        translated_results = translate_html_batch(
            missing_html_list, target_lang
        )
        entries_to_cache: dict[str, str] = {}

        for miss_idx, translated_html in zip(
            missing_indices, translated_results, strict=True
        ):
            f, rendered_html, _, cache_key = prepared_features[miss_idx]
            if translated_html:
                f['formatted_summary'] = translated_html
                f['summary_lang'] = target_lang
                entries_to_cache[cache_key] = translated_html
            else:
                # Graceful fallback to English if translation failed
                f['formatted_summary'] = rendered_html
                f['summary_lang'] = l10n_models.DEFAULT_LANGUAGE.value

        if entries_to_cache:
            rediscache.set_multi(
                entries_to_cache, time=TRANSLATION_CACHE_TTL_SEC
            )

    return features
