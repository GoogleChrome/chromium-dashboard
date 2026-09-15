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

"""Unit tests for framework/seo.py Metadata dataclass and StrEnums."""

import testing_config  # noqa: F401, I001

from framework import seo
import settings


class SEOMetadataTest(testing_config.CustomTestCase):
    """Unit tests for seo.Metadata dataclass and StrEnums."""

    def test_instantiation_defaults(self):
        """It applies default StrEnum values for og_type and schema_type."""
        metadata = seo.Metadata(
            canonical_url='https://chromestatus.com/release-notes/152',
            seo_title='Chrome 152 Release Notes',
            seo_description='Release notes description.',
            site_logo_url='https://chromestatus.com/static/img/crstatus_192.png',
        )

        self.assertEqual(
            'https://chromestatus.com/release-notes/152', metadata.canonical_url
        )
        self.assertEqual('Chrome 152 Release Notes', metadata.seo_title)
        self.assertEqual('Release notes description.', metadata.seo_description)
        self.assertEqual(
            'https://chromestatus.com/static/img/crstatus_192.png',
            metadata.site_logo_url,
        )
        self.assertEqual(seo.OpenGraphType.WEBSITE, metadata.og_type)
        self.assertEqual(seo.SchemaType.WEB_PAGE, metadata.schema_type)

    def test_strenum_custom_values(self):
        """It accepts explicit StrEnum members for og_type and schema_type."""
        metadata = seo.Metadata(
            canonical_url='https://chromestatus.com/release-notes/152',
            og_type=seo.OpenGraphType.WEBSITE,
            schema_type=seo.SchemaType.ITEM_PAGE,
        )

        d = metadata.to_dict()
        self.assertEqual('website', d['og_type'])
        self.assertEqual('ItemPage', d['schema_type'])

    def test_to_dict__exports_non_none_fields(self):
        """It exports metadata attributes as a primitive string template context dictionary."""
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
