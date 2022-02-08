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
MAX_TERMS = 6

def _get_referenced_feature_ids(approvals, reverse=False):
  """Retrieve the features being approved, withuot duplicates."""
  logging.info('approvals is %r', [(a.feature_id, a.state) for a in approvals])
  feature_ids = []
  seen = set()
  for appr in approvals:
    if appr.feature_id not in seen:
      seen.add(appr.feature_id)
      feature_ids.append(appr.feature_id)

  return feature_ids


def process_pending_approval_me_query():
  """Return a list of features needing approval by current user."""
  user = users.get_current_user()
  if not user:
    return []

  approvable_fields_ids = approval_defs.fields_approvable_by(user)
  pending_approvals = models.Approval.get_approvals(states=PENDING_STATES)
  pending_approvals = [pa for pa in pending_approvals
                       if pa.field_id in approvable_fields_ids]

  feature_ids = _get_referenced_feature_ids(pending_approvals)
  return feature_ids


def process_starred_me_query():
  """Return a list of features starred by the current user."""
  user = users.get_current_user()
  if not user:
    return []

  feature_ids = notifier.FeatureStar.get_user_stars(user.email())
  return feature_ids


def process_owner_me_query():
  """Return features that the current user owns."""
  user = users.get_current_user()
  if not user:
    return []
  features = models.Feature.get_all(filterby=('owner', user.email()))
  feature_ids = [f['id'] for f in features]
  return feature_ids


def process_recent_reviews_query():
  """Return features that were reviewed recently."""
  user = users.get_current_user()
  if not user:
    return []

  recent_approvals = models.Approval.get_approvals(
      states=FINAL_STATES, order=-models.Approval.set_on, limit=40)

  feature_ids = _get_referenced_feature_ids(recent_approvals, reverse=True)
  return feature_ids


def process_queriable_field(field_name, operator, val_str):
  if val_str == 'true':
    val = True
  elif val_str == 'false':
    val = False
  else:
    try:
      val = int(val_str)
    except ValueError:
      val = val_str

  logging.info('trying %r %r %r', field_name, operator, val)
  promise = models.Feature.single_field_query_async(field_name, operator, val)
  if type(promise) == list:
    return promise
  else:
    return promise.get_result()  # TODO: in parallel

def process_query_term(query_term):
  """Parse and run a user-supplied query, if we can handle it."""
  # TODO(jrobbins): Replace this with a more general approach.
  if query_term == 'pending-approval-by:me':
    return process_pending_approval_me_query()
  if query_term == 'starred-by:me':
    return process_starred_me_query()
  if query_term == 'owner:me':
    return process_owner_me_query()
  if query_term == 'is:recently-reviewed':
    return process_recent_reviews_query()

  if '=' in query_term:
    field_name, val_str = query_term.split('=', 1)
    return process_queriable_field(field_name, '=', val_str)

  logging.warning('Unexpected query: %r', query_term)
  return []


def process_query(user_query):
  """xxx"""
  feature_id_futures = []
  terms = user_query.split()[:MAX_TERMS]
  logging.info('creating parallel queries for %r', terms)
  for term in terms:
    future = process_query_term(term)
    feature_id_futures.append(future)
  logging.info('now waiting on futures')
  result_id_set = None
  for future in feature_id_futures:
    feature_ids = future  # TODO use futures and .get_result()
    term_id_set = set(feature_ids)
    if result_id_set is None:
      result_id_set = set(feature_ids)
    else:
      result_id_set.intersection_update(feature_ids)

  # TODO: sort by user-specified field
  sorted_result_ids = sorted(result_id_set)
  features = models.Feature.get_by_ids(sorted_result_ids)
  return features
