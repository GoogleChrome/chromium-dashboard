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
from typing import Any
from google.cloud import ndb  # type: ignore

from internals.core_enums import *
from internals.core_models import Feature, FeatureEntry, Stage
from internals.review_models import Gate

SIMPLE_TYPES = frozenset((int, float, bool, dict, str, list))

def to_dict(entity: ndb.Model) -> dict[str, Any]:
  output = {}
  for key, prop in entity._properties.items():
    # Skip obsolete values that are still in our datastore
    if not hasattr(entity, key):
      continue

    value = getattr(entity, key)

    if value is None or type(value) in SIMPLE_TYPES:
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

# TODO(danielrsmith): These views should be migrated properly
# for each entity to avoid invoking this function each time.
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
      'text': STANDARD_MATURITY_CHOICES.get(f.standard_maturity),
      'short_text': STANDARD_MATURITY_SHORT.get(f.standard_maturity),
      'val': f.standard_maturity,
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


## FeatureEntry converter methods ##
def _date_to_str(date: Optional[datetime.datetime]) -> Optional[str]:
  """Returns a string interpretation of a datetime object, or None."""
  return str(date) if date is not None else None

def _val_to_list(items: Optional[list]) -> list:
  """Returns the given list, or returns an empty list if null."""
  return items if items is not None else []

def _stage_attr(
    stage: Optional[Stage], field: str, is_mstone: bool=False) -> Optional[Any]:
  """Returns a specified field of a Stage entity."""
  if stage is None:
    return None
  if is_mstone:
    return getattr(stage.milestones, field)
  return getattr(stage, field)

# These FeatureEntry fields should be copied over as basic properties
# without additional work when converting to JSON.
BASIC_FE_FIELDS = [
    "activation_risks",
    "all_platforms",
    "all_platforms_descr",
    "anticipated_spec_changes",
    "api_spec",
    "debuggability",
    "deleted",
    "ergonomics_risks",
    "feature_notes",
    "flag_name",
    "interop_compat_risks",
    "measurement",
    "motivation",
    "name",
    "non_oss_deps",
    "ongoing_constraints",
    "requires_embedder_support",
    "security_risks",
    "star_count",
    "summary",
    "tag_review",
    "unlisted",
    "webview_risks",
    "wpt",
    "wpt_descr"]

def _prep_stage_gate_info(
    fe: FeatureEntry, d: dict) -> dict[str, Optional[Stage]]:
  """Adds stage and gate info to the dict and returns major stage info."""
  proto_type = STAGE_TYPES_PROTOTYPE[fe.feature_type]
  dev_trial_type = STAGE_TYPES_DEV_TRIAL[fe.feature_type]
  ot_type = STAGE_TYPES_ORIGIN_TRIAL[fe.feature_type]
  extend_type = STAGE_TYPES_EXTEND_ORIGIN_TRIAL[fe.feature_type]
  ship_type = STAGE_TYPES_SHIPPING[fe.feature_type]

  stages = Stage.query(Stage.feature_id == d['id'])
  gates = Gate.query(Gate.feature_id == d['id'])
  major_stages: dict[str, Optional[Stage]] = {
      'proto': None,
      'dev_trial': None,
      'ot': None,
      'extend': None,
      'ship': None}

  # Write a collection of stages and gates associated with the feature,
  # sorted by type.
  d['stages'] = {}
  d['gates'] = collections.defaultdict(list)
  # Stages and gates are given as a dictionary, with the type as the key,
  # and a list of entity IDs as the value.
  for s in stages:
    # Keep major stages for referencing additional fields.
    if s.stage_type == proto_type:
      major_stages['proto'] = s
    elif s.stage_type == dev_trial_type:
      major_stages['dev_trial'] = s
    elif s.stage_type == ot_type:
      major_stages['ot'] = s
    elif s.stage_type == extend_type:
      major_stages['extend'] = s
    elif s.stage_type == ship_type:
      major_stages['ship'] = s
    d['stages'][s.stage_type] = s.key.integer_id()
  for g in gates:
    d['gates'][g.gate_type].append(g.key.integer_id())
  
  return major_stages

def feature_entry_to_json_verbose(fe: FeatureEntry) -> dict[str, Any]:
  """Returns a verbose dictionary with all info about a feature."""
  # Do not convert to JSON if the entity has not been saved.
  if not fe.key:
    return {}

  d: dict[str, Any] = {}
  for field in BASIC_FE_FIELDS:
    d[field] = str(getattr(fe, field))

  d['id'] = fe.key.integer_id()

  # Get stage and gate info, returning stage info to be more explicitly added.
  stages = _prep_stage_gate_info(fe, d)
  # Prototype stage fields.
  d['intent_to_implement_url'] = _stage_attr(
      stages['proto'], 'intent_thread_url')

  # Dev trial stage fields.
  d['dt_milestone_desktop_start'] = _stage_attr(
      stages['dev_trial'], 'desktop_first', True)
  d['dt_milestone_android_start'] = _stage_attr(
      stages['dev_trial'], 'android_first', True)
  d['dt_milestone_ios_start'] = _stage_attr(
      stages['dev_trial'], 'ios_first', True)
  d['dt_milestone_webview_start'] = _stage_attr(
      stages['dev_trial'], 'webview_first', True)

  # Origin trial stage fields.
  d['ot_milestone_desktop_start'] = _stage_attr(
      stages['ot'], 'desktop_first', True)
  d['ot_milestone_android_start'] = _stage_attr(
      stages['ot'], 'android_first', True)
  d['ot_milestone_webview_start'] = _stage_attr(
      stages['ot'], 'webview_first', True)
  d['ot_milestone_desktop_end'] = _stage_attr(
      stages['ot'], 'desktop_last', True)
  d['ot_milestone_android_end'] = _stage_attr(
      stages['ot'], 'android_last', True)
  d['ot_milestone_webview_end'] = _stage_attr(
      stages['ot'], 'webview_last', True)
  d['origin_trial_feeback_url'] = _stage_attr(
      stages['ot'], 'origin_trial_feedback_url')
  d['intent_to_experiment_url'] = _stage_attr(
      stages['ot'], 'intent_thread_url')
  d['experiment_goals'] = _stage_attr(stages['ot'], 'experiment_goals')
  d['experiment_risks'] = _stage_attr(stages['ot'], 'experiment_risks')
  d['announcement_url'] = _stage_attr(stages['ot'], 'announcement_url')

  # Extend origin trial stage fields.
  d['experiment_extension_reason'] = _stage_attr(
      stages['extend'], 'experiment_extension_reason')
  d['intent_to_extend_experiment_url'] = _stage_attr(
      stages['extend'], 'intent_thread_url')

  # Ship stage fields.
  d['intent_to_ship_url'] = _stage_attr(stages['ship'], 'intent_thread_url')

  d['is_released'] = fe.impl_status_chrome in RELEASE_IMPL_STATES
  d['category'] = FEATURE_CATEGORIES[fe.category]
  d['category_int'] = fe.category
  if fe.feature_type is not None:
    d['feature_type'] = FEATURE_TYPES[fe.feature_type]
    d['feature_type_int'] = fe.feature_type
  if fe.intent_stage is not None:
    d['intent_stage'] = INTENT_STAGES[fe.intent_stage]
    d['intent_stage_int'] = fe.intent_stage
  d['created'] = {
    'by': fe.creator_email,
    'when': _date_to_str(fe.created),
  }
  d['updated'] = {
    'by': fe.updater_email,
    'when': _date_to_str(fe.updated),
  }
  d['accurate_as_of'] = _date_to_str(fe.accurate_as_of)
  d['standards'] = {
    'spec': fe.spec_link,
    'maturity': {
      'text': STANDARD_MATURITY_CHOICES.get(fe.standard_maturity),
      'short_text': STANDARD_MATURITY_SHORT.get(fe.standard_maturity),
      'val': fe.standard_maturity,
    },
  }
  d['tag_review_status'] = REVIEW_STATUS_CHOICES[fe.tag_review_status]
  d['tag_review_status_int'] = fe.tag_review_status
  d['security_review_status'] = REVIEW_STATUS_CHOICES[
      fe.security_review_status]
  d['security_review_status_int'] = fe.security_review_status
  d['privacy_review_status'] = REVIEW_STATUS_CHOICES[fe.privacy_review_status]
  d['privacy_review_status_int'] = fe.privacy_review_status
  d['resources'] = {
    'samples': _val_to_list(fe.sample_links),
    'docs': _val_to_list(fe.doc_links),
  }
  d['tags'] = _val_to_list(fe.search_tags)
  d['editors'] =  _val_to_list(fe.editor_emails)
  d['cc_emails'] = _val_to_list(fe.cc_emails)
  d['creator'] = fe.creator_email

  d['browsers'] = {
    'chrome': {
      'bug': fe.bug_url,
      'blink_components': _val_to_list(fe.blink_components),
      'devrel': _val_to_list(fe.devrel_emails),
      'owners': _val_to_list(fe.owner_emails),
      'origintrial': fe.impl_status_chrome == ORIGIN_TRIAL,
      'intervention': fe.impl_status_chrome == INTERVENTION,
      'prefixed': fe.prefixed,
      'flag': fe.impl_status_chrome == BEHIND_A_FLAG,
      'status': {
        'text': IMPLEMENTATION_STATUS[fe.impl_status_chrome],
        'val': fe.impl_status_chrome
      },
      'desktop': _stage_attr(stages['ship'], 'desktop_first', True),
      'android': _stage_attr(stages['ship'], 'android_first', True),
      'webview': _stage_attr(stages['ship'], 'webview_first', True),
      'ios': _stage_attr(stages['ship'], 'ios_first', True),
    },
    'ff': {
      'view': {
        'text': VENDOR_VIEWS[fe.ff_views],
        'val': fe.ff_views,
        'url': fe.ff_views_link,
        'notes': fe.ff_views_notes,
      }
    },
    'safari': {
      'view': {
        'text': VENDOR_VIEWS[fe.safari_views],
        'val': fe.safari_views,
        'url': fe.safari_views_link,
        'notes': fe.safari_views_notes,
      }
    },
    'webdev': {
      'view': {
        'text': WEB_DEV_VIEWS[fe.web_dev_views],
        'val': fe.web_dev_views,
        'url': fe.web_dev_views_link,
        'notes': fe.web_dev_views_notes,
      }
    },
    'other': {
      'view': {
        'notes': fe.other_views_notes,
      }
    },
  }

  if d['is_released'] and _stage_attr(stages['ship'], 'desktop_first', True):
    d['browsers']['chrome']['status']['milestone_str'] = (
        _stage_attr(stages['ship'], 'desktop_first', True))
  elif d['is_released'] and _stage_attr(stages['ship'], 'android_first', True):
    d['browsers']['chrome']['status']['milestone_str'] = (
        _stage_attr(stages['ship'], 'android_first', True))
  else:
    d['browsers']['chrome']['status']['milestone_str'] = (
        d['browsers']['chrome']['status']['text'])

  del_none(d) # Further prune response by removing null/[] values.
  return d
