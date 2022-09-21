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

from framework import utils
from internals import core_models
from internals import review_models


def single_field_query_async(
    field_name, operator, val, limit=None):
  """Create a query for one Feature field and run it, returning a promise."""
  field = QUERIABLE_FIELDS.get(field_name.lower())
  if field is None:
    logging.info('Ignoring field name %r', field_name)
    return []
  # TODO(jrobbins): support sorting by any fields of other model classes.
  query = core_models.Feature.query()
  # Note: We don't exclude deleted features, that's done by process_query.

  # TODO(jrobbins): Handle ":" operator as substrings for text fields.
  if (operator == '='):
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

  keys_promise = query.fetch_async(keys_only=True, limit=limit)
  return keys_promise


def total_order_query_async(sort_spec):
  """Create a query promise for all Feature IDs sorted by sort_spec."""
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
  query = core_models.Feature.query().order(field)

  keys_promise = query.fetch_async(keys_only=True)
  return keys_promise


def _sorted_by_joined_model(
    joinable_model_class, condition, descending, order_by):
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


def sorted_by_pending_request_date(descending):
  """Return feature_ids of pending approvals sorted by request date."""
  return _sorted_by_joined_model(
      review_models.Approval,
      review_models.Approval.state == review_models.Approval.REVIEW_REQUESTED,
      descending, review_models.Approval.set_on)


def sorted_by_review_date(descending):
  """Return feature_ids of reviewed approvals sorted by last review."""
  return _sorted_by_joined_model(
      review_models.Approval,
      review_models.Approval.state.IN(review_models.Approval.FINAL_STATES),
      descending, review_models.Approval.set_on)


QUERIABLE_FIELDS = {
    'created.when': core_models.Feature.created,
    'updated.when': core_models.Feature.updated,
    'deleted': core_models.Feature.deleted,

    # TODO(jrobbins): We cannot query user fields because Cloud NDB does not
    # seem to support it.  We should migrate these to string fields.
    #'created.by': Feature.created_by,
    #'updated.by': Feature.updated_by,

    'category': core_models.Feature.category,
    'name': core_models.Feature.name,
    'feature_type': core_models.Feature.feature_type,
    'intent_stage': core_models.Feature.intent_stage,
    'summary': core_models.Feature.summary,
    'unlisted': core_models.Feature.unlisted,
    'motivation': core_models.Feature.motivation,
    'star_count': core_models.Feature.star_count,
    'tags': core_models.Feature.search_tags,
    'owner': core_models.Feature.owner,
    'creator': core_models.Feature.creator,
    'browsers.chrome.owners': core_models.Feature.owner,
    'editors': core_models.Feature.editors,
    'cc_recipients': core_models.Feature.cc_recipients,
    'intent_to_implement_url': core_models.Feature.intent_to_implement_url,
    'intent_to_ship_url': core_models.Feature.intent_to_ship_url,
    'ready_for_trial_url': core_models.Feature.ready_for_trial_url,
    'intent_to_experiment_url': core_models.Feature.intent_to_experiment_url,
    'intent_to_extend_experiment_url':
        core_models.Feature.intent_to_extend_experiment_url,
    'i2e_lgtms': core_models.Feature.i2e_lgtms,
    'i2s_lgtms': core_models.Feature.i2s_lgtms,
    'browsers.chrome.bug': core_models.Feature.bug_url,
    'launch_bug_url': core_models.Feature.launch_bug_url,
    'initial_public_proposal_url':
        core_models.Feature.initial_public_proposal_url,
    'browsers.chrome.blink_components': core_models.Feature.blink_components,
    'browsers.chrome.devrel': core_models.Feature.devrel,
    'browsers.chrome.prefixed': core_models.Feature.prefixed,

    'browsers.chrome.status': core_models.Feature.impl_status_chrome,
    'browsers.chrome.desktop': core_models.Feature.shipped_milestone,
    'browsers.chrome.android': core_models.Feature.shipped_android_milestone,
    'browsers.chrome.ios': core_models.Feature.shipped_ios_milestone,
    'browsers.chrome.webview': core_models.Feature.shipped_webview_milestone,
    'requires_embedder_support': core_models.Feature.requires_embedder_support,

    'browsers.chrome.flag_name': core_models.Feature.flag_name,
    'all_platforms': core_models.Feature.all_platforms,
    'all_platforms_descr': core_models.Feature.all_platforms_descr,
    'wpt': core_models.Feature.wpt,
    'browsers.chrome.devtrial.desktop.start':
        core_models.Feature.dt_milestone_desktop_start,
    'browsers.chrome.devtrial.android.start':
        core_models.Feature.dt_milestone_android_start,
    'browsers.chrome.devtrial.ios.start':
        core_models.Feature.dt_milestone_ios_start,
    'browsers.chrome.devtrial.webview.start':
        core_models.Feature.dt_milestone_webview_start,

    'standards.maturity': core_models.Feature.standard_maturity,
    'standards.spec': core_models.Feature.spec_link,
    'standards.anticipated_spec_changes':
        core_models.Feature.anticipated_spec_changes,
    'api_spec': core_models.Feature.api_spec,
    'spec_mentors': core_models.Feature.spec_mentors,
    'security_review_status': core_models.Feature.security_review_status,
    'privacy_review_status': core_models.Feature.privacy_review_status,
    'tag_review.url': core_models.Feature.tag_review,
    'tag_review.status': core_models.Feature.tag_review_status,
    'explainer': core_models.Feature.explainer_links,

    'browsers.ff.view': core_models.Feature.ff_views,
    'browsers.safari.view': core_models.Feature.safari_views,
    'browsers.webdev.view': core_models.Feature.web_dev_views,
    'browsers.ff.view.url': core_models.Feature.ff_views_link,
    'browsers.safari.view.url': core_models.Feature.safari_views_link,
    'browsers.webdev.url.url': core_models.Feature.web_dev_views_link,

    'resources.docs': core_models.Feature.doc_links,
    'non_oss_deps': core_models.Feature.non_oss_deps,

    'browsers.chrome.ot.desktop.start':
        core_models.Feature.ot_milestone_desktop_start,
    'browsers.chrome.ot.desktop.end':
        core_models.Feature.ot_milestone_desktop_end,
    'browsers.chrome.ot.android.start':
        core_models.Feature.ot_milestone_android_start,
    'browsers.chrome.ot.android.end':
        core_models.Feature.ot_milestone_android_end,
    'browsers.chrome.ot.webview.start':
        core_models.Feature.ot_milestone_webview_start,
    'browsers.chrome.ot.webview.end':
        core_models.Feature.ot_milestone_webview_end,
    'browsers.chrome.ot.feedback_url':
        core_models.Feature.origin_trial_feedback_url,
    'finch_url': core_models.Feature.finch_url,
    }

SORTABLE_FIELDS = QUERIABLE_FIELDS.copy()
SORTABLE_FIELDS.update({
    'approvals.requested_on': sorted_by_pending_request_date,
    'approvals.reviewed_on': sorted_by_review_date,
    })
