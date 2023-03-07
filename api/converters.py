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
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.legacy_models import Feature
from internals.review_models import Vote, Gate
from internals import approval_defs


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


def feature_to_legacy_json(f: Feature) -> dict[str, Any]:
  d: dict[str, Any] = to_dict(f)
  is_released = f.impl_status_chrome in RELEASE_IMPL_STATES
  d['is_released'] = is_released

  if f.is_saved():
    d['id'] = f.key.integer_id()
  else:
    d['id'] = None
  d['category'] = FEATURE_CATEGORIES[f.category]
  d['enterprise_feature_categories'] = f.enterprise_feature_categories
  d['category_int'] = f.category
  if f.feature_type is not None:
    d['feature_type'] = FEATURE_TYPES[f.feature_type]
    d['feature_type_int'] = f.feature_type
    d['is_enterprise_feature'] = f.feature_type == FEATURE_TYPE_ENTERPRISE_ID
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

  ff_views = d.pop('ff_views', NO_PUBLIC_SIGNALS)
  ie_views = d.pop('ie_views', NO_PUBLIC_SIGNALS)
  safari_views = d.pop('safari_views', NO_PUBLIC_SIGNALS)
  web_dev_views = d.pop('web_dev_views', DEV_NO_SIGNALS)
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
        'text': VENDOR_VIEWS.get(ff_views,
            VENDOR_VIEWS_COMMON[NO_PUBLIC_SIGNALS]),
        'val': ff_views if ff_views in VENDOR_VIEWS else NO_PUBLIC_SIGNALS,
        'url': d.pop('ff_views_link', None),
        'notes': d.pop('ff_views_notes', None),
      }
    },
    'edge': {  # Deprecated
      'view': {
        'text': VENDOR_VIEWS.get(ie_views,
            VENDOR_VIEWS_COMMON[NO_PUBLIC_SIGNALS]),
        'val': ie_views if ie_views in VENDOR_VIEWS else NO_PUBLIC_SIGNALS,
        'url': d.pop('ie_views_link', None),
        'notes': d.pop('ie_views_notes', None),
      }
    },
    'safari': {
      'view': {
        'text': VENDOR_VIEWS.get(safari_views,
            VENDOR_VIEWS_COMMON[NO_PUBLIC_SIGNALS]),
        'val': (safari_views if safari_views in VENDOR_VIEWS
            else NO_PUBLIC_SIGNALS),
        'url': d.pop('safari_views_link', None),
        'notes': d.pop('safari_views_notes', None),
      }
    },
    'webdev': {
      'view': {
        'text': WEB_DEV_VIEWS.get(f.web_dev_views,
            WEB_DEV_VIEWS[DEV_NO_SIGNALS]),
        'val': (web_dev_views if web_dev_views in WEB_DEV_VIEWS
            else DEV_NO_SIGNALS),
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
  if not is_mstone:
    return getattr(stage, field)

  if stage.milestones is None:
    return None
  return getattr(stage.milestones, field)


def _prep_stage_gate_info(
    fe: FeatureEntry, d: dict,
    prefetched_stages: list[Stage] | None=None
    ) -> dict[str, Optional[Stage]]:
  """Adds stage and gate info to the dict and returns major stage info."""
  proto_type = STAGE_TYPES_PROTOTYPE[fe.feature_type]
  dev_trial_type = STAGE_TYPES_DEV_TRIAL[fe.feature_type]
  ot_type = STAGE_TYPES_ORIGIN_TRIAL[fe.feature_type]
  extend_type = STAGE_TYPES_EXTEND_ORIGIN_TRIAL[fe.feature_type]
  ship_type = STAGE_TYPES_SHIPPING[fe.feature_type]
  rollout_type = STAGE_TYPES_ROLLOUT[fe.feature_type]

  # Get all stages associated with the feature, sorted by stage type.
  if prefetched_stages is not None:
    prefetched_stages.sort(key=lambda s: s.stage_type)
    stages = prefetched_stages
  else:
    stages = Stage.query(Stage.feature_id == d['id']).order(Stage.stage_type)

  major_stages: dict[str, Optional[Stage]] = {
      'proto': None,
      'dev_trial': None,
      'ot': None,
      'extend': None,
      'ship': None,
      'rollout': None}

  # Write a list of stages associated with the feature.
  d['stages'] = []

  # Keep track of trial stage indexes so that we can add trial extension
  # stages as a property of the trial stage later.
  ot_stage_indexes: dict[int, int] = {}
  for s in stages:
    stage_dict = stage_to_json_dict(s, fe.feature_type)
    # Keep major stages for referencing additional fields.
    if s.stage_type == proto_type:
      major_stages['proto'] = s
    elif s.stage_type == dev_trial_type:
      major_stages['dev_trial'] = s
    elif s.stage_type == ot_type:
      # Keep the stage's index to add trial extensions later.
      ot_stage_indexes[s.key.integer_id()] = len(d['stages'])
      stage_dict['extensions'] = []
      major_stages['ot'] = s
    elif s.stage_type == extend_type:
      # Trial extensions are kept as a list on the associated trial stage dict.
      if s.ot_stage_id and s.ot_stage_id in ot_stage_indexes:
        (d['stages'][ot_stage_indexes[s.ot_stage_id]]['extensions']
            .append(stage_dict))
      major_stages['extend'] = s
      # No need to append the extension stage to the overall stages list.
      continue
    elif s.stage_type == ship_type:
      major_stages['ship'] = s
    elif s.stage_type == rollout_type:
      major_stages['rollout'] = s
    d['stages'].append(stage_dict)

  return major_stages


# This function is a workaround to reference extension stage info on
# origin trial stages.
# TODO(danielrsmith): Remove this once users can manually add trial extension
# stages.
def _add_ot_extension_fields(d: dict):
  """Adds info from the trial extension stage to the OT stage dict."""
  extension_stage = Stage.query(
      Stage.ot_stage_id == d['id']).get()
  if extension_stage is None:
    return
  d['experiment_extension_reason'] = extension_stage.experiment_extension_reason
  d['intent_to_extend_experiment_url'] = (
    extension_stage.intent_thread_url)


def stage_to_json_dict(
    stage: Stage, feature_type: int | None=None) -> dict[str, Any]:
  """Convert a stage entity into a JSON dict."""
  # Get feature type if not supplied.
  if feature_type is None:
    f = FeatureEntry.get_by_id(stage.feature_id)
    feature_type = f.feature_type

  d: dict[str, Any] = {}
  d['id'] = stage.key.integer_id()
  d['feature_id'] = stage.feature_id
  d['stage_type'] = stage.stage_type
  d['intent_stage'] = INTENT_STAGES_BY_STAGE_TYPE.get(
      d['stage_type'], INTENT_NONE)

  # Determine the stage type and handle stage-specific fields.
  # TODO(danielrsmith): Change client to use new field names.
  milestone_field_names: list[dict] | None = None
  if d['stage_type'] == STAGE_TYPES_PROTOTYPE[feature_type]:
    d['intent_to_implement_url'] = stage.intent_thread_url
  elif d['stage_type'] == STAGE_TYPES_DEV_TRIAL[feature_type]:
    d['ready_for_trial_url'] = stage.announcement_url
    milestone_field_names = MilestoneSet.DEV_TRIAL_MILESTONE_FIELD_NAMES
  elif d['stage_type'] == STAGE_TYPES_ORIGIN_TRIAL[feature_type]:
    d['intent_to_experiment_url'] = stage.intent_thread_url
    d['experiment_goals'] = stage.experiment_goals
    d['experiment_risks'] = stage.experiment_risks
    d['origin_trial_feedback_url'] = stage.origin_trial_feedback_url
    _add_ot_extension_fields(d)
    milestone_field_names = MilestoneSet.OT_MILESTONE_FIELD_NAMES
  elif d['stage_type'] == STAGE_TYPES_EXTEND_ORIGIN_TRIAL[feature_type]:
    d['experiment_extension_reason'] = stage.experiment_extension_reason
    d['intent_to_extend_experiment_url'] = stage.intent_thread_url
    d['ot_stage_id'] = stage.ot_stage_id
    milestone_field_names = MilestoneSet.OT_EXTENSION_MILESTONE_FIELD_NAMES
  elif d['stage_type'] == STAGE_TYPES_SHIPPING[feature_type]:
    d['intent_to_ship_url'] = stage.intent_thread_url
    d['finch_url'] = stage.finch_url
    milestone_field_names = MilestoneSet.SHIPPING_MILESTONE_FIELD_NAMES
  elif d['stage_type'] == STAGE_TYPES_ROLLOUT[feature_type]:
    d['rollout_milestone'] = stage.rollout_milestone
    d['rollout_platforms'] = stage.rollout_platforms
    d['rollout_details'] = stage.rollout_details
    d['enterprise_policies'] = stage.enterprise_policies

  # Add milestone fields
  if stage.milestones is not None and milestone_field_names is not None:
    for name_info in milestone_field_names:
      # The old val name is still used on the client side.
      # TODO(danielrsmith): Change client to use new field names.
      d[name_info['old']] = getattr(stage.milestones, name_info['new'])
      d[name_info['new']] = getattr(stage.milestones, name_info['new'])

  d['pm_emails'] = stage.pm_emails
  d['tl_emails'] = stage.tl_emails
  d['ux_emails'] = stage.ux_emails
  d['te_emails'] = stage.te_emails
  d['intent_thread_url'] = stage.intent_thread_url

  return d


def feature_entry_to_json_verbose(
    fe: FeatureEntry, prefetched_stages: list[Stage] | None=None
    ) -> dict[str, Any]:
  """Returns a verbose dictionary with all info about a feature."""
  # Do not convert to JSON if the entity has not been saved.
  if not fe.key:
    return {}

  d: dict[str, Any] = fe.to_dict()

  d['id'] = fe.key.integer_id()

  # Get stage and gate info, returning stage info to be more explicitly added.
  stages = _prep_stage_gate_info(fe, d, prefetched_stages=prefetched_stages)
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
  d['ready_for_trial_url'] = _stage_attr(
      stages['dev_trial'], 'announcement_url')

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
  d['finch_url'] = _stage_attr(stages['ship'], 'finch_url')
  d['rollout_milestone'] = _stage_attr(stages['rollout'], 'rollout_milestone')
  d['rollout_platforms'] = _stage_attr(stages['rollout'], 'rollout_platforms')
  d['rollout_details'] = _stage_attr(stages['rollout'], 'rollout_details')
  d['enterprise_policies'] = _stage_attr(stages['rollout'], 'enterprise_policies')

  # TODO(danielrsmith): Adjust the references to this JSON to use
  # the new renamed field names.
  impl_status_chrome = d.pop('impl_status_chrome', None)
  standard_maturity = d.pop('standard_maturity', None)
  d['is_released'] = fe.impl_status_chrome in RELEASE_IMPL_STATES
  d['category'] = FEATURE_CATEGORIES[fe.category]
  d['category_int'] = fe.category
  d['enterprise_feature_categories'] = d.pop('enterprise_feature_categories', [])
  if fe.feature_type is not None:
    d['feature_type'] = FEATURE_TYPES[fe.feature_type]
    d['feature_type_int'] = fe.feature_type
    d['is_enterprise_feature'] = fe.feature_type == FEATURE_TYPE_ENTERPRISE_ID
  if fe.intent_stage is not None:
    d['intent_stage'] = INTENT_STAGES.get(
        fe.intent_stage, INTENT_STAGES[INTENT_NONE])
    d['intent_stage_int'] = fe.intent_stage
  d['active_stage_id'] = fe.active_stage_id
  d['created'] = {
    'by': d.pop('creator_email', None),
    'when': _date_to_str(fe.created),
  }
  d['updated'] = {
    'by': d.pop('updater_email', None),
    'when': _date_to_str(fe.updated),
  }
  d['accurate_as_of'] = _date_to_str(fe.accurate_as_of)
  d['standards'] = {
    'spec': fe.spec_link,
    'maturity': {
      'text': STANDARD_MATURITY_CHOICES.get(standard_maturity),
      'short_text': STANDARD_MATURITY_SHORT.get(standard_maturity),
      'val': standard_maturity,
    },
  }
  d['spec_mentors'] = fe.spec_mentor_emails
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
  d['tags'] = d.pop('search_tags', None)
  d['editors'] =  d.pop('editor_emails', [])
  d['cc_recipients'] = d.pop('cc_emails', [])
  d['creator'] = fe.creator_email
  d['comments'] = d.pop('feature_notes', None)

  ff_views = d.pop('ff_views', NO_PUBLIC_SIGNALS)
  safari_views = d.pop('safari_views', NO_PUBLIC_SIGNALS)
  web_dev_views = d.pop('web_dev_views', DEV_NO_SIGNALS)
  d['browsers'] = {
    'chrome': {
      'bug': fe.bug_url,
      'blink_components': d.pop('blink_components', []),
      'devrel': _val_to_list(fe.devrel_emails),
      'owners': d.pop('owner_emails', []),
      'origintrial': fe.impl_status_chrome == ORIGIN_TRIAL,
      'intervention': fe.impl_status_chrome == INTERVENTION,
      'prefixed': fe.prefixed,
      'flag': fe.impl_status_chrome == BEHIND_A_FLAG,
      'status': {
        'text': IMPLEMENTATION_STATUS[impl_status_chrome],
        'val': impl_status_chrome
      },
      'desktop': _stage_attr(stages['ship'], 'desktop_first', True),
      'android': _stage_attr(stages['ship'], 'android_first', True),
      'webview': _stage_attr(stages['ship'], 'webview_first', True),
      'ios': _stage_attr(stages['ship'], 'ios_first', True),
    },
    'ff': {
      'view': {
        'text': VENDOR_VIEWS.get(ff_views,
            VENDOR_VIEWS_COMMON[NO_PUBLIC_SIGNALS]),
        'val': ff_views if ff_views in VENDOR_VIEWS else NO_PUBLIC_SIGNALS,
        'url': d.pop('ff_views_link', None),
        'notes': d.pop('ff_views_notes'),
      }
    },
    'safari': {
      'view': {
        'text': VENDOR_VIEWS.get(safari_views,
            VENDOR_VIEWS_COMMON[NO_PUBLIC_SIGNALS]),
        'val': (safari_views if safari_views in VENDOR_VIEWS
            else NO_PUBLIC_SIGNALS),
        'url': d.pop('safari_views_link', None),
        'notes': d.pop('safari_views_notes', None),
      }
    },
    'webdev': {
      'view': {
        'text': WEB_DEV_VIEWS.get(web_dev_views,
            WEB_DEV_VIEWS[DEV_NO_SIGNALS]),
        'val': (web_dev_views if web_dev_views in WEB_DEV_VIEWS
            else DEV_NO_SIGNALS),
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


def feature_entry_to_json_basic(fe: FeatureEntry,
    stages: list[Stage] | None=None) -> dict[str, Any]:
  """Returns a dictionary with basic info about a feature."""
  # Return an empty dictionary if the entity has not been saved to datastore.
  if not fe.key:
    return {}

  d: dict[str, Any] = {
    'id': fe.key.integer_id(),
    'name': fe.name,
    'summary': fe.summary,
    'unlisted': fe.unlisted,
    'breaking_change': fe.breaking_change,
    'blink_components': fe.blink_components or [],
    'resources': {
      'samples': fe.sample_links or [],
      'docs': fe.doc_links or [],
    },
    'created': {
      'by': fe.creator_email,
      'when': _date_to_str(fe.created)
    },
    'updated': {
      'by': fe.updater_email,
      'when': _date_to_str(fe.updated)
    },
    'standards': {
      'spec': fe.spec_link,
      'maturity': {
        'text': STANDARD_MATURITY_CHOICES.get(fe.standard_maturity),
        'short_text': STANDARD_MATURITY_SHORT.get(fe.standard_maturity),
        'val': fe.standard_maturity,
      },
    },
    'browsers': {
      'chrome': {
        'bug': fe.bug_url,
        'blink_components': fe.blink_components or [],
        'devrel': fe.devrel_emails or [],
        'owners': fe.owner_emails or [],
        'origintrial': fe.impl_status_chrome == ORIGIN_TRIAL,
        'intervention': fe.impl_status_chrome == INTERVENTION,
        'prefixed': fe.prefixed,
        'flag': fe.impl_status_chrome == BEHIND_A_FLAG,
        'status': {
          'text': IMPLEMENTATION_STATUS[fe.impl_status_chrome],
          'val': fe.impl_status_chrome
        }
      },
      'ff': {
        'view': {
        'text': VENDOR_VIEWS.get(fe.ff_views,
            VENDOR_VIEWS_COMMON[NO_PUBLIC_SIGNALS]),
        'val': (fe.ff_views if fe.ff_views in VENDOR_VIEWS
            else NO_PUBLIC_SIGNALS),
          'url': fe.ff_views_link,
          'notes': fe.ff_views_notes,
        }
      },
      'safari': {
        'view': {
        'text': VENDOR_VIEWS.get(fe.safari_views,
            VENDOR_VIEWS_COMMON[NO_PUBLIC_SIGNALS]),
        'val': (fe.safari_views if fe.safari_views in VENDOR_VIEWS
            else NO_PUBLIC_SIGNALS),
          'url': fe.safari_views_link,
          'notes': fe.safari_views_notes,
        }
      },
      'webdev': {
        'view': {
        'text': WEB_DEV_VIEWS.get(fe.web_dev_views,
            WEB_DEV_VIEWS[DEV_NO_SIGNALS]),
        'val': (fe.web_dev_views if fe.web_dev_views in WEB_DEV_VIEWS
            else DEV_NO_SIGNALS),
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
  }

  is_released = fe.impl_status_chrome in RELEASE_IMPL_STATES
  d['is_released'] = is_released

  # This key is used for filtering on the featurelist page.
  # This does not take into account multiple shipping milestones
  milestone = None
  # This field is only updated if the feature is released and
  # the feature's stages were passed to the function.
  if stages and d['is_released']:
    for s in stages:
      if (s.stage_type == STAGE_TYPES_SHIPPING[fe.feature_type]
          and s.milestones is not None):
        milestone = (s.milestones.desktop_first or
            s.milestones.android_first or
            s.milestones.ios_first or s.milestones.webview_first)
  d['milestone'] = milestone

  return d


def vote_value_to_json_dict(vote: Vote) -> dict[str, Any]:

  return {
      'feature_id': vote.feature_id,
      'gate_id': vote.gate_id,
      'gate_type': vote.gate_type,
      'state': vote.state,
      'set_on': str(vote.set_on),  # YYYY-MM-DD HH:MM:SS.SSS
      'set_by': vote.set_by,
      }


def gate_value_to_json_dict(gate: Gate) -> dict[str, Any]:
  next_action = str(gate.next_action) if gate.next_action else None
  requested_on = str(gate.requested_on) if gate.requested_on else None
  appr_def = approval_defs.APPROVAL_FIELDS_BY_ID.get(gate.gate_type)
  return {
      'id': gate.key.integer_id(),
      'feature_id': gate.feature_id,
      'stage_id': gate.stage_id,
      'gate_type': gate.gate_type,
      'team_name': appr_def.team_name if appr_def else 'Team',
      'gate_name': appr_def.name if appr_def else 'Gate',
      'state': gate.state,
      'requested_on': requested_on,  # YYYY-MM-DD HH:MM:SS or None
      'owners': gate.owners,
      'next_action': next_action,  # YYYY-MM-DD or None
      'additional_review': gate.additional_review
      }
