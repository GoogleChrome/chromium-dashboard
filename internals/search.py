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
from typing import Any, Union

from google.cloud.ndb import Key
from google.cloud.ndb.tasklets import Future  # for type checking only

from framework import users
from framework import utils
from internals import approval_defs
from internals import core_models
from internals import feature_helpers
from internals import notifier
from internals import review_models
from internals import search_queries
from internals import search_fulltext

MAX_TERMS = 6
DEFAULT_RESULTS_PER_PAGE = 100


def _get_referenced_feature_ids(
    approvals: list[review_models.Approval], reverse=False) -> list[int]:
  """Retrieve the features being approved, withuot duplicates."""
  logging.info('approvals is %r', [(a.feature_id, a.state) for a in approvals])
  feature_ids = utils.dedupe(a.feature_id for a in approvals)

  return feature_ids


def process_pending_approval_me_query() -> list[int]:
  """Return a list of features needing approval by current user."""
  user = users.get_current_user()
  if not user:
    return []

  approvable_fields_ids = approval_defs.fields_approvable_by(user)
  pending_approvals = review_models.Approval.get_approvals(
      states=[review_models.Approval.REVIEW_REQUESTED])
  pending_approvals = [pa for pa in pending_approvals
                       if pa.field_id in approvable_fields_ids]

  feature_ids = _get_referenced_feature_ids(pending_approvals)
  return feature_ids


def process_starred_me_query() -> list[int]:
  """Return a list of features starred by the current user."""
  user = users.get_current_user()
  if not user:
    return []

  feature_ids = notifier.FeatureStar.get_user_stars(user.email())
  return feature_ids


def process_recent_reviews_query() -> list[int]:
  """Return features that were reviewed recently."""
  user = users.get_current_user()
  if not user:
    return []

  recent_approvals = review_models.Approval.get_approvals(
      states=review_models.Approval.FINAL_STATES, limit=40)

  feature_ids = _get_referenced_feature_ids(recent_approvals, reverse=True)
  return feature_ids


def parse_query_value(val_str: str) -> Union[bool, datetime.datetime, int, str]:
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


def process_queriable_field(
    field_name: str, operator: str, val_str: str
    ) -> Future:
  """Return a list of feature IDs or a promise for keys."""
  val = parse_query_value(val_str)
  logging.info('trying %r %r %r', field_name, operator, val)
  future = search_queries.single_field_query_async(field_name, operator, val)
  return future


# A full-text query term consisting of a single word or quoted string.
# The single word case cannot contain an operator.
# We do not support any kind of escaped quotes in quoted strings.
TEXT_PATTERN = r'[^":=><! ]+|"[^"]+"'
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


def process_query_term(
    field_name: str, op_str: str, val_str: str) -> Future:
  """Parse and run a user-supplied query, if we can handle it."""
  query_term = field_name + op_str + val_str
  if query_term == 'pending-approval-by:me':
    return process_pending_approval_me_query()
  if query_term == 'starred-by:me':
    return process_starred_me_query()
  if query_term == 'is:recently-reviewed':
    return process_recent_reviews_query()

  if query_term == 'owner:me':
    return search_queries.handle_me_query_async('owner')
  if query_term == 'editor:me':
    return search_queries.handle_me_query_async('editor')
  if query_term == 'can_edit:me':
    return search_queries.handle_can_edit_me_query_async()
  if query_term == 'cc:me':
    return search_queries.handle_me_query_async('cc')

  if val_str.startswith('"') and val_str.endswith('"'):
    val_str = val_str[1:-1]
  return process_queriable_field(field_name, op_str, val_str)


def _resolve_promise_to_id_list(
    list_or_future: Union[list, Future]) -> list[int]:
  """Given an object that might be a future or an ID list, return IDs."""
  if type(list_or_future) == list:
    logging.info('got list %r', list_or_future)
    return list_or_future  # Which is actually an ID list.
  else:
    future: Future = list_or_future
    key_or_projection_list = future.get_result()
    if key_or_projection_list and isinstance(key_or_projection_list[0], Key):
      id_list = [k.integer_id() for k in key_or_projection_list]
      logging.info('got key future that yielded %r', id_list)
    else:
      id_list = [proj.feature_id for proj in key_or_projection_list]
      logging.info('got projection future that yielded %r', id_list)

    return id_list


def _sort_by_total_order(
    result_id_list: list[int], total_order_ids: list[int]) -> list[int]:
  """Sort the result_ids according to their position in the total order.

  If some result ID is not present in the total order, use the feature ID
  value itself as the sorting value, which will effectively put those
  features at the end of the list in order of creation.
  """
  total_order_dict = {f_id: idx for idx, f_id in enumerate(total_order_ids)}
  sorted_id_list = sorted(
      result_id_list,
      key=lambda f_id: total_order_dict.get(f_id, f_id))
  return sorted_id_list


def process_query(
    user_query: str, sort_spec: str = None,
    show_unlisted=False, show_deleted=False,
    start=0, num=DEFAULT_RESULTS_PER_PAGE) -> tuple[list[dict[str, Any]], int]:
  """Parse the user's query, run it, and return a list of features."""
  # 1a. Parse the user query into terms.  And, add permission terms.
  feature_id_futures = []
  terms = TERM_RE.findall(user_query + ' ')[:MAX_TERMS] or []
  if not show_deleted:
    terms.append(('deleted', '=', 'false', None))
  # TODO(jrobbins): include unlisted features that the user is allowed to view.
  if not show_unlisted:
    terms.append(('unlisted', '=', 'false', None))
  # 1b. Parse the sort directive.
  sort_spec = sort_spec or '-created.when'

  # 2a. Create parallel queries for each term.  Each yields a future.
  logging.info('creating parallel queries for %r', terms)
  for field_name, op_str, val_str, textterm in terms:
    if textterm:
      future = search_fulltext.search_fulltext(textterm)
    else:
      future = process_query_term(field_name, op_str, val_str)
    if future is not None:
      feature_id_futures.append(future)
  # 2b. Create a parallel query for total sort order.
  total_order_promise = search_queries.total_order_query_async(sort_spec)

  # 3a. Get the result of each future and combine them into a result ID set.
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
  result_id_list = list(result_id_set or [])
  total_count = len(result_id_list)
  # 3b. Finish getting the total sort order.
  total_order_ids = _resolve_promise_to_id_list(total_order_promise)

  # 4. Sort the IDs according to their position in the complete sorted list.
  sorted_id_list = _sort_by_total_order(result_id_list, total_order_ids)

  # 5. Paginate
  paginated_id_list = sorted_id_list[start : start + num]

  # 6. Fetch the actual issues that have those IDs in the sorted results.
  # TODO(jrobbins): This still returns Feature objects.
  features_on_page = feature_helpers.get_by_ids(paginated_id_list)

  logging.info('features_on_page is %r', features_on_page)
  return features_on_page, total_count
