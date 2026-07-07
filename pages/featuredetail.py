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



from api import converters
from framework import basehandlers, permissions, users
from internals.core_enums import INTENT_STAGES
from internals.core_models import FeatureEntry


class FeatureDetailHandler(basehandlers.SPAHandler):
    """SPA + SSR handler for showing one feature entry in detail."""

    def get_crawler_data(self, defaults):
        """Retrieves basic details of the current feature."""
        crawler_data = super(FeatureDetailHandler, self).get_crawler_data(defaults)
        user = users.get_current_user()
        feature_id = defaults.get('feature_id', None)
        fe = None
        if feature_id:
            fe = FeatureEntry.get_by_id(feature_id)
        if fe:
            if permissions.can_view_feature(user, fe):
                feature_dict = converters.feature_entry_to_json_verbose(fe)
                crawler_data['heading'] = self.make_heading(fe)
                crawler_data['sections'] = self.make_sections(feature_dict)

        return crawler_data

    def make_heading(self, fe: FeatureEntry):
        """Create heading data for the crawler."""
        return {
            'title': fe.name,
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
                    'Stage: ' +
                    INTENT_STAGES.get(s.get('intent_stage'), '') + ' ' +
                    (s.get('display_name') or '')
                ),
                'fields': s
                }
            for s in stages
        ]
        return [metadata] + stage_data
