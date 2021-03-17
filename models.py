from __future__ import division
from __future__ import print_function

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

from google.appengine.ext import db
# from google.appengine.ext.db import djangoforms
from google.appengine.api import mail
from framework import ramcache
import requests
from google.appengine.api import users

from framework import cloud_tasks_helpers
import settings
import util

import hack_components
import hack_wf_components


#from django.forms import ModelForm
from collections import OrderedDict
from django import forms
# import google.appengine.ext.django as django


SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)

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
  for key, value in d.items():
    if value is None or (isinstance(value, list) and len(value) == 0):
      del d[key]
    elif isinstance(value, dict):
      del_none(value)
  return d

class DictModel(db.Model):
  # def to_dict(self):
  #   return dict([(p, unicode(getattr(self, p))) for p in self.properties()])

  def format_for_template(self):
    d = self.to_dict()
    d['id'] = self.key().id()
    return d

  def to_dict(self):
    output = {}

    for key, prop in self.properties().iteritems():
      value = getattr(self, key)

      if value is None or isinstance(value, SIMPLE_TYPES):
        output[key] = value
      elif isinstance(value, datetime.date):
        # Convert date/datetime to ms-since-epoch ("new Date()").
        #ms = time.mktime(value.utctimetuple())
        #ms += getattr(value, 'microseconds', 0) / 1000
        #output[key] = int(ms)
        output[key] = unicode(value)
      elif isinstance(value, db.GeoPt):
        output[key] = {'lat': value.lat, 'lon': value.lon}
      elif isinstance(value, db.Model):
        output[key] = to_dict(value)
      elif isinstance(value, users.User):
        output[key] = value.email()
      else:
        raise ValueError('cannot encode ' + repr(prop))

    return output


class BlinkComponent(DictModel):

  DEFAULT_COMPONENT = 'Blink'
  COMPONENTS_URL = 'https://blinkcomponents-b48b5.firebaseapp.com'
  COMPONENTS_ENDPOINT = '%s/blinkcomponents' % COMPONENTS_URL
  WF_CONTENT_ENDPOINT = '%s/wfcomponents' % COMPONENTS_URL

  name = db.StringProperty(required=True, default=DEFAULT_COMPONENT)
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  @property
  def subscribers(self):
    return FeatureOwner.all().filter('blink_components = ', self.key()).order('name').fetch(None)

  @property
  def owners(self):
    return FeatureOwner.all().filter('primary_blink_components = ', self.key()).order('name').fetch(None)

  @classmethod
  def fetch_all_components(self, update_cache=False):
    """Returns the list of blink components from live endpoint if unavailable in the cache."""
    key = 'blinkcomponents'

    components = ramcache.get(key)
    if components is None or update_cache:
      components = []
      url = self.COMPONENTS_ENDPOINT + '?cache-buster=%s' % time.time()
      result = requests.get(url, timeout=60)
      if result.status_code == 200:
        components = sorted(json.loads(result.content))
        ramcache.set(key, components)
      else:
        logging.error('Fetching blink components returned: %s' % result.status_code)

    if not components:
      components = sorted(hack_components.HACK_BLINK_COMPONENTS)
      logging.info('using hard-coded blink components')

    return components

  @classmethod
  def fetch_wf_content_for_components(self, update_cache=False):
    """Returns the /web content that use each blink component."""
    key = 'wfcomponents'

    components = ramcache.get(key)
    if components is None or update_cache:
      components = {}
      url = self.WF_CONTENT_ENDPOINT + '?cache-buster=%s' % time.time()
      try:
        result = requests.get(url, timeout=50)
        if result.status_code == 200:
          components = json.loads(result.content)
          ramcache.set(key, components)
        else:
          logging.error('Fetching /web blink components content returned: %s' % result.status_code)
      except requests.Timeout:
        logging.info('deadline exceeded when fetching %r', url)

    if not components:
      components = hack_wf_components.HACK_WF_COMPONENTS
      logging.info('using hard-coded WF components')

    return components

  @classmethod
  def update_db(self):
    """Updates the db with new Blink components from the json endpoint"""
    self.fetch_wf_content_for_components(update_cache=True) # store /web content in cache
    new_components = self.fetch_all_components(update_cache=True)
    existing_comps = self.all().fetch(None)
    for name in new_components:
      if not len([x.name for x in existing_comps if x.name == name]):
        logging.info('Adding new BlinkComponent: ' + name)
        c = BlinkComponent(name=name)
        c.put()

  @classmethod
  def get_by_name(self, component_name):
    """Fetch blink component with given name."""
    q = self.all()
    q.filter('name =', component_name)
    component = q.fetch(1)
    if not component:
      logging.error('%s is an unknown BlinkComponent.' % (component_name))
      return None
    return component[0]


# UMA metrics.
class StableInstance(DictModel):
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  property_name = db.StringProperty(required=True)
  bucket_id = db.IntegerProperty(required=True)
  date = db.DateProperty(verbose_name='When the data was fetched',
                         required=True)
  #hits = db.IntegerProperty(required=True)
  #total_pages = db.IntegerProperty()
  day_percentage = db.FloatProperty()
  rolling_percentage = db.FloatProperty()


class AnimatedProperty(StableInstance):
  pass


class FeatureObserver(StableInstance):
  pass


# Feature dashboard.
class Feature(DictModel):
  """Container for a feature."""

  DEFAULT_CACHE_KEY = 'features'

  @classmethod
  def _first_of_milestone(self, feature_list, milestone, start=0):
    for i in xrange(start, len(feature_list)):
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
    for i in xrange(start, len(feature_list)):
      f = feature_list[i]
      desktop_milestone = f['browsers']['chrome'].get('desktop', None)
      android_milestone = f['browsers']['chrome'].get('android', None)
      status = f['browsers']['chrome']['status'].get('text', None)

      if (str(desktop_milestone) == str(milestone) or status == str(milestone)):
        return i
      elif (desktop_milestone == None and str(android_milestone) == str(milestone)):
        return i

    return -1

  @classmethod
  def _annotate_first_of_milestones(self, feature_list, version=None):
    try:
      omaha_data = util.get_omaha_data()

      win_versions = omaha_data[0]['versions']

      # Find the latest canary major version from the list of windows versions.
      canary_versions = [x for x in win_versions if x.get('channel') and x.get('channel').startswith('canary')]
      LATEST_VERSION = int(canary_versions[0].get('version').split('.')[0])

      milestones = range(1, LATEST_VERSION + 1)
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

  def format_for_template(self, version=None):
    self.migrate_views()
    d = self.to_dict()
    is_released = self.impl_status_chrome in RELEASE_IMPL_STATES
    d['is_released'] = is_released

    if version == 2:
      if self.is_saved():
        d['id'] = self.key().id()
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
      d['standards'] = {
        'spec': d.pop('spec_link', None),
        'status': {
          'text': STANDARDIZATION[self.standardization],
          'val': d.pop('standardization', None),
        },
      }
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
        'edge': {
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
        }
      }

      if is_released and self.shipped_milestone:
        d['browsers']['chrome']['status']['milestone_str'] = self.shipped_milestone
      elif is_released and self.shipped_android_milestone:
        d['browsers']['chrome']['status']['milestone_str'] = self.shipped_android_milestone
      else:
        d['browsers']['chrome']['status']['milestone_str'] = d['browsers']['chrome']['status']['text']

      del d['created']

      del_none(d) # Further prune response by removing null/[] values.

    else:
      if self.is_saved():
        d['id'] = self.key().id()
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
    d['explainer_links'] = '\r\n'.join(self.explainer_links)
    d['spec_mentors'] = ', '.join(self.spec_mentors)
    d['doc_links'] = '\r\n'.join(self.doc_links)
    d['sample_links'] = '\r\n'.join(self.sample_links)
    d['search_tags'] = ', '.join(self.search_tags)
    d['blink_components'] = self.blink_components[0] #TODO: support more than one component.
    d['devrel'] = ', '.join(self.devrel)
    d['i2e_lgtms'] = ', '.join(self.i2e_lgtms)
    d['i2s_lgtms'] = ', '.join(self.i2s_lgtms)
    return d

  @classmethod
  def get_all(self, limit=None, order='-updated', filterby=None,
              update_cache=False):
    KEY = '%s|%s|%s' % (Feature.DEFAULT_CACHE_KEY, order, limit)

    # TODO(ericbidelman): Support more than one filter.
    if filterby is not None:
      s = ('%s%s' % (filterby[0], filterby[1])).replace(' ', '')
      KEY += '|%s' % s

    feature_list = ramcache.get(KEY)

    if feature_list is None or update_cache:
      query = Feature.all().order(order) #.order('name')
      query.filter('deleted =', False)

      # TODO(ericbidelman): Support more than one filter.
      if filterby:
        query.filter(filterby[0], filterby[1])

      features = query.fetch(limit)

      feature_list = [f.format_for_template() for f in features]

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
      feature_list = [feature for feature in self.get_all(update_cache=update_cache)
                      if feature['impl_status_chrome'] in statuses]
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
        feature['updated_display'] = unformatted_feature.updated.strftime("%Y-%m-%d")
        feature['new_crbug_url'] = unformatted_feature.new_crbug_url()
        ramcache.set(KEY, feature)

    return feature

  @classmethod
  def get_chronological(
      self, limit=None, update_cache=False, version=None, show_unlisted=False):
    cache_key = '%s|%s|%s|%s' % (Feature.DEFAULT_CACHE_KEY,
                                 'cronorder', limit, version)

    feature_list = ramcache.get(cache_key)
    logging.info('getting chronological feature list')

    # On cache miss, do a db query.
    if not feature_list or update_cache:
      logging.info('recompyting chronological feature list')
      # Features that are in-dev or proposed.
      q = Feature.all()
      q.order('impl_status_chrome')
      q.order('name')
      q.filter('impl_status_chrome IN', (PROPOSED, IN_DEVELOPMENT))
      pre_release = q.fetch(None)

      # Shipping features. Exclude features that do not have a desktop
      # shipping milestone.
      q = Feature.all()
      q.order('-shipped_milestone')
      q.order('name')
      q.filter('shipped_milestone !=', None)
      shipping_features = q.fetch(None)

      # Features with an android shipping milestone but no desktop milestone.
      q = Feature.all()
      q.order('-shipped_android_milestone')
      q.order('name')
      q.filter('shipped_milestone =', None)
      android_only_shipping_features = q.fetch(None)

      # Features with no active development.
      q = Feature.all()
      q.order('name')
      q.filter('impl_status_chrome =', NO_ACTIVE_DEV)
      no_active = q.fetch(None)

      # No longer pursuing features.
      q = Feature.all()
      q.order('name')
      q.filter('impl_status_chrome =', NO_LONGER_PURSUING)
      no_longer_pursuing_features = q.fetch(None)

      shipping_features.extend(android_only_shipping_features)

      shipping_features = [f for f in shipping_features if (IN_DEVELOPMENT < f.impl_status_chrome < NO_LONGER_PURSUING)]

      def getSortingMilestone(feature):
        feature._sort_by_milestone = (feature.shipped_milestone or
                                      feature.shipped_android_milestone)
        return feature

      # Sort the feature list on either Android shipping milestone or desktop
      # shipping milestone, depending on which is specified. If a desktop
      # milestone is defined, that will take default.
      shipping_features = map(getSortingMilestone, shipping_features)

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

    allowed_feature_list = [
        f for f in feature_list
        if show_unlisted or not f['unlisted']]

    return allowed_feature_list

  @classmethod
  def get_shipping_samples(self, limit=None, update_cache=False):
    cache_key = '%s|%s|%s' % (Feature.DEFAULT_CACHE_KEY, 'samples', limit)

    feature_list = ramcache.get(cache_key)

    if feature_list is None or update_cache:
      # Get all shipping features. Ordered by shipping milestone (latest first).
      q = Feature.all()
      q.filter('impl_status_chrome IN', [ENABLED_BY_DEFAULT, ORIGIN_TRIAL, INTERVENTION])
      q.order('-impl_status_chrome')
      q.order('-shipped_milestone')
      q.order('name')
      features = q.fetch(None)

      # Get non-shipping features (sans removed or deprecated ones) and
      # append to bottom of list.
      q = Feature.all()
      q.filter('impl_status_chrome <', ENABLED_BY_DEFAULT)
      q.order('-impl_status_chrome')
      q.order('-shipped_milestone')
      q.order('name')
      others = q.fetch(None)
      features.extend(others)

      # Filter out features without sample links.
      feature_list = [f.format_for_template() for f in features
                      if len(f.sample_links) and not f.deleted]

      ramcache.set(cache_key, feature_list)

    return feature_list

  def crbug_number(self):
    if not self.bug_url:
      return
    m = re.search(r'[\/|?id=]([0-9]+)$', self.bug_url)
    if m:
      return m.group(1)

  def new_crbug_url(self):
    url = 'https://bugs.chromium.org/p/chromium/issues/entry'
    params = ['components=' + self.blink_components[0] or BlinkComponent.DEFAULT_COMPONENT]
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

  def __init__(self, *args, **kwargs):
    super(Feature, self).__init__(*args, **kwargs)

    # Stash existing values when entity is created so we can diff property
    # values later in put() to know what's changed. https://stackoverflow.com/a/41344898
    for prop_name, prop in self.properties().iteritems():
      old_val = getattr(self, prop_name, None)
      setattr(self, '_old_' + prop_name, old_val)

  def __notify_feature_subscribers_of_changes(self, is_update):
    """Async notifies subscribers of new features and property changes to features by
       posting to a task queue."""
    # Diff values to see what properties have changed.
    changed_props = []
    for prop_name, prop in self.properties().iteritems():
      new_val = getattr(self, prop_name, None)
      old_val = getattr(self, '_old_' + prop_name, None)
      if new_val != old_val:
        new_val = convert_enum_int_to_string(prop_name, new_val)
        old_val = convert_enum_int_to_string(prop_name, old_val)
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
    cache_key = '%s|%s' % (Feature.DEFAULT_CACHE_KEY, self.key().id())
    ramcache.delete(cache_key)

    return key

  # Metadata.
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)
  updated_by = db.UserProperty(auto_current_user=True)
  created_by = db.UserProperty(auto_current_user_add=True)

  intent_template_use_count = db.IntegerProperty(default = 0)

  # General info.
  category = db.IntegerProperty(required=True)
  name = db.StringProperty(required=True)
  feature_type = db.IntegerProperty(default=FEATURE_TYPE_INCUBATE_ID)
  intent_stage = db.IntegerProperty(default=0)
  summary = db.StringProperty(required=True, multiline=True)
  origin_trial_feedback_url = db.LinkProperty()
  unlisted = db.BooleanProperty(default=False)
  # TODO(jrobbins): Add an entry_state enum to track app-specific lifecycle
  # info for a feature entry as distinct from process-specific stage.
  deleted = db.BooleanProperty(default=False)
  motivation = db.StringProperty(multiline=True)

  # Tracability to intent discussion threads
  intent_to_implement_url = db.LinkProperty()
  intent_to_ship_url = db.LinkProperty()
  ready_for_trial_url = db.LinkProperty()
  intent_to_experiment_url = db.LinkProperty()
  i2e_lgtms = db.ListProperty(db.Email)  # Currently, only one is needed.
  i2s_lgtms = db.ListProperty(db.Email)

  # Chromium details.
  bug_url = db.LinkProperty()
  launch_bug_url = db.LinkProperty()
  initial_public_proposal_url = db.LinkProperty()
  blink_components = db.StringListProperty(required=True, default=[BlinkComponent.DEFAULT_COMPONENT])
  devrel = db.ListProperty(db.Email)

  impl_status_chrome = db.IntegerProperty(required=True)
  shipped_milestone = db.IntegerProperty()
  shipped_android_milestone = db.IntegerProperty()
  shipped_ios_milestone = db.IntegerProperty()
  shipped_webview_milestone = db.IntegerProperty()
  flag_name = db.StringProperty()

  owner = db.ListProperty(db.Email)
  footprint = db.IntegerProperty()  # Deprecated
  interop_compat_risks = db.StringProperty(multiline=True)
  ergonomics_risks = db.StringProperty(multiline=True)
  activation_risks = db.StringProperty(multiline=True)
  security_risks = db.StringProperty(multiline=True)
  debuggability = db.StringProperty(multiline=True)
  all_platforms = db.BooleanProperty()
  all_platforms_descr = db.StringProperty(multiline=True)
  wpt = db.BooleanProperty()
  wpt_descr = db.StringProperty(multiline=True)

  visibility = db.IntegerProperty(required=False)  # Deprecated

  #webbiness = db.IntegerProperty() # TODO: figure out what this is

  # Standards details.
  standardization = db.IntegerProperty(required=True)
  spec_link = db.LinkProperty()
  api_spec = db.BooleanProperty(default=False)
  spec_mentors = db.ListProperty(db.Email)
  security_review_status = db.IntegerProperty(default=REVIEW_PENDING)
  privacy_review_status = db.IntegerProperty(default=REVIEW_PENDING)

  tag_review = db.StringProperty(multiline=True)
  tag_review_status = db.IntegerProperty(default=REVIEW_PENDING)

  prefixed = db.BooleanProperty()

  explainer_links = db.StringListProperty()

  ff_views = db.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  ie_views = db.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  safari_views = db.IntegerProperty(required=True, default=NO_PUBLIC_SIGNALS)
  web_dev_views = db.IntegerProperty(required=True)

  ff_views_link = db.LinkProperty()
  ie_views_link = db.LinkProperty()
  safari_views_link = db.LinkProperty()
  web_dev_views_link = db.LinkProperty()

  ff_views_notes = db.StringProperty(multiline=True)
  ie_views_notes = db.StringProperty(multiline=True)
  safari_views_notes = db.StringProperty(multiline=True)
  web_dev_views_notes = db.StringProperty(multiline=True)

  doc_links = db.StringListProperty()
  measurement = db.StringProperty(multiline=True)
  sample_links = db.StringListProperty()
  #tests = db.StringProperty()

  search_tags = db.StringListProperty()

  comments = db.StringProperty(multiline=True)

  experiment_goals = db.StringProperty(multiline=True)
  experiment_timeline = db.StringProperty(multiline=True)
  ot_milestone_desktop_start = db.IntegerProperty()
  ot_milestone_desktop_end = db.IntegerProperty()
  ot_milestone_android_start = db.IntegerProperty()
  ot_milestone_android_end = db.IntegerProperty()
  experiment_risks = db.StringProperty(multiline=True)
  experiment_extension_reason = db.StringProperty(multiline=True)
  ongoing_constraints = db.StringProperty(multiline=True)

  star_count = db.IntegerProperty(default=0)


class PlaceholderCharField(forms.CharField):

  def __init__(self, *args, **kwargs):
    #super(forms.CharField, self).__init__(*args, **kwargs)

    attrs = {}
    if kwargs.get('placeholder'):
      attrs['placeholder'] = kwargs.get('placeholder')
      del kwargs['placeholder']

    label = kwargs.get('label') or ''
    if label:
      del kwargs['label']

    self.max_length = kwargs.get('max_length') or None

    super(forms.CharField, self).__init__(label=label,
        widget=forms.TextInput(attrs=attrs), *args, **kwargs)


# class PlaceholderForm(forms.Form):
#   def __init__(self, *args, **kwargs):
#     super(PlaceholderForm, self).__init__(*args, **kwargs)

#     for field_name in self.fields:
#      field = self.fields.get(field_name)
#      if field:
#        if type(field.widget) in (forms.TextInput, forms.DateInput):
#          field.widget = forms.TextInput(attrs={'placeholder': field.label})


class FeatureForm(forms.Form):

  SHIPPED_HELP_TXT = ('First milestone to ship with this '
                      'status. Applies to: Enabled by default, In developer trial, '
                      'Browser Intervention, and Deprecated. If '
                      'the flag is \'test\' rather than \'experimental\' set '
                      'status to In development.')

  SHIPPED_WEBVIEW_HELP_TXT = ('First milestone to ship with this status. '
                              'Applies to Enabled by default, Browser '
                              'Intervention, and Deprecated.\n\n NOTE: for '
                              'statuses In developer trial and Origin trial this '
                              'MUST be blank.')

  SUMMARY_PLACEHOLDER_TXT = (
    'NOTE: This text describes this feature in the eventual beta release post '
    'as well as possibly in other external documents.\n\n'
    'Begin with one line explaining what the feature does. Add one or two '
    'lines explaining how this feature helps developers. Avoid language such '
    'as "a new feature". They all are or have been new features.\n\n'
    'Follow the example link below for more guidance.')

  # Note that the "required" argument in the following field definitions only
  # mean so much in practice. There's various code in js/admin/feature_form.js,
  # including intentStageChanged(), that adjusts what fields are required (as
  # well as visible at all). IOW, when making changes to what form fields are or
  # are not required, look both in the definitions here as well as in
  # js/admin/feature_form.js and make sure the code works as intended.

  #name = PlaceholderCharField(required=True, placeholder='Feature name')
  name = forms.CharField(
      required=True, label='Feature name',
      # Use a specific autocomplete value to avoid "name" autofill.
      # https://bugs.chromium.org/p/chromium/issues/detail?id=468153#c164
      widget=forms.TextInput(attrs={'autocomplete': 'feature-name'}),
      help_text='Capitalize only the first letter and the beginnings of proper nouns.')

  summary = forms.CharField(label='Summary', required=True,
      widget=forms.Textarea(
          attrs={'cols': 50, 'maxlength': 500, 'placeholder': SUMMARY_PLACEHOLDER_TXT }),
      help_text='<a target="_blank" href="'
         'https://github.com/GoogleChrome/chromium-dashboard/wiki/'
         'EditingHelp#summary-example">Guidelines and example</a>.')

  unlisted = forms.BooleanField(
      required=False, initial=False,
      help_text=('Check this box for draft features that should not appear '
                 'on the public feature list. Anyone with the link will be able to '
                 'view the feature on the detail page.'))

  owner = forms.EmailField(
      required=True, label='Contact emails',
      widget=forms.EmailInput(
          attrs={'multiple': True, 'placeholder': 'email, email'}),
      help_text='Comma separated list of full email addresses. Prefer @chromium.org.')

  blink_components = forms.ChoiceField(
      required=False,
      label='Blink component',
      help_text='Select the most specific component. If unsure, leave as "%s".' % BlinkComponent.DEFAULT_COMPONENT,
      choices=[(x, x) for x in BlinkComponent.fetch_all_components()],
      initial=[BlinkComponent.DEFAULT_COMPONENT])

  category = forms.ChoiceField(
      required=False,
      help_text='Select the most specific category. If unsure, leave as "%s".' % FEATURE_CATEGORIES[MISC],
      initial=MISC,
      choices=sorted(FEATURE_CATEGORIES.items(), key=lambda x: x[1]))

  intent_stage = forms.ChoiceField(
      required=False,
      label='Intent stage', help_text='Select the appropriate intent stage.',
      initial=INTENT_IMPLEMENT,
      choices=INTENT_STAGES.items())

  motivation = forms.CharField(label='Motivation', required=True,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='Explain why the web needs this change. It may be useful to describe what web developers are forced to do without it. When possible, include links to back up your claims in the explainer.')

  explainer_links = forms.CharField(label='Explainer link(s)', required=False,
      widget=forms.Textarea(
          attrs={'rows': 4, 'cols': 50, 'maxlength': 500,
                 'placeholder': 'https://\nhttps://'}),
      help_text='Link to explainer(s) (one URL per line). You should have at least an explainer in hand and have shared it on a public forum before sending an Intent to Prototype in order to enable discussion with other browser vendors, standards bodies, or other interested parties.')

  intent_to_implement_url = forms.URLField(
      required=False, label='Intent to Prototype link',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text=('After you have started the "Intent to Prototype" discussion '
                 'thread, link to it here.'))

  intent_to_ship_url = forms.URLField(
      required=False, label='Intent to Ship link',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text=('After you have started the "Intent to Ship" discussion '
                 'thread, link to it here.'))

  ready_for_trial_url = forms.URLField(
      required=False, label='Ready for Trial link',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text=('After you have started the "Ready for Trial" discussion '
                 'thread, link to it here.'))

  intent_to_experiment_url = forms.URLField(
      required=False, label='Intent to Experiment link',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text=('After you have started the "Intent to Experiment" discussion '
                 'thread, link to it here.'))

  origin_trial_feedback_url = forms.URLField(
      required=False, label='Origin trial feedback summary',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text='If your feature was available as an origin trial, link to a summary of usage and developer feedback. If not, leave this empty.')

  i2e_lgtms = forms.EmailField(
      required=False, label='Intent to Experiment LGTM by',
      widget=forms.EmailInput(
          attrs={'multiple': True, 'placeholder': 'email'}),
      help_text=('Full email address of API owner who LGTM\'d the '
                 'Intent to Experiment email thread.'))

  i2s_lgtms = forms.EmailField(
      required=False, label='Intent to Ship LGTMs by',
      widget=forms.EmailInput(
          attrs={'multiple': True, 'placeholder': 'email, email, email'}),
      help_text=('Comma separated list of '
                 'full email addresses of API owners who LGTM\'d '
                 'the Intent to Ship email thread.'))

  doc_links = forms.CharField(label='Doc link(s)', required=False,
      widget=forms.Textarea(
          attrs={'rows': 4, 'cols': 50, 'maxlength': 500,
                 'placeholder': 'https://\nhttps://'}),
      help_text='Links to design doc(s) (one URL per line), if and when available. [This is not required to send out an Intent to Prototype. Please update the intent thread with the design doc when ready]. An explainer and/or design doc is sufficient to start this process. [Note: Please include links and data, where possible, to support any claims.]')

  measurement = forms.CharField(label='Measurement', required=False,
      widget=forms.Textarea(
          attrs={'rows': 4, 'cols': 50, 'maxlength': 500}),
      help_text=(
          'It\'s important to measure the adoption and success of web-exposed '
          'features.  Note here what measurements you have added to track the '
          'success of this feature, such as a link to the UseCounter(s) you '
          'have set up.'))

  standardization = forms.ChoiceField(
      required=False,
      label='Standardization', choices=STANDARDIZATION.items(),
      initial=EDITORS_DRAFT,
      help_text=("The standardization status of the API. In bodies that don't "
                 "use this nomenclature, use the closest equivalent."))

  spec_link = forms.URLField(
      required=False, label='Spec link',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text="Link to spec, if and when available. Please update the chromestatus.com entry and the intent thread(s) with the spec link when available.")

  api_spec = forms.BooleanField(
      required=False, initial=False, label='API spec',
      help_text=('The spec document has details in a specification language '
                 'such as Web IDL, or there is an existing MDN page.'))

  security_review_status = forms.ChoiceField(
      required=False,
      choices=REVIEW_STATUS_CHOICES.items(),
      initial=REVIEW_PENDING,
      help_text=('Status of the security review.'))

  privacy_review_status = forms.ChoiceField(
      required=False,
      choices=REVIEW_STATUS_CHOICES.items(),
      initial=REVIEW_PENDING,
      help_text=('Status of the privacy review.'))

  tag_review = forms.CharField(label='TAG Review', required=True,
      widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'maxlength': 1480}),
      help_text='Link(s) to TAG review(s), or explanation why this is not needed.')

  tag_review_status = forms.ChoiceField(
      required=False,
      choices=REVIEW_STATUS_CHOICES.items(),
      initial=REVIEW_PENDING,
      help_text=('Status of the tag review.'))

  interop_compat_risks = forms.CharField(label='Interoperability and Compatibility Risks', required=True,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='Describe the degree of <a target="_blank" href="https://www.chromium.org/blink/guidelines/web-platform-changes-guidelines#TOC-Finding-balance">interoperability risk</a>. For a new feature, the main risk is that it fails to become an interoperable part of the web platform if other browsers do not implement it. For a removal, please review our <a target="_blank" href="https://docs.google.com/document/d/1RC-pBBvsazYfCNNUSkPqAVpSpNJ96U8trhNkfV0v9fk/edit">principles of web compatibility</a>.<br><br>Please include citation links below where possible. Examples include resolutions from relevant standards bodies (e.g. W3C working group), tracking bugs, or links to online conversations.')

  safari_views = forms.ChoiceField(
      required=False, label='Safari views',
      choices=VENDOR_VIEWS_WEBKIT.items(),
      initial=NO_PUBLIC_SIGNALS,
      help_text=(
          'See <a target="_blank" href="https://bit.ly/blink-signals">'
          'https://bit.ly/blink-signals</a>'))
  safari_views_link = forms.URLField(
      required=False, label='',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text='Citation link.')
  safari_views_notes = forms.CharField(required=False, label='',
      widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes', 'maxlength': 1480}))

  ff_views = forms.ChoiceField(
      required=False, label='Firefox views',
      choices=VENDOR_VIEWS_GECKO.items(),
      initial=NO_PUBLIC_SIGNALS,
      help_text=(
          'See <a target="_blank" href="https://bit.ly/blink-signals">'
          'https://bit.ly/blink-signals</a>'))
  ff_views_link = forms.URLField(
      required=False, label='',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text='Citation link.')
  ff_views_notes = forms.CharField(required=False, label='',
      widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes', 'maxlength': 1480}))

  ie_views = forms.ChoiceField(
      required=False, label='Edge views',
      choices=VENDOR_VIEWS_EDGE.items(),
      initial=NO_PUBLIC_SIGNALS)
  ie_views_link = forms.URLField(
      required=False, label='',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text='Citation link.')
  ie_views_notes = forms.CharField(required=False, label='',
      widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes', 'maxlength': 1480}))

  web_dev_views = forms.ChoiceField(
      required=False, label='Web / Framework developer views',
      choices=WEB_DEV_VIEWS.items(),
      initial=DEV_NO_SIGNALS,
      help_text=(
          'If unsure, default to "No signals". '
          'See <a target="_blank" href="https://goo.gle/developer-signals">'
          'https://goo.gle/developer-signals</a>'))

  web_dev_views_link = forms.URLField(
      required=False, label='',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text='Citation link.')
  web_dev_views_notes = forms.CharField(required=False, label='',
      widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'placeholder': 'Notes', 'maxlength': 1480}),
      help_text='Reference known representative examples of opinion, both positive and negative.')

  ergonomics_risks = forms.CharField(label='Ergonomics Risks', required=False,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='Are there any other platform APIs this feature will frequently be used in tandem with? Could the default usage of this API make it hard for Chrome to maintain good performance (i.e. synchronous return, must run on a certain thread, guaranteed return timing)?')

  activation_risks = forms.CharField(label='Activation Risks', required=False,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='Will it be challenging for developers to take advantage of this feature immediately, as-is? Would this feature benefit from having polyfills, significant documentation and outreach, and/or libraries built on top of it to make it easier to use?')

  security_risks = forms.CharField(label='Security Risks', required=False,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='List any security considerations that were taken into account when deigning this feature.')

  experiment_goals = forms.CharField(label='Experiment Goals', required=False,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='Which pieces of the API surface are you looking to gain insight on? What metrics/measurement/feedback will you be using to validate designs? Double check that your experiment makes sense given that a large developer (e.g. a Google product or Facebook) likely can\'t use it in production due to the limits enforced by origin trials.\n\nIf Intent to Extend Origin Trial, highlight new/different areas for experimentation. Should not be an exact copy of goals from the first Intent to Experiment.')

  # TODO(jrobbins): Phase out this field.
  experiment_timeline = forms.CharField(
      label='Experiment Timeline', required=False,
      widget=forms.Textarea(attrs={
          'rows': 2, 'cols': 50, 'maxlength': 1480,
          'placeholder': 'This field is deprecated',
          'disabled': 'disabled'}),
      help_text=('When does the experiment start and expire? '
                 'Deprecated: '
                 'Please use the following numeric fields instead.'))

  # TODO(jrobbins and jmedley): Refine help text.
  ot_milestone_desktop_start = forms.IntegerField(
      required=False, label='OT desktop start',
      widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
      help_text=('First desktop milestone that will support an origin '
                 'trial of this feature.'))
  ot_milestone_desktop_end = forms.IntegerField(
      required=False, label='OT milestone end',
      widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
      help_text=('Last desktop milestone that will support an origin '
                 'trial of this feature.'))
  ot_milestone_android_start = forms.IntegerField(
      required=False, label='OT android start',
      widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
      help_text=('First android milestone that will support an origin '
                 'trial of this feature.'))
  ot_milestone_android_end = forms.IntegerField(
      required=False, label='OT android end',
      widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
      help_text=('Last android milestone that will support an origin '
                 'trial of this feature.'))

  experiment_risks = forms.CharField(label='Experiment Risks', required=False,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='When this experiment comes to an end are there any risks to the sites that were using it, for example losing access to important storage due to an experimental storage API?')

  experiment_extension_reason = forms.CharField(label='Experiment Extension Reason', required=False,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='If this is a repeat experiment, link to the previous Intent to Experiment thread and explain why you want to extend this experiment.')

  ongoing_constraints = forms.CharField(label='Ongoing Constraints', required=False,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='Do you anticipate adding any ongoing technical constraints to the codebase while implementing this feature? We prefer to avoid features which require or assume a specific architecture. For most features, the answer here is "None."')

  debuggability = forms.CharField(label='Debuggability', required=False,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='Description of the desired DevTools debugging support for your feature. Consider emailing the <a href="https://groups.google.com/forum/?fromgroups#!forum/google-chrome-developer-tools">google-chrome-developer-tools</a> list for additional help. For new language features in V8 specifically, refer to the debugger support checklist. If your feature doesn\'t require changes to DevTools in order to provide a good debugging experience, feel free to leave this section empty.')

  all_platforms = forms.BooleanField(required=False, initial=False, label='Supported on all platforms?',
      help_text='Will this feature be supported on all six Blink platforms (Windows, Mac, Linux, Chrome OS, Android, and Android WebView)?'
)
  all_platforms_descr = forms.CharField(label='Platform Support Explanation', required=False,
      widget=forms.Textarea(attrs={'rows': 2, 'cols': 50, 'maxlength': 2000}),
      help_text='Explanation for why this feature is, or is not, supported on all platforms.')

  wpt = forms.BooleanField(required=False, initial=False, label='Web Platform Tests', help_text='Is this feature fully tested in Web Platform Tests?')

  wpt_descr = forms.CharField(label='Web Platform Tests Description', required=True,
      widget=forms.Textarea(attrs={'cols': 50, 'maxlength': 1480}),
      help_text='Please link to the <a href="https://wpt.fyi/results">results on wpt.fyi</a>. If any part of the feature is not tested by web-platform-tests, please include links to issues, e.g. a web-platform-tests issue with the "infra" label explaining why a certain thing cannot be tested (<a href="https://github.com/w3c/web-platform-tests/issues/3867">example</a>), a spec issue for some change that would make it possible to test. (<a href="https://github.com/whatwg/fullscreen/issues/70">example</a>), or a Chromium issue to upstream some existing tests (<a href="https://bugs.chromium.org/p/chromium/issues/detail?id=695486">example</a>).')

  sample_links = forms.CharField(label='Samples links', required=False,
      widget=forms.Textarea(
          attrs={'cols': 50, 'maxlength': 500,
                 'placeholder': 'https://\nhttps://'}),
      help_text='Links to samples (one URL per line).')

  bug_url = forms.URLField(
      required=False, label='Tracking bug URL',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text='Tracking bug url (https://bugs.chromium.org/...). This bug should have "Type=Feature" set and be world readable.')

  launch_bug_url = forms.URLField(
      required=False, label='Launch bug URL',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text=(
          'Launch bug url (https://bugs.chromium.org/...) to track launch '
          'approvals. '
          '<a href="https://bugs.chromium.org/p/chromium/issues/entry?template=Chrome+Launch+Feature" '
          'target="_blank" '
          '>Create launch bug<a>'))

  initial_public_proposal_url = forms.URLField(
      required=False, label='Initial public proposal URL',
      widget=forms.URLInput(attrs={'placeholder': 'https://'}),
      help_text=(
          'Link to the first public proposal to create this feature, e.g., '
          'a WICG discourse post.'))

  devrel = forms.EmailField(
      required=False, label='Developer relations emails',
      widget=forms.EmailInput(
          attrs={'multiple': True, 'placeholder': 'email, email'}),
      help_text='Comma separated list of full email addresses.')

  impl_status_chrome = forms.ChoiceField(
      required=False,
      label='Implementation status', choices=IMPLEMENTATION_STATUS.items(),
      help_text='Implementation status in Chromium')

  #shipped_milestone = PlaceholderCharField(required=False,
  #                                         placeholder='First milestone the feature shipped with this status (either enabled by default or experimental)')
  shipped_milestone = forms.IntegerField(
      required=False, label='',
      widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
      help_text='Desktop:<br/>' + SHIPPED_HELP_TXT)

  shipped_android_milestone = forms.IntegerField(
      required=False, label='',
      widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
      help_text='Chrome for Android:</br/>' + SHIPPED_HELP_TXT)

  shipped_ios_milestone = forms.IntegerField(
      required=False, label='',
      widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
      help_text='Chrome for iOS (RARE):<br/>' + SHIPPED_HELP_TXT)

  shipped_webview_milestone = forms.IntegerField(
      required=False, label='',
      widget=forms.NumberInput(attrs={'placeholder': 'Milestone #'}),
      help_text='Android WebView:<br/>' + SHIPPED_WEBVIEW_HELP_TXT)

  flag_name = forms.CharField(label='Flag name', required=False,
      help_text='Name of the flag that enables this feature.')

  prefixed = forms.BooleanField(required=False, initial=False, label='Prefixed?')

  search_tags = forms.CharField(label='Search tags', required=False,
      help_text='Comma separated keywords used only in search')

  comments = forms.CharField(label='Comments', required=False,
      widget=forms.Textarea(attrs={
          'cols': 50, 'rows': 4, 'maxlength': 1480}),
      help_text='Additional comments, caveats, info...')

  class Meta:
    model = Feature
    #exclude = ('shipped_webview_milestone',)

  def __init__(self, *args, **keyargs):
    super(FeatureForm, self).__init__(*args, **keyargs)

    meta = getattr(self, 'Meta', None)
    exclude = getattr(meta, 'exclude', [])

    for field_name in exclude:
     if field_name in self.fields:
       del self.fields[field_name]

    for field, val in self.fields.iteritems():
      if val.required:
       self.fields[field].widget.attrs['required'] = 'required'


class UserPref(DictModel):
  """Describes a user's application preferences."""

  email = db.EmailProperty(required=True)

  # True means that user should be sent a notification email after each change
  # to each feature that the user starred.
  notify_as_starrer = db.BooleanProperty(default=True)

  # True means that we sent an email message to this user in the past
  # and it bounced.  We will not send to that address again.
  bounced = db.BooleanProperty(default=False)

  # A list of strings identifying on-page help cue cards that the user
  # has dismissed (clicked "X" or "GOT IT").
  dismissed_cues = db.StringListProperty()

  @classmethod
  def get_signed_in_user_pref(cls):
    """Return a UserPref for the signed in user or None if anon."""
    signed_in_user = users.get_current_user()
    if not signed_in_user:
      return None

    user_pref_list = UserPref.all().filter(
        'email =', signed_in_user.email()).fetch(1)
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
      q = UserPref.all()
      q.filter('email IN', chunk_emails)
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

  #user = db.UserProperty(required=True, verbose_name='Google Account')
  email = db.EmailProperty(required=True)
  #is_admin = db.BooleanProperty(default=False)
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)


def list_with_component(l, component):
  return [x for x in l if x.id() == component.key().id()]

def list_without_component(l, component):
  return [x for x in l if x.id() != component.key().id()]


class FeatureOwner(DictModel):
  """Describes subscribers of a web platform feature."""
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)
  name = db.StringProperty(required=True)
  email = db.EmailProperty(required=True)
  twitter = db.StringProperty()
  blink_components = db.ListProperty(db.Key)
  primary_blink_components = db.ListProperty(db.Key)
  watching_all_features = db.BooleanProperty(default=False)

  # def __eq__(self, other):
  #   return self.key().id() == other.key().id()

  def add_to_component_subscribers(self, component_name):
    """Adds the user to the list of Blink component subscribers."""
    c = BlinkComponent.get_by_name(component_name)
    if c:
      # Add the user if they're not already in the list.
      if not len(list_with_component(self.blink_components, c)):
        self.blink_components.append(c.key())
        return self.put()
    return None

  def remove_from_component_subscribers(self, component_name, remove_as_owner=False):
    """Removes the user from the list of Blink component subscribers or as the owner
       of the component."""
    c = BlinkComponent.get_by_name(component_name)
    if c:
      if remove_as_owner:
        self.primary_blink_components = list_without_component(self.primary_blink_components, c)
      else:
        self.blink_components = list_without_component(self.blink_components, c)
        self.primary_blink_components = list_without_component(self.primary_blink_components, c)
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
        self.primary_blink_components.append(c.key())
      return self.put()
    return None

  def remove_as_component_owner(self, component_name):
    return self.remove_from_component_subscribers(component_name, remove_as_owner=True)


class HistogramModel(db.Model):
  """Container for a histogram."""

  bucket_id = db.IntegerProperty(required=True)
  property_name = db.StringProperty(required=True)

  @classmethod
  def get_all(self):
    output = {}
    buckets = self.all().fetch(None)
    for bucket in buckets:
      output[bucket.bucket_id] = bucket.property_name
    return output

class CssPropertyHistogram(HistogramModel):
  pass

class FeatureObserverHistogram(HistogramModel):
  pass
