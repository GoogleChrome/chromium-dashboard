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

import datetime
from typing import Any, Optional
from google.cloud import ndb  # type: ignore

from internals.core_enums import *
from internals import review_models
from internals.core_models import Feature, FeatureEntry, Stage

SIMPLE_TYPES = (int, float, bool, dict, str, list)

def date_to_str(val: Optional[Any]) -> Optional[str]:
  if val is None:
    return None
  return str(val)

def val_to_list(val: Optional[list]) -> Optional[list]:
  return val if val is not None else []

def val_or_none(
    stage: Optional[Stage], field: str, is_mstone: bool=False) -> Optional[Any]:
  if stage is None:
    return None
  if is_mstone:
    return getattr(stage.milestones, field)
  return getattr(stage, field)

def to_dict(entity: ndb.Model) -> dict[str, Any]:
  output = {}
  for key, prop in entity._properties.items():
    # Skip obsolete values that are still in our datastore
    if not hasattr(entity, key):
      continue

    value = getattr(entity, key)

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

def migrate_views(f: Feature) -> None:
  """Migrate obsolete values for views on first edit."""
  if f.ff_views == MIXED_SIGNALS:
    f.ff_views = NO_PUBLIC_SIGNALS
  if f.ff_views == PUBLIC_SKEPTICISM:
    f.ff_views = OPPOSED

  if f.ie_views == MIXED_SIGNALS:
    f.ie_views = NO_PUBLIC_SIGNALS
  if f.ie_views == PUBLIC_SKEPTICISM:
    f.ie_views = OPPOSED

  if f.safari_views == MIXED_SIGNALS:
    f.safari_views = NO_PUBLIC_SIGNALS
  if f.safari_views == PUBLIC_SKEPTICISM:
    f.safari_views = OPPOSED

def feature_to_legacy_json(f: Feature) -> dict[str, Any]:
  migrate_views(f)
  d: dict[str, Any] = to_dict(f)
  is_released = f.impl_status_chrome in RELEASE_IMPL_STATES
  d['is_released'] = is_released

  standard_maturity_val = f.standard_maturity
  if (standard_maturity_val == UNSET_STD and
      f.standardization > 0):
    standard_maturity_val = STANDARD_MATURITY_BACKFILL[f.standardization]

  if f.is_saved():
    d['id'] = f.key.integer_id()
  else:
    d['id'] = None
  d['category'] = FEATURE_CATEGORIES[f.category]
  d['category_int'] = f.category
  if f.feature_type is not None:
    d['feature_type'] = FEATURE_TYPES[f.feature_type]
    d['feature_type_int'] = f.feature_type
  if f.intent_stage is not None:
    d['intent_stage'] = INTENT_STAGES[f.intent_stage]
    d['intent_stage_int'] = f.intent_stage
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
      'text': STANDARDIZATION[f.standardization],
      'val': d.pop('standardization', None),
    },
    'maturity': {
      'text': STANDARD_MATURITY_CHOICES.get(standard_maturity_val),
      'short_text': STANDARD_MATURITY_SHORT.get(standard_maturity_val),
      'val': standard_maturity_val,
    },
  }
  del d['standard_maturity']
  d['tag_review_status'] = REVIEW_STATUS_CHOICES[f.tag_review_status]
  d['tag_review_status_int'] = f.tag_review_status
  d['security_review_status'] = REVIEW_STATUS_CHOICES[
      f.security_review_status]
  d['security_review_status_int'] = f.security_review_status
  d['privacy_review_status'] = REVIEW_STATUS_CHOICES[
      f.privacy_review_status]
  d['privacy_review_status_int'] = f.privacy_review_status
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
      'origintrial': f.impl_status_chrome == ORIGIN_TRIAL,
      'intervention': f.impl_status_chrome == INTERVENTION,
      'prefixed': d.pop('prefixed', False),
      'flag': f.impl_status_chrome == BEHIND_A_FLAG,
      'status': {
        'text': IMPLEMENTATION_STATUS[f.impl_status_chrome],
        'val': d.pop('impl_status_chrome', None)
      },
      'desktop': d.pop('shipped_milestone', None),
      'android': d.pop('shipped_android_milestone', None),
      'webview': d.pop('shipped_webview_milestone', None),
      'ios': d.pop('shipped_ios_milestone', None),
    },
    'ff': {
      'view': {
        'text': VENDOR_VIEWS[f.ff_views],
        'val': d.pop('ff_views', None),
        'url': d.pop('ff_views_link', None),
        'notes': d.pop('ff_views_notes', None),
      }
    },
    'edge': {  # Deprecated
      'view': {
        'text': VENDOR_VIEWS[f.ie_views],
        'val': d.pop('ie_views', None),
        'url': d.pop('ie_views_link', None),
        'notes': d.pop('ie_views_notes', None),
      }
    },
    'safari': {
      'view': {
        'text': VENDOR_VIEWS[f.safari_views],
        'val': d.pop('safari_views', None),
        'url': d.pop('safari_views_link', None),
        'notes': d.pop('safari_views_notes', None),
      }
    },
    'webdev': {
      'view': {
        'text': WEB_DEV_VIEWS[f.web_dev_views],
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

  if is_released and f.shipped_milestone:
    d['browsers']['chrome']['status']['milestone_str'] = f.shipped_milestone
  elif is_released and f.shipped_android_milestone:
    d['browsers']['chrome']['status']['milestone_str'] = f.shipped_android_milestone
  else:
    d['browsers']['chrome']['status']['milestone_str'] = d['browsers']['chrome']['status']['text']

  del_none(d) # Further prune response by removing null/[] values.

  return d
