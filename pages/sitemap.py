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

    def get_template_data(self, **kwargs):
        """Returns the sitemap.txt content with URLs for all listed features."""
        headers = self.get_headers()
        headers['Content-Type'] = 'text/plain'

        # Query for non-deleted and non-unlisted features.
        # We filter confidential in memory to be safe with default/None values,
        # and double check unlisted and deleted as well.
        query = FeatureEntry.query(
            FeatureEntry.deleted == False,  # noqa: E712
            FeatureEntry.unlisted == False,  # noqa: E712
        )
        features = query.fetch()

        feature_ids = [
            fe.key.integer_id()
            for fe in features
            if not fe.confidential and not fe.unlisted and not fe.deleted
        ]
        feature_ids.sort()

        urls = [
            f'https://chromestatus.com/feature/{fid}' for fid in feature_ids
        ]
        content = ('\n'.join(urls) + '\n') if urls else ''
        return content, headers
