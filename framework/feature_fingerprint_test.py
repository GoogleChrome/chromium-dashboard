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

"""Unit tests for deterministic feature change detection and fingerprinting."""

import testing_config  # isort: skip  # Must be imported before other project modules.
from framework.feature_fingerprint import (
    EMPTY_FINGERPRINT,
    FeatureFingerprintPayload,
    compute_feature_fingerprint,
)
from internals.core_models import FeatureEntry


class FeatureFingerprintTest(testing_config.CustomTestCase):
    """Tests deterministic SHA-256 fingerprint generation for features."""

    def test_feature_fingerprint_payload_schema_parity(self):
        """Ensures all TypedDict payload fields exist as valid properties on FeatureEntry."""
        for field_name in FeatureFingerprintPayload.__annotations__:
            self.assertIn(
                field_name,
                FeatureEntry._properties,
                f"Fingerprint payload field '{field_name}' is not an NDB property on FeatureEntry.",
            )

    def test_compute_feature_fingerprint__deterministic(self):
        """Tests deterministic SHA-256 generation on identical FeatureEntry instances."""
        feature = FeatureEntry(
            id=12345,
            name='WebGPU Subgroups',
            summary='Enables SIMD-scoped compute operations in WGSL shaders.',
            spec_link='https://gpuweb.github.io/gpuweb/',
            standard_maturity=1,
            category=2,
            feature_type=0,
            search_tags=['webgpu', 'wgsl', 'subgroups'],
            doc_links=[
                'https://developer.chrome.com/docs/web-platform/webgpu-subgroups'
            ],
            spec_mentor_emails=['mentor@example.com'],
        )
        hash1 = compute_feature_fingerprint(feature)
        hash2 = compute_feature_fingerprint(feature)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)

    def test_compute_feature_fingerprint__detects_name_change(self):
        """Tests that modifying feature name triggers hash change."""
        base = FeatureEntry(
            id=1,
            name='Declarative Shadow DOM v1',
            summary='Initial description.',
        )
        modified = FeatureEntry(
            id=1,
            name='Declarative Shadow DOM v2',
            summary='Initial description.',
        )
        self.assertNotEqual(
            compute_feature_fingerprint(base),
            compute_feature_fingerprint(modified),
        )

    def test_compute_feature_fingerprint__detects_summary_change(self):
        """Tests that modifying summary text triggers hash change."""
        base = FeatureEntry(
            id=1,
            name='Declarative Shadow DOM',
            summary='Initial description.',
        )
        modified = FeatureEntry(
            id=1,
            name='Declarative Shadow DOM',
            summary='Updated description with new details.',
        )
        self.assertNotEqual(
            compute_feature_fingerprint(base),
            compute_feature_fingerprint(modified),
        )

    def test_compute_feature_fingerprint__detects_category_change(self):
        """Tests that changing category triggers hash change."""
        base = FeatureEntry(
            id=1,
            name='Speculation Rules API',
            summary='Allows prefetching and prerendering via JSON scripts.',
            category=1,
        )
        modified = FeatureEntry(
            id=1,
            name='Speculation Rules API',
            summary='Allows prefetching and prerendering via JSON scripts.',
            category=2,
        )
        self.assertNotEqual(
            compute_feature_fingerprint(base),
            compute_feature_fingerprint(modified),
        )

    def test_compute_feature_fingerprint__detects_spec_link_change(self):
        """Tests that changing spec_link triggers hash change."""
        base = FeatureEntry(
            id=1,
            name='CSS Subgrid',
            summary='Nested grid tracks.',
            spec_link='https://drafts.csswg.org/css-grid-2/',
        )
        modified = FeatureEntry(
            id=1,
            name='CSS Subgrid',
            summary='Nested grid tracks.',
            spec_link='https://www.w3.org/TR/css-grid-2/',
        )
        self.assertNotEqual(
            compute_feature_fingerprint(base),
            compute_feature_fingerprint(modified),
        )

    def test_compute_feature_fingerprint__doc_links_order_independent(self):
        """Tests that list field permutation does not affect output hash."""
        base = FeatureEntry(
            id=1,
            name='View Transitions',
            summary='Enables smooth visual DOM transitions.',
            doc_links=['https://example.com/b', 'https://example.com/a'],
            search_tags=['animations', 'spa'],
        )
        permuted = FeatureEntry(
            id=1,
            name='View Transitions',
            summary='Enables smooth visual DOM transitions.',
            doc_links=['https://example.com/a', 'https://example.com/b'],
            search_tags=['spa', 'animations'],
        )
        self.assertEqual(
            compute_feature_fingerprint(base),
            compute_feature_fingerprint(permuted),
        )

    def test_compute_feature_fingerprint__handles_none_and_empty_fields(self):
        """Tests robustness when given empty FeatureEntry or None input."""
        empty_feature = FeatureEntry(id=1, name='', summary='')
        fingerprint_empty = compute_feature_fingerprint(empty_feature)
        self.assertEqual(len(fingerprint_empty), 64)

        fingerprint_none = compute_feature_fingerprint(None)
        self.assertEqual(fingerprint_none, EMPTY_FINGERPRINT)
        self.assertEqual(len(fingerprint_none), 64)
