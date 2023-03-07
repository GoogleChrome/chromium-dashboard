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
import re
from typing import Any, Optional
from google.cloud import ndb  # type: ignore

from api import converters
from framework import rediscache
from framework import users
from internals import stage_helpers
from internals.core_enums import *
from internals.core_models import FeatureEntry, Stage
from internals.legacy_models import Feature
import settings


def _crbug_number(bug_url: Optional[str]) -> Optional[str]:
  if bug_url is None:
    return None
  m = re.search(r'[\/|?id=]([0-9]+)$', bug_url)
  if m:
    return m.group(1)
  return None


def _new_crbug_url(blink_components: Optional[list[str]],
    bug_url: Optional[str], impl_status_chrome: int,
    owner_emails: list[str]=list()) -> str:
  url = 'https://bugs.chromium.org/p/chromium/issues/entry'
  if blink_components and len(blink_components) > 0:
    params = ['components=' + blink_components[0]]
  else:
    params = ['components=' + settings.DEFAULT_COMPONENT]
  crbug_number = _crbug_number(bug_url)
  if crbug_number and impl_status_chrome in (
      NO_ACTIVE_DEV,
      PROPOSED,
      IN_DEVELOPMENT,
      BEHIND_A_FLAG,
      ORIGIN_TRIAL,
      INTERVENTION):
    params.append('blocking=' + crbug_number)
  if owner_emails:
    params.append('cc=' + ','.join(owner_emails))
  return url + '?' + '&'.join(params)


def get_by_ids_legacy(feature_ids: list[int],
    update_cache: bool=False) -> list[dict[str, Any]]:
  """Return a list of JSON dicts for the specified features.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  result_dict = {}
  futures = []

  for feature_id in feature_ids:
    lookup_key = Feature.feature_cache_key(
        Feature.DEFAULT_CACHE_KEY, feature_id)
    feature = rediscache.get(lookup_key)
    if feature is None or update_cache:
      futures.append(Feature.get_by_id_async(feature_id))
    else:
      result_dict[feature_id] = feature

  for future in futures:
    unformatted_feature: Optional[Feature] = future.get_result()
    if unformatted_feature and not unformatted_feature.deleted:
      feature = converters.feature_to_legacy_json(unformatted_feature)
      feature['updated_display'] = (
          unformatted_feature.updated.strftime("%Y-%m-%d"))
      feature['new_crbug_url'] = _new_crbug_url(
          unformatted_feature.blink_components, unformatted_feature.bug_url,
          unformatted_feature.impl_status_chrome, unformatted_feature.owner)
      store_key = Feature.feature_cache_key(
          Feature.DEFAULT_CACHE_KEY,  unformatted_feature.key.integer_id())
      rediscache.set(store_key, feature)
      result_dict[unformatted_feature.key.integer_id()] = feature

  result_list = [
      result_dict[feature_id] for feature_id in feature_ids
      if feature_id in result_dict]
  return result_list


def get_all_legacy(limit=None, order='-updated', filterby=None,
            update_cache=False, keys_only=False):
  """Return JSON dicts for entities that fit the filterby criteria.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  KEY = '%s|%s|%s|%s' % (Feature.DEFAULT_CACHE_KEY, order, limit, keys_only)

  # TODO(ericbidelman): Support more than one filter.
  if filterby is not None:
    s = ('%s%s' % (filterby[0], filterby[1])).replace(' ', '')
    KEY += '|%s' % s

  feature_list = rediscache.get(KEY)

  if feature_list is None or update_cache:
    query = Feature.query().order(-Feature.updated) #.order('name')
    query = query.filter(Feature.deleted == False)

    # TODO(ericbidelman): Support more than one filter.
    if filterby:
      filter_type, comparator = filterby
      if filter_type == 'can_edit':
        # can_edit will check if the user has any access to edit the feature.
        # This includes being an owner, editor, or the original creator
        # of the feature.
        query = query.filter(
          ndb.OR(Feature.owner == comparator, Feature.editors == comparator,
            Feature.creator == comparator))
      else:
        query = query.filter(getattr(Feature, filter_type) == comparator)

    feature_list = query.fetch(limit, keys_only=keys_only)
    if not keys_only:
      feature_list = [
          converters.feature_to_legacy_json(f) for f in feature_list]

    rediscache.set(KEY, feature_list)

  return feature_list


def filter_unlisted_legacy(feature_list: list[dict]) -> list[dict]:
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


def get_chronological_legacy(limit=None, update_cache: bool=False,
    show_unlisted: bool=False) -> list[dict]:
  """Return a list of JSON dicts for features, ordered by milestone.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  cache_key = '%s|%s|%s' % (Feature.DEFAULT_CACHE_KEY,
                                'cronorder', limit)

  feature_list = rediscache.get(cache_key)
  logging.info('getting chronological feature list')

  # On cache miss, do a db query.
  if not feature_list or update_cache:
    logging.info('recomputing chronological feature list')
    # Features that are in-dev or proposed.
    q = Feature.query()
    q = q.order(Feature.impl_status_chrome)
    q = q.order(Feature.name)
    q = q.filter(Feature.impl_status_chrome.IN(
        (PROPOSED, IN_DEVELOPMENT)))
    pre_release_future = q.fetch_async(None)

    # Shipping features. Exclude features that do not have a desktop
    # shipping milestone.
    q = Feature.query()
    q = q.order(-Feature.shipped_milestone)
    q = q.order(Feature.name)
    q = q.filter(Feature.shipped_milestone != None)
    shipping_features_future = q.fetch_async(None)

    # Features with an android shipping milestone but no desktop milestone.
    q = Feature.query()
    q = q.order(-Feature.shipped_android_milestone)
    q = q.order(Feature.name)
    q = q.filter(Feature.shipped_milestone == None)
    android_only_shipping_features_future = q.fetch_async(None)

    # Features with no active development.
    q = Feature.query()
    q = q.order(Feature.name)
    q = q.filter(Feature.impl_status_chrome == NO_ACTIVE_DEV)
    no_active_future = q.fetch_async(None)

    # No longer pursuing features.
    q = Feature.query()
    q = q.order(Feature.name)
    q = q.filter(Feature.impl_status_chrome == NO_LONGER_PURSUING)
    no_longer_pursuing_features_future = q.fetch_async(None)

    logging.info('Waiting on futures')
    pre_release = pre_release_future.result()
    android_only_shipping_features = (
        android_only_shipping_features_future.result())
    no_active = no_active_future.result()
    no_longer_pursuing_features = no_longer_pursuing_features_future.result()
    logging.info('Waiting on shipping_features_future')
    shipping_features = shipping_features_future.result()

    shipping_features.extend(android_only_shipping_features)

    shipping_features = [
        f for f in shipping_features
        if (IN_DEVELOPMENT < f.impl_status_chrome
            < NO_LONGER_PURSUING)]

    def getSortingMilestone(feature):
      feature._sort_by_milestone = (feature.shipped_milestone or
                                    feature.shipped_android_milestone or
                                    0)
      return feature

    # Sort the feature list on either Android shipping milestone or desktop
    # shipping milestone, depending on which is specified. If a desktop
    # milestone is defined, that will take default.
    shipping_features = list(map(getSortingMilestone, shipping_features))

    # First sort by name, then sort by feature milestone (latest first).
    shipping_features.sort(key=lambda f: f.name, reverse=False)
    shipping_features.sort(key=lambda f: f._sort_by_milestone, reverse=True)

    # Constructor the proper ordering.
    all_features = []
    all_features.extend(pre_release)
    all_features.extend(shipping_features)
    all_features.extend(no_active)
    all_features.extend(no_longer_pursuing_features)
    all_features = [f for f in all_features if not f.deleted]

    feature_list = [converters.feature_to_legacy_json(f) for f in all_features]

    Feature._annotate_first_of_milestones(feature_list)

    rediscache.set(cache_key, feature_list)

  if not show_unlisted:
    feature_list = filter_unlisted(feature_list)
  return feature_list


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


def _get_entries_by_id_async(ids) -> Future | None:
  if ids:
    q = FeatureEntry.query(FeatureEntry.key.IN(
        [ndb.Key('FeatureEntry', id) for id in ids]))
    q = q.order(FeatureEntry.name)
    return q.fetch_async()
  return None


def _get_future_results(async_features: Future | None) -> list[FeatureEntry]:
  if async_features is None:
    return []
  return async_features.result()


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
    all_features: dict[str, list[FeatureEntry]] = {}
    all_features[IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT]] = []
    all_features[IMPLEMENTATION_STATUS[DEPRECATED]] = []
    all_features[IMPLEMENTATION_STATUS[REMOVED]] = []
    all_features[IMPLEMENTATION_STATUS[INTERVENTION]] = []
    all_features[IMPLEMENTATION_STATUS[ORIGIN_TRIAL]] = []
    all_features[IMPLEMENTATION_STATUS[BEHIND_A_FLAG]] = []

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

    # Wait for all futures to complete and collect unique feature IDs.
    desktop_shipping_ids = list({
        *[s.feature_id for s in desktop_shipping_future.result()]})
    android_only_shipping_ids = list({
        *[s.feature_id for s in android_only_shipping_future.result()]})
    desktop_origin_trials_ids = list({
        *[s.feature_id for s in desktop_origin_trial_future.result()]})
    android_origin_trials_ids = list({
        *[s.feature_id for s in android_origin_trial_future.result()]})
    webview_origin_trials_ids = list({
        *[s.feature_id for s in webview_origin_trial_future.result()]})
    desktop_dev_trials_ids = list({
        *[s.feature_id for s in desktop_dev_trial_future.result()]})
    android_dev_trials_ids = list({
        *[s.feature_id for s in android_dev_trial_future.result()]})

    # Query for FeatureEntry entities that match the stage feature IDs.
    # Querying with an empty list will raise an error, so check if each
    # list is not empty first.
    desktop_shipping_future = _get_entries_by_id_async(desktop_shipping_ids)
    android_only_shipping_future = _get_entries_by_id_async(
        android_only_shipping_ids)
    desktop_origin_trial_future = _get_entries_by_id_async(
        desktop_origin_trials_ids)
    android_origin_trial_future = _get_entries_by_id_async(
        android_origin_trials_ids)
    webview_origin_trial_future = _get_entries_by_id_async(
        webview_origin_trials_ids)
    desktop_dev_trial_future = _get_entries_by_id_async(
        desktop_dev_trials_ids)
    android_dev_trial_future = _get_entries_by_id_async(
        android_dev_trials_ids)

    desktop_shipping_features = _get_future_results(desktop_shipping_future)
    android_only_shipping_features = _get_future_results(
        android_only_shipping_future)
    desktop_origin_trial_features = _get_future_results(
        desktop_origin_trial_future)
    android_origin_trial_features = _get_future_results(
        android_origin_trial_future)
    webview_origin_trial_features = _get_future_results(
        webview_origin_trial_future)
    desktop_dev_trial_features = _get_future_results(desktop_dev_trial_future)
    android_dev_trial_features = _get_future_results(android_dev_trial_future)

    # Push feature to list corresponding to the implementation status of
    # feature in queried milestone
    for feature in desktop_shipping_features:
      if feature.impl_status_chrome == ENABLED_BY_DEFAULT:
        all_features[IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT]].append(feature)
      elif feature.impl_status_chrome == DEPRECATED:
        all_features[IMPLEMENTATION_STATUS[DEPRECATED]].append(feature)
      elif feature.impl_status_chrome == REMOVED:
        all_features[IMPLEMENTATION_STATUS[REMOVED]].append(feature)
      elif feature.impl_status_chrome == INTERVENTION:
        all_features[IMPLEMENTATION_STATUS[INTERVENTION]].append(feature)
      elif (feature.feature_type == FEATURE_TYPE_DEPRECATION_ID and
            Feature.dt_milestone_desktop_start != None):
          all_features[IMPLEMENTATION_STATUS[DEPRECATED]].append(feature)
      elif feature.feature_type == FEATURE_TYPE_INCUBATE_ID:
          all_features[IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT]].append(feature)

    # Push feature to list corresponding to the implementation status
    # of feature in queried milestone
    for feature in android_only_shipping_features:
      if feature.impl_status_chrome == ENABLED_BY_DEFAULT:
        all_features[IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT]].append(feature)
      elif feature.impl_status_chrome == DEPRECATED:
        all_features[IMPLEMENTATION_STATUS[DEPRECATED]].append(feature)
      elif feature.impl_status_chrome == REMOVED:
        all_features[IMPLEMENTATION_STATUS[REMOVED]].append(feature)
      elif (feature.feature_type == FEATURE_TYPE_DEPRECATION_ID and
            Feature.dt_milestone_android_start != None):
          all_features[IMPLEMENTATION_STATUS[DEPRECATED]].append(feature)
      elif feature.feature_type == FEATURE_TYPE_INCUBATE_ID:
          all_features[IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT]].append(feature)

    for feature in desktop_origin_trial_features:
      all_features[IMPLEMENTATION_STATUS[ORIGIN_TRIAL]].append(feature)

    for feature in android_origin_trial_features:
      all_features[IMPLEMENTATION_STATUS[ORIGIN_TRIAL]].append(feature)

    for feature in webview_origin_trial_features:
      all_features[IMPLEMENTATION_STATUS[ORIGIN_TRIAL]].append(feature)

    for feature in desktop_dev_trial_features:
      all_features[IMPLEMENTATION_STATUS[BEHIND_A_FLAG]].append(feature)

    for feature in android_dev_trial_features:
      all_features[IMPLEMENTATION_STATUS[BEHIND_A_FLAG]].append(feature)

    # Construct results as: {type: [json_feature, ...], ...}.
    for shipping_type in all_features:
      all_features[shipping_type].sort(key=lambda f: f.name)
      all_features[shipping_type] = [
          f for f in all_features[shipping_type] if not f.deleted]
      features_by_type[shipping_type] = [converters.feature_entry_to_json_basic(f)
          for f in all_features[shipping_type]]

    rediscache.set(cache_key, features_by_type)

  for shipping_type in features_by_type:
    if not show_unlisted:
      features_by_type[shipping_type] = filter_unlisted(
          features_by_type[shipping_type])

  return features_by_type


def get_all(limit: Optional[int]=None,
    order: str='-updated', filterby: Optional[tuple[str, Any]]=None,
    update_cache: bool=False, keys_only: bool=False) -> list[dict]:
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
    stages_list = Stage.query(Stage.feature_id.IN(needed_ids)).fetch(None)
    stages_dict = stage_helpers.organize_all_stages_by_feature(stages_list)

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
      feature['new_crbug_url'] = _new_crbug_url(
          unformatted_feature.blink_components, unformatted_feature.bug_url,
          unformatted_feature.impl_status_chrome,
          unformatted_feature.owner_emails)
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
  return result_list


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
    stages_future = Stage.query().fetch_async()
    for impl_status in IMPLEMENTATION_STATUS.keys():
      q = FeatureEntry.query(FeatureEntry.impl_status_chrome == impl_status)
      q = q.order(FeatureEntry.impl_status_chrome)
      q = q.order(FeatureEntry.name)
      futures.append(q.fetch_async(None))
    # Put "No active development" at end of list.
    futures = futures[1:] + futures[0:1]
    logging.info('Waiting on futures')
    query_results = [future.result() for future in futures]
    all_stages = stage_helpers.organize_all_stages_by_feature(
        stages_future.result())

    # Construct the proper ordering.
    feature_list = []
    for section in query_results:
      if len(section) > 0:
        section = [converters.feature_entry_to_json_basic(
            f, all_stages[f.key.integer_id()]) for f in section]
        section[0]['first_of_section'] = True
        if not show_unlisted:
          section = filter_unlisted(section)
        feature_list.extend(section)

    rediscache.set(cache_key, feature_list)

  return feature_list
