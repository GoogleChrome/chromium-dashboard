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

import logging
from typing import Any, Optional
from google.cloud import ndb  # type: ignore

from api.converters import feature_to_legacy_json
from framework import rediscache
from framework import users
from internals.core_enums import *
from internals.core_models import Feature

def get_by_ids(feature_ids: list[int],
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
      feature = feature_to_legacy_json(unformatted_feature)
      feature['updated_display'] = (
          unformatted_feature.updated.strftime("%Y-%m-%d"))
      feature['new_crbug_url'] = unformatted_feature.new_crbug_url()
      store_key = Feature.feature_cache_key(
          Feature.DEFAULT_CACHE_KEY,  unformatted_feature.key.integer_id())
      rediscache.set(store_key, feature)
      result_dict[unformatted_feature.key.integer_id()] = feature

  result_list = [
      result_dict[feature_id] for feature_id in feature_ids
      if feature_id in result_dict]
  return result_list

def get_all(limit=None, order='-updated', filterby=None,
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
          feature_to_legacy_json(f) for f in feature_list]

    rediscache.set(KEY, feature_list)

  return feature_list

def get_feature(feature_id: int, update_cache: bool=False) -> Optional[Feature]:
  """Return a JSON dict for a feature.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  KEY = Feature.feature_cache_key(Feature.DEFAULT_CACHE_KEY, feature_id)
  feature = rediscache.get(KEY)

  if feature is None or update_cache:
    unformatted_feature = Feature.get_by_id(feature_id)
    if unformatted_feature:
      if unformatted_feature.deleted:
        return None
      feature = feature_to_legacy_json(unformatted_feature)
      feature['updated_display'] = (
          unformatted_feature.updated.strftime("%Y-%m-%d"))
      feature['new_crbug_url'] = unformatted_feature.new_crbug_url()
      rediscache.set(KEY, feature)

  return feature

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

def get_chronological(limit=None, update_cache: bool=False,
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

    feature_list = [feature_to_legacy_json(f) for f in all_features]

    Feature._annotate_first_of_milestones(feature_list)

    rediscache.set(cache_key, feature_list)

  if not show_unlisted:
    feature_list = filter_unlisted(feature_list)
  return feature_list

def get_in_milestone(milestone: int,
    show_unlisted: bool=False) -> dict[str, list[dict[str, Any]]]:
  """Return {reason: [feaure_dict]} with all the reasons a feature can
  be part of a milestone.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  features_by_type = {}
  cache_key = '%s|%s|%s' % (
      Feature.DEFAULT_CACHE_KEY, 'milestone', milestone)
  cached_features_by_type = rediscache.get(cache_key)
  if cached_features_by_type:
    features_by_type = cached_features_by_type
  else:
    all_features: dict[str, list[Feature]] = {}
    all_features[IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT]] = []
    all_features[IMPLEMENTATION_STATUS[DEPRECATED]] = []
    all_features[IMPLEMENTATION_STATUS[REMOVED]] = []
    all_features[IMPLEMENTATION_STATUS[INTERVENTION]] = []
    all_features[IMPLEMENTATION_STATUS[ORIGIN_TRIAL]] = []
    all_features[IMPLEMENTATION_STATUS[BEHIND_A_FLAG]] = []

    logging.info('Getting chronological feature list in milestone %d',
                milestone)
    # Start each query asynchronously in parallel.
    q = Feature.query()
    q = q.order(Feature.name)
    q = q.filter(Feature.shipped_milestone == milestone)
    desktop_shipping_features_future = q.fetch_async(None)

    # Features with an android shipping milestone but no desktop milestone.
    q = Feature.query()
    q = q.order(Feature.name)
    q = q.filter(Feature.shipped_android_milestone == milestone)
    q = q.filter(Feature.shipped_milestone == None)
    android_only_shipping_features_future = q.fetch_async(None)

    # Features that are in origin trial (Desktop) in this milestone
    q = Feature.query()
    q = q.order(Feature.name)
    q = q.filter(Feature.ot_milestone_desktop_start == milestone)
    desktop_origin_trial_features_future = q.fetch_async(None)

    # Features that are in origin trial (Android) in this milestone
    q = Feature.query()
    q = q.order(Feature.name)
    q = q.filter(Feature.ot_milestone_android_start == milestone)
    q = q.filter(Feature.ot_milestone_desktop_start == None)
    android_origin_trial_features_future = q.fetch_async(None)

    # Features that are in origin trial (Webview) in this milestone
    q = Feature.query()
    q = q.order(Feature.name)
    q = q.filter(Feature.ot_milestone_webview_start == milestone)
    q = q.filter(Feature.ot_milestone_desktop_start == None)
    webview_origin_trial_features_future = q.fetch_async(None)

    # Features that are in dev trial (Desktop) in this milestone
    q = Feature.query()
    q = q.order(Feature.name)
    q = q.filter(Feature.dt_milestone_desktop_start == milestone)
    desktop_dev_trial_features_future = q.fetch_async(None)

    # Features that are in dev trial (Android) in this milestone
    q = Feature.query()
    q = q.order(Feature.name)
    q = q.filter(Feature.dt_milestone_android_start == milestone)
    q = q.filter(Feature.dt_milestone_desktop_start == None)
    android_dev_trial_features_future = q.fetch_async(None)

    # Wait for all futures to complete.
    desktop_shipping_features = desktop_shipping_features_future.result()
    android_only_shipping_features = (
        android_only_shipping_features_future.result())
    desktop_origin_trial_features = (
        desktop_origin_trial_features_future.result())
    android_origin_trial_features = (
        android_origin_trial_features_future.result())
    webview_origin_trial_features = (
        webview_origin_trial_features_future.result())
    desktop_dev_trial_features = desktop_dev_trial_features_future.result()
    android_dev_trial_features = android_dev_trial_features_future.result()

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
      features_by_type[shipping_type] = [
          feature_to_legacy_json(f) for f in all_features[shipping_type]]

    rediscache.set(cache_key, features_by_type)

  for shipping_type in features_by_type:
    if not show_unlisted:
      features_by_type[shipping_type] = filter_unlisted(features_by_type[shipping_type])

  return features_by_type

def get_all_with_statuses(statuses, update_cache=False):
  """Return JSON dicts for entities with the given statuses.

  Because the cache may rarely have stale data, this should only be
  used for displaying data read-only, not for populating forms or
  procesing a POST to edit data.  For editing use case, load the
  data from NDB directly.
  """
  if not statuses:
    return []

  KEY = '%s|%s' % (Feature.DEFAULT_CACHE_KEY, sorted(statuses))

  feature_list = rediscache.get(KEY)

  if feature_list is None or update_cache:
    # There's no way to do an OR in a single datastore query, and there's a
    # very good chance that the self.get_all() results will already be in
    # rediscache, so use an array comprehension to grab the features we
    # want from the array of everything.
    feature_list = [
        feature for feature in get_all(update_cache=update_cache)
        if feature['browsers']['chrome']['status']['text'] in statuses]
    rediscache.set(KEY, feature_list)

  return feature_list
