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

from framework import users
from internals import approval_defs
from internals import models
from internals import notifier


PENDING_STATES = [
    models.Approval.REVIEW_REQUESTED, models.Approval.REVIEW_STARTED,
    models.Approval.NEED_INFO]
FINAL_STATES = [
    models.Approval.NA, models.Approval.APPROVED,
    models.Approval.NOT_APPROVED]

def _get_referenced_features(approvals, reverse=False):
  """Retrieve the features being approved, withuot duplicates."""
  logging.info('approvals is %r', [(a.feature_id, a.state) for a in approvals])
  feature_ids = []
  seen = set()
  for appr in approvals:
    if appr.feature_id not in seen:
      seen.add(appr.feature_id)
      feature_ids.append(appr.feature_id)

  features = models.Feature.get_by_ids(feature_ids)
  return features


def process_pending_approval_me_query():
  """Return a list of features needing approval by current user."""
  user = users.get_current_user()
  if not user:
    return []

  approvable_fields_ids = approval_defs.fields_approvable_by(user)
  pending_approvals = models.Approval.get_approvals(states=PENDING_STATES)
  pending_approvals = [pa for pa in pending_approvals
                       if pa.field_id in approvable_fields_ids]

  features = _get_referenced_features(pending_approvals)
  return features


def process_starred_me_query():
  """Return a list of features starred by the current user."""
  user = users.get_current_user()
  if not user:
    return []

  feature_ids = notifier.FeatureStar.get_user_stars(user.email())
  features = models.Feature.get_by_ids(feature_ids)
  return features


def process_owner_me_query():
  """Return features that the current user owns."""
  user = users.get_current_user()
  if not user:
    return []
  features = models.Feature.get_all(filterby=('owner', user.email()))
  return features


def process_recent_reviews_query():
  """Return features that were reviewed recently."""
  user = users.get_current_user()
  if not user:
    return []

  recent_approvals = models.Approval.get_approvals(
      states=FINAL_STATES, order=-models.Approval.set_on, limit=40)

  features = _get_referenced_features(recent_approvals, reverse=True)
  return features


def process_query(user_query):
  """Parse and run a user-supplied query, if we can handle it."""
  # TODO(jrobbins): Replace this with a more general approach.
  if user_query == 'pending-approval-by:me':
    return process_pending_approval_me_query()
  if user_query == 'starred-by:me':
    return process_starred_me_query()
  if user_query == 'owner:me':
    return process_owner_me_query()
  if user_query == 'is:recently-reviewed':
    return process_recent_reviews_query()

  logging.warning('Unexpected query: %r', user_query)
  return []
