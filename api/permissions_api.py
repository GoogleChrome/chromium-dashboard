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

import logging

from framework import basehandlers
from framework import permissions
from framework.users import User
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
      if not self.get_bool_arg('returnPairedUser'):
        user_data = self.get_all_perms(user)
      else:
        paired_user = self.find_paired_user(user)
        if paired_user:
          user_data = self.get_all_perms(paired_user)

    return {'user': user_data}

  def get_all_perms(self, user):
    """Return a dict of permissions for the given user."""
    logging.info('In get_all_perms')
    can_create_feature = permissions.can_create_feature(user)
    approvable_gate_types = sorted(
        approval_defs.fields_approvable_by(user))
    can_comment = permissions.can_comment(user)
    can_edit_all = permissions.can_edit_any_feature(user)
    is_admin = permissions.can_admin_site(user)
    editable_features = permissions.feature_edit_list(user)
    logging.info('got editable_features')

    return {
      'can_create_feature': can_create_feature,
      'approvable_gate_types': approvable_gate_types,
      'can_comment': can_comment,
      'can_edit_all': can_edit_all,
      'is_admin': is_admin,
      'email': user.email(),
      'editable_features': editable_features,
    }

  def find_paired_user(self, user):
    """If @google.com or @chromium.org, return the other one."""
    username, domain = user.email().split('@', 1)
    if domain == 'google.com':
      return User(email=username + '@chromium.org')
    if domain == 'chromium.org':
      return User(email=username + '@google.com')
    return None
