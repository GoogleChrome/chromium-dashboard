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
from typing import Optional
import flask
from google.cloud import ndb  # type: ignore

import settings
from framework.users import User
from internals import feature_helpers
from internals.core_models import FeatureEntry
from internals.review_models import Gate
from internals.user_models import AppUser


def can_admin_site(user: User) -> bool:
  """Return True if the current user is allowed to administer the site."""
  # A user is an admin if they have an AppUser entity that has is_admin set.
  if user:
    app_user = AppUser.get_app_user(user.email())
    if app_user is not None:
      return app_user.is_admin

  return False

def is_google_or_chromium_account(user: User) -> bool:
  """Return True if the current uses a @chromium.org or @google.com email."""
  # A user is an admin if they have an AppUser entity that has is_admin set.
  if user:
    return user.email().endswith(('@chromium.org', '@google.com'))
  return False

def can_view_feature(unused_user, unused_feature) -> bool:
  """Return True if the user is allowed to view the given feature."""
  # Note, for now there are no private features, only unlisted ones.
  return True


def can_create_feature(user: User) -> bool:
  """Return True if the user is allowed to create features."""
  if not user:
    return False

  if can_admin_site(user):
    return True

  # TODO(jrobbins): generalize this.
  if user.email().endswith(('@chromium.org', '@google.com')):
    return True

  app_user = AppUser.get_app_user(user.email())
  if app_user:
    return True

  return False


def can_comment(user: User) -> bool:
  """Return true if the user is allowed to post review comments."""
  return can_create_feature(user)


def can_edit_any_feature(user: User) -> bool:
  """Return True if the user is allowed to edit all features."""
  if not user:
    return False
  app_user = AppUser.get_app_user(user.email())
  if not app_user:
    return False

  # Site editors or admins should be able to edit any feature.
  return app_user.is_admin or app_user.is_site_editor


def feature_edit_list(user: User) -> list[int]:
  """Return a list of features the current user can edit"""
  if not user:
    return []

  # If the user can edit any feature, we don't need the full list.
  # We can just assume they will have edit access to all features.
  if can_edit_any_feature(user):
    return []

  # Query features to find which can be edited.
  editable_feature_keys: list[ndb.Key] = feature_helpers.get_all(
      filterby=('can_edit', user.email()), keys_only=True)
  # Return a list of unique ids of features that can be edited.
  return list(set([fk.integer_id() for fk in editable_feature_keys]))


def can_edit_feature(user: User, feature_id: int) -> bool:
  """Return True if the user is allowed to edit the given feature."""
# If the user can edit any feature, they can edit this feature.
  if can_edit_any_feature(user):
    return True

  if not feature_id or not user:
    return False

  # Load feature directly from NDB so as to never get a stale cached copy.
  feature: Optional[FeatureEntry] = FeatureEntry.get_by_id(feature_id)
  if not feature:
    return False

  email = user.email()
  # Check if the user is an owner, editor, spec mentor, or creator
  # for this feature. If yes, the feature can be edited.
  return (
      email in feature.owner_emails or
      email in feature.editor_emails or
      (feature.spec_mentor_emails and email in feature.spec_mentor_emails) or
      email == feature.creator_email)


def can_review_gate(
    user: User, feature: FeatureEntry, gate: Gate | None,
    approvers: list[str]) -> bool:
  """Return True if the user is allowed to review the given gate."""
  if not can_view_feature(user, feature):
    return False
  if can_admin_site(user):
    return True
  is_approver = user is not None and user.email() in approvers
  is_assigned = (user is not None and gate is not None and
                 user.email() in gate.assignee_emails)
  return is_approver or is_assigned


def _maybe_redirect_to_login(handler_obj) -> flask.Response | dict:
  # Don't redirect if the handler is not an UI page (it is an API handler).
  if not hasattr(handler_obj, 'get_common_data'):
      return {}

  # Don't redirect if this is a UI page and we already redirected.
  common_data = handler_obj.get_common_data()
  if ('current_path' in common_data and
      'loginStatus=False' in common_data['current_path']):
    return {}

  return handler_obj.redirect(settings.LOGIN_PAGE_URL)


def _reject_or_proceed(
    handler_obj, handler_method, handler_args, handler_kwargs,
    perm_function):
  """Redirect, abort(403), or call handler_method."""
  user = handler_obj.get_current_user()
  req = handler_obj.request

  # Give the user a chance to sign in
  if not user and req.method == 'GET':
    redirect = _maybe_redirect_to_login(handler_obj)
    if redirect:
      return redirect

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


def validate_feature_create_permission(handler_obj):
  """Check if user has permission to create feature and abort if not."""
  user = handler_obj.get_current_user()
  req = handler_obj.request

  # Give the user a chance to sign in
  if not user and req.method == 'GET':
    redirect = _maybe_redirect_to_login(handler_obj)
    if redirect:
      return redirect

  # Respond with 403 if user does not have create permission for feature.
  if not can_create_feature(user):
    handler_obj.abort(403)


def validate_feature_edit_permission(
    handler_obj, feature_id: int) -> flask.Response | dict:
  """Check if user has permission to edit feature and abort if not."""
  user = handler_obj.get_current_user()
  req = handler_obj.request

  # Give the user a chance to sign in
  if not user and req.method == 'GET':
    redirect = _maybe_redirect_to_login(handler_obj)
    if redirect:
      return redirect

  # Respond with 404 if feature is not found.
  # Load feature directly from NDB so as to never get a stale cached copy.
  if FeatureEntry.get_by_id(int(feature_id)) is None:
    handler_obj.abort(404, msg='Feature not found')

  # Respond with 403 if user does not have edit permission for feature.
  if not can_edit_feature(user, feature_id):
    handler_obj.abort(403, msg='User cannot edit feature %r' % feature_id)

  return {}
