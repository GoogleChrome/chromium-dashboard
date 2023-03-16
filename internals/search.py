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
from internals.core_models import FeatureEntry
from internals.review_models import Gate
from internals import approval_defs
from internals import core_enums
from internals import feature_helpers
from internals import notifier
from internals import search_queries
from internals import search_fulltext

MAX_TERMS = 6
DEFAULT_RESULTS_PER_PAGE = 100


def process_pending_approval_me_query() -> list[int]:
  """Return a list of features needing approval by current user."""
  user = users.get_current_user()
  if not user:
    return []

  approvable_gate_types = approval_defs.fields_approvable_by(user)
  if not approvable_gate_types:
    return []
  query = Gate.query(
      Gate.state.IN(Gate.PENDING_STATES),
      Gate.gate_type.IN(approvable_gate_types))
  future_feature_ids = query.fetch_async(projection=['feature_id'])
  return future_feature_ids


def process_starred_me_query() -> list[int]:
  """Return a list of features starred by the current user."""
  user = users.get_current_user()
  if not user:
    return []

  feature_ids = notifier.FeatureStar.get_user_stars(user.email())
  return feature_ids


def process_recent_reviews_query() -> list[int]:
  """Return features that were reviewed recently."""
  query = Gate.query(
      Gate.state.IN(Gate.FINAL_STATES))
  future_feature_ids = query.fetch_async(projection=['feature_id'], limit=40)
  return future_feature_ids


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
# Logical operators.
# TODO(kyleju): support 'OR' logic
LOGICAL_OPERATORS_PATTERN = r'OR\s+|-'

# Overall, a query term can be either a structured term or a full-text term.
# Structured terms look like: FIELD OPERATOR VALUE.
# Full-text terms look like: SINGLE_WORD, or like: "QUOTED STRING".
TERM_RE = re.compile(
    '(?P<logical>%s)?(?:(?P<field>%s)(?P<op>%s)(?P<val>%s)|(?P<textterm>%s))\s+' % (
        LOGICAL_OPERATORS_PATTERN, FIELD_NAME_PATTERN, OPERATORS_PATTERN,
        VALUE_PATTERN, TEXT_PATTERN),
    re.I)

SIMPLE_QUERY_TERMS = ['pending-approval-by:me', 'starred-by:me',
                      'is:recently-reviewed', 'owner:me', 'editor:me', 'can_edit:me', 'cc:me']


def process_query_term(
    is_negation: bool, field_name: str, op_str: str, val_str: str) -> Future:
  """Parse and run a user-supplied query, if we can handle it."""
  if is_negation:
    op_str = search_queries.negate_operator(op_str)

  if val_str.startswith('"') and val_str.endswith('"'):
    val_str = val_str[1:-1]

  val = parse_query_value(val_str)
  logging.info('trying %r %r %r', field_name, op_str, val)

  future = search_queries.single_field_query_async(
      field_name, op_str, val)
  return future


def process_predefined_query_term(
    field_name: str, op_str: str, val_str: str) -> Future:
  """Parse and run a simple query term."""
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

  return None


def is_predefined_query_term(
  field_name: str, op_str: str, val_str: str) -> bool:
  """Determine if a query is a simple query term."""
  query_term = field_name + op_str + val_str
  return query_term in SIMPLE_QUERY_TERMS


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
    show_unlisted=False, show_deleted=False, show_enterprise=False,
    start=0, num=DEFAULT_RESULTS_PER_PAGE) -> tuple[list[dict[str, Any]], int]:
  """Parse the user's query, run it, and return a list of features."""
  # 1a. Parse the user query into terms.
  terms = TERM_RE.findall(user_query + ' ')[:MAX_TERMS] or []

  # 1b. Add permission and search scope terms.
  permission_terms = []
  if not show_deleted:
    permission_terms.append(('', 'deleted', '=', 'false', None))
  # TODO(jrobbins): include unlisted features that the user is allowed to view.
  if not show_unlisted:
    permission_terms.append(('', 'unlisted', '=', 'false', None))
  if not show_enterprise:
    permission_terms.append(
        ('', 'feature_type', '<=',
         str(core_enums.FEATURE_TYPE_DEPRECATION_ID), None))

  # 1c. Parse the sort directive.
  sort_spec = sort_spec or '-created.when'

  # 2a. Create parallel queries for each term.  Each yields a future.
  logging.info('creating parallel queries for %r', terms)
  feature_id_future_ops = create_future_operations_from_queries(terms)

  # 2b. Create parallel queries for each permission queries.
  logging.info('creating parallel queries for %r', permission_terms)
  permissions_future_ops = create_future_operations_from_queries(
      permission_terms)

  # 2c. Create a parallel query for total sort order.
  total_order_promise = search_queries.total_order_query_async(sort_spec)

  # 3. Get the result of each future and combine them into a result ID set.
  logging.info('now waiting on futures')

  # 3a. Process user query: negation, AND, and OR.
  feature_id_future_ops = process_negation_operations(feature_id_future_ops)
  query_clauses = process_and_operations(feature_id_future_ops)
  result_id_set = process_or_operations(query_clauses)

  # 3b. Process all permission ops, then interesect to apply permisisons.
  permission_clauses = process_and_operations(permissions_future_ops)
  permission_ids = process_or_operations(permission_clauses)
  result_id_set.intersection_update(permission_ids)

  result_id_list = list(result_id_set)
  total_count = len(result_id_list)

  # 4. Finish getting the total sort order. Then, sort the IDs according
  # to their position in the complete sorted list.
  total_order_ids = _resolve_promise_to_id_list(total_order_promise)
  sorted_id_list = _sort_by_total_order(result_id_list, total_order_ids)

  # 5. Paginate
  paginated_id_list = sorted_id_list[start : start + num]

  # 6. Fetch the actual issues that have those IDs in the sorted results.
  # TODO(jrobbins): This still returns Feature objects.
  features_on_page = feature_helpers.get_by_ids(paginated_id_list)

  logging.info('features_on_page is %r', features_on_page)
  return features_on_page, total_count


def create_future_operations_from_queries(terms):
  """Create parallel queries for each term. Each yields a future operation"""
  feature_id_future_ops = []
  for logical_op, field_name, op_str, val_str, textterm in terms:
    is_negation = (logical_op.strip() == '-')
    is_normal_query = False
    if textterm:
      future = search_fulltext.search_fulltext(textterm)
    elif is_predefined_query_term(field_name, op_str, val_str):
      future = process_predefined_query_term(field_name, op_str, val_str)
    else:
      future = process_query_term(is_negation, field_name, op_str, val_str)
      is_normal_query = True

    if future is None:
      continue

    if is_negation and is_normal_query:
      feature_id_future_ops.append(('', future))
    else:
      feature_id_future_ops.append((logical_op.strip(), future))

  return feature_id_future_ops


def process_or_operations(or_clauses):
  """Process OR operations for all id sets."""
  # If there were no conditions, all features match.
  if not or_clauses:
    return fetch_all_feature_ids_set()

  result_id_set = set()
  for id_set in or_clauses:
    result_id_set.update(id_set)
  return result_id_set


def process_and_operations(feature_id_future_ops):
  """ Process all AND operations in between OR clauses."""
  or_clauses = []

  current_result_set = None
  for logical_op, future in feature_id_future_ops:
    if logical_op == 'OR' and current_result_set is not None:
      # Add the proceeding AND result
      or_clauses.append(current_result_set)
      current_result_set = None

    if type(future) == set:
      feature_ids = future
    else:
      feature_ids = _resolve_promise_to_id_list(future)

    if current_result_set is None:
      logging.info('first term yields %r', feature_ids)
      current_result_set = set(feature_ids)
      continue

    logging.info('combining result so far with %r', feature_ids)
    current_result_set.intersection_update(feature_ids)

  if current_result_set is not None:
    or_clauses.append(current_result_set)
  return or_clauses


def process_negation_operations(feature_id_future_ops):
  """ Turn all negation operations into AND operations."""
  new_future_ops = []
  all_ids_set = None
  for logical_op, future in feature_id_future_ops:
    if logical_op != '-':
      # Skip all non-negation operations.
      new_future_ops.append((logical_op, future))
      continue

    if all_ids_set is None:
      all_ids_set = fetch_all_feature_ids_set()

    feature_ids = _resolve_promise_to_id_list(future)
    result_set = all_ids_set.difference(feature_ids)
    new_future_ops.append(('', result_set))

  return new_future_ops


def fetch_all_feature_ids_set():
  """Fetch all FeatureEntry ids. """
  all_feature_keys = FeatureEntry.query().fetch(keys_only=True)
  feature_ids_set = set(key.integer_id() for key in all_feature_keys)
  return feature_ids_set
