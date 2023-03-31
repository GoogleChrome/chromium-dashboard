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
from typing import Any, TypedDict
from google.cloud import ndb  # type: ignore

from internals.core_enums import *
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.data_types import StageDict, VerboseFeatureDict
from internals.review_models import Vote, Gate
from internals import approval_defs


SIMPLE_TYPES = frozenset((int, float, bool, dict, str, list))


def to_dict(entity: ndb.Model) -> dict[str, Any]: # pragma: no cover
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


## FeatureEntry converter methods ##
def _date_to_str(date: Optional[datetime.datetime]) -> Optional[str]:
  """Returns a string interpretation of a datetime object, or None."""
  return str(date) if date is not None else None


def _val_to_list(items: list | None) -> list:
  """Returns the given list, or returns an empty list if null."""
  return items if items is not None else []


def _stage_attr(stage: Stage | None, field: str) -> Any:
  """Returns a specified field of a Stage entity."""
  return None if stage is None else getattr(stage, field)

def _get_milestone_attr(stage: Stage | None, field: str) -> int | None:
  """Returns a specified milestone field of a Stage entity."""
  if stage is None or stage.milestones is None:
    return None
  return getattr(stage.milestones, field)


# Return type for _prep_stage_info function.
class StagePrepResponse(TypedDict):
  proto: Stage | None
  dev_trial: Stage | None
  ot: Stage | None
  extend: Stage | None
  ship: Stage | None
  rollout: Stage | None
  all_stages: list[StageDict]


def _prep_stage_info(
    fe: FeatureEntry,
    prefetched_stages: list[Stage] | None=None
    ) -> StagePrepResponse:
  """Prepares stage info of a feature to help create JSON dictionaries."""
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
    stages = Stage.query(
        Stage.feature_id == fe.key.integer_id()).order(Stage.stage_type)

  stage_info: StagePrepResponse = {
      'proto': None,
      'dev_trial': None,
      'ot': None,
      'extend': None,
      'ship': None,
      'rollout': None,
      # Write a list of all stages associated with the feature.
      'all_stages': []}

  # Keep track of trial stage indexes so that we can add trial extension
  # stages as a property of the trial stage later.
  ot_stage_indexes: dict[int, int] = {}
  for s in stages:
    stage_dict = stage_to_json_dict(s, fe.feature_type)
    # Keep major stages for referencing additional fields.
    if s.stage_type == proto_type:
      stage_info['proto'] = s
    elif s.stage_type == dev_trial_type:
      stage_info['dev_trial'] = s
    elif s.stage_type == ot_type:
      # Keep the stage's index to add trial extensions later.
      ot_stage_indexes[s.key.integer_id()] = len(stage_info['all_stages'])
      stage_dict['extensions'] = []
      stage_info['ot'] = s
    elif s.stage_type == extend_type:
      # Trial extensions are kept as a list on the associated trial stage dict.
      if s.ot_stage_id and s.ot_stage_id in ot_stage_indexes:
        (stage_info['all_stages'][ot_stage_indexes[s.ot_stage_id]]['extensions']
            .append(stage_dict))
      stage_info['extend'] = s
      # No need to append the extension stage to the overall stages list.
      continue
    elif s.stage_type == ship_type:
      stage_info['ship'] = s
    elif s.stage_type == rollout_type:
      stage_info['rollout'] = s
    stage_info['all_stages'].append(stage_dict)

  return stage_info


def stage_to_json_dict(
    stage: Stage, feature_type: int | None=None) -> StageDict:
  """Convert a stage entity into a JSON dict."""
  # Get feature type if not supplied.
  if feature_type is None:
    f = FeatureEntry.get_by_id(stage.feature_id)
    feature_type = f.feature_type
  milestones: MilestoneSet = stage.milestones or MilestoneSet()

  d: StageDict = {
    'id': stage.key.integer_id(),
    'feature_id': stage.feature_id,
    'stage_type': stage.stage_type,
    'display_name': stage.display_name,
    'intent_stage': INTENT_STAGES_BY_STAGE_TYPE.get(
        stage.stage_type, INTENT_NONE),
    'pm_emails': stage.pm_emails,
    'tl_emails': stage.tl_emails,
    'ux_emails': stage.ux_emails,
    'te_emails': stage.te_emails,
    'intent_thread_url': stage.intent_thread_url,

    'announcement_url': stage.announcement_url,
    'experiment_goals': stage.experiment_goals,
    'experiment_risks': stage.experiment_risks,
    'origin_trial_feedback_url': stage.origin_trial_feedback_url,
    'extensions': [],
    'experiment_extension_reason': stage.experiment_extension_reason,
    'ot_stage_id': stage.ot_stage_id,
    'finch_url': stage.finch_url,

    'rollout_milestone': stage.rollout_milestone,
    'rollout_platforms': stage.rollout_platforms,
    'rollout_details': stage.rollout_details,
    'rollout_impact': stage.rollout_impact,
    'enterprise_policies': stage.enterprise_policies,

    # Milestone fields to be populated later.
    'desktop_first': milestones.desktop_first,
    'android_first': milestones.android_first,
    'ios_first': milestones.ios_first,
    'webview_first': milestones.webview_first,
    'desktop_last': milestones.desktop_last,
    'android_last': milestones.android_last,
    'ios_last': milestones.ios_last,
    'webview_last': milestones.webview_last,
  }

  return d


def feature_entry_to_json_verbose(
    fe: FeatureEntry, prefetched_stages: list[Stage] | None=None
    ) -> VerboseFeatureDict:
  """Returns a verbose dictionary with all info about a feature."""
  # Do not convert to JSON if the entity has not been saved.
  if not fe.key:
    raise Exception('Unsaved FeatureEntry cannot be converted.')

  id: int = fe.key.integer_id()

  # Get stage info, returning it to be more explicitly added.
  stage_info = _prep_stage_info(
      fe, prefetched_stages=prefetched_stages)

  d: VerboseFeatureDict = {
    'id': id,
    'name': fe.name,
    'summary': fe.summary,
    'blink_components': fe.blink_components or [],
    'star_count': fe.star_count,
    'search_tags': fe.search_tags or [],
    'created': {
      'by': fe.creator_email,
      'when': _date_to_str(fe.created),
    },
    'updated': {
      'by': fe.updater_email,
      'when': _date_to_str(fe.updated),
    },
    'category': FEATURE_CATEGORIES[fe.category],
    'category_int': fe.category,
    'feature_notes': fe.feature_notes,
    'enterprise_feature_categories': fe.enterprise_feature_categories or [],
    'stages': stage_info['all_stages'],
    'accurate_as_of': _date_to_str(fe.accurate_as_of),
    'creator_email': fe.creator_email,
    'updater_email': fe.updater_email,
    'owner_emails': fe.owner_emails or [],
    'editor_emails': fe.editor_emails or [],
    'cc_emails': fe.cc_emails or [],
    'spec_mentor_emails': fe.spec_mentor_emails or [],
    'unlisted': fe.unlisted,
    'deleted': fe.deleted,
    'editors': fe.editor_emails or [],
    'cc_recipients': fe.cc_emails or [],
    'spec_mentors': fe.spec_mentor_emails or [],
    'creator': fe.creator_email,
    'feature_type': FEATURE_TYPES[fe.feature_type],
    'feature_type_int': fe.feature_type,
    'intent_stage': INTENT_STAGES.get(
        fe.intent_stage, INTENT_STAGES[INTENT_NONE]),
    'intent_stage_int': fe.intent_stage,
    'active_stage_id': fe.active_stage_id,
    'bug_url': fe.bug_url,
    'launch_bug_url': fe.launch_bug_url,
    'new_crbug_url': None,
    'breaking_change': fe.breaking_change,
    'flag_name': fe.flag_name,
    'ongoing_constraints': fe.ongoing_constraints,
    'motivation': fe.motivation,
    'devtrial_instructions': fe.devtrial_instructions,
    'activation_risks': fe.activation_risks,
    'measurement': fe.measurement,
    'availability_expectation': fe.availability_expectation,
    'adoption_expectation': fe.adoption_expectation,
    'adoption_plan': fe.adoption_plan,
    'initial_public_proposal_url': fe.initial_public_proposal_url,
    'explainer_links': fe.explainer_links,
    'requires_embedder_support': fe.requires_embedder_support,
    'spec_link': fe.spec_link,
    'api_spec': fe.api_spec,
    'interop_compat_risks': fe.interop_compat_risks,
    'all_platforms': fe.all_platforms,
    'all_platforms_descr': fe.all_platforms_descr,
    'non_oss_deps': fe.non_oss_deps,
    'anticipated_spec_changes': fe.anticipated_spec_changes,
    'security_risks': fe.security_risks,
    'ergonomics_risks': fe.ergonomics_risks,
    'wpt': fe.wpt,
    'wpt_descr': fe.wpt_descr,
    'webview_risks': fe.webview_risks,
    'devrel_emails': fe.devrel_emails or [],
    'debuggability': fe.debuggability,
    'doc_links': fe.doc_links or [],
    'sample_links': fe.sample_links or [],
    'prefixed': fe.prefixed,
    'tags': fe.search_tags,
    'tag_review': fe.tag_review,
    'tag_review_status': REVIEW_STATUS_CHOICES[fe.tag_review_status],
    'tag_review_status_int': fe.tag_review_status,
    'security_review_status': REVIEW_STATUS_CHOICES[fe.security_review_status],
    'security_review_status_int': fe.security_review_status,
    'privacy_review_status': REVIEW_STATUS_CHOICES[fe.privacy_review_status],
    'privacy_review_status_int': fe.privacy_review_status,
    'updated_display': None,
    'resources': {
      'samples': fe.sample_links or [],
      'docs': fe.doc_links or [],
    },
    'comments': fe.feature_notes,
    'ff_views': fe.ff_views or NO_PUBLIC_SIGNALS,
    'safari_views': fe.safari_views or NO_PUBLIC_SIGNALS,
    'web_dev_views': fe.web_dev_views or DEV_NO_SIGNALS,
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
          'val': fe.impl_status_chrome,
          'milestone_str': None
        },

        # TODO(danielrsmith): Find out if these are used and delete if not.
        'desktop': _get_milestone_attr(stage_info['ship'], 'desktop_first'),
        'android': _get_milestone_attr(stage_info['ship'], 'android_first'),
        'webview': _get_milestone_attr(stage_info['ship'], 'webview_first'),
        'ios': _get_milestone_attr(stage_info['ship'], 'ios_first'),

      },
      'ff': {
        'view': {
          'text': VENDOR_VIEWS.get(
              fe.ff_views, VENDOR_VIEWS_COMMON[NO_PUBLIC_SIGNALS]),
          'val': fe.ff_views if fe.ff_views in VENDOR_VIEWS else NO_PUBLIC_SIGNALS,
          'url': fe.ff_views_link,
          'notes': fe.ff_views_notes,
        },
      },
      'safari': {
        'view': {
          'text': VENDOR_VIEWS.get(
              fe.safari_views,VENDOR_VIEWS_COMMON[NO_PUBLIC_SIGNALS]),
          'val': (fe.safari_views if fe.safari_views in VENDOR_VIEWS
                  else NO_PUBLIC_SIGNALS),
          'url': fe.safari_views_link,
          'notes': fe.safari_views_notes,
        },
      },
      'webdev': {
        'view': {
          'text': WEB_DEV_VIEWS.get(fe.web_dev_views, WEB_DEV_VIEWS[DEV_NO_SIGNALS]),
          'val': (fe.web_dev_views if fe.web_dev_views in WEB_DEV_VIEWS
                  else DEV_NO_SIGNALS),
          'url': fe.web_dev_views_link,
          'notes': fe.web_dev_views_notes,
        },
      },
      'other': {
        'view': {
          'text': None,
          'val': None,
          'url': None,
          'notes':fe.other_views_notes,
        },
      },
    },
    'enterprise_feature_categories': fe.enterprise_feature_categories or [],
    'standards': {
      'spec': fe.spec_link,
      'maturity': {
        'text': STANDARD_MATURITY_CHOICES.get(fe.standard_maturity),
        'short_text': STANDARD_MATURITY_SHORT.get(fe.standard_maturity),
        'val': fe.standard_maturity,
      },
    },
    'is_released': fe.impl_status_chrome in RELEASE_IMPL_STATES,
    'is_enterprise_feature': fe.feature_type == FEATURE_TYPE_ENTERPRISE_ID,

    'experiment_timeline': fe.experiment_timeline,
  }

  if (d['is_released'] and
      _get_milestone_attr(stage_info['ship'], 'desktop_first')):
    d['browsers']['chrome']['status']['milestone_str'] = str(
        _get_milestone_attr(stage_info['ship'], 'desktop_first'))
  elif (d['is_released'] and
        _get_milestone_attr(stage_info['ship'], 'android_first')):
    d['browsers']['chrome']['status']['milestone_str'] = str(
        _get_milestone_attr(stage_info['ship'], 'android_first'))
  else:
    d['browsers']['chrome']['status']['milestone_str'] = (
        d['browsers']['chrome']['status']['text'])

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
