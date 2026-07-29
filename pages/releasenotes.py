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

"""Handler for displaying release notes via Server-Side Rendering (SSR)."""

from typing import Any

import flask

import settings
from framework import basehandlers, seo
from internals import feature_helpers, fetchchannels

# Milestones prior to M151 were published as standalone blog posts on developer.chrome.com.
# ChromeStatus SSR release notes curation begins with Chrome 151.
EXTERNAL_RELEASE_NOTES_URL_TEMPLATE: str = (
    'https://developer.chrome.com/release-notes/{milestone}'
)


class ReleaseNotesHandler(basehandlers.FlaskHandler):
    """Flask handler for rendering the Server-Side Rendered (SSR) Release Notes page."""

    # Public caching policy: Release notes are public content suitable for global CDN caching.
    HTTP_CACHE_TYPE = 'public'
    TEMPLATE_PATH = 'release-notes.html'

    def get_template_data(
        self, **kwargs: Any
    ) -> dict[str, Any] | flask.Response:
        """Assembles template context data for rendering release notes."""
        milestone_param = kwargs.get('milestone')

        if milestone_param is None:
            milestone = fetchchannels.get_current_stable_milestone()
        else:
            try:
                milestone = int(milestone_param)
            except (ValueError, TypeError):
                self.abort(
                    400, f'Invalid milestone parameter: {milestone_param}'
                )

        if milestone <= 0:
            self.abort(400, f'Invalid milestone parameter: {milestone}')

        # Milestones prior to 151 redirect immediately to developer.chrome.com/release-notes/<milestone>
        if milestone < settings.MIN_SSR_RELEASE_NOTES_MILESTONE:
            redirect_url = EXTERNAL_RELEASE_NOTES_URL_TEMPLATE.format(
                milestone=milestone
            )
            return self.redirect(redirect_url)

        # Channel quick-jumps (Stable, Beta, Dev)
        try:
            stable_milestone = fetchchannels.get_current_stable_milestone()
            beta_milestone = fetchchannels.get_current_beta_milestone()
            dev_milestone = fetchchannels.get_current_channel_milestone(
                fetchchannels.Channel.DEV
            )
        except Exception:
            stable_milestone = milestone - 2
            beta_milestone = milestone
            dev_milestone = milestone + 1

        release_note_features = (
            feature_helpers.get_developer_release_notes_features(milestone)
        )

        features_by_category: dict[str, list[dict[str, Any]]] = {}
        for feature in release_note_features:
            category = feature.get('category_name') or 'Other'
            features_by_category.setdefault(category, []).append(feature)

        milestones_list = list(range(1, max(150, milestone + 10)))

        site_url = settings.SITE_URL.rstrip('/')
        seo_metadata = seo.Metadata(
            canonical_url=f'{site_url}/release-notes/{milestone}',
            seo_title=f'Chrome {milestone} Release Notes',
            seo_description=(
                f'Discover web platform features, deprecations, and developer updates '
                f'shipped in Google Chrome {milestone}.'
            ),
            site_logo_url=f'{site_url}{settings.DEFAULT_SITE_LOGO_PATH}',
            schema_type=seo.SchemaType.ITEM_PAGE,
        )

        return {
            'milestone': milestone,
            'stable_milestone': stable_milestone,
            'beta_milestone': beta_milestone,
            'dev_milestone': dev_milestone,
            'features_by_category': features_by_category,
            'total_features_count': len(release_note_features),
            'milestones_list': milestones_list,
            'seo': seo_metadata.to_dict(),
        }
