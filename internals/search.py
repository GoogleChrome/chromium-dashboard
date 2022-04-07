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

import datetime
import logging
import re

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


def parse_query_value(val_str):
  """Return a python object that can be used as a value in an NDB query."""
  if val_str == 'true':
    return True
  if val_str == 'false':
    return False

  try:
    return datetime.datetime.strptime(val_str, '%Y-%m-%d')
  except ValueError:
    logging.info('%r is not a date' % val_str)
    pass

  try:
    return int(val_str)
  except ValueError:
    pass

  return val_str


def process_queriable_field(field_name, operator, val_str):
  """Return a list of feature IDs or a promise for keys."""
  val = parse_query_value(val_str)
  logging.info('trying %r %r %r', field_name, operator, val)
  promise = models.Feature.single_field_query_async(field_name, operator, val)
  return promise


# A full-text query term consisting of a single word or quoted string.
# The single word case cannot contain an operator.
# We do not support any kind of escaped quotes in quoted strings.
TEXT_PATTERN = r'[^":=><! ]+|"[^S]+"'
# The JSON field name of a feature field.
FIELD_NAME_PATTERN = r'[-.a-z_0-9]+'
# Comparison operators.
OPERATORS_PATTERN = r':|=|<=|<|>=|>|!='
# A value that a feature field can be compared against.  It can be
# a single word or a quoted string.
VALUE_PATTERN = r'[^" ]+|"[^"]+"'

# Overall, a query term can be either a structured term or a full-text term.
# Structured terms look like: FIELD OPERATOR VALUE.
# Full-text terms look like: SINGLE_WORD, or like: "QUOTED STRING".
TERM_RE = re.compile(
    '(?P<field>%s)(?P<op>%s)(?P<val>%s)\s+|(?P<textterm>%s)\s+' % (
        FIELD_NAME_PATTERN, OPERATORS_PATTERN, VALUE_PATTERN,
        TEXT_PATTERN),
    re.I)


def process_query_term(field_name, op_str, val_str):
  """Parse and run a user-supplied query, if we can handle it."""
  query_term = field_name + op_str + val_str
  if query_term == 'pending-approval-by:me':
    return process_pending_approval_me_query()
  if query_term == 'starred-by:me':
    return process_starred_me_query()
  if query_term == 'owner:me':
    return process_owner_me_query()
  if query_term == 'is:recently-reviewed':
    return process_recent_reviews_query()

  if val_str.startswith('"') and val_str.endswith('"'):
    val_str = val_str[1:-1]
  return process_queriable_field(field_name, op_str, val_str)

  logging.warning('Unexpected query: %r', query_term)
  return []


def _resolve_promise_to_id_list(promise):
  """Given an object that might be a promise or an ID list, return IDs."""
  if type(promise) == list:
    logging.info('got list %r', promise)
    return promise  # Which is actually an ID list.
  else:
    key_list = promise.get_result()
    id_list = [k.integer_id() for k in key_list]
    logging.info('got promise that yielded %r', id_list)
    return id_list


def process_query(user_query, show_unlisted=False):
  """Parse the user's query, run it, and return a list of features."""
  # 1. Parse the user query into terms.
  feature_id_futures = []
  terms = TERM_RE.findall(user_query + ' ')[:MAX_TERMS] or []

  # 2. Create parallel queries for each term.  Each yields a future.
  logging.info('creating parallel queries for %r', terms)
  for field_name, op_str, val_str, textterm in terms:
    if textterm:
      logging.warning('Full-text term %r not supported yet', textterm)
    future = process_query_term(field_name, op_str, val_str)
    feature_id_futures.append(future)

  # 3. Get the result of each future and combine them into a result ID set.
  logging.info('now waiting on futures')
  result_id_set = None
  for future in feature_id_futures:
    feature_ids = _resolve_promise_to_id_list(future)
    if result_id_set is None:
      logging.info('first term yields %r', feature_ids)
      result_id_set = set(feature_ids)
    else:
      logging.info('combining result so far with %r', feature_ids)
      result_id_set.intersection_update(feature_ids)

  # 4. Fetch the actual issues that have those IDs in the sorted results.
  feature_list = models.Feature.get_by_ids(list(result_id_set or []))

  # 5. Filter by permissions.
  allowed_feature_list = [
      f for f in feature_list
      if show_unlisted or not f['unlisted']]

  logging.info('allowed_feature_list is %r', allowed_feature_list)
  # 6. Sort.
  # TODO(jrobbins): sort by user-specified field.  And paginate.
  sorted_allowed_feature_list = sorted(
      allowed_feature_list, key=lambda f: f['created']['when'])

  return allowed_feature_list
