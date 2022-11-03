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

# Import needed to reference a class within its own class method.
# https://stackoverflow.com/a/33533514
from __future__ import annotations

import collections
import datetime
import logging
import re
from typing import Any, Optional

from google.cloud import ndb  # type: ignore

from framework import rediscache
from framework import users
from internals.core_enums import *
from internals import fetchchannels
from internals import notifier_helpers
from internals import review_models
import settings


SIMPLE_TYPES = (int, float, bool, dict, str, list)


class DictModel(ndb.Model):
  # def to_dict(self):
  #   return dict([(p, str(getattr(self, p))) for p in self.properties()])

  def is_saved(self):
    if self.key:
      return True
    return False

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
  def feature_cache_key(cls, cache_key, feature_id):
    return '%s|%s' % (cache_key, feature_id)

  @classmethod
  def feature_cache_prefix(cls):
    return '%s|*' % (Feature.DEFAULT_CACHE_KEY)

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
  def _annotate_first_of_milestones(self, feature_list):
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

      last_good_idx = 0
      for i, ver in enumerate(versions):
        idx = Feature._first_of_milestone_v2(
            feature_list, ver, start=last_good_idx)
        if idx != -1:
          feature_list[idx]['first_of_milestone'] = True
          last_good_idx = idx
    except Exception as e:
      logging.error(e)

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
  intent_stage = ndb.IntegerProperty(default=INTENT_NONE)
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

  impl_status_chrome = ndb.IntegerProperty(required=True, default=NO_ACTIVE_DEV)
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

  visibility = ndb.IntegerProperty(required=False, default=1)  # Deprecated

  # Standards details.
  standardization = ndb.IntegerProperty(required=True,
      default=EDITORS_DRAFT)  # Deprecated
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
  web_dev_views = ndb.IntegerProperty(required=True, default=DEV_NO_SIGNALS)

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

  # Flag set to avoid migrating data that has already been migrated.
  stages_migrated = ndb.BooleanProperty(default=False)


# Note: This class is not used yet.
class FeatureEntry(ndb.Model):  # Copy from Feature
  """This is the main representation of a feature that we are tracking."""

  # Metadata: Creation and updates.
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty()
  accurate_as_of = ndb.DateTimeProperty()
  creator_email = ndb.StringProperty()
  updater_email = ndb.StringProperty()

  # Metadata: Access controls
  owner_emails = ndb.StringProperty(repeated=True)  # copy from owner
  editor_emails = ndb.StringProperty(repeated=True)
  cc_emails = ndb.StringProperty(repeated=True)
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
  intent_stage = ndb.IntegerProperty(default=INTENT_NONE)
  bug_url = ndb.StringProperty()  # Tracking bug
  launch_bug_url = ndb.StringProperty()  # FLT or go/launch

  # Implementation in Chrome
  impl_status_chrome = ndb.IntegerProperty(required=True, default=NO_ACTIVE_DEV)
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
  spec_mentor_emails = ndb.StringProperty(repeated=True)
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
  web_dev_views = ndb.IntegerProperty(required=True, default=DEV_NO_SIGNALS)
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
  devrel_emails = ndb.StringProperty(repeated=True)
  debuggability = ndb.TextProperty()
  doc_links = ndb.StringProperty(repeated=True)
  sample_links = ndb.StringProperty(repeated=True)

  # Legacy fields that we display on old entries, but don't allow editing.
  experiment_timeline = ndb.TextProperty()  # Display-only

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
  def feature_cache_key(cls, cache_key, feature_id):
    return '%s|%s' % (cache_key, feature_id)

  @classmethod
  def feature_cache_prefix(cls):
    return '%s|*' % (cls.DEFAULT_CACHE_KEY)

  @classmethod
  def get_feature_entry(self, feature_id: int, update_cache: bool=False
      ) -> Optional[FeatureEntry]:
    KEY = self.feature_cache_key(
        FeatureEntry.DEFAULT_CACHE_KEY, feature_id)
    feature = rediscache.get(KEY)

    if feature is None or update_cache:
      entry = FeatureEntry.get_by_id(feature_id)
      if entry:
        if entry.deleted:
          return None
        rediscache.set(KEY, entry)

    return entry

  @classmethod
  def filter_unlisted(self, entry_list: list[FeatureEntry]
      ) -> list[FeatureEntry]:
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
  def get_by_ids(self, entry_ids: list[int], update_cache: bool=False
      ) -> list[int]:
    """Return a list of FeatureEntry instances for the specified features.

    Because the cache may rarely have stale data, this should only be
    used for displaying data read-only, not for populating forms or
    procesing a POST to edit data.  For editing use case, load the
    data from NDB directly.
    """
    result_dict: dict[int, int] = {}
    futures = []

    for fe_id in entry_ids:
      lookup_key = self.feature_cache_key(
          FeatureEntry.DEFAULT_CACHE_KEY, fe_id)
      entry = rediscache.get(lookup_key)
      if entry is None or update_cache:
        futures.append(FeatureEntry.get_by_id_async(fe_id))
      else:
        result_dict[fe_id] = entry

    for future in futures:
      entry = future.get_result()
      if entry and not entry.deleted:
        store_key = self.feature_cache_key(
            FeatureEntry.DEFAULT_CACHE_KEY, entry.key.integer_id())
        rediscache.set(store_key, entry)
        result_dict[entry.key.integer_id()] = entry

    result_list = [result_dict[fe_id] for fe_id in entry_ids
                   if fe_id in result_dict]
    return result_list
  
  def stash_values(self) -> None:
    # Stash existing values when entity is created so we can diff property
    # values later in put() to know what's changed.
    # https://stackoverflow.com/a/41344898

    for prop_name in self._properties.keys():
      old_val = getattr(self, prop_name, None)
      setattr(self, '_old_' + prop_name, old_val)
    setattr(self, '_values_stashed', True)

  def put(self, notify: bool=True, **kwargs) -> Any:
    key = super(FeatureEntry, self).put(**kwargs)
    notifier_helpers.notify_subscribers_and_save_amendments(self, notify)
    # Invalidate rediscache for the individual feature view.
    cache_key = FeatureEntry.feature_cache_key(
        FeatureEntry.DEFAULT_CACHE_KEY, self.key.integer_id())
    rediscache.delete(cache_key)

    return key

  # Note: get_in_milestone will be in a new file legacy_queries.py.


# Note: This class is not used yet.
class MilestoneSet(ndb.Model):  # copy from milestone fields of Feature
  """Range of milestones during which a feature will be in a certain stage."""

  # Mapping of old milestone fields to the new fields they should use
  # in the MilestoneSet kind.
  MILESTONE_FIELD_MAPPING = {
      'shipped_milestone': 'desktop_first',
      'shipped_android_milestone': 'android_first',
      'shipped_ios_milestone': 'ios_first',
      'shipped_webview_milestone': 'webview_first',
      'ot_milestone_desktop_start': 'desktop_first',
      'ot_milestone_desktop_end': 'desktop_last',
      'ot_milestone_android_start': 'android_first',
      'ot_milestone_android_end': 'android_last',
      'ot_milestone_ios_start': 'ios_first',
      'ot_milestone_ios_end': 'ios_last',
      'ot_milestone_webview_start': 'webview_first',
      'ot_milestone_webview_end': 'webview_last',
      'dt_milestone_desktop_start': 'desktop_first',
      'dt_milestone_android_start': 'android_first',
      'dt_milestone_ios_start': 'ios_first',
      'dt_milestone_webview_start': 'webview_first'
    }

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
  announcement_url = ndb.StringProperty()
  # Origin trial stage id that this stage extends, if trial extension stage.
  ot_stage_id = ndb.IntegerProperty()

  @classmethod
  def get_feature_stages(cls, feature_id: int) -> dict[int, Stage]:
    """Return a dictionary of stages associated with a given feature."""
    stages: list[Stage] = cls.query(cls.feature_id == feature_id).fetch()
    return {stage.stage_type: stage for stage in stages}
