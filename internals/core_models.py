# -*- coding: utf-8 -*-
# Copyright 2020 Google Inc.
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

from google.cloud import ndb

from framework import rediscache
from framework import users

from framework import cloud_tasks_helpers
import settings
from internals.core_enums import *
from internals import review_models
from internals import fetchchannels


SIMPLE_TYPES = (int, float, bool, dict, str, list)


def del_none(d):
  """
  Delete dict keys with None values, and empty lists, recursively.
  """
  for key, value in list(d.items()):
    if value is None or (isinstance(value, list) and len(value) == 0):
      del d[key]
    elif isinstance(value, dict):
      del_none(value)
  return d

def feature_cache_key(cache_key, feature_id):
  return '%s|%s' % (cache_key, feature_id)

def feature_cache_prefix():
  return '%s|*' % (Feature.DEFAULT_CACHE_KEY)


class DictModel(ndb.Model):
  # def to_dict(self):
  #   return dict([(p, str(getattr(self, p))) for p in self.properties()])

  def is_saved(self):
    if self.key:
      return True
    return False

  def format_for_template(self, add_id=True):
    d = self.to_dict()
    if add_id:
      d['id'] = self.key.integer_id()
    return d

  def to_dict(self):
    output = {}

    for key, prop in self._properties.items():
      # Skip obsolete values that are still in our datastore
      if not hasattr(self, key):
        continue

      value = getattr(self, key)

      if value is None or isinstance(value, SIMPLE_TYPES):
        output[key] = value
      elif isinstance(value, datetime.date):
        # Convert date/datetime to ms-since-epoch ("new Date()").
        #ms = time.mktime(value.utctimetuple())
        #ms += getattr(value, 'microseconds', 0) / 1000
        #output[key] = int(ms)
        output[key] = str(value)
      elif isinstance(value, ndb.GeoPt):
        output[key] = {'lat': value.lat, 'lon': value.lon}
      elif isinstance(value, ndb.Model):
        output[key] = value.to_dict()
      elif isinstance(value, ndb.model.User):
        output[key] = value.email()
      else:
        raise ValueError('cannot encode ' + repr(prop))

    return output



class Feature(DictModel):
  """Container for a feature."""

  DEFAULT_CACHE_KEY = 'features'

  def __init__(self, *args, **kwargs):
    # Initialise Feature.blink_components with a default value.  If
    # name is present in kwargs then it would mean constructor is
    # being called for creating a new feature rather than for fetching
    # an existing feature.
    if 'name' in kwargs:
      if 'blink_components' not in kwargs:
        kwargs['blink_components'] = [settings.DEFAULT_COMPONENT]

    super(Feature, self).__init__(*args, **kwargs)

  @classmethod
  def _first_of_milestone(self, feature_list, milestone, start=0):
    for i in range(start, len(feature_list)):
      f = feature_list[i]
      if (str(f['shipped_milestone']) == str(milestone) or
          f['impl_status_chrome'] == str(milestone)):
        return i
      elif (f['shipped_milestone'] == None and
            str(f['shipped_android_milestone']) == str(milestone)):
        return i

    return -1

  @classmethod
  def _first_of_milestone_v2(self, feature_list, milestone, start=0):
    for i in range(start, len(feature_list)):
      f = feature_list[i]
      desktop_milestone = f['browsers']['chrome'].get('desktop', None)
      android_milestone = f['browsers']['chrome'].get('android', None)
      status = f['browsers']['chrome']['status'].get('text', None)

      if (str(desktop_milestone) == str(milestone) or status == str(milestone)):
        return i
      elif (desktop_milestone == None and
            str(android_milestone) == str(milestone)):
        return i

    return -1

  @classmethod
  def _annotate_first_of_milestones(self, feature_list, version=None):
    try:
      omaha_data = fetchchannels.get_omaha_data()

      win_versions = omaha_data[0]['versions']

      # Find the latest canary major version from the list of windows versions.
      canary_versions = [
          x for x in win_versions
          if x.get('channel') and x.get('channel').startswith('canary')]
      LATEST_VERSION = int(canary_versions[0].get('version').split('.')[0])

      milestones = list(range(1, LATEST_VERSION + 1))
      milestones.reverse()
      versions = [
        IMPLEMENTATION_STATUS[PROPOSED],
        IMPLEMENTATION_STATUS[IN_DEVELOPMENT],
        IMPLEMENTATION_STATUS[DEPRECATED],
        ]
      versions.extend(milestones)
      versions.append(IMPLEMENTATION_STATUS[NO_ACTIVE_DEV])
      versions.append(IMPLEMENTATION_STATUS[NO_LONGER_PURSUING])

      first_of_milestone_func = Feature._first_of_milestone
      if version == 2:
        first_of_milestone_func = Feature._first_of_milestone_v2

      last_good_idx = 0
      for i, ver in enumerate(versions):
        idx = first_of_milestone_func(feature_list, ver, start=last_good_idx)
        if idx != -1:
          feature_list[idx]['first_of_milestone'] = True
          last_good_idx = idx
    except Exception as e:
      logging.error(e)

  def migrate_views(self):
    """Migrate obsolete values for views on first edit."""
    if self.ff_views == MIXED_SIGNALS:
      self.ff_views = NO_PUBLIC_SIGNALS
    if self.ff_views == PUBLIC_SKEPTICISM:
      self.ff_views = OPPOSED

    if self.ie_views == MIXED_SIGNALS:
      self.ie_views = NO_PUBLIC_SIGNALS
    if self.ie_views == PUBLIC_SKEPTICISM:
      self.ie_views = OPPOSED

    if self.safari_views == MIXED_SIGNALS:
      self.safari_views = NO_PUBLIC_SIGNALS
    if self.safari_views == PUBLIC_SKEPTICISM:
      self.safari_views = OPPOSED

  # TODO(jrobbins): Eliminate format version 1.
  def format_for_template(self, version=2):
    self.migrate_views()
    logging.info('In format_for_template for %s',
                 repr(self)[:settings.MAX_LOG_LINE])
    d = self.to_dict()
    is_released = self.impl_status_chrome in RELEASE_IMPL_STATES
    d['is_released'] = is_released

    standard_maturity_val = self.standard_maturity
    if (standard_maturity_val == UNSET_STD and
        self.standardization > 0):
      standard_maturity_val = STANDARD_MATURITY_BACKFILL[self.standardization]

    if version == 2:
      if self.is_saved():
        d['id'] = self.key.integer_id()
      else:
        d['id'] = None
      d['category'] = FEATURE_CATEGORIES[self.category]
      d['category_int'] = self.category
      if self.feature_type is not None:
        d['feature_type'] = FEATURE_TYPES[self.feature_type]
        d['feature_type_int'] = self.feature_type
      if self.intent_stage is not None:
        d['intent_stage'] = INTENT_STAGES[self.intent_stage]
        d['intent_stage_int'] = self.intent_stage
      d['created'] = {
        'by': d.pop('created_by', None),
        'when': d.pop('created', None),
      }
      d['updated'] = {
        'by': d.pop('updated_by', None),
        'when': d.pop('updated', None),
      }
      d['accurate_as_of'] = d.pop('accurate_as_of', None)
      d['standards'] = {
        'spec': d.pop('spec_link', None),
        'status': {
          'text': STANDARDIZATION[self.standardization],
          'val': d.pop('standardization', None),
        },
        'maturity': {
          'text': STANDARD_MATURITY_CHOICES.get(standard_maturity_val),
          'short_text': STANDARD_MATURITY_SHORT.get(standard_maturity_val),
          'val': standard_maturity_val,
        },
      }
      del d['standard_maturity']
      d['tag_review_status'] = REVIEW_STATUS_CHOICES[self.tag_review_status]
      d['tag_review_status_int'] = self.tag_review_status
      d['security_review_status'] = REVIEW_STATUS_CHOICES[
          self.security_review_status]
      d['security_review_status_int'] = self.security_review_status
      d['privacy_review_status'] = REVIEW_STATUS_CHOICES[
          self.privacy_review_status]
      d['privacy_review_status_int'] = self.privacy_review_status
      d['resources'] = {
        'samples': d.pop('sample_links', []),
        'docs': d.pop('doc_links', []),
      }
      d['tags'] = d.pop('search_tags', [])
      d['editors'] = d.pop('editors', [])
      d['cc_recipients'] = d.pop('cc_recipients', [])
      d['creator'] = d.pop('creator', None)
      d['browsers'] = {
        'chrome': {
          'bug': d.pop('bug_url', None),
          'blink_components': d.pop('blink_components', []),
          'devrel': d.pop('devrel', []),
          'owners': d.pop('owner', []),
          'origintrial': self.impl_status_chrome == ORIGIN_TRIAL,
          'intervention': self.impl_status_chrome == INTERVENTION,
          'prefixed': d.pop('prefixed', False),
          'flag': self.impl_status_chrome == BEHIND_A_FLAG,
          'status': {
            'text': IMPLEMENTATION_STATUS[self.impl_status_chrome],
            'val': d.pop('impl_status_chrome', None)
          },
          'desktop': d.pop('shipped_milestone', None),
          'android': d.pop('shipped_android_milestone', None),
          'webview': d.pop('shipped_webview_milestone', None),
          'ios': d.pop('shipped_ios_milestone', None),
        },
        'ff': {
          'view': {
            'text': VENDOR_VIEWS[self.ff_views],
            'val': d.pop('ff_views', None),
            'url': d.pop('ff_views_link', None),
            'notes': d.pop('ff_views_notes', None),
          }
        },
        'edge': {  # Deprecated
          'view': {
            'text': VENDOR_VIEWS[self.ie_views],
            'val': d.pop('ie_views', None),
            'url': d.pop('ie_views_link', None),
            'notes': d.pop('ie_views_notes', None),
          }
        },
        'safari': {
          'view': {
            'text': VENDOR_VIEWS[self.safari_views],
            'val': d.pop('safari_views', None),
            'url': d.pop('safari_views_link', None),
            'notes': d.pop('safari_views_notes', None),
          }
        },
        'webdev': {
          'view': {
            'text': WEB_DEV_VIEWS[self.web_dev_views],
            'val': d.pop('web_dev_views', None),
            'url': d.pop('web_dev_views_link', None),
            'notes': d.pop('web_dev_views_notes', None),
          }
        },
        'other': {
          'view': {
            'notes': d.pop('other_views_notes', None),
          }
        },
      }

      if is_released and self.shipped_milestone:
        d['browsers']['chrome']['status']['milestone_str'] = self.shipped_milestone
      elif is_released and self.shipped_android_milestone:
        d['browsers']['chrome']['status']['milestone_str'] = self.shipped_android_milestone
      else:
        d['browsers']['chrome']['status']['milestone_str'] = d['browsers']['chrome']['status']['text']

      del_none(d) # Further prune response by removing null/[] values.

    else:
      if self.is_saved():
        d['id'] = self.key.integer_id()
      else:
        d['id'] = None
      d['category'] = FEATURE_CATEGORIES[self.category]
      if self.feature_type is not None:
        d['feature_type'] = FEATURE_TYPES[self.feature_type]
        d['feature_type_int'] = self.feature_type
      if self.intent_stage is not None:
        d['intent_stage'] = INTENT_STAGES[self.intent_stage]
        d['intent_stage_int'] = self.intent_stage
      d['impl_status_chrome'] = IMPLEMENTATION_STATUS[self.impl_status_chrome]
      d['tag_review_status'] = REVIEW_STATUS_CHOICES[self.tag_review_status]
      d['security_review_status'] = REVIEW_STATUS_CHOICES[
          self.security_review_status]
      d['privacy_review_status'] = REVIEW_STATUS_CHOICES[
          self.privacy_review_status]
      d['meta'] = {
        'origintrial': self.impl_status_chrome == ORIGIN_TRIAL,
        'intervention': self.impl_status_chrome == INTERVENTION,
        'needsflag': self.impl_status_chrome == BEHIND_A_FLAG,
        }
      if is_released and self.shipped_milestone:
        d['meta']['milestone_str'] = self.shipped_milestone
      elif is_released and self.shipped_android_milestone:
        d['meta']['milestone_str'] = self.shipped_android_milestone
      else:
        d['meta']['milestone_str'] = d['impl_status_chrome']
      d['ff_views'] = {'value': self.ff_views,
                       'text': VENDOR_VIEWS[self.ff_views]}
      # Deprecated
      d['ie_views'] = {'value': self.ie_views,
                       'text': VENDOR_VIEWS[self.ie_views]}
      d['safari_views'] = {'value': self.safari_views,
                           'text': VENDOR_VIEWS[self.safari_views]}
      d['standardization'] = {'value': self.standardization,
                              'text': STANDARDIZATION[self.standardization]}
      d['web_dev_views'] = {'value': self.web_dev_views,
                            'text': WEB_DEV_VIEWS[self.web_dev_views]}

    return d

  def format_for_edit(self):
    self.migrate_views()
    d = self.to_dict()
    #d['id'] = self.key().id
    d['owner'] = ', '.join(self.owner)
    d['editors'] = ', '.join(self.editors)
    d['cc_recipients'] = ', '.join(self.cc_recipients)
    d['explainer_links'] = '\r\n'.join(self.explainer_links)
    d['spec_mentors'] = ', '.join(self.spec_mentors)
    d['standard_maturity'] = self.standard_maturity or UNKNOWN_STD
    d['doc_links'] = '\r\n'.join(self.doc_links)
    d['sample_links'] = '\r\n'.join(self.sample_links)
    d['search_tags'] = ', '.join(self.search_tags)
    d['blink_components'] = self.blink_components[0]
    d['devrel'] = ', '.join(self.devrel)
    d['i2e_lgtms'] = ', '.join(self.i2e_lgtms)
    d['i2s_lgtms'] = ', '.join(self.i2s_lgtms)
    return d

  @classmethod
  def get_all(self, limit=None, order='-updated', filterby=None,
              update_cache=False, version=2, keys_only=False):
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
            f.format_for_template(version=version) for f in feature_list]

      rediscache.set(KEY, feature_list)

    return feature_list

  @classmethod
  def get_all_with_statuses(self, statuses, update_cache=False):
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
          feature for feature in self.get_all(update_cache=update_cache)
          if feature['browsers']['chrome']['status']['text'] in statuses]
      rediscache.set(KEY, feature_list)

    return feature_list

  @classmethod
  def get_feature(self, feature_id, update_cache=False):
    """Return a JSON dict for a feature.

    Because the cache may rarely have stale data, this should only be
    used for displaying data read-only, not for populating forms or
    procesing a POST to edit data.  For editing use case, load the
    data from NDB directly.
    """
    KEY = feature_cache_key(Feature.DEFAULT_CACHE_KEY, feature_id)
    feature = rediscache.get(KEY)

    if feature is None or update_cache:
      unformatted_feature = Feature.get_by_id(feature_id)
      if unformatted_feature:
        if unformatted_feature.deleted:
          return None
        feature = unformatted_feature.format_for_template()
        feature['updated_display'] = (
            unformatted_feature.updated.strftime("%Y-%m-%d"))
        feature['new_crbug_url'] = unformatted_feature.new_crbug_url()
        rediscache.set(KEY, feature)

    return feature

  @classmethod
  def filter_unlisted(self, feature_list):
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

  @classmethod
  def get_by_ids(self, feature_ids, update_cache=False):
    """Return a list of JSON dicts for the specified features.

    Because the cache may rarely have stale data, this should only be
    used for displaying data read-only, not for populating forms or
    procesing a POST to edit data.  For editing use case, load the
    data from NDB directly.
    """
    result_dict = {}
    futures = []

    for feature_id in feature_ids:
      lookup_key = feature_cache_key(Feature.DEFAULT_CACHE_KEY, feature_id)
      feature = rediscache.get(lookup_key)
      if feature is None or update_cache:
        futures.append(Feature.get_by_id_async(feature_id))
      else:
        result_dict[feature_id] = feature

    for future in futures:
      unformatted_feature = future.get_result()
      if unformatted_feature and not unformatted_feature.deleted:
        feature = unformatted_feature.format_for_template()
        feature['updated_display'] = (
            unformatted_feature.updated.strftime("%Y-%m-%d"))
        feature['new_crbug_url'] = unformatted_feature.new_crbug_url()
        store_key = feature_cache_key(Feature.DEFAULT_CACHE_KEY,  unformatted_feature.key.integer_id())
        rediscache.set(store_key, feature)
        result_dict[unformatted_feature.key.integer_id()] = feature

    result_list = [
        result_dict.get(feature_id) for feature_id in feature_ids
        if feature_id in result_dict]
    return result_list

  @classmethod
  def get_chronological(
      self, limit=None, update_cache=False, version=None, show_unlisted=False):
    """Return a list of JSON dicts for features, ordered by milestone.

    Because the cache may rarely have stale data, this should only be
    used for displaying data read-only, not for populating forms or
    procesing a POST to edit data.  For editing use case, load the
    data from NDB directly.
    """
    cache_key = '%s|%s|%s|%s' % (Feature.DEFAULT_CACHE_KEY,
                                 'cronorder', limit, version)

    feature_list = rediscache.get(cache_key)
    logging.info('getting chronological feature list')

    # On cache miss, do a db query.
    if not feature_list or update_cache:
      logging.info('recomputing chronological feature list')
      # Features that are in-dev or proposed.
      q = Feature.query()
      q = q.order(Feature.impl_status_chrome)
      q = q.order(Feature.name)
      q = q.filter(Feature.impl_status_chrome.IN((PROPOSED, IN_DEVELOPMENT)))
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
          if (IN_DEVELOPMENT < f.impl_status_chrome < NO_LONGER_PURSUING)]

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

      feature_list = [f.format_for_template(version) for f in all_features]

      self._annotate_first_of_milestones(feature_list, version=version)

      rediscache.set(cache_key, feature_list)

    if not show_unlisted:
      feature_list = self.filter_unlisted(feature_list)
    return feature_list

  @classmethod
  def get_in_milestone(
      self, show_unlisted=False, milestone=None):
    """Return {reason: [feaure_dict]} with all the reasons a feature can
    be part of a milestone.

    Because the cache may rarely have stale data, this should only be
    used for displaying data read-only, not for populating forms or
    procesing a POST to edit data.  For editing use case, load the
    data from NDB directly.
    """
    if milestone == None:
      return None

    features_by_type = {}
    cache_key = '%s|%s|%s' % (
        Feature.DEFAULT_CACHE_KEY, 'milestone', milestone)
    cached_features_by_type = rediscache.get(cache_key)
    if cached_features_by_type:
      features_by_type = cached_features_by_type
    else:
      all_features = {}
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
            f.format_for_template() for f in all_features[shipping_type]]

      rediscache.set(cache_key, features_by_type)

    for shipping_type in features_by_type:
      if not show_unlisted:
        features_by_type[shipping_type] = self.filter_unlisted(features_by_type[shipping_type])

    return features_by_type

  def crbug_number(self):
    if not self.bug_url:
      return
    m = re.search(r'[\/|?id=]([0-9]+)$', self.bug_url)
    if m:
      return m.group(1)

  def new_crbug_url(self):
    url = 'https://bugs.chromium.org/p/chromium/issues/entry'
    if len(self.blink_components) > 0:
      params = ['components=' + self.blink_components[0]]
    else:
      params = ['components=' + settings.DEFAULT_COMPONENT]
    crbug_number = self.crbug_number()
    if crbug_number and self.impl_status_chrome in (
        NO_ACTIVE_DEV,
        PROPOSED,
        IN_DEVELOPMENT,
        BEHIND_A_FLAG,
        ORIGIN_TRIAL,
        INTERVENTION):
      params.append('blocking=' + crbug_number)
    if self.owner:
      params.append('cc=' + ','.join(self.owner))
    return url + '?' + '&'.join(params)

  def stash_values(self):

    # Stash existing values when entity is created so we can diff property
    # values later in put() to know what's changed.
    # https://stackoverflow.com/a/41344898

    setattr(self, '_values_stashed', True)
    for prop_name, prop in list(self._properties.items()):
      old_val = getattr(self, prop_name, None)
      setattr(self, '_old_' + prop_name, old_val)

  def _get_changes_as_amendments(self):
    """Get all feature changes as Amendment entities."""
    # Diff values to see what properties have changed.
    amendments = []
    for prop_name, prop in list(self._properties.items()):
      if prop_name in (
          'created_by', 'updated_by', 'updated', 'created'):
        continue
      new_val = getattr(self, prop_name, None)
      old_val = getattr(self, '_old_' + prop_name, None)
      if new_val != old_val:
        if (new_val == '' or new_val == False) and old_val is None:
          continue
        new_val = convert_enum_int_to_string(prop_name, new_val)
        old_val = convert_enum_int_to_string(prop_name, old_val)
        amendments.append(
            review_models.Amendment(field_name=prop_name,
            old_value=str(old_val), new_value=str(new_val)))

    return amendments

  def __notify_feature_subscribers_of_changes(self, amendments, is_update):
    """Async notifies subscribers of new features and property changes to
       features by posting to a task queue.
    """
    changed_props = [{
        'prop_name': a.field_name,
        'old_val': a.old_value,
        'new_val': a.new_value
      } for a in amendments]

    params = {
      'changes': changed_props,
      'is_update': is_update,
      'feature': self.format_for_template(version=2)
    }

    # Create task to email subscribers.
    cloud_tasks_helpers.enqueue_task('/tasks/email-subscribers', params)

  def put(self, notify=True, **kwargs):
    is_update = self.is_saved()
    amendments = self._get_changes_as_amendments()

    # Document changes as new Activity entity with amendments only if all true:
    # 1. This is an update to an existing feature.
    # 2. We used stash_values() to document what fields changed.
    # 3. One or more fields were changed.
    should_write_activity = (is_update and hasattr(self, '_values_stashed')
        and len(amendments) > 0)

    if should_write_activity:
      user = users.get_current_user()
      email = user.email() if user else None
      activity = review_models.Activity(feature_id=self.key.integer_id(),
          author=email, content='')
      activity.amendments = amendments
      activity.put()

    key = super(Feature, self).put(**kwargs)
    if notify:
      self.__notify_feature_subscribers_of_changes(amendments, is_update)

    # Invalidate rediscache for the individual feature view.
    cache_key = feature_cache_key(Feature.DEFAULT_CACHE_KEY, self.key.integer_id())
    rediscache.delete(cache_key)

    return key

  # Metadata.
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)
  accurate_as_of = ndb.DateTimeProperty(auto_now=False)
  updated_by = ndb.UserProperty()
  created_by = ndb.UserProperty()

  # General info.
  category = ndb.IntegerProperty(required=True)
  creator = ndb.StringProperty()
  name = ndb.StringProperty(required=True)
  feature_type = ndb.IntegerProperty(default=FEATURE_TYPE_INCUBATE_ID)
  intent_stage = ndb.IntegerProperty(default=0)
  summary = ndb.StringProperty(required=True)
  unlisted = ndb.BooleanProperty(default=False)
  # TODO(jrobbins): Add an entry_state enum to track app-specific lifecycle
  # info for a feature entry as distinct from process-specific stage.
  deleted = ndb.BooleanProperty(default=False)
  motivation = ndb.StringProperty()
  star_count = ndb.IntegerProperty(default=0)
  search_tags = ndb.StringProperty(repeated=True)
  comments = ndb.StringProperty()
  owner = ndb.StringProperty(repeated=True)
  editors = ndb.StringProperty(repeated=True)
  cc_recipients = ndb.StringProperty(repeated=True)
  footprint = ndb.IntegerProperty()  # Deprecated

  # Tracability to intent discussion threads
  intent_to_implement_url = ndb.StringProperty()
  intent_to_implement_subject_line = ndb.StringProperty()
  intent_to_ship_url = ndb.StringProperty()
  intent_to_ship_subject_line = ndb.StringProperty()
  ready_for_trial_url = ndb.StringProperty()
  intent_to_experiment_url = ndb.StringProperty()
  intent_to_experiment_subject_line = ndb.StringProperty()
  intent_to_extend_experiment_url = ndb.StringProperty()
  intent_to_extend_experiment_subject_line = ndb.StringProperty()
  # Currently, only one is needed.
  i2e_lgtms = ndb.StringProperty(repeated=True)
  i2s_lgtms = ndb.StringProperty(repeated=True)

  # Chromium details.
  bug_url = ndb.StringProperty()
  launch_bug_url = ndb.StringProperty()
  initial_public_proposal_url = ndb.StringProperty()
  blink_components = ndb.StringProperty(repeated=True)
  devrel = ndb.StringProperty(repeated=True)

  impl_status_chrome = ndb.IntegerProperty(required=True)
  shipped_milestone = ndb.IntegerProperty()
  shipped_android_milestone = ndb.IntegerProperty()
  shipped_ios_milestone = ndb.IntegerProperty()
  shipped_webview_milestone = ndb.IntegerProperty()
  requires_embedder_support = ndb.BooleanProperty(default=False)

  # DevTrial details.
  devtrial_instructions = ndb.StringProperty()
  flag_name = ndb.StringProperty()
  interop_compat_risks = ndb.StringProperty()
  ergonomics_risks = ndb.StringProperty()
  activation_risks = ndb.StringProperty()
  security_risks = ndb.StringProperty()
  webview_risks = ndb.StringProperty()
  debuggability = ndb.StringProperty()
  all_platforms = ndb.BooleanProperty()
  all_platforms_descr = ndb.StringProperty()
  wpt = ndb.BooleanProperty()
  wpt_descr = ndb.StringProperty()
  dt_milestone_desktop_start = ndb.IntegerProperty()
  dt_milestone_android_start = ndb.IntegerProperty()
  dt_milestone_ios_start = ndb.IntegerProperty()
  # Webview DT is currently not offered in the UI because there is no way
  # to set flags.
  dt_milestone_webview_start = ndb.IntegerProperty()
  # Note: There are no dt end milestones because a dev trail implicitly
  # ends when the feature ships or is abandoned.

  visibility = ndb.IntegerProperty(required=False)  # Deprecated

  # Standards details.
  standardization = ndb.IntegerProperty(required=True)  # Deprecated
  standard_maturity = ndb.IntegerProperty(required=True, default=UNSET_STD)
  spec_link = ndb.StringProperty()
  api_spec = ndb.BooleanProperty(default=False)
  spec_mentors = ndb.StringProperty(repeated=True)

  security_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  privacy_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)

  tag_review = ndb.StringProperty()
  tag_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)

  prefixed = ndb.BooleanProperty()

  explainer_links = ndb.StringProperty(repeated=True)

  ff_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  # Deprecated
  ie_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  safari_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  web_dev_views = ndb.IntegerProperty(required=True)

  ff_views_link = ndb.StringProperty()
  ie_views_link = ndb.StringProperty()  # Deprecated
  safari_views_link = ndb.StringProperty()
  web_dev_views_link = ndb.StringProperty()

  ff_views_notes = ndb.StringProperty()
  ie_views_notes = ndb.StringProperty()  # Deprecated
  safari_views_notes = ndb.StringProperty()
  web_dev_views_notes = ndb.StringProperty()
  other_views_notes = ndb.StringProperty()

  doc_links = ndb.StringProperty(repeated=True)
  measurement = ndb.StringProperty()
  sample_links = ndb.StringProperty(repeated=True)
  non_oss_deps = ndb.StringProperty()

  experiment_goals = ndb.StringProperty()
  experiment_timeline = ndb.StringProperty()
  ot_milestone_desktop_start = ndb.IntegerProperty()
  ot_milestone_desktop_end = ndb.IntegerProperty()
  ot_milestone_android_start = ndb.IntegerProperty()
  ot_milestone_android_end = ndb.IntegerProperty()
  ot_milestone_webview_start = ndb.IntegerProperty()
  ot_milestone_webview_end = ndb.IntegerProperty()
  experiment_risks = ndb.StringProperty()
  experiment_extension_reason = ndb.StringProperty()
  ongoing_constraints = ndb.StringProperty()
  origin_trial_feedback_url = ndb.StringProperty()
  anticipated_spec_changes = ndb.StringProperty()

  finch_url = ndb.StringProperty()


# Note: This class is not used yet.
class FeatureEntry(ndb.Model):  # Copy from Feature
  """This is the main representation of a feature that we are tracking."""

  # Metadata: Creation and updates.
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty()
  accurate_as_of = ndb.DateTimeProperty()
  creator = ndb.StringProperty()
  updater = ndb.StringProperty()

  # Metadata: Access controls
  owners = ndb.StringProperty(repeated=True)  # copy from owner
  editors = ndb.StringProperty(repeated=True)
  cc_recipients = ndb.StringProperty(repeated=True)
  unlisted = ndb.BooleanProperty(default=False)
  deleted = ndb.BooleanProperty(default=False)

  # Descriptive info.
  name = ndb.StringProperty(required=True)
  summary = ndb.TextProperty(required=True)
  category = ndb.IntegerProperty(required=True)
  blink_components = ndb.StringProperty(repeated=True)
  star_count = ndb.IntegerProperty(default=0)
  search_tags = ndb.StringProperty(repeated=True)
  feature_notes = ndb.TextProperty()  # copy from comments

  # Metadata: Process information
  feature_type = ndb.IntegerProperty(default=FEATURE_TYPE_INCUBATE_ID)
  intent_stage = ndb.IntegerProperty(default=0)
  bug_url = ndb.StringProperty()  # Tracking bug
  launch_bug_url = ndb.StringProperty()  # FLT or go/launch

  # Implementation in Chrome
  impl_status_chrome = ndb.IntegerProperty(required=True)
  flag_name = ndb.StringProperty()
  ongoing_constraints = ndb.TextProperty()

  # Gate: Adoption
  motivation = ndb.TextProperty()
  devtrial_instructions = ndb.TextProperty()
  activation_risks = ndb.TextProperty()
  measurement = ndb.TextProperty()

  # Gate: Standardization & Interop
  initial_public_proposal_url = ndb.StringProperty()
  explainer_links = ndb.StringProperty(repeated=True)
  requires_embedder_support = ndb.BooleanProperty(default=False)
  standard_maturity = ndb.IntegerProperty(required=True, default=UNSET_STD)
  spec_link = ndb.StringProperty()
  api_spec = ndb.BooleanProperty(default=False)
  spec_mentors = ndb.StringProperty(repeated=True)
  interop_compat_risks = ndb.TextProperty()
  prefixed = ndb.BooleanProperty()
  all_platforms = ndb.BooleanProperty()
  all_platforms_descr = ndb.TextProperty()
  tag_review = ndb.StringProperty()
  tag_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  non_oss_deps = ndb.TextProperty()
  anticipated_spec_changes = ndb.TextProperty()

  ff_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  safari_views = ndb.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  web_dev_views = ndb.IntegerProperty(required=True)
  ff_views_link = ndb.StringProperty()
  safari_views_link = ndb.StringProperty()
  web_dev_views_link = ndb.StringProperty()
  ff_views_notes = ndb.StringProperty()
  safari_views_notes = ndb.TextProperty()
  web_dev_views_notes = ndb.TextProperty()
  other_views_notes = ndb.TextProperty()

  # Gate: Security & Privacy
  security_risks = ndb.TextProperty()
  security_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)
  privacy_review_status = ndb.IntegerProperty(default=REVIEW_PENDING)

  # Gate: Testing / Regressions
  ergonomics_risks = ndb.TextProperty()
  wpt = ndb.BooleanProperty()
  wpt_descr = ndb.TextProperty()
  webview_risks = ndb.TextProperty()

  # Gate: Devrel & Docs
  devrel = ndb.StringProperty(repeated=True)
  debuggability = ndb.TextProperty()
  doc_links = ndb.StringProperty(repeated=True)
  sample_links = ndb.StringProperty(repeated=True)

  DEFAULT_CACHE_KEY = 'FeatureEntries'

  def __init__(self, *args, **kwargs):
    # Initialise Feature.blink_components with a default value.  If
    # name is present in kwargs then it would mean constructor is
    # being called for creating a new feature rather than for fetching
    # an existing feature.
    if 'name' in kwargs:
      if 'blink_components' not in kwargs:
        kwargs['blink_components'] = [settings.DEFAULT_COMPONENT]

    super(FeatureEntry, self).__init__(*args, **kwargs)


  @classmethod
  def get_feature_entry(self, feature_id, update_cache=False):
    KEY = feature_cache_key(FeatureEntry.DEFAULT_CACHE_KEY, feature_id)
    feature = rediscache.get(KEY)

    if feature is None or update_cache:
      entry = FeatureEntry.get_by_id(feature_id)
      if entry:
        if entry.deleted:
          return None
        rediscache.set(KEY, entry)

    return entry

  @classmethod
  def filter_unlisted(self, entry_list):
    """Filters feature entries to display only features the user should see."""
    user = users.get_current_user()
    email = None
    if user:
      email = user.email()
    allowed_entries = []
    for fe in entry_list:
      # Owners and editors of a feature can see their unlisted features.
      if (not fe.unlisted or
          email in fe.owners or
          email in fe.editors or
          (email is not None and fe.creator == email)):
        allowed_entries.append(fe)

    return allowed_entries

  @classmethod
  def get_by_ids(self, entry_ids, update_cache=False):
    """Return a list of FeatureEntry instances for the specified features.

    Because the cache may rarely have stale data, this should only be
    used for displaying data read-only, not for populating forms or
    procesing a POST to edit data.  For editing use case, load the
    data from NDB directly.
    """
    result_dict = {}
    futures = []

    for fe_id in entry_ids:
      lookup_key = feature_cache_key(FeatureEntry.DEFAULT_CACHE_KEY, fe_id)
      entry = rediscache.get(lookup_key)
      if entry is None or update_cache:
        futures.append(FeatureEntry.get_by_id_async(fe_id))
      else:
        result_dict[fe_id] = entry

    for future in futures:
      entry = future.get_result()
      if entry and not entry.deleted:
        store_key = feature_cache_key(FeatureEntry.DEFAULT_CACHE_KEY, entry.key.integer_id())
        rediscache.set(store_key, entry)
        result_dict[entry.key.integer_id()] = entry

    result_list = [
        result_dict.get(fe_id) for fe_id in entry_ids
        if fe_id in result_dict]
    return result_list

  # Note: get_in_milestone will be in a new file legacy_queries.py.


# Note: This class is not used yet.
class MilestoneSet(ndb.Model):  # copy from milestone fields of Feature
  """Range of milestones during which a feature will be in a certain stage."""
  desktop_first = ndb.IntegerProperty()
  desktop_last = ndb.IntegerProperty()
  android_first = ndb.IntegerProperty()
  android_last = ndb.IntegerProperty()
  ios_first = ndb.IntegerProperty()
  ios_last = ndb.IntegerProperty()
  webview_first = ndb.IntegerProperty()
  webview_last = ndb.IntegerProperty()


# Note: This class is not used yet.
class Stage(ndb.Model):
  """A stage of a feature's development."""
  # Identifying information: what.
  feature_id = ndb.IntegerProperty(required=True)
  stage_type = ndb.IntegerProperty(required=True)

  # Pragmatic information: where and when.
  browser = ndb.StringProperty()  # Blank or "Chrome" for now.
  milestones = ndb.StructuredProperty(MilestoneSet)
  finch_url = ndb.StringProperty()  # copy from Feature

  # Feature stage launch team
  pm_emails = ndb.StringProperty(repeated=True)
  tl_emails = ndb.StringProperty(repeated=True)
  ux_emails = ndb.StringProperty(repeated=True)
  te_emails = ndb.StringProperty(repeated=True)

  # Gate-related fields that need separate values for repeated stages.
  # copy from Feature.
  experiment_goals = ndb.TextProperty()
  experiment_risks = ndb.TextProperty()
  experiment_extension_reason = ndb.TextProperty()
  intent_thread_url = ndb.StringProperty()
  origin_trial_feedback_url = ndb.StringProperty()
