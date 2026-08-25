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

import logging
import urllib.parse
from typing import Any

import flask

import settings
from framework import basehandlers, seo
from internals import (
    core_enums,
    feature_helpers,
    fetchchannels,
    l10n_helpers,
    l10n_models,
    markdown_helpers,
    releasenotes_l10n_helpers,
)

# Milestones prior to M151 were published as standalone blog posts on developer.chrome.com.
# ChromeStatus SSR release notes curation begins with Chrome 151.
MIN_SSR_RELEASE_NOTES_MILESTONE: int = 151

# developer.chrome.com began publishing standalone release notes with Chrome 124.
MIN_EXTERNAL_RELEASE_NOTES_MILESTONE: int = 124

# Maximum future milestone offset above stable milestone allowed before returning 404 (DoS defense).
MAX_SSR_RELEASE_NOTES_FUTURE_OFFSET: int = 20

# Active release channel horizon offset above stable milestone (Stable = +0, Beta = +1, Dev/Canary = +2).
ACTIVE_RELEASE_CHANNELS_OFFSET: int = 2

# Stepper delta for sequential milestone navigation.
STEPPER_MILESTONE_OFFSET: int = 1

EXTERNAL_RELEASE_NOTES_URL_TEMPLATE: str = (
    'https://developer.chrome.com/release-notes/{milestone}'
)
EXTERNAL_RELEASE_NOTES_ARCHIVE_URL: str = (
    'https://developer.chrome.com/release-notes'
)


class ReleaseNotesHandler(basehandlers.FlaskHandler):
    """Flask handler for rendering the Server-Side Rendered (SSR) Release Notes page."""

    # Private caching policy: Browser can cache locally, but shared CDNs must not
    # cache authenticated responses containing user XSRF tokens or unlisted features.
    HTTP_CACHE_TYPE = 'private'
    TEMPLATE_PATH = 'release-notes.html'

    def get_template_data(
        self, **kwargs: Any
    ) -> dict[str, Any] | flask.Response:
        """Assembles template context data for rendering release notes."""
        # 1. Resolve current stable milestone with resilience against upstream Omaha downtime.
        # If the upstream Chromium Dash / Omaha API is unreachable, get_current_stable_milestone()
        # returns 0. In that scenario, fall back to MIN_SSR_RELEASE_NOTES_MILESTONE to ensure the
        # default /release-notes landing page remains functional and never errors with 400.
        raw_stable_milestone = fetchchannels.get_current_stable_milestone()
        if raw_stable_milestone > 0:
            stable_milestone = raw_stable_milestone
        else:
            logging.warning(
                'Could not fetch current stable milestone from Omaha; falling back to %d',
                MIN_SSR_RELEASE_NOTES_MILESTONE,
            )
            stable_milestone = MIN_SSR_RELEASE_NOTES_MILESTONE

        milestone_param = kwargs.get('milestone')
        if milestone_param is None:
            milestone = stable_milestone
        else:
            try:
                milestone = int(milestone_param)
            except (ValueError, TypeError):
                self.abort(
                    400, f'Invalid milestone parameter: {milestone_param}'
                )

        if milestone <= 0:
            self.abort(400, f'Invalid milestone parameter: {milestone}')

        # 2. Denial of Service (DoS) protection:
        # Prevent memory and CPU exhaustion from arbitrary or inflated milestone numbers (e.g.,
        # /release-notes/10000000). Allocating an unbounded list(range(max_milestone, 0, -1))
        # array and rendering millions of <option> tags in Jinja template datalists causes severe
        # server memory pressure and can crash App Engine worker processes (OOM).
        max_allowed_milestone = (
            max(stable_milestone, MIN_SSR_RELEASE_NOTES_MILESTONE)
            + MAX_SSR_RELEASE_NOTES_FUTURE_OFFSET
        )
        if milestone > max_allowed_milestone:
            self.abort(404, f'Milestone {milestone} is not available')

        # Milestones prior to M151 redirect to developer.chrome.com
        if milestone < MIN_SSR_RELEASE_NOTES_MILESTONE:
            if milestone < MIN_EXTERNAL_RELEASE_NOTES_MILESTONE:
                # Pre-124 milestones do not exist on d.c.c/release-notes/<m>; redirect to archive root.
                return self.redirect(EXTERNAL_RELEASE_NOTES_ARCHIVE_URL)
            redirect_url = EXTERNAL_RELEASE_NOTES_URL_TEMPLATE.format(
                milestone=milestone
            )
            return self.redirect(redirect_url)

        raw_lang = flask.request.args.get('hl') or flask.request.args.get(
            'lang'
        )
        current_lang = l10n_helpers.resolve_supported_language(raw_lang)
        translations = l10n_helpers.get_release_notes_translations(current_lang)

        release_note_features = (
            feature_helpers.get_developer_release_notes_features(milestone)
        )

        if current_lang != l10n_models.SupportedLanguage.EN:
            if (
                current_lang.value
                in releasenotes_l10n_helpers.SUPPORTED_LANGUAGES
            ):
                release_note_features = (
                    releasenotes_l10n_helpers.merge_translations(
                        release_note_features, current_lang.value
                    )
                )

        features_by_category: dict[str, list[dict[str, Any]]] = {}
        origin_trials: list[dict[str, Any]] = []
        deprecations_and_removals: list[dict[str, Any]] = []

        for feature in release_note_features:
            feature['formatted_summary'] = markdown_helpers.render_markdown(
                feature.get('summary') or ''
            )
            if (
                current_lang != l10n_models.SupportedLanguage.EN
                and 'links' in feature
            ):
                feature['links'] = translations.localize_links(feature['links'])

            classification = feature.get('milestone_classification')
            if (
                classification
                == core_enums.ReleaseNoteMilestoneClassification.ORIGIN_TRIAL
            ):
                origin_trials.append(feature)
            elif classification in (
                core_enums.ReleaseNoteMilestoneClassification.DEPRECATION,
                core_enums.ReleaseNoteMilestoneClassification.REMOVAL,
            ):
                deprecations_and_removals.append(feature)
            else:
                category = translations.get_category(
                    feature.get('category_name')
                )
                features_by_category.setdefault(category, []).append(feature)

        # Bound the datalist dropdown options to the visible release horizon down to M124.
        max_dropdown_milestone = (
            max(stable_milestone, MIN_SSR_RELEASE_NOTES_MILESTONE)
            + ACTIVE_RELEASE_CHANNELS_OFFSET
        )
        milestones_list = list(
            range(
                max_dropdown_milestone,
                MIN_EXTERNAL_RELEASE_NOTES_MILESTONE - 1,
                -1,
            )
        )

        prev_milestone = (
            milestone - STEPPER_MILESTONE_OFFSET
            if milestone > MIN_EXTERNAL_RELEASE_NOTES_MILESTONE
            else None
        )
        next_milestone = (
            milestone + STEPPER_MILESTONE_OFFSET
            if milestone < max_allowed_milestone
            else None
        )

        ui = translations.format_ui(
            milestone=milestone,
            prev_milestone=prev_milestone,
            next_milestone=next_milestone,
        )
        supported_languages = l10n_helpers.get_supported_languages(
            l10n_helpers.RELEASE_NOTES_TRANSLATIONS
        )

        canonical_path = f'/release-notes/{milestone}'
        if current_lang != l10n_models.SupportedLanguage.EN:
            canonical_path += f'?hl={current_lang.value}'

        seo_metadata = seo.Metadata(
            canonical_url=urllib.parse.urljoin(
                settings.SITE_URL, canonical_path
            ),
            seo_title=ui['page_title'],
            seo_description=(
                f'Discover web platform features, deprecations, and developer updates '
                f'shipped in Google Chrome {milestone}.'
            ),
            site_logo_url=urllib.parse.urljoin(
                settings.SITE_URL, settings.SITE_LOGO_PATH
            ),
            schema_type=seo.SchemaType.ITEM_PAGE,
        )

        return {
            'milestone': milestone,
            'stable_milestone': stable_milestone,
            'prev_milestone': prev_milestone,
            'next_milestone': next_milestone,
            'is_min_ssr_milestone': (
                milestone == MIN_SSR_RELEASE_NOTES_MILESTONE
            ),
            'min_ssr_milestone': MIN_SSR_RELEASE_NOTES_MILESTONE,
            'min_dropdown_milestone': MIN_EXTERNAL_RELEASE_NOTES_MILESTONE,
            'max_dropdown_milestone': max_dropdown_milestone,
            'features_by_category': features_by_category,
            'origin_trials': origin_trials,
            'deprecations_and_removals': deprecations_and_removals,
            'total_features_count': len(release_note_features),
            'milestones_list': milestones_list,
            'current_lang': current_lang.value,
            'supported_languages': supported_languages,
            'ui': ui,
            'seo': seo_metadata.to_dict(),
        }
