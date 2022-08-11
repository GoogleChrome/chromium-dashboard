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

import collections
import datetime
import json
import logging
import re
import time

from google.cloud import ndb

from framework import ramcache
from framework import users

from framework import cloud_tasks_helpers
from framework import utils
import settings
from internals import fetchchannels

import hack_components


from collections import OrderedDict
from django import forms


SIMPLE_TYPES = (int, float, bool, dict, str, list)

WEBCOMPONENTS = 1
MISC = 2
SECURITY = 3
MULTIMEDIA = 4
DOM = 5
FILE = 6
OFFLINE = 7
DEVICE = 8
COMMUNICATION = 9
JAVASCRIPT = 10
NETWORKING = 11
INPUT = 12
PERFORMANCE = 13
GRAPHICS = 14
CSS = 15
HOUDINI = 16
SERVICEWORKER = 17
WEBRTC = 18
LAYERED = 19
WEBASSEMBLY = 20
CAPABILITIES = 21

FEATURE_CATEGORIES = {
  CSS: 'CSS',
  WEBCOMPONENTS: 'Web Components',
  MISC: 'Miscellaneous',
  SECURITY: 'Security',
  MULTIMEDIA: 'Multimedia',
  DOM: 'DOM',
  FILE: 'File APIs',
  OFFLINE: 'Offline / Storage',
  DEVICE: 'Device',
  COMMUNICATION: 'Realtime / Communication',
  JAVASCRIPT: 'JavaScript',
  NETWORKING: 'Network / Connectivity',
  INPUT: 'User input',
  PERFORMANCE: 'Performance',
  GRAPHICS: 'Graphics',
  HOUDINI: 'Houdini',
  SERVICEWORKER: 'Service Worker',
  WEBRTC: 'Web RTC',
  LAYERED: 'Layered APIs',
  WEBASSEMBLY: 'WebAssembly',
  CAPABILITIES: 'Capabilities (Fugu)'
  }

FEATURE_TYPE_INCUBATE_ID = 0
FEATURE_TYPE_EXISTING_ID = 1
FEATURE_TYPE_CODE_CHANGE_ID = 2
FEATURE_TYPE_DEPRECATION_ID = 3

FEATURE_TYPES = {
    FEATURE_TYPE_INCUBATE_ID: 'New feature incubation',
    FEATURE_TYPE_EXISTING_ID: 'Existing feature implementation',
    FEATURE_TYPE_CODE_CHANGE_ID: 'Web developer facing change to existing code',
    FEATURE_TYPE_DEPRECATION_ID: 'Feature deprecation',
}


# Intent stages and mapping from stage to stage name.
INTENT_NONE = 0
INTENT_INCUBATE = 7  # Start incubating
INTENT_IMPLEMENT = 1  # Start prototyping
INTENT_EXPERIMENT = 2  # Dev trials
INTENT_IMPLEMENT_SHIP = 4  # Eval readiness to ship
INTENT_EXTEND_TRIAL = 3  # Origin trials
INTENT_SHIP = 5  # Prepare to ship
INTENT_REMOVED = 6
INTENT_SHIPPED = 8
INTENT_PARKED = 9

INTENT_STAGES = collections.OrderedDict([
  (INTENT_NONE, 'None'),
  (INTENT_INCUBATE, 'Start incubating'),
  (INTENT_IMPLEMENT, 'Start prototyping'),
  (INTENT_EXPERIMENT, 'Dev trials'),
  (INTENT_IMPLEMENT_SHIP, 'Evaluate readiness to ship'),
  (INTENT_EXTEND_TRIAL, 'Origin Trial'),
  (INTENT_SHIP, 'Prepare to ship'),
  (INTENT_REMOVED, 'Removed'),
  (INTENT_SHIPPED, 'Shipped'),
  (INTENT_PARKED, 'Parked'),
])


NO_ACTIVE_DEV = 1
PROPOSED = 2
IN_DEVELOPMENT = 3
BEHIND_A_FLAG = 4
ENABLED_BY_DEFAULT = 5
DEPRECATED = 6
REMOVED = 7
ORIGIN_TRIAL = 8
INTERVENTION = 9
ON_HOLD = 10
NO_LONGER_PURSUING = 1000 # insure bottom of list

RELEASE_IMPL_STATES = {
    BEHIND_A_FLAG, ENABLED_BY_DEFAULT,
    DEPRECATED, REMOVED, ORIGIN_TRIAL, INTERVENTION,
}

# Ordered dictionary, make sure the order of this dictionary matches that of
# the sorted list above!
IMPLEMENTATION_STATUS = OrderedDict()
IMPLEMENTATION_STATUS[NO_ACTIVE_DEV] = 'No active development'
IMPLEMENTATION_STATUS[PROPOSED] = 'Proposed'
IMPLEMENTATION_STATUS[IN_DEVELOPMENT] = 'In development'
IMPLEMENTATION_STATUS[BEHIND_A_FLAG] = 'In developer trial (Behind a flag)'
IMPLEMENTATION_STATUS[ENABLED_BY_DEFAULT] = 'Enabled by default'
IMPLEMENTATION_STATUS[DEPRECATED] = 'Deprecated'
IMPLEMENTATION_STATUS[REMOVED] = 'Removed'
IMPLEMENTATION_STATUS[ORIGIN_TRIAL] = 'Origin trial'
IMPLEMENTATION_STATUS[INTERVENTION] = 'Browser Intervention'
IMPLEMENTATION_STATUS[ON_HOLD] = 'On hold'
IMPLEMENTATION_STATUS[NO_LONGER_PURSUING] = 'No longer pursuing'

MAJOR_NEW_API = 1
MAJOR_MINOR_NEW_API = 2
SUBSTANTIVE_CHANGES = 3
MINOR_EXISTING_CHANGES = 4
EXTREMELY_SMALL_CHANGE = 5

# Status for security and privacy reviews.
REVIEW_PENDING = 1
REVIEW_ISSUES_OPEN = 2
REVIEW_ISSUES_ADDRESSED = 3
REVIEW_NA = 4

REVIEW_STATUS_CHOICES = {
    REVIEW_PENDING: 'Pending',
    REVIEW_ISSUES_OPEN: 'Issues open',
    REVIEW_ISSUES_ADDRESSED: 'Issues addressed',
    REVIEW_NA: 'Not applicable',
    }


FOOTPRINT_CHOICES = {
  MAJOR_NEW_API: ('A major new independent API (e.g. adding many '
                  'independent concepts with many methods/properties/objects)'),
  MAJOR_MINOR_NEW_API: ('Major changes to an existing API OR a minor new '
                        'independent API (e.g. adding many new '
                        'methods/properties or introducing new concepts to '
                        'augment an existing API)'),
  SUBSTANTIVE_CHANGES: ('Substantive changes to an existing API (e.g. small '
                        'number of new methods/properties)'),
  MINOR_EXISTING_CHANGES: (
      'Minor changes to an existing API (e.g. adding a new keyword/allowed '
      'argument to a property/method)'),
  EXTREMELY_SMALL_CHANGE: ('Extremely small tweaks to an existing API (e.g. '
                           'how existing keywords/arguments are interpreted)'),
  }

MAINSTREAM_NEWS = 1
WARRANTS_ARTICLE = 2
IN_LARGER_ARTICLE = 3
SMALL_NUM_DEVS = 4
SUPER_SMALL = 5

# Signals from other implementations in an intent-to-ship
SHIPPED = 1
IN_DEV = 2
PUBLIC_SUPPORT = 3
MIXED_SIGNALS = 4  # Deprecated
NO_PUBLIC_SIGNALS = 5
PUBLIC_SKEPTICISM = 6  # Deprecated
OPPOSED = 7
NEUTRAL = 8
SIGNALS_NA = 9
GECKO_UNDER_CONSIDERATION = 10
GECKO_IMPORTANT = 11
GECKO_WORTH_PROTOTYPING = 12
GECKO_NONHARMFUL = 13
GECKO_DEFER = 14
GECKO_HARMFUL = 15


VENDOR_VIEWS_COMMON = {
  SHIPPED: 'Shipped/Shipping',
  IN_DEV: 'In development',
  PUBLIC_SUPPORT: 'Positive',
  NO_PUBLIC_SIGNALS: 'No signal',
  OPPOSED: 'Negative',
  NEUTRAL: 'Neutral',
  SIGNALS_NA: 'N/A',
  }

VENDOR_VIEWS_GECKO = VENDOR_VIEWS_COMMON.copy()
VENDOR_VIEWS_GECKO.update({
  GECKO_UNDER_CONSIDERATION: 'Under consideration',
  GECKO_IMPORTANT: 'Important',
  GECKO_WORTH_PROTOTYPING: 'Worth prototyping',
  GECKO_NONHARMFUL: 'Non-harmful',
  GECKO_DEFER: 'Defer',
  GECKO_HARMFUL: 'Harmful',
  })

# These vendors have no "custom" views values yet.
VENDOR_VIEWS_EDGE = VENDOR_VIEWS_COMMON
VENDOR_VIEWS_WEBKIT = VENDOR_VIEWS_COMMON

VENDOR_VIEWS = {}
VENDOR_VIEWS.update(VENDOR_VIEWS_GECKO)
VENDOR_VIEWS.update(VENDOR_VIEWS_EDGE)
VENDOR_VIEWS.update(VENDOR_VIEWS_WEBKIT)

DEFACTO_STD = 1
ESTABLISHED_STD = 2
WORKING_DRAFT = 3
EDITORS_DRAFT = 4
PUBLIC_DISCUSSION = 5
NO_STD_OR_DISCUSSION = 6

STANDARDIZATION = {
  DEFACTO_STD: 'De-facto standard',
  ESTABLISHED_STD: 'Established standard',
  WORKING_DRAFT: 'Working draft or equivalent',
  EDITORS_DRAFT: "Editor's draft",
  PUBLIC_DISCUSSION: 'Public discussion',
  NO_STD_OR_DISCUSSION: 'No public standards discussion',
  }

UNSET_STD = 0
UNKNOWN_STD = 1
PROPOSAL_STD = 2
INCUBATION_STD = 3
WORKINGDRAFT_STD = 4
STANDARD_STD = 5

STANDARD_MATURITY_CHOICES = {
  # No text for UNSET_STD.  One of the values below will be set on first edit.
  UNKNOWN_STD: 'Unknown standards status - check spec link for status',
  PROPOSAL_STD: 'Proposal in a personal repository, no adoption from community',
  INCUBATION_STD: 'Specification being incubated in a Community Group',
  WORKINGDRAFT_STD: ('Specification currently under development in a '
                     'Working Group'),
  STANDARD_STD: ('Final published standard: Recommendation, Living Standard, '
                 'Candidate Recommendation, or similar final form'),
}

STANDARD_MATURITY_SHORT = {
  UNSET_STD: 'Unknown status',
  UNKNOWN_STD: 'Unknown status',
  PROPOSAL_STD: 'Pre-incubation',
  INCUBATION_STD: 'Incubation',
  WORKINGDRAFT_STD: 'Working draft',
  STANDARD_STD: 'Published standard',
}

# For features that don't have a standard_maturity value set, but do have
# the old standardization field, infer a maturity.
STANDARD_MATURITY_BACKFILL = {
    DEFACTO_STD: STANDARD_STD,
    ESTABLISHED_STD: STANDARD_STD,
    WORKING_DRAFT: WORKINGDRAFT_STD,
    EDITORS_DRAFT: INCUBATION_STD,
    PUBLIC_DISCUSSION: INCUBATION_STD,
    NO_STD_OR_DISCUSSION: PROPOSAL_STD,
}

DEV_STRONG_POSITIVE = 1
DEV_POSITIVE = 2
DEV_MIXED_SIGNALS = 3
DEV_NO_SIGNALS = 4
DEV_NEGATIVE = 5
DEV_STRONG_NEGATIVE = 6

WEB_DEV_VIEWS = {
  DEV_STRONG_POSITIVE: 'Strongly positive',
  DEV_POSITIVE: 'Positive',
  DEV_MIXED_SIGNALS: 'Mixed signals',
  DEV_NO_SIGNALS: 'No signals',
  DEV_NEGATIVE: 'Negative',
  DEV_STRONG_NEGATIVE: 'Strongly negative',
  }


PROPERTY_NAMES_TO_ENUM_DICTS = {
    'category': FEATURE_CATEGORIES,
    'intent_stage': INTENT_STAGES,
    'impl_status_chrome': IMPLEMENTATION_STATUS,
    'security_review_status': REVIEW_STATUS_CHOICES,
    'privacy_review_status': REVIEW_STATUS_CHOICES,
    'standard_maturity': STANDARD_MATURITY_CHOICES,
    'standardization': STANDARDIZATION,
    'ff_views': VENDOR_VIEWS,
    'ie_views': VENDOR_VIEWS,
    'safari_views': VENDOR_VIEWS,
    'web_dev_views': WEB_DEV_VIEWS,
  }


def convert_enum_int_to_string(property_name, value):
  """If the property is an enum, return human-readable string, else value."""
  if type(value) != int:
    return value
  enum_dict = PROPERTY_NAMES_TO_ENUM_DICTS.get(property_name, {})
  converted_value = enum_dict.get(value, value)
  return converted_value


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
        output[key] = to_dict(value)
      elif isinstance(value, ndb.model.User):
        output[key] = value.email()
      else:
        raise ValueError('cannot encode ' + repr(prop))

    return output


class BlinkComponent(DictModel):

  DEFAULT_COMPONENT = 'Blink'

  name = ndb.StringProperty(required=True, default=DEFAULT_COMPONENT)
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)

  @property
  def subscribers(self):
    q = FeatureOwner.query(FeatureOwner.blink_components == self.key)
    q = q.order(FeatureOwner.name)
    return q.fetch(None)

  @property
  def owners(self):
    q = FeatureOwner.query(FeatureOwner.primary_blink_components == self.key)
    q = q.order(FeatureOwner.name)
    return q.fetch(None)

  @classmethod
  def fetch_all_components(self, update_cache=False):
    """Returns the list of blink components."""
    key = 'blinkcomponents'

    components = ramcache.get(key)
    if components is None or update_cache:
      # TODO(jrobbins): Re-implement fetching the list of blink components
      # by getting it via the monorail API.
      pass

    if not components:
      components = sorted(hack_components.HACK_BLINK_COMPONENTS)
      logging.info('using hard-coded blink components')

    return components

  @classmethod
  def update_db(self):
    """Updates the db with new Blink components from the json endpoint"""
    new_components = self.fetch_all_components(update_cache=True)
    existing_comps = self.query().fetch(None)
    for name in new_components:
      if not len([x.name for x in existing_comps if x.name == name]):
        logging.info('Adding new BlinkComponent: ' + name)
        c = BlinkComponent(name=name)
        c.put()

  @classmethod
  def get_by_name(self, component_name):
    """Fetch blink component with given name."""
    q = self.query()
    q = q.filter(self.name == component_name)
    component = q.fetch(1)
    if not component:
      logging.error('%s is an unknown BlinkComponent.' % (component_name))
      return None
    return component[0]


# UMA metrics.
class StableInstance(DictModel):
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)

  property_name = ndb.StringProperty(required=True)
  bucket_id = ndb.IntegerProperty(required=True)
  date = ndb.DateProperty(verbose_name='When the data was fetched',
                         required=True)
  day_percentage = ndb.FloatProperty()
  rolling_percentage = ndb.FloatProperty()


class AnimatedProperty(StableInstance):
  pass


class FeatureObserver(StableInstance):
  pass


# Feature dashboard.
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
        kwargs['blink_components'] = [BlinkComponent.DEFAULT_COMPONENT]

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
      d['security_review_status'] = REVIEW_STATUS_CHOICES[
          self.security_review_status]
      d['privacy_review_status'] = REVIEW_STATUS_CHOICES[
          self.privacy_review_status]
      d['resources'] = {
        'samples': d.pop('sample_links', []),
        'docs': d.pop('doc_links', []),
      }
      d['tags'] = d.pop('search_tags', [])
      d['editors'] = d.pop('editors', [])
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
              update_cache=False, version=2):
    KEY = '%s|%s|%s' % (Feature.DEFAULT_CACHE_KEY, order, limit)

    # TODO(ericbidelman): Support more than one filter.
    if filterby is not None:
      s = ('%s%s' % (filterby[0], filterby[1])).replace(' ', '')
      KEY += '|%s' % s

    feature_list = ramcache.get(KEY)

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

      features = query.fetch(limit)

      feature_list = [
          f.format_for_template(version=version) for f in features]

      ramcache.set(KEY, feature_list)

    return feature_list

  @classmethod
  def get_all_with_statuses(self, statuses, update_cache=False):
    if not statuses:
      return []

    KEY = '%s|%s' % (Feature.DEFAULT_CACHE_KEY, sorted(statuses))

    feature_list = ramcache.get(KEY)

    if feature_list is None or update_cache:
      # There's no way to do an OR in a single datastore query, and there's a
      # very good chance that the self.get_all() results will already be in
      # ramcache, so use an array comprehension to grab the features we
      # want from the array of everything.
      feature_list = [
          feature for feature in self.get_all(update_cache=update_cache)
          if feature['browsers']['chrome']['status']['text'] in statuses]
      ramcache.set(KEY, feature_list)

    return feature_list

  @classmethod
  def get_feature(self, feature_id, update_cache=False):
    KEY = '%s|%s' % (Feature.DEFAULT_CACHE_KEY, feature_id)
    feature = ramcache.get(KEY)

    if feature is None or update_cache:
      unformatted_feature = Feature.get_by_id(feature_id)
      if unformatted_feature:
        if unformatted_feature.deleted:
          return None
        feature = unformatted_feature.format_for_template()
        feature['updated_display'] = (
            unformatted_feature.updated.strftime("%Y-%m-%d"))
        feature['new_crbug_url'] = unformatted_feature.new_crbug_url()
        ramcache.set(KEY, feature)

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
    result_dict = {}
    futures = []

    for feature_id in feature_ids:
      lookup_key = '%s|%s' % (Feature.DEFAULT_CACHE_KEY, feature_id)
      feature = ramcache.get(lookup_key)
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
        store_key = '%s|%s' % (Feature.DEFAULT_CACHE_KEY,
                               unformatted_feature.key.integer_id())
        ramcache.set(store_key, feature)
        result_dict[unformatted_feature.key.integer_id()] = feature

    result_list = [
        result_dict.get(feature_id) for feature_id in feature_ids
        if feature_id in result_dict]
    return result_list

  @classmethod
  def get_chronological(
      self, limit=None, update_cache=False, version=None, show_unlisted=False):
    cache_key = '%s|%s|%s|%s' % (Feature.DEFAULT_CACHE_KEY,
                                 'cronorder', limit, version)

    feature_list = ramcache.get(cache_key)
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

      ramcache.set(cache_key, feature_list)

    if not show_unlisted:
      feature_list = self.filter_unlisted(feature_list)
    return feature_list

  @classmethod
  def get_in_milestone(
      self, show_unlisted=False, milestone=None):
    if milestone == None:
      return None

    features_by_type = {}
    cache_key = '%s|%s|%s' % (
        Feature.DEFAULT_CACHE_KEY, 'milestone', milestone)
    cached_features_by_type = ramcache.get(cache_key)
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

      ramcache.set(cache_key, features_by_type)

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
      params = ['components=' + BlinkComponent.DEFAULT_COMPONENT]
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

    for prop_name, prop in list(self._properties.items()):
      old_val = getattr(self, prop_name, None)
      setattr(self, '_old_' + prop_name, old_val)

  def __notify_feature_subscribers_of_changes(self, is_update):
    """Async notifies subscribers of new features and property changes to
       features by posting to a task queue.
    """
    # Diff values to see what properties have changed.
    changed_props = []
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
        # Convert any dateime props to string.
        if isinstance(new_val, datetime.datetime):
          new_val = str(new_val)
          if old_val is not None:
            old_val = str(old_val)
        changed_props.append({
            'prop_name': prop_name, 'old_val': old_val, 'new_val': new_val})

    params = {
      'changes': changed_props,
      'is_update': is_update,
      'feature': self.format_for_template(version=2)
    }

    # Create task to email subscribers.
    cloud_tasks_helpers.enqueue_task('/tasks/email-subscribers', params)

  def put(self, notify=True, **kwargs):
    is_update = self.is_saved()
    key = super(Feature, self).put(**kwargs)
    if notify:
      self.__notify_feature_subscribers_of_changes(is_update)

    # Invalidate ramcache for the individual feature view.
    cache_key = '%s|%s' % (Feature.DEFAULT_CACHE_KEY, self.key.integer_id())
    ramcache.delete(cache_key)

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


def single_field_query_async(
    field_name, operator, val, limit=None):
  """Create a query for one Feature field and run it, returning a promise."""
  field = QUERIABLE_FIELDS.get(field_name.lower())
  if field is None:
    logging.info('Ignoring field name %r', field_name)
    return []
  # TODO(jrobbins): support sorting by any fields of other model classes.
  query = Feature.query()
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
  query = Feature.query().order(field)

  keys_promise = query.fetch_async(keys_only=True)
  return keys_promise


class Approval(DictModel):
  """Describes the current state of one approval on a feature."""

  # Not used: NEEDS_REVIEW = 0
  NA = 1
  REVIEW_REQUESTED = 2
  REVIEW_STARTED = 3
  NEED_INFO = 4
  APPROVED = 5
  NOT_APPROVED = 6
  APPROVAL_VALUES = {
      # Not used: NEEDS_REVIEW: 'needs_review',
      NA: 'na',
      REVIEW_REQUESTED: 'review_requested',
      REVIEW_STARTED: 'review_started',
      NEED_INFO: 'need_info',
      APPROVED: 'approved',
      NOT_APPROVED: 'not_approved',
  }

  PENDING_STATES = [REVIEW_REQUESTED, REVIEW_STARTED, NEED_INFO]
  FINAL_STATES = [NA, APPROVED, NOT_APPROVED]

  feature_id = ndb.IntegerProperty(required=True)
  field_id = ndb.IntegerProperty(required=True)
  state = ndb.IntegerProperty(required=True)
  set_on = ndb.DateTimeProperty(required=True)
  set_by = ndb.StringProperty(required=True)

  @classmethod
  def get_approvals(
      cls, feature_id=None, field_id=None, states=None, set_by=None,
      limit=None):
    """Return the requested approvals."""
    query = Approval.query()
    if feature_id is not None:
      query = query.filter(Approval.feature_id == feature_id)
    if field_id is not None:
      query = query.filter(Approval.field_id == field_id)
    if states is not None:
      query = query.filter(Approval.state.IN(states))
    if set_by is not None:
      query = query.filter(Approval.set_by == set_by)
    # Query with STRONG consistency because ndb defaults to
    # EVENTUAL consistency and we run this query immediately after
    # saving the user's change that we want included in the query.
    approvals = query.fetch(limit, read_consistency=ndb.STRONG)
    return approvals

  @classmethod
  def sorted_by_pending_request_date(cls, descending):
    """Return feature_ids of pending approvals sorted by request date."""
    query = Approval.query(Approval.state == Approval.REVIEW_REQUESTED)
    if descending:
      query = query.order(-Approval.set_on)
    else:
      query = query.order(Approval.set_on)

    pending_approvals = query.fetch(projection=['feature_id'])
    feature_ids = utils.dedupe(pa.feature_id for pa in pending_approvals)
    return feature_ids

  @classmethod
  def sorted_by_review_date(cls, descending):
    """Return feature_ids of reviewed approvals sorted by last review."""
    query = Approval.query(Approval.state.IN(Approval.FINAL_STATES))
    if descending:
      query = query.order(-Approval.set_on)
    else:
      query = query.order(Approval.set_on)
    recent_approvals = query.fetch(projection=['feature_id'])

    feature_ids = utils.dedupe(ra.feature_id for ra in recent_approvals)
    return feature_ids

  @classmethod
  def is_valid_state(cls, new_state):
    """Return true if new_state is valid."""
    return new_state in cls.APPROVAL_VALUES

  @classmethod
  def set_approval(cls, feature_id, field_id, new_state, set_by_email):
    """Add or update an approval value."""
    if not cls.is_valid_state(new_state):
      raise ValueError('Invalid approval state')

    now = datetime.datetime.now()
    existing_list = cls.get_approvals(
        feature_id=feature_id, field_id=field_id, set_by=set_by_email)
    if existing_list:
      existing = existing_list[0]
      existing.set_on = now
      existing.state = new_state
      existing.put()
      logging.info('existing approval is %r', existing.key.integer_id())
      return

    new_appr = Approval(
        feature_id=feature_id, field_id=field_id, state=new_state,
        set_on=now, set_by=set_by_email)
    new_appr.put()
    logging.info('new_appr is %r', new_appr.key.integer_id())

  @classmethod
  def clear_request(cls, feature_id, field_id):
    """After the review requirement has been satisfied, remove the request."""
    review_requests = cls.get_approvals(
        feature_id=feature_id, field_id=field_id, states=[cls.REVIEW_REQUESTED])
    for rr in review_requests:
      rr.key.delete()


class ApprovalConfig(DictModel):
  """Allows customization of an approval field for one feature."""

  feature_id = ndb.IntegerProperty(required=True)
  field_id = ndb.IntegerProperty(required=True)
  owners = ndb.StringProperty(repeated=True)
  next_action = ndb.DateProperty()
  additional_review = ndb.BooleanProperty(default=False)

  @classmethod
  def get_configs(cls, feature_id):
    """Return approval configs for all approval fields."""
    query = ApprovalConfig.query(ApprovalConfig.feature_id == feature_id)
    configs = query.fetch(None)
    return configs

  @classmethod
  def set_config(
      cls, feature_id, field_id, owners, next_action, additional_review):
    """Add or update an approval config object."""
    config = ApprovalConfig(feature_id=feature_id, field_id=field_id)
    for existing in cls.get_configs(feature_id):
      if existing.field_id == field_id:
        config = existing

    config.owners = owners or []
    config.next_action = next_action
    config.additional_review = additional_review
    config.put()


class Comment(DictModel):
  """A review comment on a feature."""
  feature_id = ndb.IntegerProperty(required=True)
  field_id = ndb.IntegerProperty()  # The approval field_id, or general comment.
  created = ndb.DateTimeProperty(auto_now=True)
  author = ndb.StringProperty()
  content = ndb.StringProperty()
  deleted_by = ndb.StringProperty()
  # If the user set an approval value, we capture that here so that we can
  # display a change log.  This could be generalized to a list of separate
  # Amendment entities, but that complexity is not needed yet.
  old_approval_state = ndb.IntegerProperty()
  new_approval_state = ndb.IntegerProperty()

  @classmethod
  def get_comments(cls, feature_id, field_id=None):
    """Return review comments for an approval."""
    query = Comment.query().order(Comment.created)
    query = query.filter(Comment.feature_id == feature_id)
    if field_id:
      query = query.filter(Comment.field_id == field_id)
    comments = query.fetch(None)
    return comments


class UserPref(DictModel):
  """Describes a user's application preferences."""

  email = ndb.StringProperty(required=True)

  # True means that user should be sent a notification email after each change
  # to each feature that the user starred.
  notify_as_starrer = ndb.BooleanProperty(default=True)

  # True means that we sent an email message to this user in the past
  # and it bounced.  We will not send to that address again.
  bounced = ndb.BooleanProperty(default=False)

  # A list of strings identifying on-page help cue cards that the user
  # has dismissed (clicked "X" or "GOT IT").
  dismissed_cues = ndb.StringProperty(repeated=True)

  @classmethod
  def get_signed_in_user_pref(cls):
    """Return a UserPref for the signed in user or None if anon."""
    signed_in_user = users.get_current_user()
    if not signed_in_user:
      return None

    user_pref_list = UserPref.query().filter(
        UserPref.email == signed_in_user.email()).fetch(1)
    if user_pref_list:
      user_pref = user_pref_list[0]
    else:
      user_pref = UserPref(email=signed_in_user.email())
    return user_pref

  @classmethod
  def dismiss_cue(cls, cue):
    """Add cue to the signed in user's dismissed_cues."""
    user_pref = cls.get_signed_in_user_pref()
    if not user_pref:
      return  # Anon users cannot store dismissed cue names.

    if cue not in user_pref.dismissed_cues:
      user_pref.dismissed_cues.append(cue)
      user_pref.put()

  @classmethod
  def get_prefs_for_emails(cls, emails):
    """Return a list of UserPrefs for each of the given emails."""
    result = []
    CHUNK_SIZE = 25  # Query 25 at a time because IN operator is limited to 30.
    chunks = [emails[i : i + CHUNK_SIZE]
              for i in range(0, len(emails), CHUNK_SIZE)]
    for chunk_emails in chunks:
      q = UserPref.query()
      q = q.filter(UserPref.email.IN(chunk_emails))
      chunk_prefs = q.fetch(None)
      result.extend(chunk_prefs)
      found_set = set(up.email for up in chunk_prefs)

      # Make default prefs for any user that does not already have an entity.
      new_prefs = [UserPref(email=e) for e in chunk_emails
                   if e not in found_set]
      for np in new_prefs:
        np.put()
        result.append(np)

    return result


class UserPrefForm(forms.Form):
  notify_as_starrer = forms.BooleanField(
      required=False,
      label='Notify as starrer',
      help_text='Send you notification emails for features that you starred?')


class AppUser(DictModel):
  """Describes a user for permission checking."""

  email = ndb.StringProperty(required=True)
  is_admin = ndb.BooleanProperty(default=False)
  is_site_editor = ndb.BooleanProperty(default=False)
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)
  last_visit = ndb.DateTimeProperty()

  def put(self, **kwargs):
    """when we update an AppUser, also invalidate ramcache."""
    key = super(DictModel, self).put(**kwargs)
    cache_key = 'user|%s' % self.email
    ramcache.delete(cache_key)

  def delete(self, **kwargs):
    """when we delete an AppUser, also invalidate ramcache."""
    key = super(DictModel, self).key.delete(**kwargs)
    cache_key = 'user|%s' % self.email
    ramcache.delete(cache_key)

  @classmethod
  def get_app_user(cls, email):
    """Return the AppUser for the specified user, or None."""
    cache_key = 'user|%s' % email
    cached_app_user = ramcache.get(cache_key)
    if cached_app_user:
      return cached_app_user

    query = cls.query()
    query = query.filter(cls.email == email)
    found_app_user_or_none = query.get()
    ramcache.set(cache_key, found_app_user_or_none)
    return found_app_user_or_none


def list_with_component(l, component):
  return [x for x in l if x.id() == component.key.integer_id()]

def list_without_component(l, component):
  return [x for x in l if x.id() != component.key.integer_id()]


class FeatureOwner(DictModel):
  """Describes subscribers of a web platform feature."""
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)
  name = ndb.StringProperty(required=True)
  email = ndb.StringProperty(required=True)
  twitter = ndb.StringProperty()
  blink_components = ndb.KeyProperty(repeated=True)
  primary_blink_components = ndb.KeyProperty(repeated=True)
  watching_all_features = ndb.BooleanProperty(default=False)

  # def __eq__(self, other):
  #   return self.key().id() == other.key().id()

  def add_to_component_subscribers(self, component_name):
    """Adds the user to the list of Blink component subscribers."""
    c = BlinkComponent.get_by_name(component_name)
    if c:
      # Add the user if they're not already in the list.
      if not len(list_with_component(self.blink_components, c)):
        self.blink_components.append(c.key)
        return self.put()
    return None

  def remove_from_component_subscribers(
      self, component_name, remove_as_owner=False):
    """Removes the user from the list of Blink component subscribers or as
       the owner of the component.
    """
    c = BlinkComponent.get_by_name(component_name)
    if c:
      if remove_as_owner:
        self.primary_blink_components = (
            list_without_component(self.primary_blink_components, c))
      else:
        self.blink_components = list_without_component(self.blink_components, c)
        self.primary_blink_components = (
            list_without_component(self.primary_blink_components, c))
      return self.put()
    return None

  def add_as_component_owner(self, component_name):
    """Adds the user as the Blink component owner."""
    c = BlinkComponent.get_by_name(component_name)
    if c:
      # Update both the primary list and blink components subscribers if the
      # user is not already in them.
      self.add_to_component_subscribers(component_name)
      if not len(list_with_component(self.primary_blink_components, c)):
        self.primary_blink_components.append(c.key)
      return self.put()
    return None

  def remove_as_component_owner(self, component_name):
    return self.remove_from_component_subscribers(
        component_name, remove_as_owner=True)


class OwnersFile(DictModel):
  """Describes the properties to store raw API_OWNERS content."""
  url = ndb.StringProperty(required=True)
  raw_content = ndb.TextProperty(required=True)
  created_on = ndb.DateTimeProperty(auto_now_add=True)

  def put(self):
    """Add the owner file's content in ndb and delete all other entities."""
    # Delete all other entities.
    ndb.delete_multi(OwnersFile.query(
        OwnersFile.url == self.url).fetch(keys_only=True))
    return super(OwnersFile, self).put()

  @classmethod
  def get_raw_api_owners(cls, url):
    """Retrieve raw the owner file's content, if it is created with an hour."""
    q = cls.query()
    q = q.filter(cls.url == url)
    owners_file_list = q.fetch(1)
    if not owners_file_list:
      logging.info('API_OWNERS content does not exist for URL %s.' % (url))
      return None

    owners_file = owners_file_list[0]
    # Check if it is created within an hour.
    an_hour_before = datetime.datetime.now() - datetime.timedelta(hours=1)
    if owners_file.created_on < an_hour_before:
      return None

    return owners_file.raw_content


class HistogramModel(ndb.Model):
  """Container for a histogram."""

  bucket_id = ndb.IntegerProperty(required=True)
  property_name = ndb.StringProperty(required=True)

  @classmethod
  def get_all(self):
    output = {}
    buckets = self.query().fetch(None)
    for bucket in buckets:
      output[bucket.bucket_id] = bucket.property_name
    return output

class CssPropertyHistogram(HistogramModel):
  pass

class FeatureObserverHistogram(HistogramModel):
  pass


QUERIABLE_FIELDS = {
    'created.when': Feature.created,
    'updated.when': Feature.updated,
    'deleted': Feature.deleted,

    # TODO(jrobbins): We cannot query user fields because Cloud NDB does not
    # seem to support it.  We should migrate these to string fields.
    #'created.by': Feature.created_by,
    #'updated.by': Feature.updated_by,

    'category': Feature.category,
    'name': Feature.name,
    'feature_type': Feature.feature_type,
    'intent_stage': Feature.intent_stage,
    'summary': Feature.summary,
    'unlisted': Feature.unlisted,
    'motivation': Feature.motivation,
    'star_count': Feature.star_count,
    'tags': Feature.search_tags,
    'owner': Feature.owner,
    'creator': Feature.creator,
    'browsers.chrome.owners': Feature.owner,
    'editors': Feature.editors,
    'intent_to_implement_url': Feature.intent_to_implement_url,
    'intent_to_ship_url': Feature.intent_to_ship_url,
    'ready_for_trial_url': Feature.ready_for_trial_url,
    'intent_to_experiment_url': Feature.intent_to_experiment_url,
    'intent_to_extend_experiment_url': Feature.intent_to_extend_experiment_url,
    'i2e_lgtms': Feature.i2e_lgtms,
    'i2s_lgtms': Feature.i2s_lgtms,
    'browsers.chrome.bug': Feature.bug_url,
    'launch_bug_url': Feature.launch_bug_url,
    'initial_public_proposal_url': Feature.initial_public_proposal_url,
    'browsers.chrome.blink_components': Feature.blink_components,
    'browsers.chrome.devrel': Feature.devrel,
    'browsers.chrome.prefixed': Feature.prefixed,

    'browsers.chrome.status': Feature.impl_status_chrome,
    'browsers.chrome.desktop': Feature.shipped_milestone,
    'browsers.chrome.android': Feature.shipped_android_milestone,
    'browsers.chrome.ios': Feature.shipped_ios_milestone,
    'browsers.chrome.webview': Feature.shipped_webview_milestone,
    'requires_embedder_support': Feature.requires_embedder_support,

    'browsers.chrome.flag_name': Feature.flag_name,
    'all_platforms': Feature.all_platforms,
    'all_platforms_descr': Feature.all_platforms_descr,
    'wpt': Feature.wpt,
    'browsers.chrome.devtrial.desktop.start': Feature.dt_milestone_desktop_start,
    'browsers.chrome.devtrial.android.start': Feature.dt_milestone_android_start,
    'browsers.chrome.devtrial.ios.start': Feature.dt_milestone_ios_start,
    'browsers.chrome.devtrial.webview.start': Feature.dt_milestone_webview_start,

    'standards.maturity': Feature.standard_maturity,
    'standards.spec': Feature.spec_link,
    'standards.anticipated_spec_changes': Feature.anticipated_spec_changes,
    'api_spec': Feature.api_spec,
    'spec_mentors': Feature.spec_mentors,
    'security_review_status': Feature.security_review_status,
    'privacy_review_status': Feature.privacy_review_status,
    'tag_review.url': Feature.tag_review,
    'tag_review.status': Feature.tag_review_status,
    'explainer': Feature.explainer_links,

    'browsers.ff.view': Feature.ff_views,
    'browsers.safari.view': Feature.safari_views,
    'browsers.webdev.view': Feature.web_dev_views,
    'browsers.ff.view.url': Feature.ff_views_link,
    'browsers.safari.view.url': Feature.safari_views_link,
    'browsers.webdev.url.url': Feature.web_dev_views_link,

    'resources.docs': Feature.doc_links,
    'non_oss_deps': Feature.non_oss_deps,

    'browsers.chrome.ot.desktop.start': Feature.ot_milestone_desktop_start,
    'browsers.chrome.ot.desktop.end': Feature.ot_milestone_desktop_end,
    'browsers.chrome.ot.android.start': Feature.ot_milestone_android_start,
    'browsers.chrome.ot.android.end': Feature.ot_milestone_android_end,
    'browsers.chrome.ot.webview.start': Feature.ot_milestone_webview_start,
    'browsers.chrome.ot.webview.end': Feature.ot_milestone_webview_end,
    'browsers.chrome.ot.feedback_url': Feature.origin_trial_feedback_url,
    'finch_url': Feature.finch_url,
    }

SORTABLE_FIELDS = QUERIABLE_FIELDS.copy()
SORTABLE_FIELDS.update({
    'approvals.requested_on': Approval.sorted_by_pending_request_date,
    'approvals.reviewed_on': Approval.sorted_by_review_date,
    })
