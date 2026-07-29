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

"""SEO metadata models and helpers for Server-Side Rendering (SSR)."""

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class OpenGraphType(StrEnum):
    """Open Graph protocol entity type values used in ChromeStatus.

    Reference: https://ogp.me/#types
    """

    WEBSITE = 'website'


class SchemaType(StrEnum):
    """Schema.org structured data entity type values used in ChromeStatus.

    Reference: https://schema.org/docs/full.html
    """

    WEB_PAGE = 'WebPage'
    ITEM_PAGE = 'ItemPage'


@dataclass(frozen=True)
class Metadata:
    """Strongly-typed container for page SEO and social sharing metadata.

    Attributes:
        canonical_url: Absolute canonical URL for preferred search indexing.
            Ref: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
        seo_title: Specific SEO title tag content.
            Ref: https://developers.google.com/search/docs/appearance/title-link
        seo_description: Concise page summary for search engine snippet display.
            Ref: https://developers.google.com/search/docs/appearance/snippet
        site_logo_url: Absolute image URL for social preview cards (og:image).
            Ref: https://ogp.me/#metadata
        og_type: Open Graph category type (default: OpenGraphType.WEBSITE).
            Ref: https://ogp.me/#types
        schema_type: Schema.org entity type (default: SchemaType.WEB_PAGE).
            Ref: https://schema.org/WebPage
    """

    canonical_url: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    site_logo_url: str | None = None
    og_type: OpenGraphType | str = OpenGraphType.WEBSITE
    schema_type: SchemaType | str = SchemaType.WEB_PAGE

    def to_dict(self) -> dict[str, Any]:
        """Export non-None metadata fields as a template context dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}
