# Copyright 2026 Google Inc.
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

"""Serves the SPA with minimal semantic HTML for feature details."""

from framework import basehandlers, permissions, users
from internals import feature_helpers
from internals.core_enums import INTENT_STAGES


class FeatureDetailHandler(basehandlers.SPAHandler):
    """SPA + SSR handler for showing one feature entry in detail."""

    def get_crawler_data(self, defaults):
        """Retrieves basic details of the current feature."""
        crawler_data = super(FeatureDetailHandler, self).get_crawler_data(
            defaults
        )
        user = users.get_current_user()
        feature_id = defaults.get('feature_id', None)
        feature_dict = None
        if feature_id:
            features = feature_helpers.get_by_ids([feature_id])
            feature_dict = features[0] if features else None
        if feature_dict:
            if permissions.can_view_feature_formatted(user, feature_dict):
                crawler_data['heading'] = self.make_heading(feature_dict)
                crawler_data['sections'] = self.make_sections(feature_dict)

        return crawler_data

    def make_heading(self, fe: dict):
        """Create heading data for the crawler."""
        return {
            'title': 'Feature entry: ' + fe['name'],
        }

    def make_sections(self, feature_dict):
        """Create sections data (metadata and stages) for the crawler."""
        stages = feature_dict['stages']
        feature_without_stages = feature_dict.copy()
        del feature_without_stages['stages']
        metadata = {
            'summary': 'Metadata',
            'fields': feature_without_stages,
        }
        stage_data = [
            {
                'summary': (
                    'Stage: '
                    + INTENT_STAGES.get(s.get('intent_stage'), '')
                    + ' '
                    + (s.get('display_name') or '')
                ),
                'fields': s,
            }
            for s in stages
        ]
        return [metadata] + stage_data
