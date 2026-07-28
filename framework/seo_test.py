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

"""Unit tests for framework/seo.py Metadata dataclass."""

import testing_config  # noqa: F401, I001

from framework import seo
import settings


class SEOMetadataTest(testing_config.CustomTestCase):
    """Unit tests for seo.Metadata dataclass."""

    def test_instantiation_defaults(self):
        """It applies default values for og_type, schema_type, and twitter_card."""
        metadata = seo.Metadata(
            canonical_url='https://chromestatus.com/release-notes/151',
            seo_title='Chrome 151 Release Notes',
            seo_description='Release notes description.',
            site_logo_url='https://chromestatus.com/static/img/crstatus_192.png',
        )

        self.assertEqual(
            'https://chromestatus.com/release-notes/151', metadata.canonical_url
        )
        self.assertEqual('Chrome 151 Release Notes', metadata.seo_title)
        self.assertEqual('Release notes description.', metadata.seo_description)
        self.assertEqual(
            'https://chromestatus.com/static/img/crstatus_192.png',
            metadata.site_logo_url,
        )
        self.assertEqual('website', metadata.og_type)
        self.assertEqual('WebPage', metadata.schema_type)
        self.assertEqual('summary_large_image', metadata.twitter_card)

    def test_to_dict__exports_non_none_fields(self):
        """It exports metadata attributes as a template context dictionary."""
        metadata = seo.Metadata(
            canonical_url=f'{settings.SITE_URL.rstrip("/")}/feature/123',
            seo_title='Feature Detail',
            seo_description='Feature Description',
        )

        d = metadata.to_dict()
        self.assertIn('canonical_url', d)
        self.assertIn('seo_title', d)
        self.assertIn('seo_description', d)
        self.assertNotIn('site_logo_url', d)
        self.assertEqual('website', d['og_type'])
        self.assertEqual('WebPage', d['schema_type'])
        self.assertEqual('summary_large_image', d['twitter_card'])
