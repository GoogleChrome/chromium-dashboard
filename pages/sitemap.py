# -*- coding: utf-8 -*-
# Copyright 2026 Google LLC
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

"""Handler for serving the sitemap.txt file."""

from framework import basehandlers
from internals.core_models import FeatureEntry


class SitemapHandler(basehandlers.FlaskHandler):
    """Handler for serving the sitemap.txt file."""

    HTTP_CACHE_TYPE = 'public'

    def get_template_data(self, **kwargs):
        """Returns the sitemap.txt content with URLs for all listed features."""
        headers = self.get_headers()
        headers['Content-Type'] = 'text/plain'

        # Query for non-deleted, non-unlisted, and non-confidential features.
        # We use keys_only=True for optimal performance and memory footprint.
        query = FeatureEntry.query(
            FeatureEntry.deleted == False,  # noqa: E712
            FeatureEntry.unlisted == False,  # noqa: E712
            FeatureEntry.confidential == False,  # noqa: E712
        )
        keys = query.fetch(keys_only=True)

        feature_ids = [k.integer_id() for k in keys]
        feature_ids.sort()

        content = ''.join(f'https://chromestatus.com/feature/{fid}\n' for fid in feature_ids)
        return content, headers
