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

"""API handlers for retrieving localized release notes."""

import logging
from typing import Any

from chromestatus_openapi.models import (
    ReleaseNotesL10nResponse,
    ReleaseNotesResponse,
)
from google.cloud import ndb

from api import converters
from framework import basehandlers
from internals import core_enums, feature_helpers
from internals.core_models import FeatureEntry, FeatureSummarySuggestion


class ReleaseNotesAPI(basehandlers.APIHandler):
    """API handler for fetching public release notes features for a milestone (GET /api/v0/releasenotes/{milestone})."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Get public release notes features for a specific milestone.

        Args:
            **kwargs: Keyword arguments containing path or query parameters.

        Returns:
            A dictionary matching the ReleaseNotesResponse OpenAPI schema:
            { "milestone": milestone, "features": [ReleaseNoteFeature, ...] }
        """
        milestone = self._extract_id_param(kwargs, 'milestone')
        if milestone is None or milestone <= 0:
            self.abort(400, msg='Milestone must be a positive integer')

        # 1. Collect feature IDs shipping in milestone
        milestone_data = feature_helpers.get_in_milestone(milestone)
        seen_ids: set[int] = set()

        for reason, feature_dicts in milestone_data.items():
            for fdict in feature_dicts:
                fid = fdict.get('id')
                if fid:
                    seen_ids.add(fid)

        if not seen_ids:
            return ReleaseNotesResponse.from_dict(
                {'milestone': milestone, 'features': []}
            ).to_dict()

        # 2. Batch fetch FeatureEntry entities (prevents N+1 query loop)
        feature_keys = [ndb.Key(FeatureEntry, fid) for fid in seen_ids]
        raw_features = ndb.get_multi(feature_keys)
        feature_entries = [
            fe
            for fe in raw_features
            if fe and not fe.deleted and not fe.unlisted and not fe.confidential
        ]
        feature_entries.sort(key=lambda f: f.name or '')

        # 3. Batch fetch FeatureSummarySuggestion entities by key (prevents unbounded table scan)
        valid_fids = [fe.key.integer_id() for fe in feature_entries if fe.key]
        suggestion_keys = [
            ndb.Key(FeatureSummarySuggestion, fid) for fid in valid_fids
        ]
        suggestions = ndb.get_multi(suggestion_keys) if suggestion_keys else []
        applied_map: dict[int, FeatureSummarySuggestion] = {
            s.key.id(): s
            for s in suggestions
            if s and s.status == core_enums.SummarySuggestionStatus.APPLIED
        }

        # 4. Convert to release note feature dicts
        release_note_features = []
        for fe in feature_entries:
            fid = fe.key.integer_id() if fe.key else 0
            applied_suggestion = applied_map.get(fid)
            rn_dict = converters.feature_entry_to_release_note_feature_dict(
                fe, applied_suggestion=applied_suggestion
            )
            release_note_features.append(rn_dict)

        payload = {
            'milestone': milestone,
            'features': release_note_features,
        }
        return ReleaseNotesResponse.from_dict(payload).to_dict()


class ReleaseNotesL10nAPI(basehandlers.APIHandler):
    """Implements the OpenAPI /releasenotes/l10n path."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Get release notes for a milestone range.

        Returns:
          A dictionary representing ReleaseNotesL10nResponse.
        """
        start_milestone = self.get_int_arg('startMilestone')
        end_milestone = self.get_int_arg('endMilestone')

        if start_milestone is None:
            self.abort(400, msg='Missing startMilestone')
        if end_milestone is None:
            self.abort(400, msg='Missing endMilestone')

        if start_milestone <= 0 or end_milestone <= 0:
            self.abort(400, msg='Milestones must be positive integers')
        if start_milestone > end_milestone:
            self.abort(
                400,
                msg='startMilestone must be less than or equal to endMilestone',
            )

        logging.info(
            'Release notes requested for milestones %d to %d',
            start_milestone,
            end_milestone,
        )

        l10n_features = feature_helpers.get_features_for_l10n_extraction(
            start_milestone=start_milestone, end_milestone=end_milestone
        )

        return ReleaseNotesL10nResponse.from_dict(
            {
                'features': l10n_features,
                'descriptions': core_enums.RELEASE_NOTES_L10N_FIELDS_DESCRIPTIONS,
            }
        ).to_dict()
