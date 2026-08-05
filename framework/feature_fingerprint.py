# Copyright 2026 Google Inc. All rights reserved.
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

"""Utility for computing deterministic SHA-256 fingerprints of features.

Used for change detection and cache validation before generating AI release notes.
"""

import hashlib
import json
from typing import Any


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely converts a value to int, defaulting to `default` on error."""
    if val is None or isinstance(val, bool):
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_str_list(val: Any) -> list[str]:
    """Extracts and normalizes a list of strings."""
    if not val or not isinstance(val, (list, tuple)):
        return []
    cleaned = [
        str(x).strip()
        for x in val
        if x is not None and str(x).strip() and str(x).strip().lower() != 'none'
    ]
    return sorted(list(set(cleaned)))


def _safe_int_list(val: Any) -> list[int]:
    """Extracts and normalizes a list of integers.

    Deduplicates and sorts integer values for permutation invariance. Reserved for
    future milestone array and rollout stage fingerprinting in the release notes stack.
    """
    if not val or not isinstance(val, (list, tuple)):
        return []
    cleaned = []
    for x in val:
        if x is not None and not isinstance(x, bool):
            try:
                cleaned.append(int(x))
            except (ValueError, TypeError):
                pass
    return sorted(list(set(cleaned)))


def compute_feature_fingerprint(feature: Any) -> str:
    """Computes a deterministic SHA-256 fingerprint from a feature entity or dict.

    Normalizes core properties (name, summary, shipped milestone, spec link,
    standards maturity, category, feature type, tags, doc links) into a canonical
    JSON payload to detect specification drift.

    Args:
      feature: A `FeatureEntry` NDB entity or a dictionary containing feature fields.

    Returns:
      A 64-character lowercase hex string representing the SHA-256 fingerprint.
    """
    if feature is None:
        return hashlib.sha256(b'{}').hexdigest()

    def get_attr(key: str, default: Any = None) -> Any:
        if isinstance(feature, dict):
            return feature.get(key, default)
        return getattr(feature, key, default)

    shipped = get_attr('shipped_milestone')
    if shipped is None:
        shipped = get_attr('shipped_desktop_milestone')

    spec_mentors = get_attr('spec_mentors')
    if not spec_mentors:
        spec_mentors = get_attr('spec_mentor_emails')

    doc_links = get_attr('doc_links')

    canonical_payload: dict[str, Any] = {
        'name': str(get_attr('name') or '').strip(),
        'summary': str(get_attr('summary') or '').strip(),
        'shipped_milestone': _safe_int(shipped, default=0),
        'spec_link': str(get_attr('spec_link') or '').strip(),
        'standard_maturity': _safe_int(
            get_attr('standard_maturity'), default=0
        ),
        'category': _safe_int(get_attr('category'), default=0),
        'feature_type': _safe_int(get_attr('feature_type'), default=0),
        'search_tags': _safe_str_list(get_attr('search_tags')),
        'doc_links': _safe_str_list(doc_links),
        'spec_mentors': _safe_str_list(spec_mentors),
    }

    canonical_json = json.dumps(
        canonical_payload, sort_keys=True, separators=(',', ':')
    )
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
