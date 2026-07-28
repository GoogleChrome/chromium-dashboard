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
from typing import Any


@dataclass(frozen=True)
class Metadata:
    """Strongly-typed container for page SEO and social sharing metadata."""

    canonical_url: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    site_logo_url: str | None = None
    og_type: str = 'website'
    schema_type: str = 'WebPage'
    twitter_card: str = 'summary_large_image'

    def to_dict(self) -> dict[str, Any]:
        """Export non-None metadata fields as a template context dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}
