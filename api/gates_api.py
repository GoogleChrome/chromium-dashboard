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

"""Admin API handlers for inspecting and updating review gate definitions."""

from chromestatus_openapi.models import GateDefAdmin, GetGateDefsResponse

from framework import basehandlers, permissions, rediscache
from internals import approval_defs
from internals.review_models import GateDef


def _is_valid_email(email: str) -> bool:
    """Return True if email looks like a plausible email address."""
    if not email or any(ch.isspace() for ch in email):
        return False
    local, sep, domain = email.partition('@')
    return bool(
        sep and local and domain and '.' in domain and '@' not in domain
    )


class GatesAdminAPI(basehandlers.APIHandler):
    """Site-admin API for listing gate definitions and editing approvers."""

    def _build_gate_def_admin(
        self,
        gate_type: int,
        afd: approval_defs.GateInfo,
        gate_def: GateDef | None = None,
    ) -> GateDefAdmin:
        """Build a GateDefAdmin model for a single gate type."""
        if afd.approvers == approval_defs.IN_NDB:
            if gate_def is None:
                gate_def = GateDef.get_gate_def(gate_type)
            approvers = list(gate_def.approvers)
            is_editable = True
            approvers_url = None
            rotation_url = gate_def.rotation_url
        else:
            approvers = approval_defs.get_approvers(gate_type)
            is_editable = False
            approvers_url = (
                afd.approvers if isinstance(afd.approvers, str) else None
            )
            rotation_url = None

        return GateDefAdmin(
            gate_type=gate_type,
            name=afd.name,
            description=afd.description,
            team_name=afd.team_name,
            rule=afd.rule,
            approvers=approvers,
            is_editable=is_editable,
            approvers_url=approvers_url,
            escalation_email=afd.escalation_email,
            rotation_url=rotation_url,
            slo_initial_response=afd.slo_initial_response,
            slo_resolve=afd.slo_resolve,
        )

    @permissions.require_admin_site
    def do_get(self, **kwargs):
        """Return all gate definitions and their current approvers."""
        if kwargs.get('id') is not None:
            self.abort(405, msg='Method not allowed')
        gates = [
            self._build_gate_def_admin(gate_type, afd)
            for gate_type, afd in approval_defs.APPROVAL_FIELDS_BY_ID.items()
        ]
        return GetGateDefsResponse(gates=gates).to_dict()

    @permissions.require_admin_site
    def do_patch(self, **kwargs):
        """Update the list of approvers for an editable gate definition."""
        gate_type = kwargs.get('id')
        if (
            gate_type is None
            or gate_type not in approval_defs.APPROVAL_FIELDS_BY_ID
        ):
            self.abort(404, msg=f'Gate type {gate_type} not found')

        afd = approval_defs.APPROVAL_FIELDS_BY_ID[gate_type]
        if afd.approvers != approval_defs.IN_NDB:
            self.abort(
                400,
                msg='Approvers for this gate are managed externally and cannot be edited',
            )

        raw_approvers = self.get_param('approvers', required=True)
        if not isinstance(raw_approvers, list):
            self.abort(400, msg='approvers must be a list of email addresses')

        cleaned_approvers: list[str] = []
        seen: set[str] = set()
        for entry in raw_approvers:
            if not isinstance(entry, str):
                self.abort(
                    400, msg='Each approver must be an email address string'
                )
            email = entry.strip()
            if not email:
                continue
            if not _is_valid_email(email):
                self.abort(400, msg=f'Invalid email address: {email}')
            if email not in seen:
                seen.add(email)
                cleaned_approvers.append(email)

        gate_def = GateDef.get_gate_def(gate_type)
        gate_def.approvers = cleaned_approvers
        gate_def.put()

        cache_key = '%s|%s' % (approval_defs.APPROVERS_CACHE_KEY, gate_type)
        rediscache.delete(cache_key)

        return self._build_gate_def_admin(
            gate_type, afd, gate_def=gate_def
        ).to_dict()
