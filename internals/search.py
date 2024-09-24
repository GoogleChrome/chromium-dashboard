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

import dataclasses
import datetime
import logging
import re
from typing import Any, Optional, Self, Union

from google.cloud.ndb import Key
from google.cloud.ndb.tasklets import Future  # for type checking only

from framework import rediscache
from framework import users
from internals import (
  approval_defs,
  core_enums,
  feature_helpers,
  fetchchannels,
  notifier,
  search_fulltext,
  search_queries,
)
from internals.core_models import FeatureEntry
from internals.review_models import (Gate, Vote)

MAX_TERMS = 6
DEFAULT_RESULTS_PER_PAGE = 100
SEARCH_CACHE_TTL = 60 * 60  # One hour

def process_exclude_deleted_unlisted_query() -> Future:
  """Return a future for all features, minus deleted and unlisted."""
  query = FeatureEntry.query(
      FeatureEntry.deleted == False,
      FeatureEntry.unlisted == False)
  future_feature_ids = query.fetch_async(keys_only=True)
  return future_feature_ids


def process_exclude_deleted_unlisted_enterprise_query() -> Future:
  """Return a future for all features, minus deleted, unlisted, enterprise."""
  query = FeatureEntry.query(
      FeatureEntry.deleted == False,
      FeatureEntry.unlisted == False,
      FeatureEntry.feature_type <= core_enums.FEATURE_TYPE_DEPRECATION_ID)
  future_feature_ids = query.fetch_async(keys_only=True)
  return future_feature_ids


def process_pending_approval_me_query() -> list[int] | Future:
  """Return a list of features needing approval by current user."""
  user = users.get_current_user()
  if not user:
    return []

  approvable_gate_types = approval_defs.fields_approvable_by(user)
  if not approvable_gate_types:
    logging.info('User has no approvable_gate_types')
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


def process_recent_reviews_query() -> list[int] | Future:
  """Return features that were reviewed recently."""
  query = Vote.query(Vote.state.IN(Gate.FINAL_STATES))
  query = query.filter(
      Vote.set_on > (datetime.datetime.now() - datetime.timedelta(days=90)))
  future_feature_ids = query.fetch_async(projection=['feature_id'])
  return future_feature_ids


@dataclasses.dataclass
class QueryContext:
  now: datetime.datetime
  current_stable_milestone: int

  @classmethod
  def current(cls) -> Self:
    """Computes the "current" QueryContext based on ambient information."""
    current_stable = None
    for version in fetchchannels.get_omaha_data()[0]['versions']:
      if version['channel'] == 'stable':
        current_stable = int(version['version'].split('.')[0])
        break
    assert current_stable is not None
    return cls(now=datetime.datetime.now(), current_stable_milestone=current_stable)


NOW_RELATIVE_DATE = re.compile(r'now(?:(?P<offset>[+-]\d+)(?P<unit>[dw]))?')
MILESTONE_RELATIVE_TO_STABLE = re.compile(r'current_stable(?P<offset>[+-]\d+)?')


def parse_query_value(val_str: str, context: QueryContext) -> search_queries.QueryValue:
  """Return a python object that can be used as a value in an NDB query."""

  if val_str.startswith('"') and val_str.endswith('"'):
    val_str = val_str[1:-1]

  if val_str == 'true':
    return True
  if val_str == 'false':
    return False

  now_relative_date = NOW_RELATIVE_DATE.fullmatch(val_str)
  if now_relative_date:
    try:
      unit = now_relative_date.group('unit')
      if unit is None:
        # Value was just a literal "now".
        return context.now
      offset = int(now_relative_date.group('offset'))
      if unit == 'd':
        return context.now + datetime.timedelta(days=offset)
      if unit == 'w':
        return context.now + datetime.timedelta(weeks=offset)
    except OverflowError:
      pass
    # Otherwise, treat the value as a literal string.

  try:
    return datetime.datetime.strptime(val_str, '%Y-%m-%d')
  except ValueError:
    logging.info('%r is not a date' % val_str)
    pass

  milestone_relative_to_stable = MILESTONE_RELATIVE_TO_STABLE.fullmatch(val_str)
  if milestone_relative_to_stable:
    result = context.current_stable_milestone
    offset_str = milestone_relative_to_stable.group('offset')
    if offset_str:
      result += int(offset_str)
    return result

  try:
    return int(val_str)
  except ValueError:
    pass

  return val_str


def parse_query_value_interval(
  val_str: str, context: QueryContext
) -> search_queries.QueryValue | search_queries.Interval[search_queries.QueryValue]:
  """Return a value or interval of values that can be used in an NDB query."""
  try_interval = val_str.split('..')
  if len(try_interval) == 2:
    return search_queries.Interval(
      parse_query_value(try_interval[0], context),
      parse_query_value(try_interval[1], context),
    )
  return parse_query_value(val_str, context)


def parse_query_value_list(
  vals_str: str, context: QueryContext
) -> list[
  search_queries.QueryValue | search_queries.Interval[search_queries.QueryValue]
]:
  """Return a list of values that can be used in an NDB query."""
  return [parse_query_value_interval(part, context) for part in vals_str.split(',')]


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
VALUE_PATTERN = r'(?:[^", .]|\.[^", .])+|"[^"]+"'
VALUES_PATTERN = (
  rf'(?:{VALUE_PATTERN})(?:\.\.(?:{VALUE_PATTERN})|(?:,(?:{VALUE_PATTERN}))*)'
)
# Logical operators.
LOGICAL_OPERATORS_PATTERN = r'OR\s+|-'

# Overall, a query term can be either a structured term or a full-text term.
# Structured terms look like: FIELD OPERATOR VALUE.
# Full-text terms look like: SINGLE_WORD, or like: "QUOTED STRING".
TERM_RE = re.compile(
    '(?P<logical>%s)?(?:(?P<field>%s)(?P<op>%s)(?P<val>%s)|(?P<textterm>%s))\s+' % (
        LOGICAL_OPERATORS_PATTERN, FIELD_NAME_PATTERN, OPERATORS_PATTERN,
        VALUES_PATTERN, TEXT_PATTERN),
    re.I)

SIMPLE_QUERY_TERMS = [
    'deleted_unlisted=false', 'deleted_unlisted_enterprise=false',
    'pending-approval-by:me', 'starred-by:me',
    'is:recently-reviewed', 'owner:me', 'editor:me', 'can_edit:me', 'cc:me']


def process_query_term(
  is_negation: bool, field_name: str, op_str: str, vals_str: str, context: QueryContext
) -> Future:
  """Parse and run a user-supplied query, if we can handle it."""
  if is_negation:
    op_str = search_queries.negate_operator(op_str)

  val_list = parse_query_value_list(vals_str, context)
  logging.info('trying %r %r %r', field_name, op_str, val_list)

  future = search_queries.single_field_query_async(
      field_name, op_str, val_list)
  return future


def process_predefined_query_term(
    field_name: str, op_str: str, val_str: str) -> Future:
  """Parse and run a simple query term."""
  query_term = field_name + op_str + val_str

  if query_term == 'deleted_unlisted_enterprise=false':
    return process_exclude_deleted_unlisted_enterprise_query()
  if query_term == 'deleted_unlisted=false':
    return process_exclude_deleted_unlisted_query()

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
  field_name: str, op_str: str, vals_str: str) -> bool:
  """Determine if a query is a simple query term."""
  query_term = field_name + op_str + vals_str
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
  total_order_dict = {}
  # For each feature entry ID in the total-order list, record the index of
  # the first time that it occurs.  A feature could be in the list multiple
  # times if it was produced via a join.  E.g., sorting by gate.requested_on
  # would have total_order_ids items for every gate, not just one per feature.
  for idx, f_id in enumerate(total_order_ids):
    if f_id not in total_order_dict:
      total_order_dict[f_id] = idx

  sorted_id_list = sorted(
      result_id_list,
      key=lambda f_id: total_order_dict.get(f_id, f_id))
  return sorted_id_list


def make_cache_key(
  user_query: str, sort_spec: str | None, show_unlisted: bool,
  show_deleted: bool, show_enterprise: bool, start: int, num: int,
  name_only: bool) -> str:
  """Return a redis key string to store cached search results."""
  return '|'.join([
      FeatureEntry.SEARCH_CACHE_KEY,
      user_query,
      'sort_spec=' + str(sort_spec),
      'show_unlisted=' + str(show_unlisted),
      'show_deleted=' + str(show_deleted),
      'show_enterprise=' + str(show_enterprise),
      'start=' + str(start),
      'num=' + str(num),
      'name_only=' + str(name_only),
  ])


def is_cacheable(user_query: str, name_only: bool):
  """Return True if this user query can be stored and viewed by other users."""
  if not name_only:
    logging.info('Search query not cached: could be large')
    return False

  if ':me' in user_query:
    logging.info('Search query not cached: personalized')
    return False

  if ('is:recently-reviewed' in user_query or
      'now' in user_query or
      'current_stable' in user_query):
    logging.info('Search query not cached: time-based')
    return False

  logging.info('Search query can be cached')
  return True


def process_query_using_cache(
  user_query: str,
  sort_spec: str | None = None,
  show_unlisted=False,
  show_deleted=False,
  show_enterprise=False,
  start=0,
  num=DEFAULT_RESULTS_PER_PAGE,
  context: Optional[QueryContext] = None,
  name_only=False,
) -> tuple[list[dict[str, Any]], int]:
  """"""
  cache_key = make_cache_key(
      user_query, sort_spec, show_unlisted, show_deleted, show_enterprise,
      start, num, name_only)
  if is_cacheable(user_query, name_only):
    logging.info('Checking cache at %r', cache_key)
    cached_result = rediscache.get(cache_key)
    if cached_result is not None:
      logging.info('Found cached search result for %r', cache_key)
      return cached_result

  logging.info('Computing search result')
  computed_result = process_query(
      user_query, sort_spec=sort_spec, show_unlisted=show_unlisted,
      show_deleted=show_deleted, show_enterprise=show_enterprise,
      start=start, num=num, context=context, name_only=name_only)

  if is_cacheable(user_query, name_only):
    logging.info('Storing search result in cache: %r', cache_key)
    rediscache.set(cache_key, computed_result, SEARCH_CACHE_TTL)

  return computed_result


def process_query(
  user_query: str,
  sort_spec: str | None = None,
  show_unlisted=False,
  show_deleted=False,
  show_enterprise=False,
  start=0,
  num=DEFAULT_RESULTS_PER_PAGE,
  context: Optional[QueryContext] = None,
  name_only=False,
) -> tuple[list[dict[str, Any]], int]:
  if context is None:
    context = QueryContext.current()

  """Parse the user's query, run it, and return a list of features."""
  # 1a. Parse the user query into terms.
  terms = TERM_RE.findall(user_query + ' ')[:MAX_TERMS] or []

  # 1b. Add permission and search scope terms.
  permission_terms = []
  if not show_deleted and not show_unlisted and not show_enterprise:
    permission_terms.append(
        ('', 'deleted_unlisted_enterprise', '=', 'false', None))
  elif not show_deleted and not show_unlisted:
    permission_terms.append(
        ('', 'deleted_unlisted', '=', 'false', None))
  else:
    if not show_deleted:
      permission_terms.append(('', 'deleted', '=', 'false', None))
    # TODO(jrobbins): include unlisted features that the user is allowed to view.
    # However, that would greatly complicate the search cache.
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
  feature_id_future_ops = create_future_operations_from_queries(terms, context)

  # 2b. Create parallel queries for each permission queries.
  logging.info('creating parallel queries for %r', permission_terms)
  permissions_future_ops = create_future_operations_from_queries(
    permission_terms, context
  )

  # 2c. Create a parallel query for total sort order.
  logging.info('creating total sort order for %r', sort_spec)
  total_order_promise = search_queries.total_order_query_async(sort_spec)

  # 3. Get the result of each future and combine them into a result ID set.
  logging.info('now waiting on futures')

  # 3a. Process user query: negation, AND, and OR.
  feature_id_future_ops = process_negation_operations(feature_id_future_ops)
  query_clauses = process_and_operations(feature_id_future_ops)
  result_id_set = process_or_operations(query_clauses)
  logging.info('got %r result IDs w/o permissions', len(result_id_set))

  # 3b. Process all permission ops, then interesect to apply permisisons.
  permission_clauses = process_and_operations(permissions_future_ops)
  permission_ids = process_or_operations(permission_clauses)
  result_id_set.intersection_update(permission_ids)
  logging.info('got %r result IDs with permissions', len(result_id_set))

  result_id_list = list(result_id_set)
  total_count = len(result_id_list)

  # 4. Finish getting the total sort order. Then, sort the IDs according
  # to their position in the complete sorted list.
  total_order_ids = _resolve_promise_to_id_list(total_order_promise)
  logging.info('sorting')
  sorted_id_list = _sort_by_total_order(result_id_list, total_order_ids)
  logging.info('sorted %r result IDs', len(sorted_id_list))

  # 5. Paginate
  paginated_id_list = sorted_id_list[start : start + num]

  # 6. Fetch the actual issues that have those IDs in the sorted results.
  if name_only:
    features_on_page = feature_helpers.get_feature_names_by_ids(paginated_id_list)
  else:
    features_on_page = feature_helpers.get_by_ids(paginated_id_list)

  logging.info('features_on_page is %r',
               [f['name'] for f in features_on_page])
  return features_on_page, total_count


def create_future_operations_from_queries(terms, context: QueryContext):
  """Create parallel queries for each term. Each yields a future operation"""
  feature_id_future_ops = []
  for logical_op, field_name, op_str, vals_str, textterm in terms:
    is_negation = (logical_op.strip() == '-')
    is_normal_query = False
    if textterm:
      future = search_fulltext.search_fulltext(textterm)
    elif is_predefined_query_term(field_name, op_str, vals_str):
      logging.info('Running predefined query term: %r %r %r',
                   field_name, op_str, vals_str)
      future = process_predefined_query_term(field_name, op_str, vals_str)
    else:
      future = process_query_term(is_negation, field_name, op_str, vals_str, context)
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
