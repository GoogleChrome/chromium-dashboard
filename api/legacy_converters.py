# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
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

from typing import Any

from api.converters import to_dict, del_none
from internals.core_enums import *
from internals.legacy_models import Feature


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
