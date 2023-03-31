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
import datetime
from typing import Union, Callable, Optional

from google.cloud import ndb  # type: ignore
from google.cloud.ndb.model import Model, Property  # for type checking only
from google.cloud.ndb.tasklets import Future  # for type checking only
from google.cloud.ndb.query import FilterNode  # for type checking only

from framework import users
from framework import utils
from internals import core_enums
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Gate


def single_field_query_async(
    field_name: str, operator: str, val: Union[str, int, datetime.datetime],
    limit: int = None) -> Union[list[int], Future]:
  """Create a query for one FeatureEntry field and run it, returning a promise."""
  # Note: We don't exclude deleted features, that's done by process_query.
  field_name = field_name.lower()
  if field_name in QUERIABLE_FIELDS:
    # It is a query on a field in FeatureEntry.
    query = FeatureEntry.query()
    field = QUERIABLE_FIELDS[field_name]
    if core_enums.is_enum_field(field_name):
      enum_val = core_enums.convert_enum_string_to_int(field_name, val)
      if enum_val < 0:
        logging.warning('Cannot find enum %r:%r', field_name, val)
        return []
      val = enum_val
  elif field_name in STAGE_QUERIABLE_FIELDS:
    # It is a query on a field in Stage.
    query = Stage.query()
    stage_type_dict = STAGE_TYPES_BY_QUERY_FIELD[field_name]
    # Only consider the appropriate stage type(s).
    stage_types = [st for st in stage_type_dict.values() if st is not None]
    query = query.filter(Stage.stage_type.IN(stage_types))
    field = STAGE_QUERIABLE_FIELDS[field_name]
  else:
    logging.warning('Ignoring field name %r', field_name)
    return []

  if not field._indexed:
    logging.warning('Field is not indexed in NDB %r', field_name)
    # TODO(jrobbins): Implement a text_eq operator w/ post-processing
    return []

  # TODO(jrobbins): Handle ":" operator as substrings for text fields.
  if (operator == '='):
    val_list = str(val).split(',')
    if len(val_list) > 1:
      query = query.filter(field.IN(val_list))
    else:
      query = query.filter(field == val)
  elif (operator == '<='):
    query = query.filter(field <= val)
  elif (operator == '<'):
    query = query.filter(field < val)
  elif (operator == '>='):
    query = query.filter(field >= val)
  elif (operator == '>'):
    query = query.filter(field > val)
  elif (operator == '!='):
    query = query.filter(field != val)
  else:
    raise ValueError('Unexpected query operator: %r' % operator)

  if field_name in QUERIABLE_FIELDS:
    # It was a query directly on FeatureEntry, use keys to get feature IDs.
    future = query.fetch_async(keys_only=True, limit=limit)
  else:
    # It was on a Stage, so get Stage.feature_id values.
    future = query.fetch_async(projection=['feature_id'], limit=limit)

  return future


def negate_operator(operator: str) -> str:
  """Negate field operators."""
  if operator == '=':
    return '!='
  if operator == '<=':
    return '>'
  if operator == '<':
    return '>='
  if operator == '>=':
    return '<'
  if operator == '>':
    return '<='
  if operator == '!=':
    return '='

  return operator


def handle_me_query_async(field_name: str) -> Future:
  """Return a future for feature IDs that reference the current user."""
  user = users.get_current_user()
  if not user:
    return []
  return single_field_query_async(field_name, '=', user.email())


def handle_can_edit_me_query_async() -> Future:
  """Return a future for features that the current user can edit."""
  user = users.get_current_user()
  if not user:
    return []
  email = user.email()
  query = FeatureEntry.query(
      ndb.OR(FeatureEntry.owner_emails == email,
             FeatureEntry.editor_emails == email,
             FeatureEntry.creator_email == email))
  keys_promise = query.fetch_async(keys_only=True)
  return keys_promise


def total_order_query_async(sort_spec: str) -> Union[list[int], Future]:
  """Create a query promise for all FeatureEntry IDs sorted by sort_spec."""
  # TODO(jrobbins): Support multi-column sort.
  descending = False
  if sort_spec.startswith('-'):
    descending = True
    sort_spec = sort_spec[1:]
  field = SORTABLE_FIELDS.get(sort_spec.lower())
  if field is None:
    logging.info('Ignoring sort field name %r', sort_spec)
    return []

  # Some special cases are implemented as python functions.
  if callable(field):
    return field(descending)

  if descending:
    field = -field
  # TODO(jrobbins): support sorting by any fields of other model classes.
  query = FeatureEntry.query().order(field)

  keys_promise = query.fetch_async(keys_only=True)
  return keys_promise


def _sorted_by_joined_model(
    joinable_model_class: Model, condition: FilterNode, descending: bool,
    order_by: Property) -> list[int]:
  """Return feature_ids sorted by a field in a joined entity kind."""
  query = joinable_model_class.query()
  if condition:
    query = query.filter(condition)
  if descending:
    query = query.order(-order_by)
  else:
    query = query.order(order_by)

  joined_models = query.fetch(projection=['feature_id'])
  feature_ids = utils.dedupe(jm.feature_id for jm in joined_models)
  return feature_ids


def sorted_by_pending_request_date(descending: bool) -> list[int]:
  """Return feature_ids of pending approvals sorted by request date."""
  return _sorted_by_joined_model(
      Gate,
      Gate.state.IN(Gate.PENDING_STATES),
      descending, Gate.requested_on)


def sorted_by_review_date(descending: bool) -> list[int]:
  """Return feature_ids of reviewed approvals sorted by last review."""
  return _sorted_by_joined_model(
      Gate,
      Gate.state.IN(Gate.FINAL_STATES),
      descending, Gate.requested_on)


QUERIABLE_FIELDS: dict[str, Property] = {
    'created.when': FeatureEntry.created,
    'updated.when': FeatureEntry.updated,
    # accurate_as_of
    'creator': FeatureEntry.creator_email,
    'updater': FeatureEntry.updater_email,
    'owner': FeatureEntry.owner_emails,
    'browsers.chrome.owners': FeatureEntry.owner_emails,
    'editor': FeatureEntry.editor_emails,
    'cc': FeatureEntry.cc_emails,
    'unlisted': FeatureEntry.unlisted,
    'deleted': FeatureEntry.deleted,

    'name': FeatureEntry.name,
    'summary': FeatureEntry.summary,

    'browsers.chrome.blink_component': FeatureEntry.blink_components,
    'star_count': FeatureEntry.star_count,
    'tag': FeatureEntry.search_tags,
    'feature_notes': FeatureEntry.feature_notes,

    'browsers.chrome.bug': FeatureEntry.bug_url,
    'launch_bug_url': FeatureEntry.launch_bug_url,
    'breaking_change': FeatureEntry.breaking_change,

    'browsers.chrome.status': FeatureEntry.impl_status_chrome,
    'browsers.chrome.flag_name': FeatureEntry.flag_name,
    'ongoing_constraints': FeatureEntry.ongoing_constraints,

    'motivation': FeatureEntry.motivation,
    'devtrial_instructions': FeatureEntry.devtrial_instructions,
    'activation_risks': FeatureEntry.activation_risks,
    'measurement': FeatureEntry.measurement,

    'initial_public_proposal_url':
        FeatureEntry.initial_public_proposal_url,
    'explainer': FeatureEntry.explainer_links,
    'requires_embedder_support': FeatureEntry.requires_embedder_support,
    'standards.spec': FeatureEntry.spec_link,
    'api_spec': FeatureEntry.api_spec,
    'spec_mentors': FeatureEntry.spec_mentor_emails,
    'interop_compat_risks': FeatureEntry.interop_compat_risks,
    'browsers.chrome.prefixed': FeatureEntry.prefixed,
    'all_platforms': FeatureEntry.all_platforms,
    'all_platforms_descr': FeatureEntry.all_platforms_descr,
    'tag_review.url': FeatureEntry.tag_review,
    'non_oss_deps': FeatureEntry.non_oss_deps,
    'standards.anticipated_spec_changes':
        FeatureEntry.anticipated_spec_changes,

    'browsers.ff.view.url': FeatureEntry.ff_views_link,
    'browsers.safari.view.url': FeatureEntry.safari_views_link,
    'browsers.webdev.view.url': FeatureEntry.web_dev_views_link,

    'security_risks': FeatureEntry.security_risks,
    'ergonomics_risks': FeatureEntry.ergonomics_risks,
    'wpt': FeatureEntry.wpt,
    'wpt_descr': FeatureEntry.wpt_descr,
    'webview_risks': FeatureEntry.webview_risks,

    'browsers.chrome.devrel': FeatureEntry.devrel_emails,
    'debuggability': FeatureEntry.debuggability,
    'resources.doc': FeatureEntry.doc_links,
    'resources.sample': FeatureEntry.sample_links,

    # Enum fields
    'feature_type': FeatureEntry.feature_type,
    'category': FeatureEntry.category,
    'intent_stage': FeatureEntry.intent_stage,
    'impl_status_chrome': FeatureEntry.impl_status_chrome,
    'security_review_status': FeatureEntry.security_review_status,
    'privacy_review_status': FeatureEntry.privacy_review_status,
    'tag_review_status': FeatureEntry.tag_review_status,
    'standards.maturity': FeatureEntry.standard_maturity,
    'browsers.ff.view': FeatureEntry.ff_views,
    'browsers.safari.view': FeatureEntry.safari_views,
    'browsers.webdev.view': FeatureEntry.web_dev_views,
}


STAGE_QUERIABLE_FIELDS: dict[str, Property] = {
    # The stage_type condition is added in single_field_query_async().
    'browsers.chrome.android': Stage.milestones.android_first,
    'browsers.chrome.desktop': Stage.milestones.desktop_first,
    'browsers.chrome.devtrial.android.start': Stage.milestones.android_first,
    'browsers.chrome.devtrial.desktop.start': Stage.milestones.desktop_first,
    'browsers.chrome.devtrial.ios.start': Stage.milestones.ios_first,
    'browsers.chrome.devtrial.webview.start': Stage.milestones.webview_first,
    'browsers.chrome.ios': Stage.milestones.ios_first,
    'browsers.chrome.ot.android.end': Stage.milestones.android_last,
    'browsers.chrome.ot.android.start': Stage.milestones.android_first,
    'browsers.chrome.ot.desktop.end': Stage.milestones.desktop_last,
    'browsers.chrome.ot.desktop.start': Stage.milestones.desktop_first,
    'browsers.chrome.ot.feedback_url': Stage.origin_trial_feedback_url,
    'browsers.chrome.ot.ios.end': Stage.milestones.ios_last,
    'browsers.chrome.ot.ios.start': Stage.milestones.ios_first,
    'browsers.chrome.ot.webview.end': Stage.milestones.webview_last,
    'browsers.chrome.ot.webview.start': Stage.milestones.webview_first,
    'browsers.chrome.webview': Stage.milestones.webview_first,
    'experiment_extension_reason': Stage.experiment_extension_reason,
    'experiment_goals': Stage.experiment_goals,
    'experiment_risks': Stage.experiment_risks,
    'finch_url': Stage.finch_url,
    'intent_to_experiment_url': Stage.intent_thread_url,
    'intent_to_extend_experiment_url': Stage.intent_thread_url,
    'intent_to_implement_url': Stage.intent_thread_url,
    'intent_to_ship_url': Stage.intent_thread_url,
    'announcement_url': Stage.announcement_url,

    # Obsolete fields
    # 'i2e_lgtms': Feature.i2e_lgtms,
    # 'i2s_lgtms': Feature.i2s_lgtms,
    }

# Mapping of user query fields to the new stage types the fields live on.
STAGE_TYPES_BY_QUERY_FIELD: dict[str, dict[int, Optional[int]]] = {
    'browsers.chrome.android': core_enums.STAGE_TYPES_SHIPPING,
    'browsers.chrome.desktop': core_enums.STAGE_TYPES_SHIPPING,
    'browsers.chrome.devtrial.android.start': core_enums.STAGE_TYPES_DEV_TRIAL,
    'browsers.chrome.devtrial.desktop.start': core_enums.STAGE_TYPES_DEV_TRIAL,
    'browsers.chrome.devtrial.ios.start': core_enums.STAGE_TYPES_DEV_TRIAL,
    'browsers.chrome.devtrial.webview.start': core_enums.STAGE_TYPES_DEV_TRIAL,
    'browsers.chrome.ios': core_enums.STAGE_TYPES_SHIPPING,
    'browsers.chrome.ot.android.end': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'browsers.chrome.ot.android.start': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'browsers.chrome.ot.desktop.end': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'browsers.chrome.ot.desktop.start': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'browsers.chrome.ot.feedback_url': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'browsers.chrome.ot.ios.end': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'browsers.chrome.ot.ios.start': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'browsers.chrome.ot.webview.end': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'browsers.chrome.ot.webview.start': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'browsers.chrome.webview': core_enums.STAGE_TYPES_SHIPPING,
    'experiment_extension_reason': core_enums.STAGE_TYPES_EXTEND_ORIGIN_TRIAL,
    'experiment_goals': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'experiment_risks': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'finch_url': core_enums.STAGE_TYPES_SHIPPING,
    'intent_to_experiment_url': core_enums.STAGE_TYPES_ORIGIN_TRIAL,
    'intent_to_extend_experiment_url': core_enums.STAGE_TYPES_EXTEND_ORIGIN_TRIAL,
    'intent_to_implement_url': core_enums.STAGE_TYPES_PROTOTYPE,
    'intent_to_ship_url': core_enums.STAGE_TYPES_SHIPPING,
    'announcement_url': core_enums.STAGE_TYPES_PROTOTYPE,
  }



SORTABLE_FIELDS: dict[str, Union[Property, Callable]] = QUERIABLE_FIELDS.copy()
SORTABLE_FIELDS.update({
    # TODO(jrobbins): remove the 'approvals.*' items after 2023-01-01.
    'approvals.requested_on': sorted_by_pending_request_date,
    'approvals.reviewed_on': sorted_by_review_date,

    'gate.requested_on': sorted_by_pending_request_date,
    'gate.reviewed_on': sorted_by_review_date,
    })
