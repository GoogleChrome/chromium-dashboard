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


from framework import basehandlers
from framework import permissions
from internals import approval_defs


class PermissionsAPI(basehandlers.APIHandler):
  """Permissions determine whether a user can create, approve,
  or edit any feature, or admin the site"""

  def do_get(self, **kwargs):
    """Return the permissions and the email of the user."""

    # No user data if not signed in
    user_data = None

    # get user permission data if signed in
    user = self.get_current_user()
    if user:
      field_id = approval_defs.ShipApproval.field_id
      approvers = approval_defs.get_approvers(field_id)
      user_data = {
        'can_create_feature': permissions.can_create_feature(user),
        'approvable_gate_types': sorted(
            approval_defs.fields_approvable_by(user)),
        'can_comment': permissions.can_comment(user),
        'can_edit_all': permissions.can_edit_any_feature(user),
        'is_admin': permissions.can_admin_site(user),
        'email': user.email(),
        'editable_features': permissions.feature_edit_list(user)
      }

    return {'user': user_data}
