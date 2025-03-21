# -*- coding: utf-8 -*-
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

from asyncio import Future
import logging
from typing import Any, Optional
from google.cloud import ndb  # type: ignore

from api import converters
from framework import rediscache
from framework import users
from framework import permissions
from internals.stage_helpers import organize_all_stages_by_feature
from internals.core_enums import *
from internals.core_models import FeatureEntry, Stage
from internals.data_types import VerboseFeatureDict


def filter_unlisted(feature_list: list[dict]) -> list[dict]:
  """Filters a feature list to display only features the user should see."""
  user = users.get_current_user()
  email = None
  if user:
    email = user.email()
  listed_features = []
  for f in feature_list:
    # Owners and editors of a feature should still be able to see their features.
    if ((not f.get('unlisted', False)) or
        ('browsers' in f and email in f['browsers']['chrome']['owners']) or
        (email in f.get('editors', [])) or
        (email is not None and f.get('creator') == email)):
      listed_features.append(f)

  return listed_features


def filter_confidential(feature_list: list[dict]) -> list[dict]:
  """Filters a feature list to display only features the user should see."""
  user = users.get_current_user()
  visible_features = []
  for f in feature_list:
    if permissions.can_view_feature_formatted(user, f):
      visible_features.append(f)

  return visible_features


def get_entries_by_id_async(ids) -> Future | None:
  if ids:
    q = FeatureEntry.query(FeatureEntry.key.IN(
        [ndb.Key('FeatureEntry', id) for id in ids]))
    q = q.order(FeatureEntry.name)
    return q.fetch_async()
  return None


def get_future_results(async_features: Future | None) -> list[FeatureEntry]:
  if async_features is None:
    return []
  return async_features.result()

def get_features_in_release_notes(milestone: int):
  cache_key = '%s|%s|%s' % (
      FeatureEntry.DEFAULT_CACHE_KEY, 'release_notes_milestone', milestone)

  cached_features = rediscache.get(cache_key)
  if cached_features:
    return cached_features

  stages = Stage.query(
          Stage.archived == False,
      ndb.OR(Stage.milestones.desktop_first >= milestone,
          Stage.milestones.android_first >= milestone,
          Stage.milestones.ios_first >= milestone,
          Stage.milestones.webview_first >= milestone,
          Stage.milestones.desktop_last >= milestone,
          Stage.milestones.ios_last >= milestone,
          Stage.milestones.webview_last >= milestone,
          Stage.rollout_milestone >= milestone),
      Stage.stage_type.IN([STAGE_BLINK_SHIPPING, STAGE_PSA_SHIPPING,
          STAGE_FAST_SHIPPING, STAGE_DEP_SHIPPING, STAGE_ENT_ROLLOUT])).filter().fetch()

  feature_ids = list(set({
      *[s.feature_id for s in stages]}))
  features = [dict(converters.feature_entry_to_json_verbose(f))
            for f in get_future_results(get_entries_by_id_async(feature_ids))]
  features = [f for f in filter_unlisted(features)
    if not f['deleted'] and
      (f['enterprise_impact'] > ENTERPRISE_IMPACT_NONE or
       f['feature_type_int'] == FEATURE_TYPE_ENTERPRISE_ID) and
      (f['first_enterprise_notification_milestone'] == None or
       f['first_enterprise_notification_milestone'] <= milestone)]
  features = [f for f in features]

  rediscache.set(cache_key, features)
  return filter_confidential(features)


def get_in_milestone(milestone: int,
    show_unlisted: bool=False) -> dict[str, list[dict[str, Any]]]:
  """Return {reason: [feature_dict]} with all the reasons a feature can
  be part of a milestone.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  features_by_type = {}
  cache_key = '%s|%s|%s' % (
      FeatureEntry.DEFAULT_CACHE_KEY, 'milestone', milestone)
  cached_features_by_type = rediscache.get(cache_key)
  if cached_features_by_type:
    features_by_type = cached_features_by_type
  else:
    logging.info('Getting chronological feature list in milestone %d',
                milestone)
    # Start each query asynchronously in parallel.

    # Shipping stages with a matching desktop milestone.
    # Note: Enterprise features use STAGE_ENT_ROLLOUT and are NOT included.
    q = Stage.query(Stage.milestones.desktop_first == milestone,
        ndb.OR(Stage.stage_type == STAGE_BLINK_SHIPPING,
            Stage.stage_type == STAGE_PSA_SHIPPING,
            Stage.stage_type == STAGE_FAST_SHIPPING,
            Stage.stage_type == STAGE_DEP_SHIPPING))
    q = q.filter()
    desktop_shipping_future = q.fetch_async()

    # Shipping stages with a matching android shipping milestone
    # but no desktop milestone.
    q = Stage.query(Stage.milestones.android_first == milestone,
        Stage.milestones.desktop_first == None,
        Stage.stage_type.IN((STAGE_BLINK_SHIPPING, STAGE_PSA_SHIPPING,
            STAGE_FAST_SHIPPING, STAGE_DEP_SHIPPING)))
    android_only_shipping_future = q.fetch_async()

    # Origin trial stages (Desktop) in this milestone.
    q = Stage.query(Stage.milestones.desktop_first == milestone,
        Stage.stage_type.IN((STAGE_BLINK_ORIGIN_TRIAL, STAGE_FAST_ORIGIN_TRIAL,
            STAGE_DEP_DEPRECATION_TRIAL)))
    desktop_origin_trial_future = q.fetch_async()

    # Origin trial stages (Android) in this milestone.
    q = Stage.query(Stage.milestones.android_first == milestone,
        Stage.milestones.desktop_first == None,
        Stage.stage_type.IN((STAGE_BLINK_ORIGIN_TRIAL, STAGE_FAST_ORIGIN_TRIAL,
            STAGE_DEP_DEPRECATION_TRIAL)))
    android_origin_trial_future = q.fetch_async()

    # Origin trial stages (Webview) in this milestone.
    q = Stage.query(Stage.milestones.webview_first == milestone,
        Stage.milestones.desktop_first == None,
        Stage.stage_type.IN((STAGE_BLINK_ORIGIN_TRIAL, STAGE_FAST_ORIGIN_TRIAL,
            STAGE_DEP_DEPRECATION_TRIAL)))
    webview_origin_trial_future = q.fetch_async()

    # Dev trial stages (Desktop) in this milestone.
    q = Stage.query(Stage.milestones.desktop_first == milestone,
        Stage.stage_type.IN((STAGE_BLINK_DEV_TRIAL, STAGE_PSA_DEV_TRIAL,
            STAGE_FAST_DEV_TRIAL, STAGE_DEP_DEV_TRIAL)))
    desktop_dev_trial_future = q.fetch_async()

    # Dev trial stages (Android) in this milestone.
    q = Stage.query(Stage.milestones.android_first == milestone,
        Stage.milestones.desktop_first == None,
        Stage.stage_type.IN((STAGE_BLINK_DEV_TRIAL, STAGE_PSA_DEV_TRIAL,
            STAGE_FAST_DEV_TRIAL, STAGE_DEP_DEV_TRIAL)))
    android_dev_trial_future = q.fetch_async()

    # Rollout stages are mostly used for enterprise features, but some
    # web platform features may add them.  Enterprise features are
    # filtered out below.
    q = Stage.query(Stage.rollout_milestone == milestone,
        Stage.stage_type == STAGE_ENT_ROLLOUT)
    q = q.filter()
    rollout_future = q.fetch_async()

    # Wait for all futures to complete and collect unique feature IDs.
    shipping_stages_by_fid = organize_all_stages_by_feature(
        desktop_shipping_future.result() +
        android_only_shipping_future.result())
    origin_trial_stages_by_fid = organize_all_stages_by_feature(
        desktop_origin_trial_future.result() +
        android_origin_trial_future.result() +
        webview_origin_trial_future.result())
    dev_trial_stages_by_fid = organize_all_stages_by_feature(
        desktop_dev_trial_future.result() +
        android_dev_trial_future.result())
    rollout_stages_by_fid = organize_all_stages_by_feature(
        rollout_future.result())

    # Query for FeatureEntry entities that match the stage feature IDs.
    shipping_future = get_entries_by_id_async(
        shipping_stages_by_fid.keys())
    origin_trial_future = get_entries_by_id_async(
        origin_trial_stages_by_fid.keys())
    dev_trial_future = get_entries_by_id_async(
        dev_trial_stages_by_fid.keys())
    rollout_future = get_entries_by_id_async(
        rollout_stages_by_fid.keys())

    shipping_features = get_future_results(shipping_future)
    origin_trial_features = get_future_results(origin_trial_future)
    dev_trial_features = get_future_results(dev_trial_future)
    rollout_features = get_future_results(rollout_future)

    all_features = _group_by_roadmap_section(
        shipping_features, origin_trial_features, dev_trial_features,
        rollout_features)

    # Filter out deleted and inactive features, then
    # construct results as: {type: [json_feature, ...], ...}.
    for shipping_type in all_features:
      all_features[shipping_type].sort(key=lambda f: f.name)
      all_features[shipping_type] = [
          fe for fe in all_features[shipping_type]
          if _should_appear_on_roadmap(fe)]
      features_by_type[shipping_type] = []
      for f in all_features[shipping_type]:
        formatted_feature = converters.feature_entry_to_json_basic(f)
        features_by_type[shipping_type].append(formatted_feature)

    # Fill in the IDs of the stages that caused each feature to appear,
    # and any finch URLs.
    _set_feature_fields_for_roadmap(
        features_by_type[IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT]] +
        features_by_type[IMPLEMENTATION_STATUS[DEPRECATED]] +
        features_by_type[IMPLEMENTATION_STATUS[REMOVED]] +
        features_by_type[IMPLEMENTATION_STATUS[INTERVENTION]],
        shipping_stages_by_fid)

    _set_feature_fields_for_roadmap(
        features_by_type[IMPLEMENTATION_STATUS[ORIGIN_TRIAL]],
        origin_trial_stages_by_fid)

    _set_feature_fields_for_roadmap(
        features_by_type[IMPLEMENTATION_STATUS[BEHIND_A_FLAG]],
        dev_trial_stages_by_fid)

    rediscache.set(cache_key, features_by_type)

  for shipping_type in features_by_type:
    if not show_unlisted:
      features_by_type[shipping_type] = filter_unlisted(
          features_by_type[shipping_type])
    features_by_type[shipping_type] = filter_confidential(
        features_by_type[shipping_type])

  return features_by_type


def _group_by_roadmap_section(
    shipping_features: list[FeatureEntry],
    origin_trial_features: list[FeatureEntry],
    dev_trial_features: list[FeatureEntry],
    rollout_features: list[FeatureEntry]) -> dict[str, list[FeatureEntry]]:
  """Return a dict of roadmap sections with features belonging in each."""
  removed_features = []
  deprecated_features = []
  intervention_features = []
  enabled_features = []

  # Push features to lists corresponding to the appropriate section
  # of the milestone card.
  for fe in shipping_features:
    if fe.impl_status_chrome == REMOVED:
      removed_features.append(fe)
    elif fe.feature_type == FEATURE_TYPE_DEPRECATION_ID:
      deprecated_features.append(fe)
    elif fe.impl_status_chrome == INTERVENTION:
      intervention_features.append(fe)
    else:
      enabled_features.append(fe)

  all_features: dict[str, list[FeatureEntry]] = {
      IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT]: enabled_features,
      IMPLEMENTATION_STATUS[DEPRECATED]: deprecated_features,
      IMPLEMENTATION_STATUS[REMOVED]: removed_features,
      IMPLEMENTATION_STATUS[INTERVENTION]: intervention_features,
      ROLLOUT_SECTION: rollout_features,
      IMPLEMENTATION_STATUS[ORIGIN_TRIAL]: origin_trial_features,
      IMPLEMENTATION_STATUS[BEHIND_A_FLAG]: dev_trial_features,
  }
  return all_features


def _should_appear_on_roadmap(fe: FeatureEntry) -> bool:
  """Return True for features that should appear on the roadmap."""
  return (not fe.deleted and
          fe.impl_status_chrome not in INACTIVE_IMPL_STATUSES and
          fe.feature_type in ROADMAP_FEATURE_TYPES)


def _set_feature_fields_for_roadmap(
    formatted_features: list[dict[str, Any]],
    triggering_stages_by_fid: dict[int, list[Stage]]) -> None:
  """Add roadmap_stage_ids and finch_urls items to formated features."""
  for ff in formatted_features:
    # The feature's stages that caused it to appear in this roadmap section.
    feature_trigger_stages = triggering_stages_by_fid.get(ff['id'], [])
    ff['roadmap_stage_ids'] = [s.key.integer_id() for s in feature_trigger_stages]
    ff['finch_urls'] = [
        s.finch_url for s in feature_trigger_stages if s.finch_url]


def get_all(limit: Optional[int]=None,
    order: str='-updated', filterby: Optional[tuple[str, Any]]=None,
    update_cache: bool=False, keys_only: bool=False
 ) -> list[dict] | list[ndb.Key]:
  """Return JSON dicts for entities that fit the filterby criteria.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  KEY = '%s|%s|%s|%s' % (
      FeatureEntry.DEFAULT_CACHE_KEY, order, limit, keys_only)

  # TODO(ericbidelman): Support more than one filter.
  if filterby is not None:
    s = ('%s%s' % (filterby[0], filterby[1])).replace(' ', '')
    KEY += '|%s' % s

  feature_list = rediscache.get(KEY)

  if feature_list is None or update_cache:
    query = FeatureEntry.query().order(-FeatureEntry.updated) #.order('name')
    query = query.filter(FeatureEntry.deleted == False)

    # TODO(ericbidelman): Support more than one filter.
    if filterby:
      filter_type, comparator = filterby
      if filter_type == 'can_edit':
        # can_edit will check if the user has any access to edit the feature.
        # This includes being an owner, editor, or the original creator
        # of the feature.
        query = query.filter(
          ndb.OR(FeatureEntry.owner_emails == comparator,
              FeatureEntry.editor_emails == comparator,
              FeatureEntry.creator_email == comparator,
              FeatureEntry.spec_mentor_emails == comparator))
      else:
        query = query.filter(getattr(FeatureEntry, filter_type) == comparator)

    feature_list = query.fetch(limit, keys_only=keys_only)
    if not keys_only:
      feature_list = [
          converters.feature_entry_to_json_basic(f) for f in feature_list]

    rediscache.set(KEY, feature_list)

  return feature_list

def get_feature_names_by_ids(feature_ids: list[int],
               update_cache: bool=True) -> list[dict[str, Any]]:
  """Return a list of JSON dicts for the specified feature names.
  """
  result_dict = {}
  futures_by_id = {}

  if update_cache:
    lookup_keys = [
        FeatureEntry.feature_cache_key(
            FeatureEntry.FEATURE_NAME_CACHE_KEY, feature_id)
        for feature_id in feature_ids]
    cached_features = rediscache.get_multi(lookup_keys)
    if cached_features:
      result_dict = {f['id']: f
                     for f in cached_features.values()
                     if f is not None and f.get('id')}

  for feature_id in feature_ids:
    if feature_id not in result_dict:
      futures_by_id[feature_id] = FeatureEntry.get_by_id_async(feature_id)

  for future in futures_by_id.values():
    fe: Optional[FeatureEntry] = future.get_result()
    if fe and not fe.deleted:
      feature_id = fe.key.integer_id()
      result_dict[feature_id] = converters.feature_entry_to_json_tiny(fe)

  if update_cache:
    to_cache = {}
    for feature_id in futures_by_id:
      if feature_id in result_dict:
        store_key = FeatureEntry.feature_cache_key(
            FeatureEntry.FEATURE_NAME_CACHE_KEY, feature_id)
        to_cache[store_key] = result_dict[feature_id]
    rediscache.set_multi(to_cache)

  result_list = [
      result_dict[feature_id] for feature_id in feature_ids
      if feature_id in result_dict]
  return filter_confidential(result_list)

def get_by_ids(feature_ids: list[int],
               update_cache: bool=True) -> list[dict[str, Any]]:
  """Return a list of JSON dicts for the specified features.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  result_dict = {}
  futures_by_id = {}

  if update_cache:
    lookup_keys = [
        FeatureEntry.feature_cache_key(
            FeatureEntry.DEFAULT_CACHE_KEY, feature_id)
        for feature_id in feature_ids]
    cached_features = rediscache.get_multi(lookup_keys)
    if cached_features:
      result_dict = {f['id']: f
                     for f in cached_features.values()
                     if f is not None and f.get('id')}

  for feature_id in feature_ids:
    if result_dict.get(feature_id) is None:
      futures_by_id[feature_id] = FeatureEntry.get_by_id_async(feature_id)

  stages_dict = {}
  if futures_by_id:
    needed_ids = list(futures_by_id.keys())
    stages_list = Stage.query(Stage.feature_id.IN(needed_ids), Stage.archived == False).fetch(None)
    stages_dict = organize_all_stages_by_feature(stages_list)

  for future in futures_by_id.values():
    unformatted_feature: Optional[FeatureEntry] = future.get_result()
    if unformatted_feature and not unformatted_feature.deleted:
      feature_id = unformatted_feature.key.integer_id()
      feature = converters.feature_entry_to_json_verbose(
          unformatted_feature, prefetched_stages=stages_dict.get(feature_id))
      if unformatted_feature.updated is not None:
        feature['updated_display'] = (
            unformatted_feature.updated.strftime("%Y-%m-%d"))
      else:
        feature['updated_display'] = ''
      result_dict[feature_id] = feature

  if update_cache:
    to_cache = {}
    for feature_id in futures_by_id:
      if feature_id in result_dict:
        store_key = FeatureEntry.feature_cache_key(
            FeatureEntry.DEFAULT_CACHE_KEY, feature_id)
        to_cache[store_key] = result_dict[feature_id]
    rediscache.set_multi(to_cache)

  result_list = [
      result_dict[feature_id] for feature_id in feature_ids
      if feature_id in result_dict]
  return filter_confidential(result_list)


def get_features_by_impl_status(limit: int | None=None, update_cache: bool=False,
    show_unlisted: bool=False) -> list[dict]:
  """Return a list of JSON dicts for features, ordered by chrome_impl_status.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  cache_key = '%s|%s|%s|%s' % (FeatureEntry.DEFAULT_CACHE_KEY,
                                'impl_order', limit, show_unlisted)

  feature_list = rediscache.get(cache_key)
  logging.info('getting feature list, sorted by chrome_impl_status')

  # On cache miss, do a db query.
  if not feature_list or update_cache:
    logging.info('recomputing feature list')
    # Get features by implementation status.
    futures: list[Future] = []
    stages_future = Stage.query(Stage.archived == False).fetch_async()
    for impl_status in IMPLEMENTATION_STATUS.keys():
      q = FeatureEntry.query(FeatureEntry.impl_status_chrome == impl_status)
      q = q.order(FeatureEntry.impl_status_chrome)
      q = q.order(FeatureEntry.name)
      futures.append(q.fetch_async(None))
    # Put "No active development" at end of list.
    futures = futures[1:] + futures[0:1]
    logging.info('Waiting on futures')
    query_results = [future.result() for future in futures]
    all_stages = organize_all_stages_by_feature(
        stages_future.result())

    # Construct the proper ordering.
    feature_list = []
    for section in query_results:
      if len(section) > 0:
        section = [f for f in section if not f.deleted]
        section = [f for f in section if f.feature_type != FEATURE_TYPE_ENTERPRISE_ID]
        section = [converters.feature_entry_to_json_basic(
            f, all_stages[f.key.integer_id()]) for f in section]
        section[0]['first_of_section'] = True
        if not show_unlisted:
          section = filter_unlisted(section)
        feature_list.extend(section)

    rediscache.set(cache_key, feature_list)

  return filter_confidential(feature_list)
