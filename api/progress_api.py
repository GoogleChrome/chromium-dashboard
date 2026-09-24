# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
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

"""API endpoint for retrieving the progress of feature implementation processes."""

import datetime

from chromestatus_openapi.models import SuccessMessage

from framework import basehandlers, permissions
from internals import progress, stage_helpers


class ProgressAPI(basehandlers.APIHandler):
    """Progress returns a dictionary mapping progress item names to vote status objects."""

    def do_get(self, **kwargs):
        """Return the progress of the feature."""
        fe = self.get_specified_feature(**kwargs)
        feature_id = fe.key.integer_id()
        stages = stage_helpers.get_feature_stages(feature_id)
        now_iso = datetime.datetime.now().isoformat()
        progress_so_far: dict[str, dict[str, int | str | None]] = {}
        for progress_item, detector in list(
            progress.PROGRESS_DETECTORS.items()
        ):
            detected = detector(fe, stages)
            if detected:
                progress_so_far[progress_item] = {
                    'state': progress.ProgressVote.VERIFIED,
                    'set_on': now_iso,
                    'set_by': 'ChromeStatus',
                }

        votes: list[progress.ProgressVote] = progress.ProgressVote.query(
            progress.ProgressVote.feature_id == feature_id
        ).fetch()
        for vote in votes:
            progress_so_far[vote.progress_item_name] = {
                'state': vote.state,
                'feedback': vote.feedback,
                'set_on': vote.set_on.isoformat(),
                'set_by': vote.set_by,
            }

        return progress_so_far

    def do_post(self, **kwargs):
        """Set a user's vote value for a progress item on the specified feature."""
        user = self.get_current_user()
        fe = self.get_specified_feature(**kwargs)
        feature_id = fe.key.integer_id()
        progress_item_name = self.get_param('progress_item_name')
        new_state = self.get_int_param(
            'state', validator=progress.ProgressVote.is_valid_state
        )
        feedback = self.get_param('feedback', required=False)

        self.require_permissions(user, fe, progress_item_name, new_state)

        progress.set_progress_vote(
            feature_id,
            progress_item_name,
            new_state,
            user.email(),
            feedback=feedback,
        )
        return SuccessMessage(message='Done').to_dict()

    def require_permissions(
        self,
        user=None,
        feature=None,
        progress_item_name=None,
        new_state=None,
    ) -> None:
        """Abort the request if the user lacks permission to set this vote."""
        if not permissions.can_edit_any_feature(user):
            self.abort(403, 'User lacks permission to vote')
        return
