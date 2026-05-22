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
)

from framework import basehandlers
from internals import core_enums, feature_helpers


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
