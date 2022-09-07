# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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

from google.cloud import ndb

from framework import basehandlers
from framework import permissions
from internals import user_models


def user_to_json_dict(user):
  return {
      'is_admin': user.is_admin,
      'is_site_editor': user.is_site_editor,
      'email': user.email,
      'id': user.key.integer_id(),
  }


class AccountsAPI(basehandlers.APIHandler):
  """User accounts store info on registered users."""

  # TODO(jrobbins): do_get

  @permissions.require_admin_site
  def do_post(self):
    """Process a request to create an account."""
    email = self.get_param('email', required=True)
    is_admin = self.get_bool_param('isAdmin')
    is_site_editor = self.get_bool_param('isSiteEditor')
    user = self.create_account(email, is_admin, is_site_editor)
    response_json = user_to_json_dict(user)
    return response_json

  def create_account(self, email, is_admin, is_site_editor):
    """Create and store a new account entity."""
    # Don't add a duplicate email address.
    user = user_models.AppUser.query(
        user_models.AppUser.email == email).get(keys_only=True)
    if not user:
      user = user_models.AppUser(email=str(email))
      user.is_admin = is_admin
      user.is_site_editor = is_site_editor
      user.put()
      return user
    else:
      self.abort(400, 'User already exists')

  # TODO(jrobbins): do_patch

  @permissions.require_admin_site
  def do_delete(self, account_id):
    """Process a request to delete the specified account."""
    if account_id:
      self.delete_account(account_id)
      return {'message': 'Done'}
    else:
      self.abort(400, msg='Account ID not specified')

  def delete_account(self, account_id):
    """Delete the specified account."""
    if account_id:
      found_user = user_models.AppUser.get_by_id(int(account_id))
      if found_user:
        found_user.delete()
      else:
        self.abort(404, msg='Specified account ID not found')
