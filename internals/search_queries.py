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
from internals import models


def single_field_query_async(
    field_name, operator, val, limit=None):
  """Create a query for one Feature field and run it, returning a promise."""
  field = QUERIABLE_FIELDS.get(field_name.lower())
  if field is None:
    logging.info('Ignoring field name %r', field_name)
    return []
  # TODO(jrobbins): support sorting by any fields of other model classes.
  query = models.Feature.query()
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
  query = models.Feature.query().order(field)

  keys_promise = query.fetch_async(keys_only=True)
  return keys_promise


def sorted_by_pending_request_date(descending):
  """Return feature_ids of pending approvals sorted by request date."""
  query = models.Approval.query(
      models.Approval.state == models.Approval.REVIEW_REQUESTED)
  if descending:
    query = query.order(-models.Approval.set_on)
  else:
    query = query.order(models.Approval.set_on)

  pending_approvals = query.fetch(projection=['feature_id'])
  feature_ids = utils.dedupe(pa.feature_id for pa in pending_approvals)
  return feature_ids


def sorted_by_review_date(descending):
  """Return feature_ids of reviewed approvals sorted by last review."""
  query = models.Approval.query(
      models.Approval.state.IN(models.Approval.FINAL_STATES))
  if descending:
    query = query.order(-models.Approval.set_on)
  else:
    query = query.order(models.Approval.set_on)
  recent_approvals = query.fetch(projection=['feature_id'])

  feature_ids = utils.dedupe(ra.feature_id for ra in recent_approvals)
  return feature_ids


QUERIABLE_FIELDS = {
    'created.when': models.Feature.created,
    'updated.when': models.Feature.updated,
    'deleted': models.Feature.deleted,

    # TODO(jrobbins): We cannot query user fields because Cloud NDB does not
    # seem to support it.  We should migrate these to string fields.
    #'created.by': Feature.created_by,
    #'updated.by': Feature.updated_by,

    'category': models.Feature.category,
    'name': models.Feature.name,
    'feature_type': models.Feature.feature_type,
    'intent_stage': models.Feature.intent_stage,
    'summary': models.Feature.summary,
    'unlisted': models.Feature.unlisted,
    'motivation': models.Feature.motivation,
    'star_count': models.Feature.star_count,
    'tags': models.Feature.search_tags,
    'owner': models.Feature.owner,
    'creator': models.Feature.creator,
    'browsers.chrome.owners': models.Feature.owner,
    'editors': models.Feature.editors,
    'intent_to_implement_url': models.Feature.intent_to_implement_url,
    'intent_to_ship_url': models.Feature.intent_to_ship_url,
    'ready_for_trial_url': models.Feature.ready_for_trial_url,
    'intent_to_experiment_url': models.Feature.intent_to_experiment_url,
    'intent_to_extend_experiment_url':
        models.Feature.intent_to_extend_experiment_url,
    'i2e_lgtms': models.Feature.i2e_lgtms,
    'i2s_lgtms': models.Feature.i2s_lgtms,
    'browsers.chrome.bug': models.Feature.bug_url,
    'launch_bug_url': models.Feature.launch_bug_url,
    'initial_public_proposal_url': models.Feature.initial_public_proposal_url,
    'browsers.chrome.blink_components': models.Feature.blink_components,
    'browsers.chrome.devrel': models.Feature.devrel,
    'browsers.chrome.prefixed': models.Feature.prefixed,

    'browsers.chrome.status': models.Feature.impl_status_chrome,
    'browsers.chrome.desktop': models.Feature.shipped_milestone,
    'browsers.chrome.android': models.Feature.shipped_android_milestone,
    'browsers.chrome.ios': models.Feature.shipped_ios_milestone,
    'browsers.chrome.webview': models.Feature.shipped_webview_milestone,
    'requires_embedder_support': models.Feature.requires_embedder_support,

    'browsers.chrome.flag_name': models.Feature.flag_name,
    'all_platforms': models.Feature.all_platforms,
    'all_platforms_descr': models.Feature.all_platforms_descr,
    'wpt': models.Feature.wpt,
    'browsers.chrome.devtrial.desktop.start':
        models.Feature.dt_milestone_desktop_start,
    'browsers.chrome.devtrial.android.start':
        models.Feature.dt_milestone_android_start,
    'browsers.chrome.devtrial.ios.start':
        models.Feature.dt_milestone_ios_start,
    'browsers.chrome.devtrial.webview.start':
        models.Feature.dt_milestone_webview_start,

    'standards.maturity': models.Feature.standard_maturity,
    'standards.spec': models.Feature.spec_link,
    'standards.anticipated_spec_changes': models.Feature.anticipated_spec_changes,
    'api_spec': models.Feature.api_spec,
    'spec_mentors': models.Feature.spec_mentors,
    'security_review_status': models.Feature.security_review_status,
    'privacy_review_status': models.Feature.privacy_review_status,
    'tag_review.url': models.Feature.tag_review,
    'tag_review.status': models.Feature.tag_review_status,
    'explainer': models.Feature.explainer_links,

    'browsers.ff.view': models.Feature.ff_views,
    'browsers.safari.view': models.Feature.safari_views,
    'browsers.webdev.view': models.Feature.web_dev_views,
    'browsers.ff.view.url': models.Feature.ff_views_link,
    'browsers.safari.view.url': models.Feature.safari_views_link,
    'browsers.webdev.url.url': models.Feature.web_dev_views_link,

    'resources.docs': models.Feature.doc_links,
    'non_oss_deps': models.Feature.non_oss_deps,

    'browsers.chrome.ot.desktop.start': models.Feature.ot_milestone_desktop_start,
    'browsers.chrome.ot.desktop.end': models.Feature.ot_milestone_desktop_end,
    'browsers.chrome.ot.android.start': models.Feature.ot_milestone_android_start,
    'browsers.chrome.ot.android.end': models.Feature.ot_milestone_android_end,
    'browsers.chrome.ot.webview.start': models.Feature.ot_milestone_webview_start,
    'browsers.chrome.ot.webview.end': models.Feature.ot_milestone_webview_end,
    'browsers.chrome.ot.feedback_url': models.Feature.origin_trial_feedback_url,
    'finch_url': models.Feature.finch_url,
    }

SORTABLE_FIELDS = QUERIABLE_FIELDS.copy()
SORTABLE_FIELDS.update({
    'approvals.requested_on': sorted_by_pending_request_date,
    'approvals.reviewed_on': sorted_by_review_date,
    })
