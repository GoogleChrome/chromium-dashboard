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
    _safe_int,
    _safe_int_list,
    _safe_str_list,
    compute_feature_fingerprint,
)
from internals.core_models import FeatureEntry


class FeatureFingerprintTest(testing_config.CustomTestCase):
    """Tests deterministic SHA-256 fingerprint generation for features."""

    def test_safe_int(self):
        """Tests safe integer parsing and fallback handling."""
        self.assertEqual(_safe_int(123), 123)
        self.assertEqual(_safe_int('456'), 456)
        self.assertEqual(_safe_int(None, default=0), 0)
        self.assertEqual(_safe_int('abc', default=0), 0)
        self.assertEqual(_safe_int(True, default=0), 0)
        self.assertEqual(_safe_int(False, default=0), 0)

    def test_safe_str_list(self):
        """Tests safe string list normalization and whitespace stripping."""
        self.assertEqual(
            _safe_str_list([' b ', 'a', 'b', None, 'None', '']), ['a', 'b']
        )
        self.assertEqual(_safe_str_list(None), [])
        self.assertEqual(_safe_str_list('not a list'), [])

    def test_safe_int_list(self):
        """Tests safe integer list normalization."""
        self.assertEqual(
            _safe_int_list([3, 1, '2', None, 'abc', True]), [1, 2, 3]
        )
        self.assertEqual(_safe_int_list(None), [])
        self.assertEqual(_safe_int_list('not a list'), [])

    def test_compute_feature_fingerprint__deterministic(self):
        """Tests deterministic SHA-256 generation on identical dictionaries."""
        feature_dict = {
            'name': 'WebGPU Subgroups',
            'summary': 'Enables SIMD-scoped compute operations in WGSL shaders.',
            'shipped_milestone': 130,
            'spec_link': 'https://gpuweb.github.io/gpuweb/',
            'standard_maturity': 1,
            'category': 2,
            'feature_type': 0,
            'search_tags': ['webgpu', 'wgsl', 'subgroups'],
            'doc_links': [
                'https://developer.chrome.com/docs/web-platform/webgpu-subgroups'
            ],
            'spec_mentors': ['mentor@example.com'],
        }
        hash1 = compute_feature_fingerprint(feature_dict)
        hash2 = compute_feature_fingerprint(feature_dict)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)

    def test_compute_feature_fingerprint__entity_vs_dict(self):
        """Tests that FeatureEntry entity and equivalent dictionary yield identical hashes."""
        feature_entry = FeatureEntry(
            id=12345,
            name='CSS Anchor Positioning',
            summary='Anchors positioned elements relative to target elements.',
            spec_link='https://drafts.csswg.org/css-anchor-1/',
            standard_maturity=2,
            category=1,
            feature_type=0,
            search_tags=['css', 'anchor', 'layout'],
            doc_links=['https://developer.chrome.com/blog/anchor-positioning'],
            spec_mentor_emails=['css-expert@example.com'],
        )
        feature_dict = {
            'name': 'CSS Anchor Positioning',
            'summary': 'Anchors positioned elements relative to target elements.',
            'shipped_milestone': 0,
            'spec_link': 'https://drafts.csswg.org/css-anchor-1/',
            'standard_maturity': 2,
            'category': 1,
            'feature_type': 0,
            'search_tags': ['css', 'anchor', 'layout'],
            'doc_links': [
                'https://developer.chrome.com/blog/anchor-positioning'
            ],
            'spec_mentors': ['css-expert@example.com'],
        }
        self.assertEqual(
            compute_feature_fingerprint(feature_entry),
            compute_feature_fingerprint(feature_dict),
        )

    def test_compute_feature_fingerprint__detects_summary_change(self):
        """Tests that modifying summary text triggers hash change."""
        base = {
            'name': 'Declarative Shadow DOM',
            'summary': 'Initial description.',
            'shipped_milestone': 90,
        }
        modified = {
            'name': 'Declarative Shadow DOM',
            'summary': 'Updated description with new details.',
            'shipped_milestone': 90,
        }
        self.assertNotEqual(
            compute_feature_fingerprint(base),
            compute_feature_fingerprint(modified),
        )

    def test_compute_feature_fingerprint__detects_milestone_change(self):
        """Tests that changing shipped milestone triggers hash change."""
        base = {
            'name': 'Speculation Rules API',
            'summary': 'Allows prefetching and prerendering via JSON scripts.',
            'shipped_milestone': 108,
        }
        modified = {
            'name': 'Speculation Rules API',
            'summary': 'Allows prefetching and prerendering via JSON scripts.',
            'shipped_milestone': 109,
        }
        self.assertNotEqual(
            compute_feature_fingerprint(base),
            compute_feature_fingerprint(modified),
        )

    def test_compute_feature_fingerprint__doc_links_order_independent(self):
        """Tests that list field permutation does not affect output hash."""
        base = {
            'name': 'View Transitions',
            'summary': 'Enables smooth visual DOM transitions.',
            'doc_links': ['https://example.com/b', 'https://example.com/a'],
            'search_tags': ['animations', 'spa'],
        }
        permuted = {
            'name': 'View Transitions',
            'summary': 'Enables smooth visual DOM transitions.',
            'doc_links': ['https://example.com/a', 'https://example.com/b'],
            'search_tags': ['spa', 'animations'],
        }
        self.assertEqual(
            compute_feature_fingerprint(base),
            compute_feature_fingerprint(permuted),
        )

    def test_compute_feature_fingerprint__handles_none_and_empty_fields(self):
        """Tests robustness when given empty or None input."""
        empty_feature = {}
        fingerprint_empty = compute_feature_fingerprint(empty_feature)
        self.assertEqual(len(fingerprint_empty), 64)

        none_feature = None
        fingerprint_none = compute_feature_fingerprint(none_feature)
        self.assertEqual(len(fingerprint_none), 64)

    def test_compute_feature_fingerprint__shipped_desktop_milestone_fallback(
        self,
    ):
        """Tests fallback from shipped_milestone to shipped_desktop_milestone."""
        feature_with_desktop = {
            'name': 'AudioContext',
            'summary': 'Web Audio API context.',
            'shipped_desktop_milestone': 115,
        }
        feature_with_standard = {
            'name': 'AudioContext',
            'summary': 'Web Audio API context.',
            'shipped_milestone': 115,
        }
        self.assertEqual(
            compute_feature_fingerprint(feature_with_desktop),
            compute_feature_fingerprint(feature_with_standard),
        )
