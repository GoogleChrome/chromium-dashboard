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

"""API handler for milestone editorial curation workflow (GET and PATCH /api/v0/milestone-curation/<int:milestone>)."""

from datetime import datetime, timezone
from typing import Any

from chromestatus_openapi.models import MilestoneCurationResponse

from api import converters
from framework import basehandlers, permissions
from internals import core_enums
from internals.core_models import MilestoneCuration


class MilestoneCurationAPI(basehandlers.APIHandler):
    """API handler for milestone editorial curation state (GET and PATCH /api/v0/milestone-curation/<int:milestone>)."""

    def do_get(self, **kwargs: Any) -> dict[str, Any]:
        """Retrieves editorial curation state for a given release milestone."""
        milestone = self._extract_id_param(kwargs, 'milestone')
        if milestone is None or milestone <= 0:
            self.abort(400, msg='Milestone must be a positive integer')

        curation = MilestoneCuration.get_by_id(str(milestone))
        if not curation:
            curation = MilestoneCuration(
                id=str(milestone),
                milestone=milestone,
                status=core_enums.MilestoneCurationStatus.PENDING.value,
                curator_emails=[],
            )

        payload = converters.milestone_curation_to_dict(curation)
        return MilestoneCurationResponse.from_dict(payload).to_dict()

    def do_patch(self, **kwargs: Any) -> dict[str, Any]:
        """Updates editorial curation state or curator emails for a milestone."""
        user = self.get_current_user()
        if not user or not permissions.can_edit_any_feature(user):
            self.abort(
                403,
                msg='User does not have permission to modify milestone curation status',
            )

        milestone = self._extract_id_param(kwargs, 'milestone')
        if milestone is None or milestone <= 0:
            self.abort(400, msg='Milestone must be a positive integer')

        request_body = self.get_json_param_dict()
        curation = MilestoneCuration.get_by_id(str(milestone))
        if not curation:
            curation = MilestoneCuration(
                id=str(milestone),
                milestone=milestone,
                status=core_enums.MilestoneCurationStatus.PENDING.value,
                curator_emails=[],
            )

        if 'status' in request_body:
            raw_status = request_body['status']
            try:
                status_enum = core_enums.MilestoneCurationStatus(raw_status)
            except (ValueError, TypeError):
                self.abort(400, msg=f'Invalid status value: {raw_status}')
            curation.status = status_enum.value

        if 'curator_emails' in request_body:
            raw_emails = request_body['curator_emails']
            if not isinstance(raw_emails, list) or not all(
                isinstance(e, str) for e in raw_emails
            ):
                self.abort(
                    400, msg='curator_emails must be a list of email strings'
                )
            curation.curator_emails = raw_emails

        curation.updated = datetime.now(timezone.utc)
        curation.put()

        payload = converters.milestone_curation_to_dict(curation)
        return MilestoneCurationResponse.from_dict(payload).to_dict()
