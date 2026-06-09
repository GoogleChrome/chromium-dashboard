# Copyright 2026 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
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

"""Helper functions for loading, caching, and merging localized release notes."""

import logging
import time

import pymmh3
import requests

from framework import rediscache

# Duration for which a cached translation is considered fresh.
L10N_CACHE_TTL_SEC = 3 * 60 * 60  # 3 hours

# Lifecycle duration of the cache entry in Redis. If fresh cache check fails,
# the system uses this stale entry as a fallback for up to 24 hours.
L10N_STALE_BACKUP_TTL_SEC = 24 * 60 * 60  # 24 hours

# Timeout duration (in seconds) for HTTP requests to the SCS CDN.
L10N_FETCH_TIMEOUT_SEC = 30

L10N_URL_TEMPLATE = (
    'https://chromeenterprise.google/static/json/release_notes_{lang}.json'
)

# Strict whitelist matching the exact case of filenames on SCS CDN
SUPPORTED_LANGUAGES = {
    'de': 'de',
    'es': 'es',
    'fr': 'fr',
    'id': 'id',
    'ja': 'ja',
    'ko': 'ko',
    'nl': 'nl',
    'pt-br': 'pt-BR',
}


def murmur3_x64_128_h1(text: str) -> str:
    """Computes the lower 64-bit value of MurmurHash3 x64 128-bit hash as a hex string.

    Matches Guava's Hashing.murmur3_128().hashString(text, UTF_8).asLong() formatted as hex.
    """
    # pymmh3.hash128 returns a 128-bit unsigned integer.
    # We extract the lower 64 bits (h1) and format it as a 16-character zero-padded hex.
    h128 = pymmh3.hash128(text, seed=0, x64arch=True)
    h1 = h128 & 0xFFFFFFFFFFFFFFFF
    return f'{h1:016x}'


def fetch_translation_dict(lang: str) -> dict[str, dict]:
    """Fetches the translation dictionary for the given language from SCS, with caching."""
    # Normalize input and resolve exact case filename code
    normalized_lang = lang.strip().lower()
    scs_lang_code = SUPPORTED_LANGUAGES.get(normalized_lang)
    if not scs_lang_code:
        return {}

    cache_key = f'l10n_release_notes_{scs_lang_code}'
    cached_entry = rediscache.get(cache_key)

    current_time = time.time()

    # Check if cache is valid and fresh
    if cached_entry and (
        current_time - cached_entry.get('fetched_at', 0) < L10N_CACHE_TTL_SEC
    ):
        return cached_entry.get('data', {})

    # Cache is missing or expired, attempt to fetch from SCS.
    url = L10N_URL_TEMPLATE.format(lang=scs_lang_code)
    try:
        response = requests.get(url, timeout=L10N_FETCH_TIMEOUT_SEC)
        if response.status_code == 200:
            response.encoding = 'utf-8-sig'
            translation_dict = response.json()
            logging.info(
                'Successfully fetched translations from SCS. URL: %s, keys count: %d',
                url,
                len(translation_dict),
            )
            # Save to cache with updated fetch timestamp. Keep it as stale backup.
            rediscache.set(
                cache_key,
                {'data': translation_dict, 'fetched_at': current_time},
                time=L10N_STALE_BACKUP_TTL_SEC,
            )
            return translation_dict
        else:
            # If server returns a non-200 code (e.g. 404, 500), log it and fall back.
            logging.warning(
                'Failed to fetch translations from SCS. URL: %s, Status code: %d',
                url,
                response.status_code,
            )
    except Exception as e:
        # Catch connection timeouts, DNS errors, and other network exceptions.
        logging.error(
            'Error fetching translations from SCS. URL: %s, Error: %s', url, e
        )

    # First fallback: If fresh fetch failed, reuse the expired cache entry (up to 24 hours).
    if cached_entry:
        logging.info(
            'Falling back to stale cached translations for lang: %s',
            scs_lang_code,
        )
        return cached_entry.get('data', {})

    # Final fallback: Return empty dict. merge_translations() will skip translation
    # and serve the original English strings.
    return {}


def merge_translations(features: list[dict], lang: str) -> list[dict]:
    """Applies translations to translatable fields if hashes match."""
    translation_dict = fetch_translation_dict(lang)
    if not translation_dict:
        return features

    for f in features:
        feature_id = f.get('id')
        if not feature_id:
            continue

        # Translate feature name
        # Format template: FEATURE_{feature_id}_NAME_{hash}
        name_val = f.get('name', '')
        if name_val:
            name_hash = murmur3_x64_128_h1(name_val)
            name_key = f'feature_{feature_id}_name_{name_hash}'.upper()
            if name_key in translation_dict:
                f['name'] = translation_dict[name_key].get('message', name_val)

        # Translate feature summary
        # Format template: FEATURE_{feature_id}_SUMMARY_{hash}
        summary_val = f.get('summary', '')
        if summary_val:
            summary_hash = murmur3_x64_128_h1(summary_val)
            summary_key = f'feature_{feature_id}_summary_{summary_hash}'.upper()
            if summary_key in translation_dict:
                f['summary'] = translation_dict[summary_key].get(
                    'message', summary_val
                )

        # Translate stage rollout details
        # Format template: FEATURE_{feature_id}_STAGE_{stage_id}_ROLLOUTDETAILS_{hash}
        for stage in f.get('stages', []):
            stage_id = stage.get('id')
            rollout_details = stage.get('rollout_details')
            if stage_id and rollout_details:
                details_hash = murmur3_x64_128_h1(rollout_details)
                details_key = f'feature_{feature_id}_stage_{stage_id}_rolloutDetails_{details_hash}'.upper()
                if details_key in translation_dict:
                    stage['rollout_details'] = translation_dict[
                        details_key
                    ].get('message', rollout_details)

    return features
