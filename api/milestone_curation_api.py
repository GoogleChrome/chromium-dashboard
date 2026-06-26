# -*- coding: utf-8 -*-
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

"""REST API handlers for managing the editorial curation status of milestones."""

from typing import Any
from google.cloud import ndb  # type: ignore

from framework import basehandlers, permissions
from internals.core_models import MilestoneCuration


class MilestoneCurationAPI(basehandlers.EntitiesAPIHandler):
    """API handler to retrieve and update the curation status of milestones."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Fetch the curation status for a milestone."""
        milestone = kwargs.get('milestone')
        if milestone is None:
            self.abort(400, msg='Milestone is required.')

        # Strongly consistent key lookup (O(1))
        curation = MilestoneCuration.get_by_id(str(milestone))
        if not curation:
            return {
                'milestone': milestone,
                'status': 'not_started',
                'updated_by': None,
                'updated_at': None,
            }

        return {
            'milestone': milestone,
            'status': curation.status,
            'updated_by': curation.updated_by,
            'updated_at': curation.updated_at.isoformat() + 'Z' if curation.updated_at else None,
        }

    def do_patch(self, **kwargs: Any) -> dict[str, Any]:
        """Update the curation status for a milestone (BOLA Protected)."""
        milestone = kwargs.get('milestone')
        if milestone is None:
            self.abort(400, msg='Milestone is required.')

        user = self.get_current_user()
        if not user:
            self.abort(401, msg='Sign in required.')
        
        # BOLA Authorization Gate
        if not permissions.can_review_release_notes(user):
            self.abort(403, msg='Unauthorized.')

        params = self.get_json_param_dict()
        new_status = params.get('status')
        if not new_status:
            self.abort(400, msg='Status is required.')
            
        if new_status not in ['not_started', 'in_review', 'finalized']:
            self.abort(400, msg=f'Invalid status: {new_status}')

        @ndb.transactional()
        def update_status_tx():
            curation = MilestoneCuration.get_by_id(str(milestone))
            if not curation:
                curation = MilestoneCuration(id=str(milestone))
            curation.status = new_status
            curation.updated_by = user.email()
            curation.put()
            return curation

        curation = update_status_tx()
        return {
            'message': 'Milestone curation status updated successfully.',
            'milestone': milestone,
            'status': curation.status,
            'updated_by': curation.updated_by,
            'updated_at': curation.updated_at.isoformat() + 'Z' if curation.updated_at else None,
        }
