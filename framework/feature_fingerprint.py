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

from __future__ import annotations

import hashlib
import json
from typing import TypedDict

from internals.core_models import FeatureEntry

UTF_8 = 'utf-8'
EMPTY_FINGERPRINT = hashlib.sha256(b'{}').hexdigest()


class FeatureFingerprintPayload(TypedDict):
    """Typed dictionary defining canonical specification fields for feature fingerprinting."""

    name: str | None
    summary: str | None
    spec_link: str | None
    standard_maturity: int | None
    category: int | None
    feature_type: int | None
    search_tags: list[str]
    doc_links: list[str]
    spec_mentor_emails: list[str]


def compute_feature_fingerprint(feature: FeatureEntry | None) -> str:
    """Computes a deterministic SHA-256 fingerprint from a FeatureEntry entity.

    Serializes core specification properties into a canonical JSON payload to detect
    content changes before generating AI release notes.

    Args:
      feature: A `FeatureEntry` NDB entity, or None.

    Returns:
      A 64-character lowercase hex string representing the SHA-256 fingerprint.
    """
    if feature is None:
        return EMPTY_FINGERPRINT

    payload: FeatureFingerprintPayload = {
        'name': feature.name,
        'summary': feature.summary,
        'spec_link': feature.spec_link,
        'standard_maturity': feature.standard_maturity,
        'category': feature.category,
        'feature_type': feature.feature_type,
        'search_tags': sorted(set(feature.search_tags or [])),
        'doc_links': sorted(set(feature.doc_links or [])),
        'spec_mentor_emails': sorted(set(feature.spec_mentor_emails or [])),
    }

    canonical_json = json.dumps(
        payload, sort_keys=True, separators=(',', ':'), default=str
    )
    return hashlib.sha256(canonical_json.encode(UTF_8)).hexdigest()
