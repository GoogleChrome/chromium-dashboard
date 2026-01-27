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

from datetime import datetime, timedelta
import testing_config  # Must be imported before the module under test.
from unittest import mock

from api import converters
from framework import rediscache
from internals.core_enums import *
from internals import feature_helpers
from internals import stage_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote
from internals.user_models import AppUser


MOCK_ENABLED_FEATURES_JSON = {
  "data": [
    # For feature_1: A complete feature that is stable.
    { "name": "featureOneFinch", "status": "stable" },
    # For feature_7: An incomplete feature that is not stable.
    { "name": "feature7-unstable", "status": "experimental" },

    # Status is a dict, and at least one platform is "stable".
    {
      "name": "FeatureDictStable",
      "status": {
        "Mac": "experimental",
        "Win": "stable",
        "Linux": "dev"
      }
    },
    # Status is a dict, but no platform is "stable".
    {
      "name": "FeatureDictUnstable",
      "status": {
        "Mac": "experimental",
        "Win": "experimental",
        "Linux": "experimental"
      }
    }
  ]
}

MOCK_CONTENT_FEATURES_CC = """
// Some C++ code here...
// For feature_8: A complete feature, enabled by default.
BASE_FEATURE(kFeature8Enabled,
             // Some rogue comment.
             base::FEATURE_ENABLED_BY_DEFAULT);
// More C++ code...
// For feature_9: An incomplete feature, disabled by default.
BASE_FEATURE(kFeature9Disabled, base::FEATURE_DISABLED_BY_DEFAULT);
// Even more C++ code...
"""


class FeatureHelpersTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_2 = FeatureEntry(
        name='feature b', summary='sum',
        owner_emails=['feature_owner@example.com'], category=1,
        updated=datetime(2020, 4, 1), feature_type=FEATURE_TYPE_EXISTING_ID,
        impl_status_chrome=1)
    self.feature_2.put()

    self.feature_1 = FeatureEntry(
        name='feature a', summary='sum', impl_status_chrome=3,
        owner_emails=['feature_owner@example.com'], category=1,
        updated=datetime(2020, 3, 1), feature_type=FEATURE_TYPE_INCUBATE_ID)
    self.feature_1.put()

    self.feature_3 = FeatureEntry(
        name='feature c', summary='sum', category=1, impl_status_chrome=2,
        owner_emails=['feature_owner@example.com'],
        updated=datetime(2020, 1, 1), feature_type=FEATURE_TYPE_CODE_CHANGE_ID)
    self.feature_3.put()

    self.feature_4 = FeatureEntry(
        name='feature d', summary='sum', category=1, impl_status_chrome=2,
        owner_emails=['feature_owner@example.com'],
        updated=datetime(2020, 2, 1), feature_type=FEATURE_TYPE_DEPRECATION_ID)
    self.feature_4.put()

    fe_1_stage_types = [110, 120, 130, 140, 150, 151, 160]
    fe_2_stage_types = [220, 230, 250, 251, 260]
    fe_3_stage_types = [320, 330, 360]
    fe_4_stage_types = [410, 430, 450, 451, 460]
    self.stages: list[Stage] = []
    for s_type in fe_1_stage_types:
      stage = Stage(
          feature_id=self.feature_1.key.integer_id(), stage_type=s_type)
      stage.put()
    for s_type in fe_2_stage_types:
      stage = Stage(
          feature_id=self.feature_2.key.integer_id(), stage_type=s_type)
      stage.put()
    for s_type in fe_3_stage_types:
      stage = Stage(
          feature_id=self.feature_3.key.integer_id(), stage_type=s_type)
      stage.put()
    for s_type in fe_4_stage_types:
      stage = Stage(
          feature_id=self.feature_4.key.integer_id(), stage_type=s_type)
      stage.put()
    self.fe_1_stages_dict = stage_helpers.get_feature_stages(
        self.feature_1.key.integer_id())
    self.fe_2_stages_dict = stage_helpers.get_feature_stages(
        self.feature_2.key.integer_id())
    self.fe_3_stages_dict = stage_helpers.get_feature_stages(
        self.feature_3.key.integer_id())
    self.fe_4_stages_dict = stage_helpers.get_feature_stages(
        self.feature_4.key.integer_id())

    self.admin_email = 'admin@example.com'
    self.app_admin = AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

  def tearDown(self):
    for kind in [FeatureEntry, Stage, Gate, AppUser]:
      for entity in kind.query():
        entity.key.delete()

    rediscache.flushall()

  def test_get_by_participant(self):
    """The people who are involve in a feature can edit it, others can't."""
    self.feature_2.cc_emails = ['cc@example.com']
    self.feature_2.editor_emails = ['editor@example.com']
    self.feature_2.put()
    self.feature_3.creator_email = 'creator@example.com'
    self.feature_3.put()
    self.feature_4.spec_mentor_emails = ['mentor@example.com']
    self.feature_4.put()

    owner_keys = feature_helpers.get_by_participant('feature_owner@example.com')
    self.assertEqual(4, len(owner_keys))
    cc_keys = feature_helpers.get_by_participant('cc@example.com')
    self.assertEqual([], cc_keys)
    editor_keys = feature_helpers.get_by_participant('editor@example.com')
    self.assertEqual([self.feature_2.key], editor_keys)
    creator_keys = feature_helpers.get_by_participant('creator@example.com')
    self.assertEqual([self.feature_3.key], creator_keys)
    mentor_keys = feature_helpers.get_by_participant('mentor@example.com')
    self.assertEqual([self.feature_4.key], mentor_keys)
    other_keys = feature_helpers.get_by_participant('other@example.com')
    self.assertEqual([], other_keys)

  def test_get_by_ids__empty(self):
    """A request to load zero features returns zero results."""
    actual = feature_helpers.get_by_ids([])
    self.assertEqual([], actual)

  def test_get_by_ids__cache_miss(self):
    """We can load features from datastore, and cache them for later."""
    actual = feature_helpers.get_by_ids([
        self.feature_1.key.integer_id(),
        self.feature_2.key.integer_id()])

    self.assertEqual(2, len(actual))
    self.assertEqual('feature a', actual[0]['name'])
    self.assertEqual('feature b', actual[1]['name'])

    lookup_key_1 = '%s|%s' % (FeatureEntry.DEFAULT_CACHE_KEY,
                              self.feature_1.key.integer_id())
    lookup_key_2 = '%s|%s' % (FeatureEntry.DEFAULT_CACHE_KEY,
                              self.feature_2.key.integer_id())
    self.assertEqual('feature a', rediscache.get(lookup_key_1)['name'])
    self.assertEqual('feature b', rediscache.get(lookup_key_2)['name'])

  def test_get_by_ids__cache_hit(self):
    """We can load features from rediscache."""
    cache_key = '%s|%s' % (
        FeatureEntry.DEFAULT_CACHE_KEY, self.feature_1.key.integer_id())
    cached_feature = {
      'name': 'fake cached_feature',
      'id': self.feature_1.key.integer_id(),
      'unlisted': False,
      'confidential': False
    }
    rediscache.set(cache_key, cached_feature)

    actual = feature_helpers.get_by_ids([self.feature_1.key.integer_id()])

    self.assertEqual(1, len(actual))
    self.assertEqual(cached_feature, actual[0])

  def test_get_by_ids__batch_order(self):
    """Features are returned in the order of the given IDs."""
    actual = feature_helpers.get_by_ids([
        self.feature_4.key.integer_id(),
        self.feature_1.key.integer_id(),
        self.feature_3.key.integer_id(),
        self.feature_2.key.integer_id(),
    ])

    self.assertEqual(4, len(actual))
    self.assertEqual('feature d', actual[0]['name'])
    self.assertEqual('feature a', actual[1]['name'])
    self.assertEqual('feature c', actual[2]['name'])
    self.assertEqual('feature b', actual[3]['name'])

  def test_get_by_ids__cached_correctly(self):
    """We should no longer be able to trigger bug #1647."""
    # Cache one to try to trigger the bug.
    feature_helpers.get_by_ids([self.feature_2.key.integer_id()])

    # Now do the lookup, but it would cache feature_2 at the key for feature_3.
    feature_helpers.get_by_ids([
        self.feature_4.key.integer_id(),
        self.feature_1.key.integer_id(),
        self.feature_3.key.integer_id(),
        self.feature_2.key.integer_id(),
    ])

    # This would read the incorrect cache entry and use it.
    actual = feature_helpers.get_by_ids([
        self.feature_4.key.integer_id(),
        self.feature_1.key.integer_id(),
        self.feature_3.key.integer_id(),
        self.feature_2.key.integer_id(),
    ])

    self.assertEqual(4, len(actual))
    self.assertEqual('feature d', actual[0]['name'])
    self.assertEqual('feature a', actual[1]['name'])
    self.assertEqual('feature c', actual[2]['name'])
    self.assertEqual('feature b', actual[3]['name'])

  def test_get_feature_names_by_ids__empty(self):
    """A request to load zero feature name returns zero results."""
    actual = feature_helpers.get_feature_names_by_ids([])
    self.assertEqual([], actual)

  def test_get_feature_names_by_ids__cache_miss(self):
    """We can load feature names from datastore, and cache them for later."""
    actual = feature_helpers.get_feature_names_by_ids([
        self.feature_1.key.integer_id(),
        self.feature_2.key.integer_id()])

    self.assertEqual(2, len(actual))
    self.assertEqual(6, len(actual[0]))
    self.assertEqual('feature a', actual[0]['name'])
    self.assertEqual(6, len(actual[1]))
    self.assertEqual('feature b', actual[1]['name'])

    lookup_key_1 = '%s|%s' % (FeatureEntry.FEATURE_NAME_CACHE_KEY,
                              self.feature_1.key.integer_id())
    lookup_key_2 = '%s|%s' % (FeatureEntry.FEATURE_NAME_CACHE_KEY,
                              self.feature_2.key.integer_id())
    self.assertEqual('feature a', rediscache.get(lookup_key_1)['name'])
    self.assertEqual('feature b', rediscache.get(lookup_key_2)['name'])

  def test_get_feature_names_by_ids__cache_hit(self):
    """We can load feature names from rediscache."""
    cache_key = '%s|%s' % (
        FeatureEntry.FEATURE_NAME_CACHE_KEY, self.feature_1.key.integer_id())
    cached_feature = {
      'name': 'fake cached_feature',
      'id': self.feature_1.key.integer_id(),
      'confidential': False,
      'owner_emails': [],
      'editor_emails': [],
      'cc_emails': [],
    }
    rediscache.set(cache_key, cached_feature)

    actual = feature_helpers.get_feature_names_by_ids([self.feature_1.key.integer_id()])

    self.assertEqual(1, len(actual))
    self.assertEqual(6, len(actual[0]))
    self.assertEqual(cached_feature, actual[0])

  def test_get_feature_names_by_ids__batch_order(self):
    """Feature names are returned in the order of the given IDs."""
    actual = feature_helpers.get_feature_names_by_ids([
        self.feature_4.key.integer_id(),
        self.feature_1.key.integer_id(),
        self.feature_3.key.integer_id(),
        self.feature_2.key.integer_id(),
    ])

    self.assertEqual(4, len(actual))
    self.assertEqual(6, len(actual[0]))
    self.assertEqual('feature d', actual[0]['name'])
    self.assertEqual('feature a', actual[1]['name'])
    self.assertEqual('feature c', actual[2]['name'])
    self.assertEqual('feature b', actual[3]['name'])

  def test_get_feature_names_by_ids__cached_correctly(self):
    """We should no longer be able to trigger bug #1647."""
    # Cache one to try to trigger the bug.
    feature_helpers.get_feature_names_by_ids([self.feature_2.key.integer_id()])

    # Now do the lookup, but it would cache feature_2 at the key for feature_3.
    feature_helpers.get_feature_names_by_ids([
        self.feature_4.key.integer_id(),
        self.feature_1.key.integer_id(),
        self.feature_3.key.integer_id(),
        self.feature_2.key.integer_id(),
    ])

    # This would read the incorrect cache entry and use it.
    actual = feature_helpers.get_feature_names_by_ids([
        self.feature_4.key.integer_id(),
        self.feature_1.key.integer_id(),
        self.feature_3.key.integer_id(),
        self.feature_2.key.integer_id(),
    ])

    self.assertEqual(4, len(actual))
    self.assertEqual(6, len(actual[0]))
    self.assertEqual('feature d', actual[0]['name'])
    self.assertEqual('feature a', actual[1]['name'])
    self.assertEqual('feature c', actual[2]['name'])
    self.assertEqual('feature b', actual[3]['name'])

  def test_get_in_milestone__normal(self):
    """We can retrieve a list of features."""
    self.feature_1.impl_status_chrome = 5
    # Set shipping milestone to 1.
    self.fe_1_stages_dict[160][0].milestones = MilestoneSet(desktop_first=1)
    self.feature_1.put()
    self.fe_1_stages_dict[160][0].put()

    self.feature_2.impl_status_chrome = 7
    # Set shipping milestone to 1.
    self.fe_2_stages_dict[260][0].milestones = MilestoneSet(desktop_first=1)
    self.feature_2.put()
    self.fe_2_stages_dict[260][0].put()

    self.feature_3.impl_status_chrome = 5
    # Set shipping milestone to 1.
    self.fe_3_stages_dict[360][0].milestones = MilestoneSet(desktop_first=1)
    self.feature_3.put()
    self.fe_3_stages_dict[360][0].put()

    self.feature_4.impl_status_chrome = 7
    # Set shipping milestone to 1.
    self.fe_4_stages_dict[460][0].milestones = MilestoneSet(desktop_first=2)
    self.feature_4.put()
    self.fe_4_stages_dict[460][0].put()

    actual = feature_helpers.get_in_milestone(milestone=1)
    removed = [f['name'] for f in actual['Removed']]
    enabled_by_default = [f['name'] for f in actual['Enabled by default']]
    self.assertEqual(
        ['feature b'],
        removed)
    self.assertEqual(
        ['feature a', 'feature c'],
        enabled_by_default)
    self.assertEqual(6, len(actual))

    cache_key = '%s|%s|%s' % (
        FeatureEntry.DEFAULT_CACHE_KEY, 'milestone', 1)
    cached_result = rediscache.get(cache_key)
    self.assertEqual(cached_result, actual)

  def test_get_in_milestone__unlisted(self):
    """Unlisted features should not be listed for users who can't edit."""
    self.feature_1.impl_status_chrome = 5
    self.fe_1_stages_dict[160][0].milestones = MilestoneSet(desktop_first=1)
    self.feature_1.put()
    self.fe_1_stages_dict[160][0].put()

    self.feature_2.unlisted = True
    self.feature_2.impl_status_chrome = 7
    self.fe_2_stages_dict[260][0].milestones = MilestoneSet(desktop_first=1)
    self.feature_2.put()
    self.fe_2_stages_dict[260][0].put()

    self.feature_3.impl_status_chrome = 5
    self.fe_3_stages_dict[360][0].milestones = MilestoneSet(desktop_first=1)
    self.feature_3.put()
    self.fe_3_stages_dict[360][0].put()

    self.feature_4.impl_status_chrome = 7
    self.fe_4_stages_dict[460][0].milestones = MilestoneSet(desktop_first=2)
    self.feature_4.put()
    self.fe_4_stages_dict[460][0].put()

    actual = feature_helpers.get_in_milestone(milestone=1)
    self.assertEqual(
        0,
        len(actual['Removed']))

  def test_get_in_milestone__unlisted_shown(self):
    """Unlisted features should be listed for users who can edit."""
    self.feature_1.impl_status_chrome = 5
    self.fe_1_stages_dict[160][0].milestones = MilestoneSet(desktop_first=1)
    self.feature_1.put()
    self.fe_1_stages_dict[160][0].put()

    self.feature_2.unlisted = True
    self.feature_2.impl_status_chrome = 7
    self.fe_2_stages_dict[260][0].milestones = MilestoneSet(desktop_first=1)
    self.feature_2.put()
    self.fe_2_stages_dict[260][0].put()

    self.feature_3.impl_status_chrome = 5
    self.fe_3_stages_dict[360][0].milestones = MilestoneSet(desktop_first=1)
    self.feature_3.put()
    self.fe_3_stages_dict[360][0].put()

    self.feature_4.impl_status_chrome = 7
    self.fe_4_stages_dict[460][0].milestones = MilestoneSet(desktop_first=2)
    self.feature_4.put()
    self.fe_4_stages_dict[460][0].put()

    actual = feature_helpers.get_in_milestone(
        milestone=1, show_unlisted=True)
    self.assertEqual(
        1,
        len(actual['Removed']))

  def test_get_in_milestone__no_enterprise(self):
    """Enterprise features are not shown in the roadmap."""
    # This is not included because of feature_type.
    self.feature_1.feature_type = FEATURE_TYPE_ENTERPRISE_ID
    self.feature_1.impl_status_chrome = ENABLED_BY_DEFAULT
    rollout_stage = Stage(
        feature_id=self.feature_1.key.integer_id(),
        stage_type=STAGE_ENT_ROLLOUT,
        milestones=MilestoneSet(desktop_first=1),
        rollout_milestone=1)
    self.feature_1.put()
    rollout_stage.put()

    # This one is included because it uses a stage that is considered.
    self.feature_2.impl_status_chrome = REMOVED
    self.fe_2_stages_dict[260][0].milestones = MilestoneSet(desktop_first=1)
    self.fe_2_stages_dict[260][0].finch_url = 'https://example.com/finch'
    self.feature_2.put()
    self.fe_2_stages_dict[260][0].put()

    actual = feature_helpers.get_in_milestone(milestone=1)
    expected_fe_2 = converters.feature_entry_to_json_basic(self.feature_2)
    expected_fe_2['roadmap_stage_ids'] = [
        self.fe_2_stages_dict[260][0].key.integer_id()]
    expected_fe_2['finch_urls'] = ['https://example.com/finch']
    expected = {
        'Deprecated': [],
        'Enabled by default': [],
        'In developer trial (Behind a flag)': [],
        'Stepped rollout': [],
        'Origin trial': [],
        'Removed': [expected_fe_2]}
    self.maxDiff = None
    self.assertEqual(expected, actual)

  def test_get_in_milestone__cached(self):
    """If there is something in the cache, we use it."""
    cache_key = '%s|%s|%s' % (
        FeatureEntry.DEFAULT_CACHE_KEY, 'milestone', 1)
    cached_test_feature = {'test': [{'name': 'test_feature', 'unlisted': False, 'confidential': False}]}
    rediscache.set(cache_key, cached_test_feature)

    actual = feature_helpers.get_in_milestone(milestone=1)
    self.assertEqual(
        cached_test_feature,
        actual)

  def _create_wp_stages_and_gates(self):
    self.fe_1_stages_dict[160][0].milestones = MilestoneSet(desktop_first=1)
    self.fe_1_stages_dict[160][0].put()
    self.g1 = Gate(feature_id=self.feature_1.key.integer_id(),
                   stage_id=self.fe_1_stages_dict[160][0].key.integer_id(),
                   gate_type=GATE_ENTERPRISE_SHIP,
                   state=Vote.APPROVED)
    self.g1.put()
    self.fe_2_stages_dict[260][0].milestones = MilestoneSet(desktop_last=2)
    self.fe_2_stages_dict[260][0].put()
    self.g2 = Gate(feature_id=self.feature_2.key.integer_id(),
                   stage_id=self.fe_2_stages_dict[260][0].key.integer_id(),
                   gate_type=GATE_ENTERPRISE_SHIP,
                   state=Vote.APPROVED)
    self.g2.put()
    self.fe_3_stages_dict[360][0].milestones = MilestoneSet(ios_first=3)
    self.fe_3_stages_dict[360][0].put()
    self.g3 = Gate(feature_id=self.feature_3.key.integer_id(),
                   stage_id=self.fe_3_stages_dict[360][0].key.integer_id(),
                   gate_type=GATE_ENTERPRISE_SHIP,
                   state=Vote.APPROVED)
    self.g3.put()
    self.fe_4_stages_dict[460][0].milestones = MilestoneSet(ios_last=4)
    self.fe_4_stages_dict[460][0].put()
    self.g4 = Gate(feature_id=self.feature_4.key.integer_id(),
                   stage_id=self.fe_4_stages_dict[460][0].key.integer_id(),
                   gate_type=GATE_ENTERPRISE_SHIP,
                   state=Vote.APPROVED)
    self.g4.put()

  def test_get_features_in_release_notes__ready__or_not_admin(self):
    """Admins see the complete list regardless of being ready to publish."""
    cache_key = '%s|%s|%s' % (
        FeatureEntry.SEARCH_CACHE_KEY, 'release_notes_milestone', 1)
    self._create_wp_stages_and_gates()

    self.feature_1.enterprise_impact = ENTERPRISE_IMPACT_LOW
    self.feature_1.put()
    self.feature_2.feature_type = FEATURE_TYPE_ENTERPRISE_ID
    self.feature_2.put()
    features = feature_helpers.get_features_in_release_notes(milestone=1)
    # Nothing is ready to publish yet, and user is not an admin.
    self.assertEqual(0, len(features))

    testing_config.sign_in(self.admin_email, 1)
    features = feature_helpers.get_features_in_release_notes(milestone=1)
    # Admin sees release note items that are not yet ready for non-admins.
    self.assertEqual(2, len(features))

  def test_get_features_in_release_notes__only_ready_anon(self):
    """We include features only if they are marked ready to publish."""
    cache_key = '%s|%s|%s' % (
        FeatureEntry.SEARCH_CACHE_KEY, 'release_notes_milestone', 1)
    self._create_wp_stages_and_gates()

    self.feature_1.enterprise_impact = ENTERPRISE_IMPACT_LOW
    self.feature_1.put()
    self.feature_2.feature_type = FEATURE_TYPE_ENTERPRISE_ID
    self.feature_2.put()
    features = feature_helpers.get_features_in_release_notes(milestone=1)
    # Nothing is ready to publish yet.
    self.assertEqual(0, len(features))
    rediscache.delete(cache_key)

    self.feature_1.is_releasenotes_publish_ready = True
    self.feature_1.put()
    self.feature_2.is_releasenotes_publish_ready = True
    self.feature_2.put()
    features = feature_helpers.get_features_in_release_notes(milestone=1)
    # Now they are ready to publish.
    self.assertEqual(2, len(features))

  def test_get_features_in_release_notes__wp_need_enterprise_approval(self):
    """We include WP features only if enterprise shipping gate is approved."""
    self._create_wp_stages_and_gates()
    cache_key = '%s|%s|%s' % (
        FeatureEntry.SEARCH_CACHE_KEY, 'release_notes_milestone', 1)
    self.feature_1.enterprise_impact = ENTERPRISE_IMPACT_LOW
    self.feature_1.is_releasenotes_publish_ready = True
    self.feature_1.put()
    self.feature_2.enterprise_impact = ENTERPRISE_IMPACT_MEDIUM
    self.feature_2.is_releasenotes_publish_ready = True
    self.feature_2.put()
    self.feature_3.enterprise_impact = ENTERPRISE_IMPACT_HIGH
    self.feature_3.is_releasenotes_publish_ready = True
    self.feature_3.put()
    self.feature_4.enterprise_impact = ENTERPRISE_IMPACT_LOW
    self.feature_4.is_releasenotes_publish_ready = True
    self.feature_4.put()

    features = feature_helpers.get_features_in_release_notes(milestone=1)
    self.assertEqual(4, len(features))
    rediscache.delete(cache_key)

    self.g1.state = Gate.PREPARING
    self.g1.put()
    self.g2.state = Vote.NEEDS_WORK
    self.g2.put()
    self.g3.gate_type = GATE_API_SHIP
    self.g3.put()
    self.g4.gate_type = GATE_ENTERPRISE_PLAN
    self.g4.put()

    features = feature_helpers.get_features_in_release_notes(milestone=1)
    # feature_4 is a deprecation, so it is always included.
    self.assertEqual(['feature d'], [f['name'] for f in features])
    rediscache.delete(cache_key)

  def test_get_features_in_release_notes__non_enterprise_features(self):
    """We can retrieve a list of features."""
    self._create_wp_stages_and_gates()
    cache_key = '%s|%s|%s' % (
        FeatureEntry.SEARCH_CACHE_KEY, 'release_notes_milestone', 1)

    # There is no breaking change
    features = feature_helpers.get_features_in_release_notes(milestone=1)
    self.assertEqual(0, len(features))
    cached_result = rediscache.get(cache_key)
    rediscache.delete(cache_key)
    self.assertEqual(cached_result, features)

    # Features 1, 2, 3 and 4 are breaking changes
    self.feature_1.enterprise_impact = ENTERPRISE_IMPACT_LOW
    self.feature_1.is_releasenotes_publish_ready = True
    self.feature_1.put()
    self.feature_2.enterprise_impact = ENTERPRISE_IMPACT_MEDIUM
    self.feature_2.is_releasenotes_publish_ready = True
    self.feature_2.put()
    self.feature_3.enterprise_impact = ENTERPRISE_IMPACT_HIGH
    self.feature_3.is_releasenotes_publish_ready = True
    self.feature_3.put()
    self.feature_4.enterprise_impact = ENTERPRISE_IMPACT_LOW
    self.feature_4.is_releasenotes_publish_ready = True
    self.feature_4.put()

    features = feature_helpers.get_features_in_release_notes(milestone=1)
    self.assertEqual(4, len(features))
    self.assertEqual(
      ['feature a', 'feature b', 'feature c', 'feature d'],
      [f['name'] for f in features])
    cached_result = rediscache.get(cache_key)
    rediscache.delete(cache_key)
    self.assertEqual(cached_result, features)

    cache_key = '%s|%s|%s' % (
        FeatureEntry.SEARCH_CACHE_KEY, 'release_notes_milestone', 3)
    features = feature_helpers.get_features_in_release_notes(milestone=3)
    self.assertEqual(2, len(features))
    self.assertEqual(
      ['feature c', 'feature d'],
      [f['name'] for f in features])
    cached_result = rediscache.get(cache_key)
    rediscache.delete(cache_key)
    self.assertEqual(cached_result, features)

    # Features 1, 2, 3 are breaking changes
    # only feature 1, 2 and 4 are planned to be released
    self.feature_4.enterprise_impact = ENTERPRISE_IMPACT_NONE
    self.feature_4.put()
    self.fe_3_stages_dict[360][0].milestones = MilestoneSet()
    self.fe_3_stages_dict[360][0].put()

    features = feature_helpers.get_features_in_release_notes(milestone=3)
    self.assertEqual(0, len(features))
    cached_result = rediscache.get(cache_key)
    rediscache.delete(cache_key)
    self.assertEqual(cached_result, features)

    cache_key = '%s|%s|%s' % (
        FeatureEntry.SEARCH_CACHE_KEY, 'release_notes_milestone', 1)
    features = feature_helpers.get_features_in_release_notes(milestone=1)
    self.assertEqual(2, len(features))
    self.assertEqual(
      ['feature a', 'feature b'],
      [f['name'] for f in features])
    cached_result = rediscache.get(cache_key)
    rediscache.delete(cache_key)
    self.assertEqual(cached_result, features)

    # Enterprise features are included
    rollout_stage = Stage(
        feature_id=self.feature_4.key.integer_id(),
        stage_type=STAGE_ENT_ROLLOUT,
        rollout_milestone=1)
    rollout_stage.put()
    self.feature_4.feature_type = 4
    self.feature_4.put()

    features = feature_helpers.get_features_in_release_notes(milestone=1)
    self.assertEqual(3, len(features))
    self.assertEqual(
      ['feature a', 'feature b', 'feature d'],
      [f['name'] for f in features])
    cached_result = rediscache.get(cache_key)
    rediscache.delete(cache_key)
    self.assertEqual(cached_result, features)

    # Deleted features are not included
    self.feature_4.deleted = True
    self.feature_4.put()
    features = feature_helpers.get_features_in_release_notes(milestone=1)
    self.assertEqual(2, len(features))
    self.assertEqual(
      ['feature a', 'feature b'],
      [f['name'] for f in features])
    cached_result = rediscache.get(cache_key)
    rediscache.delete(cache_key)
    self.assertEqual(cached_result, features)

  def test_group_by_roadmap_section__empty(self):
    """An empty list of features results in an empty roadmap card."""
    actual = feature_helpers._group_by_roadmap_section(
        [], [], [], [])
    expected = {
        'Enabled by default': [],
        'Deprecated': [],
        'Removed': [],
        'Stepped rollout': [],
        'Origin trial': [],
        'In developer trial (Behind a flag)': [],
        }
    self.assertEqual(actual, expected)

  def test_group_by_roadmap_section__removed(self):
    """A shipping feature with impl_status_chrome=REMOVED is here."""
    fe = FeatureEntry(impl_status_chrome=REMOVED)
    actual = feature_helpers._group_by_roadmap_section(
        [fe], [], [], [])
    self.assertEqual(actual['Removed'], [fe])

  def test_group_by_roadmap_section__deprecated(self):
    """A shipping deprecation entry is here."""
    fe = FeatureEntry(feature_type=FEATURE_TYPE_DEPRECATION_ID)
    actual = feature_helpers._group_by_roadmap_section(
        [fe], [], [], [])
    self.assertEqual(actual['Deprecated'], [fe])

  def test_group_by_roadmap_section__enabled(self):
    """A shipping feature without a special case is here."""
    fe = FeatureEntry()
    actual = feature_helpers._group_by_roadmap_section(
        [fe], [], [], [])
    self.assertEqual(actual['Enabled by default'], [fe])

  def test_group_by_roadmap_section__origin_trial(self):
    """Any feature found because of a origin trial stage goes here."""
    fe = FeatureEntry()
    actual = feature_helpers._group_by_roadmap_section(
        [], [fe], [], [])
    self.assertEqual(actual['Origin trial'], [fe])

  def test_group_by_roadmap_section__dev_trial(self):
    """Any feature found because of a dev trail stage goes here."""
    fe = FeatureEntry()
    actual = feature_helpers._group_by_roadmap_section(
        [], [], [fe], [])
    self.assertEqual(actual['In developer trial (Behind a flag)'], [fe])

  def test_group_by_roadmap_section__rollout(self):
    """Any feature found because of a rollout stage goes here."""
    fe = FeatureEntry()
    actual = feature_helpers._group_by_roadmap_section(
        [], [], [], [fe])
    self.assertEqual(actual['Stepped rollout'], [fe])

  def test_should_appear_on_roadmap__no_deleted(self):
    """The roadmap does not include deleted feature entries."""
    self.assertTrue(feature_helpers._should_appear_on_roadmap(
        FeatureEntry()))

    self.assertFalse(feature_helpers._should_appear_on_roadmap(
        FeatureEntry(deleted=True)))

  def test_should_appear_on_roadmap__no_inactive(self):
    """The roadmap does not include inactive feature entries."""
    for status in [
        PROPOSED, IN_DEVELOPMENT, BEHIND_A_FLAG, ENABLED_BY_DEFAULT,
        DEPRECATED, REMOVED, ORIGIN_TRIAL]:
      self.assertTrue(feature_helpers._should_appear_on_roadmap(
          FeatureEntry(impl_status_chrome=status)))

    for status in [NO_ACTIVE_DEV, ON_HOLD, NO_LONGER_PURSUING]:
      self.assertFalse(feature_helpers._should_appear_on_roadmap(
          FeatureEntry(impl_status_chrome=status)))

  def test_should_appear_on_roadmap__no_enterprise(self):
    """The roadmap does not include enterprise features."""
    self.assertTrue(feature_helpers._should_appear_on_roadmap(
        FeatureEntry(feature_type=FEATURE_TYPE_INCUBATE_ID)))

    self.assertTrue(feature_helpers._should_appear_on_roadmap(
        FeatureEntry(feature_type=FEATURE_TYPE_EXISTING_ID)))

    self.assertTrue(feature_helpers._should_appear_on_roadmap(
        FeatureEntry(feature_type=FEATURE_TYPE_DEPRECATION_ID)))

    self.assertFalse(feature_helpers._should_appear_on_roadmap(
        FeatureEntry(feature_type=FEATURE_TYPE_ENTERPRISE_ID)))

  def test_get_features_by_impl_status__normal(self):
    """We can get JSON dicts for /features_v2.json."""
    features = feature_helpers.get_features_by_impl_status()
    self.assertEqual(4, len(features))
    self.assertEqual({'feature a', 'feature b', 'feature c', 'feature d'},
                     set(f['name'] for f in features))
    self.assertEqual('feature a', features[2]['name'])
    self.assertEqual('feature b', features[3]['name'])


  def test_get_features_by_impl_status__deleted(self):
    """Deleted features are not included in /features_v2.json."""
    self.feature_3.deleted = True
    self.feature_3.put()

    features = feature_helpers.get_features_by_impl_status()

    self.assertEqual(3, len(features))
    self.assertEqual({'feature a', 'feature b', 'feature d'},
                     set(f['name'] for f in features))
    self.assertEqual('feature a', features[1]['name'])
    self.assertEqual('feature b', features[2]['name'])

  @mock.patch('internals.feature_helpers.get_current_milestone_info')
  @mock.patch('internals.feature_helpers.datetime')
  def test_get_stale_features__none_stale(self, mock_dt, mock_mstone_info):
    """No features are stale, so the function should return an empty list."""
    mock_dt.now.return_value = datetime(2023, 1, 1)
    mock_mstone_info.return_value = {'mstone': '100'}

    # Set features to be recently reviewed and therefore not stale.
    self.feature_1.accurate_as_of = datetime(2022, 12, 20)
    self.feature_1.outstanding_notifications = 1
    self.feature_1.put()
    self.feature_2.accurate_as_of = datetime(2022, 12, 15)
    self.feature_2.outstanding_notifications = 1
    self.feature_2.put()

    actual = feature_helpers.get_stale_features()
    self.assertEqual([], actual)

  @mock.patch('internals.feature_helpers.get_current_milestone_info')
  @mock.patch('internals.feature_helpers.datetime')
  def test_get_stale_features__stale_but_no_relevant_milestone(
      self, mock_dt, mock_mstone_info):
    """Stale features with no milestones in the upcoming window are ignored."""
    mock_dt.now.return_value = datetime(2023, 1, 1)
    mock_mstone_info.return_value = {'mstone': '100'}

    # feature_1 is stale, but its milestone is in the past (before 100).
    self.feature_1.accurate_as_of = None
    self.feature_1.outstanding_notifications = 2
    self.feature_1.put()
    shipping_stage_1 = self.fe_1_stages_dict[160][0]
    shipping_stage_1.milestones = MilestoneSet(desktop_first=99)
    shipping_stage_1.put()

    # feature_2 is stale, but its milestone is too far in the future (after 102).
    self.feature_2.accurate_as_of = None
    self.feature_2.outstanding_notifications = 1
    self.feature_2.put()
    shipping_stage_2 = self.fe_2_stages_dict[260][0]
    shipping_stage_2.milestones = MilestoneSet(desktop_first=103)
    shipping_stage_2.put()

    # feature_3 is stale, but its stage has no milestones set.
    self.feature_3.accurate_as_of = None
    self.feature_3.outstanding_notifications = 2
    self.feature_3.put()
    shipping_stage_3 = self.fe_3_stages_dict[360][0]
    shipping_stage_3.milestones = None
    shipping_stage_3.put()

    actual = feature_helpers.get_stale_features()
    self.assertEqual([], actual)

  @mock.patch('internals.feature_helpers.get_current_milestone_info')
  @mock.patch('internals.feature_helpers.datetime')
  def test_get_stale_features__one_stale_one_fresh(
      self, mock_dt, mock_mstone_info):
    """Correctly identifies one stale feature with an upcoming milestone."""
    mock_dt.now.return_value = datetime(2023, 1, 1)
    mock_mstone_info.return_value = {'mstone': '100'}

    # This feature is stale because it was reviewed over a month ago.
    self.feature_1.accurate_as_of = datetime(2022, 11, 1)
    self.feature_1.outstanding_notifications = 1
    self.feature_1.put()

    # And its milestone is upcoming (between 100 and 102).
    shipping_stage = self.fe_1_stages_dict[160][0]
    shipping_stage.milestones = MilestoneSet(desktop_first=102)
    shipping_stage.put()

    # This feature is not stale.
    self.feature_2.accurate_as_of = datetime(2022, 12, 15)
    self.feature_2.outstanding_notifications = 1
    self.feature_2.put()
    shipping_stage_2 = self.fe_2_stages_dict[260][0]
    shipping_stage_2.milestones = MilestoneSet(desktop_first=101)
    shipping_stage_2.put()

    actual = feature_helpers.get_stale_features()
    self.assertEqual(1, len(actual))
    feature, mstone, field = actual[0]
    self.assertEqual(self.feature_1.key.integer_id(), feature.key.integer_id())
    self.assertEqual(102, mstone)
    self.assertEqual('shipped_milestone', field)

  @mock.patch('internals.feature_helpers.get_current_milestone_info')
  @mock.patch('internals.feature_helpers.datetime')
  def test_get_stale_features__no_outstanding_notifications(
      self, mock_dt, mock_mstone_info):
    """Ignores stale features that have not had a notification sent."""
    mock_dt.now.return_value = datetime(2023, 1, 1)
    mock_mstone_info.return_value = {'mstone': '100'}

    # This feature is stale because it was reviewed over a month ago,
    # but has not yet received a notification.
    self.feature_1.accurate_as_of = datetime(2022, 11, 1)
    self.feature_1.outstanding_notifications = 0
    self.feature_1.put()

    # And its milestone is upcoming (between 100 and 102).
    shipping_stage = self.fe_1_stages_dict[160][0]
    shipping_stage.milestones = MilestoneSet(desktop_first=102)
    shipping_stage.put()

    # This feature is not stale.
    self.feature_2.accurate_as_of = datetime(2022, 12, 15)
    self.feature_2.outstanding_notifications = 0
    self.feature_2.put()
    shipping_stage_2 = self.fe_2_stages_dict[260][0]
    shipping_stage_2.milestones = MilestoneSet(desktop_first=101)
    shipping_stage_2.put()

    actual = feature_helpers.get_stale_features()
    self.assertEqual(0, len(actual))

  @mock.patch('internals.feature_helpers.get_current_milestone_info')
  @mock.patch('internals.feature_helpers.datetime')
  def test_get_stale_features__non_shipping_stages(
      self, mock_dt, mock_mstone_info):
    """Ignores features with relevant milestones in non-shipping stages."""
    mock_dt.now.return_value = datetime(2023, 1, 1)
    mock_mstone_info.return_value = {'mstone': '100'}

    # This feature is stale because it was reviewed over a month ago.
    self.feature_1.accurate_as_of = datetime(2022, 11, 1)
    self.feature_1.outstanding_notifications = 1
    self.feature_1.put()

    # And its milestone is upcoming (between 100 and 102),
    # but it's a dev trial milestone.
    shipping_stage = self.fe_1_stages_dict[130][0]
    shipping_stage.milestones = MilestoneSet(desktop_first=102)
    shipping_stage.put()

    # This feature is not stale.
    self.feature_2.accurate_as_of = datetime(2022, 12, 15)
    self.feature_2.outstanding_notifications = 0
    self.feature_2.put()
    shipping_stage_2 = self.fe_2_stages_dict[260][0]
    shipping_stage_2.milestones = MilestoneSet(desktop_first=101)
    shipping_stage_2.put()

    actual = feature_helpers.get_stale_features()
    self.assertEqual(0, len(actual))

  @mock.patch('internals.feature_helpers.get_current_milestone_info')
  @mock.patch('internals.feature_helpers.datetime')
  def test_get_stale_features__deleted_feature_is_ignored(
      self, mock_dt, mock_mstone_info):
    """A deleted feature should not be returned, even if it is stale."""
    mock_dt.now.return_value = datetime(2023, 1, 1)
    mock_mstone_info.return_value = {'mstone': '100'}

    # This feature is stale and deleted.
    self.feature_1.accurate_as_of = None
    self.feature_1.deleted = True
    self.feature_1.outstanding_notifications = 2
    self.feature_1.put()
    shipping_stage = self.fe_1_stages_dict[160][0]
    shipping_stage.milestones = MilestoneSet(desktop_first=101)
    shipping_stage.put()

    actual = feature_helpers.get_stale_features()
    self.assertEqual([], actual)

  @mock.patch('internals.feature_helpers.get_current_milestone_info')
  @mock.patch('internals.feature_helpers.datetime')
  def test_get_stale_features__finds_milestone_from_relevant_stages(
      self, mock_dt, mock_mstone_info):
    """Finds a milestone from one of several stages."""
    mock_dt.now.return_value = datetime(2023, 1, 1)
    mock_mstone_info.return_value = {'mstone': '100'}

    # This feature is stale.
    self.feature_1.accurate_as_of = datetime(2022, 1, 1)
    self.feature_1.outstanding_notifications = 3
    self.feature_1.put()

    # Shipping milestone is 102 (in range).
    shipping_stage = self.fe_1_stages_dict[160][0]
    shipping_stage.milestones = MilestoneSet(desktop_first=102)
    shipping_stage.put()

    # Another shipping stage exists with a later milestone.
    shipping_stage_2 = Stage(feature_id=self.feature_1.key.integer_id(),
                             stage_type=160)
    shipping_stage_2.milestones = MilestoneSet(android_first=105)
    shipping_stage_2.put()

    actual = feature_helpers.get_stale_features()
    self.assertEqual(1, len(actual))
    feature, mstone, field = actual[0]
    self.assertEqual(self.feature_1.key.integer_id(), feature.key.integer_id())
    # The function should identify 102 as the only relevant milestone.
    self.assertEqual(102, mstone)
    self.assertEqual('shipped_milestone', field)


class FeatureHelpersFilteringTest(testing_config.CustomTestCase):

  def setUp(self):
    self.owner_email = 'owner@example.com'
    self.editor_email = 'editor@example.com'
    self.creator_email = 'creator@example.com'
    self.other_user_email = 'other@example.com'

    # FeatureEntry objects for filter_unlisted and filter_confidential
    self.feature_public = FeatureEntry(
        name='Public feature', summary='sum', category=1, unlisted=False)
    self.feature_public.put()

    self.feature_unlisted_viewable = FeatureEntry(
        name='Unlisted viewable', summary='sum', category=1, unlisted=True,
        owner_emails=[self.owner_email],
        editor_emails=[self.editor_email],
        creator_email=self.creator_email)
    self.feature_unlisted_viewable.put()

    self.feature_unlisted_hidden = FeatureEntry(
        name='Unlisted hidden', summary='sum', category=1, unlisted=True,
        owner_emails=['someone_else@example.com'])
    self.feature_unlisted_hidden.put()

    self.all_feature_entries = [
        self.feature_public,
        self.feature_unlisted_viewable,
        self.feature_unlisted_hidden,
    ]

    # Formatted dicts for the "_formatted" filter versions
    self.formatted_public = {
        'id': 1, 'name': 'Public feature', 'unlisted': False,
        'creator': 'random@example.com',
        'editors': [], 'browsers': {'chrome': {'owners': []}}}

    self.formatted_unlisted_viewable = {
        'id': 2, 'name': 'Unlisted viewable', 'unlisted': True,
        'creator': self.creator_email,
        'editors': [self.editor_email],
        'browsers': {'chrome': {'owners': [self.owner_email]}}}

    self.formatted_unlisted_hidden = {
        'id': 3, 'name': 'Unlisted hidden', 'unlisted': True,
        'creator': 'random@example.com',
        'editors': [],
        'browsers': {'chrome': {'owners': ['someone_else@example.com']}}}

    self.all_formatted_features = [
        self.formatted_public,
        self.formatted_unlisted_viewable,
        self.formatted_unlisted_hidden,
    ]

  def tearDown(self):
    for entity in FeatureEntry.query():
      entity.key.delete()
    testing_config.sign_out()

  def _get_names(self, feature_list):
    """Helper to get a list of names from FeatureEntry or dict lists."""
    if not feature_list:
      return []
    if isinstance(feature_list[0], FeatureEntry):
      return [f.name for f in feature_list]
    return [f['name'] for f in feature_list]

  def test_filter_unlisted__no_user(self):
    """Anonymous users should only see public features."""
    testing_config.sign_out()
    actual = feature_helpers.filter_unlisted(self.all_feature_entries)
    self.assertEqual(1, len(actual))
    self.assertEqual(['Public feature'], self._get_names(actual))

  def test_filter_unlisted__user_with_no_access(self):
    """A logged-in user should not see unlisted features they don't own/edit."""
    testing_config.sign_in(self.other_user_email, 1)
    actual = feature_helpers.filter_unlisted(self.all_feature_entries)
    self.assertEqual(1, len(actual))
    self.assertEqual(['Public feature'], self._get_names(actual))

  def test_filter_unlisted__user_is_owner(self):
    """A logged-in user should see unlisted features they own."""
    testing_config.sign_in(self.owner_email, 1)
    actual = feature_helpers.filter_unlisted(self.all_feature_entries)
    self.assertCountEqual(
        ['Public feature', 'Unlisted viewable'], self._get_names(actual))
    self.assertEqual(2, len(actual))

  def test_filter_unlisted__user_is_editor(self):
    """A logged-in user should see unlisted features they can edit."""
    testing_config.sign_in(self.editor_email, 1)
    actual = feature_helpers.filter_unlisted(self.all_feature_entries)
    self.assertCountEqual(
        ['Public feature', 'Unlisted viewable'], self._get_names(actual))
    self.assertEqual(2, len(actual))

  def test_filter_unlisted__user_is_creator(self):
    """A logged-in user should see unlisted features they created."""
    testing_config.sign_in(self.creator_email, 1)
    actual = feature_helpers.filter_unlisted(self.all_feature_entries)
    self.assertCountEqual(
        ['Public feature', 'Unlisted viewable'], self._get_names(actual))
    self.assertEqual(2, len(actual))

  def test_filter_unlisted_formatted__no_user(self):
    """Anonymous users should only see public features (formatted)."""
    testing_config.sign_out()
    actual = feature_helpers.filter_unlisted_formatted(
        self.all_formatted_features)
    self.assertEqual(1, len(actual))
    self.assertEqual(['Public feature'], self._get_names(actual))

  def test_filter_unlisted_formatted__user_with_no_access(self):
    """A logged-in user should not see unlisted features they don't own/edit (formatted)."""
    testing_config.sign_in(self.other_user_email, 1)
    actual = feature_helpers.filter_unlisted_formatted(
        self.all_formatted_features)
    self.assertEqual(1, len(actual))
    self.assertEqual(['Public feature'], self._get_names(actual))

  def test_filter_unlisted_formatted__user_is_owner(self):
    """A logged-in user should see unlisted features they own (formatted)."""
    testing_config.sign_in(self.owner_email, 1)
    actual = feature_helpers.filter_unlisted_formatted(
        self.all_formatted_features)
    self.assertCountEqual(
        ['Public feature', 'Unlisted viewable'], self._get_names(actual))
    self.assertEqual(2, len(actual))

  def test_filter_unlisted_formatted__user_is_editor(self):
    """A logged-in user should see unlisted features they can edit (formatted)."""
    testing_config.sign_in(self.editor_email, 1)
    actual = feature_helpers.filter_unlisted_formatted(
        self.all_formatted_features)
    self.assertCountEqual(
        ['Public feature', 'Unlisted viewable'], self._get_names(actual))
    self.assertEqual(2, len(actual))

  def test_filter_unlisted_formatted__user_is_creator(self):
    """A logged-in user should see unlisted features they created (formatted)."""
    testing_config.sign_in(self.creator_email, 1)
    actual = feature_helpers.filter_unlisted_formatted(
        self.all_formatted_features)
    self.assertCountEqual(
        ['Public feature', 'Unlisted viewable'], self._get_names(actual))
    self.assertEqual(2, len(actual))

  @mock.patch('internals.feature_helpers.permissions.can_view_feature')
  def test_filter_confidential__all_visible(self, mock_can_view):
    """Returns all features if user can view all of them."""
    mock_can_view.return_value = True
    actual = feature_helpers.filter_confidential(self.all_feature_entries)
    self.assertEqual(len(self.all_feature_entries), len(actual))

  @mock.patch('internals.feature_helpers.permissions.can_view_feature')
  def test_filter_confidential__none_visible(self, mock_can_view):
    """Returns an empty list if user can view none of them."""
    mock_can_view.return_value = False
    actual = feature_helpers.filter_confidential(self.all_feature_entries)
    self.assertEqual(0, len(actual))

  @mock.patch('internals.feature_helpers.permissions.can_view_feature')
  def test_filter_confidential__some_visible(self, mock_can_view):
    """Returns a subset of features that the user can view."""
    # The mock will return True for the first and third features in the list.
    mock_can_view.side_effect = [True, False, True]
    actual = feature_helpers.filter_confidential(self.all_feature_entries)
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        ['Public feature', 'Unlisted hidden'], self._get_names(actual))

  @mock.patch('internals.feature_helpers.permissions.can_view_feature_formatted')
  def test_filter_confidential_formatted__all_visible(self, mock_can_view):
    """Returns all features if user can view all of them (formatted)."""
    mock_can_view.return_value = True
    actual = feature_helpers.filter_confidential_formatted(
        self.all_formatted_features)
    self.assertEqual(len(self.all_formatted_features), len(actual))

  @mock.patch('internals.feature_helpers.permissions.can_view_feature_formatted')
  def test_filter_confidential_formatted__none_visible(self, mock_can_view):
    """Returns an empty list if user can view none of them (formatted)."""
    mock_can_view.return_value = False
    actual = feature_helpers.filter_confidential_formatted(
        self.all_formatted_features)
    self.assertEqual(0, len(actual))

  @mock.patch('internals.feature_helpers.permissions.can_view_feature_formatted')
  def test_filter_confidential_formatted__some_visible(self, mock_can_view):
    """Returns a subset of features that the user can view (formatted)."""
    mock_can_view.side_effect = [False, True, True]
    actual = feature_helpers.filter_confidential_formatted(
        self.all_formatted_features)
    self.assertEqual(2, len(actual))
    self.assertCountEqual(
        ['Unlisted viewable', 'Unlisted hidden'], self._get_names(actual))


class ShippingFeatureHelpersTest(testing_config.CustomTestCase):

  def setUp(self):
    self.milestone = 120

    # Feature 1: Complete.
    self.feature_1 = FeatureEntry(
        id=1, name='Feature 1 (Complete)', summary='sum', category=1,
        feature_type=FEATURE_TYPE_INCUBATE_ID,
        finch_name='featureOneFinch', owner_emails=['owner@example.com'],
        bug_url='https://example.com/bug1',
        launch_bug_url='https://example.com/launch1')
    self.feature_1.put()
    self.stage_1 = Stage(
        id=101, feature_id=1, stage_type=160,
        intent_thread_url='https://example.com/intent1',
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_1.put()
    Gate(id=1001, feature_id=1, stage_id=101, gate_type=GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 2: Incomplete (Missing LGTM).
    self.feature_2 = FeatureEntry(
        id=2, name='Feature 2 (No LGTM)', summary='sum', category=1,
        feature_type=FEATURE_TYPE_INCUBATE_ID,
        finch_name='feature2-finch')
    self.feature_2.put()
    self.stage_2 = Stage(
        id=102, feature_id=2, stage_type=160,
        intent_thread_url='https://example.com/intent2',
        milestones=MilestoneSet(android_first=self.milestone))
    self.stage_2.put()
    Gate(id=1002, feature_id=2, stage_id=102, gate_type=GATE_API_SHIP,
         state=Vote.NA).put()

    # Feature 3: Incomplete (Missing Intent to Ship).
    self.feature_3 = FeatureEntry(
        id=3, name='Feature 3 (No I2S)', summary='sum', category=1,
        feature_type=FEATURE_TYPE_INCUBATE_ID,
        finch_name='feature3-finch')
    self.feature_3.put()
    self.stage_3 = Stage(
        id=103, feature_id=3, stage_type=160,
        intent_thread_url=None,
        milestones=MilestoneSet(webview_first=self.milestone))
    self.stage_3.put()
    Gate(id=1003, feature_id=3, stage_id=103, gate_type=GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 4: Incomplete (Missing Finch name and justification).
    self.feature_4 = FeatureEntry(
        id=4, name='Feature 4 (No Finch)', summary='sum', category=1,
        feature_type=FEATURE_TYPE_INCUBATE_ID,
        finch_name=None, non_finch_justification=None)
    self.feature_4.put()
    self.stage_4 = Stage(
        id=104, feature_id=4, stage_type=160,
        intent_thread_url='https://example.com/intent4',
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_4.put()
    Gate(id=1004, feature_id=4, stage_id=104, gate_type=GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 5: Complete (PSA/Code Change) - Bypasses checks.
    self.feature_5 = FeatureEntry(
        id=5, name='Feature 5 (PSA)', summary='sum', category=1,
        feature_type=FEATURE_TYPE_CODE_CHANGE_ID)
    self.feature_5.put()
    self.stage_5 = Stage(
        id=105, feature_id=5, stage_type=360,
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_5.put()

    # Feature 7: Incomplete (Not stable in JSON).
    self.feature_7 = FeatureEntry(
        id=7, name='F7 Unstable', summary='sum', category=1,
        feature_type=FEATURE_TYPE_INCUBATE_ID,
        finch_name='feature7-unstable')
    self.feature_7.put()
    self.stage_7 = Stage(
        id=107, feature_id=7, stage_type=160,
        intent_thread_url='https://example.com/intent7',
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_7.put()
    Gate(id=1007, feature_id=7, stage_id=107, gate_type=GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 8: Complete (Enabled in content_features.cc).
    self.feature_8 = FeatureEntry(
        id=8, name='F8 Enabled', summary='sum', category=1,
        feature_type=FEATURE_TYPE_INCUBATE_ID,
        finch_name='Feature8Enabled')
    self.feature_8.put()
    self.stage_8 = Stage(
        id=108, feature_id=8, stage_type=160,
        intent_thread_url='https://example.com/intent8',
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_8.put()
    Gate(id=1008, feature_id=8, stage_id=108, gate_type=GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 9: Incomplete (Disabled in content_features.cc).
    self.feature_9 = FeatureEntry(
        id=9, name='F9 Disabled', summary='sum', category=1,
        feature_type=FEATURE_TYPE_INCUBATE_ID,
        finch_name='Feature9Disabled')
    self.feature_9.put()
    self.stage_9 = Stage(
        id=109, feature_id=9, stage_type=160,
        intent_thread_url='https://example.com/intent9',
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_9.put()
    Gate(id=1009, feature_id=9, stage_id=109, gate_type=GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 10: Incomplete (Not found in Chromium files).
    self.feature_10 = FeatureEntry(
        id=10, name='F10 Not Found', summary='sum', category=1,
        feature_type=FEATURE_TYPE_INCUBATE_ID,
        finch_name='non-existent-feature')
    self.feature_10.put()
    self.stage_10 = Stage(
        id=110, feature_id=10, stage_type=160,
        intent_thread_url='https://example.com/intent10',
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_10.put()
    Gate(id=1010, feature_id=10, stage_id=110, gate_type=GATE_API_SHIP,
         state=Vote.APPROVED).put()

    # Feature 11: Complete (skipped checks due to Blink Component).
    self.feature_11 = FeatureEntry(
        id=11, name='F11 WebGPU', summary='sum', category=1,
        feature_type=FEATURE_TYPE_INCUBATE_ID,
        finch_name='WebGPUFeature',
        blink_components=['Blink>WebGPU'])
    self.feature_11.put()
    self.stage_11 = Stage(
        id=111, feature_id=11, stage_type=160,
        intent_thread_url='https://example.com/intent11',
        milestones=MilestoneSet(desktop_first=self.milestone))
    self.stage_11.put()
    Gate(id=1011, feature_id=11, stage_id=111, gate_type=GATE_API_SHIP,
         state=Vote.APPROVED).put()

  def tearDown(self):
    for kind in [FeatureEntry, Gate, Stage, Vote]:
      for entity in kind.query():
        entity.key.delete()

  def test_validate_feature_in_chromium(self):
    """Tests parsing logic for JSON and C++ mock data."""
    # Case 1: Found in JSON and stable -> No missing criteria.
    result = feature_helpers.validate_feature_in_chromium(
        'featureOneFinch', MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertEqual(result, [])

    # Case 2: Found in JSON but not stable.
    result = feature_helpers.validate_feature_in_chromium(
        'feature7-unstable', MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertEqual(result,
        [feature_helpers.Criteria.RUNTIME_FEATURE_NOT_STABLE])

    # Case 3: Found in .cc file and enabled.
    result = feature_helpers.validate_feature_in_chromium(
        'Feature8Enabled', MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertEqual(result, [])

    # Case 4: Found in .cc file but disabled.
    result = feature_helpers.validate_feature_in_chromium(
        'Feature9Disabled', MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertEqual(result,
        [feature_helpers.Criteria.CONTENT_FEATURE_NOT_ENABLED])

    # Case 5: Not found in either file.
    result = feature_helpers.validate_feature_in_chromium(
        'not-a-real-feature', MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertEqual(result,
        [feature_helpers.Criteria.CHROMIUM_FEATURE_NOT_FOUND])

    # Case 6: Found in JSON, status is dict, one platform is "stable".
    result = feature_helpers.validate_feature_in_chromium(
        'FeatureDictStable', MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertEqual(result, [])

    # Case 7: Found in JSON, status is dict, no platforms are "stable".
    result = feature_helpers.validate_feature_in_chromium(
        'FeatureDictUnstable', MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertEqual(result,
        [feature_helpers.Criteria.RUNTIME_FEATURE_NOT_STABLE])

  def test_build_feature_info(self):
    """Verifies that the feature info dict is constructed correctly."""

    with mock.patch('settings.SITE_URL', 'http://localhost'):
      info = feature_helpers.build_feature_info(self.feature_1, self.stage_1)

    self.assertEqual(info['name'], 'Feature 1 (Complete)')
    self.assertEqual(info['chromestatus_url'], 'http://localhost/feature/1')
    self.assertEqual(info['tracking_bug_url'], 'https://example.com/bug1')
    self.assertEqual(info['intent_to_ship'], 'https://example.com/intent1')
    self.assertEqual(info['owner_emails'], ['owner@example.com'])

  def test_validate_shipping_criteria(self):
    """Tests specific validation logic for Gates and Intents."""
    # Case 1: Success (Complete Feature 1)
    result = feature_helpers.validate_shipping_criteria(
        self.feature_1, self.stage_1,
        MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertEqual(result, [])

    # Case 2: Missing Intent
    result = feature_helpers.validate_shipping_criteria(
        self.feature_3, self.stage_3,
        MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    # Feature 3 also has 'feature3-finch' which is not in the mock files.
    self.assertIn(feature_helpers.Criteria.INTENT_TO_SHIP_MISSING, result)

    # Case 3: Missing LGTM
    result = feature_helpers.validate_shipping_criteria(
        self.feature_2, self.stage_2,
        MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertIn(feature_helpers.Criteria.API_OWNER_LGTMS_MISSING, result)

    # Case 4: Skipped checks (Feature 11)
    result = feature_helpers.validate_shipping_criteria(
        self.feature_11, self.stage_11,
        MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)
    self.assertEqual(result, [])

  def test_aggregate_shipping_features(self):
    """Tests the full aggregation logic."""
    stages = [
        self.stage_1, self.stage_2, self.stage_3, self.stage_4,
        self.stage_5, self.stage_7, self.stage_8, self.stage_9, self.stage_10,
        self.stage_11
    ]

    complete, incomplete = feature_helpers.aggregate_shipping_features(
        stages, MOCK_ENABLED_FEATURES_JSON, MOCK_CONTENT_FEATURES_CC)

    # Verify Complete Features
    self.assertEqual(len(complete), 4)
    # IDs 1, 5, 8, 11 are complete.
    complete_names = sorted([f['name'] for f in complete])
    self.assertEqual(complete_names,
        ['F11 WebGPU', 'F8 Enabled', 'Feature 1 (Complete)', 'Feature 5 (PSA)'])

    # Verify Incomplete Features
    self.assertEqual(len(incomplete), 6)
    # Map name -> missing criteria list
    incomplete_map = {item[0]['name']: item[1] for item in incomplete}

    # Feature 2: Missing LGTM + Not in Chromium
    self.assertIn('Feature 2 (No LGTM)', incomplete_map)
    self.assertIn('lgtms', incomplete_map['Feature 2 (No LGTM)'])

    # Feature 7: Unstable in JSON
    self.assertIn('F7 Unstable', incomplete_map)
    self.assertEqual(incomplete_map['F7 Unstable'], ['runtime_feature_not_stable'])

    # Feature 9: Disabled in CC
    self.assertIn('F9 Disabled', incomplete_map)
    self.assertEqual(incomplete_map['F9 Disabled'], ['content_feature_not_enabled'])
