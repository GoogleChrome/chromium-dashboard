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
import flask

import settings
from framework import users
from internals import models


def can_admin_site(user):
  """Return True if the current user is allowed to administer the site."""
  # A user is an admin if they have an AppUser entity that has is_admin set.
  if user:
    app_user = models.AppUser.get_app_user(user.email())
    if app_user is not None:
      return app_user.is_admin

  return False


def can_view_feature(unused_user, unused_feature):
  """Return True if the user is allowed to view the given feature."""
  # Note, for now there are no private features, only unlisted ones.
  return True


def can_create_feature(user):
  """Return True if the user is allowed to create features."""
  if not user:
    return False

  if can_admin_site(user):
    return True

  # TODO(jrobbins): generalize this.
  if user.email().endswith(('@chromium.org', '@google.com')):
    return True

  query = models.AppUser.query(models.AppUser.email == user.email())
  found_user = query.get(keys_only=True)
  if found_user is not None:
    return True

  return False


def can_edit_any_feature(user):
  """Return True if the user is allowed to edit features."""
  return can_create_feature(user)


def can_edit_feature(user, feature):
  """Return True if the user is allowed to edit the given feature."""
  # TODO(jrobbins): make this per-feature
  if not can_view_feature(user, feature):
    return False
  return can_edit_any_feature(user)


def strict_can_edit_feature(user, feature_id):
  """Return True if the user is allowed to edit the given feature."""
  if not feature_id or not user:
    return False

  # If the user is an admin or site editor, they can edit this feature.
  app_user = models.AppUser.get_app_user(user.email())
  if app_user is not None and (app_user.is_admin or app_user.is_admin):
    return True

  feature = models.Feature.get_by_id(feature_id)
  if not feature:
    return False
  
  email = user.email()
  # Check if the user is an owner, editor, or creator for this feature.
  # If yes, the feature can be edited.
  return (email in feature.owner or
          email in feature.editors or email == feature.creator)


def can_approve_feature(user, feature, approvers):
  """Return True if the user is allowed to approve the given feature."""
  # TODO(jrobbins): make this per-feature
  if not can_view_feature(user, feature):
    return False
  if can_admin_site(user):
    return True
  is_approver = user is not None and user.email() in approvers
  return is_approver


def _reject_or_proceed(
    handler_obj, handler_method, handler_args, handler_kwargs,
    perm_function):
  """Redirect, abort(403), or call handler_method."""
  user = handler_obj.get_current_user()
  req = handler_obj.request

  # Give the user a chance to sign in
  if not user and req.method == 'GET':
    return handler_obj.redirect(settings.LOGIN_PAGE_URL)

  if not perm_function(user):
    handler_obj.abort(403)
  else:
    return handler_method(handler_obj, *handler_args, **handler_kwargs)


def require_admin_site(handler):
  """Handler decorator to require the user can admin the site."""
  def check_login(self, *args, **kwargs):
    return _reject_or_proceed(
        self, handler, args, kwargs, can_admin_site)

  return check_login


def require_view_feature(handler):
  """Handler decorator to require the user can view the current feature."""
  # TODO(jrobbins): make this per-feature
  def check_login(self, *args, **kwargs):
    return _reject_or_proceed(
        self, handler, args, kwargs, can_view_feature)

  return check_login


def require_create_feature(handler):
  """Handler decorator to require the user can create a feature."""
  def check_login(self, *args, **kwargs):
    return _reject_or_proceed(
        self, handler, args, kwargs, can_create_feature)

  return check_login


def require_edit_feature(handler):
  """Handler decorator to require the user can edit the current feature."""
  # TODO(jrobbins): make this per-feature
  def check_login(self, *args, **kwargs):
    return _reject_or_proceed(
        self, handler, args, kwargs, can_edit_any_feature)

  return check_login
