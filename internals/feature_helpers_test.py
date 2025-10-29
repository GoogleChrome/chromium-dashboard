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


class FeatureHelpersTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_2 = FeatureEntry(
        name='feature b', summary='sum',
        owner_emails=['feature_owner@example.com'], category=1,
        updated=datetime(2020, 4, 1), feature_type=1, impl_status_chrome=1)
    self.feature_2.put()

    self.feature_1 = FeatureEntry(
        name='feature a', summary='sum', impl_status_chrome=3,
        owner_emails=['feature_owner@example.com'], category=1,
        updated=datetime(2020, 3, 1), feature_type=0)
    self.feature_1.put()

    self.feature_3 = FeatureEntry(
        name='feature c', summary='sum', category=1, impl_status_chrome=2,
        owner_emails=['feature_owner@example.com'],
        updated=datetime(2020, 1, 1), feature_type=2)
    self.feature_3.put()

    self.feature_4 = FeatureEntry(
        name='feature d', summary='sum', category=1, impl_status_chrome=2,
        owner_emails=['feature_owner@example.com'],
        updated=datetime(2020, 2, 1), feature_type=3)
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

  def tearDown(self):
    for kind in [FeatureEntry, Stage, Gate]:
      for entity in kind.query():
        entity.key.delete()

    rediscache.flushall()

  def test_get_all__normal(self):
    """We can retrieve a list of all features with no filter."""
    actual = feature_helpers.get_all(update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature b', 'feature a', 'feature d', 'feature c'],
        names)

    self.feature_1.summary = 'revised summary'
    self.feature_1.put()  # Changes updated field.
    actual = feature_helpers.get_all(update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature b', 'feature a', 'feature d', 'feature c'],
        names)

  def test_get_all__category(self):
    """We can retrieve a list of all features of a given category."""
    actual = feature_helpers.get_all(
        filterby=('category', CSS), update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        [],
        names)

    self.feature_1.category = CSS
    self.feature_1.put()  # Changes updated field.
    actual = feature_helpers.get_all(
        filterby=('category', CSS), update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature a'],
        names)

  def test_get_all__owner(self):
    """We can retrieve a list of all features with a given owner."""
    actual = feature_helpers.get_all(
        filterby=('owner_emails', 'owner@example.com'), update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        [],
        names)

    self.feature_1.owner_emails = ['owner@example.com']
    self.feature_1.put()  # Changes updated field.
    actual = feature_helpers.get_all(
        filterby=('owner_emails', 'owner@example.com'), update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature a'],
        names)

  def test_get_all__owner_unlisted(self):
    """Unlisted features should still be visible to their owners."""
    self.feature_2.unlisted = True
    self.feature_2.owner_emails = ['feature_owner@example.com']
    self.feature_2.put()
    testing_config.sign_in('feature_owner@example.com', 1234567890)
    actual = feature_helpers.get_all(update_cache=True)
    names = [f['name'] for f in actual]
    testing_config.sign_out()
    self.assertEqual(
      ['feature b', 'feature a', 'feature d', 'feature c'], names)

  def test_get_all__editor_unlisted(self):
    """Unlisted features should still be visible to feature editors."""
    self.feature_2.unlisted = True
    self.feature_2.editor_emails = ['feature_editor@example.com']
    self.feature_2.put()
    testing_config.sign_in("feature_editor@example.com", 1234567890)
    actual = feature_helpers.get_all(update_cache=True)
    names = [f['name'] for f in actual]
    testing_config.sign_out()
    self.assertEqual(
      ['feature b', 'feature a', 'feature d', 'feature c'], names)

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

  def test_get_in_milestone__wp_need_enterprise_approval(self):
    """We include WP features only if enterprise shipping gate is approved."""
    self._create_wp_stages_and_gates()
    cache_key = '%s|%s|%s' % (
        FeatureEntry.DEFAULT_CACHE_KEY, 'release_notes_milestone', 1)
    self.feature_1.enterprise_impact = ENTERPRISE_IMPACT_LOW
    self.feature_1.put()
    self.feature_2.enterprise_impact = ENTERPRISE_IMPACT_MEDIUM
    self.feature_2.put()
    self.feature_3.enterprise_impact = ENTERPRISE_IMPACT_HIGH
    self.feature_3.put()
    self.feature_4.enterprise_impact = ENTERPRISE_IMPACT_LOW
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
    self.assertEqual(0, len(features))
    rediscache.delete(cache_key)

  def test_get_in_milestone__non_enterprise_features(self):
    """We can retrieve a list of features."""
    self._create_wp_stages_and_gates()
    cache_key = '%s|%s|%s' % (
        FeatureEntry.DEFAULT_CACHE_KEY, 'release_notes_milestone', 1)

    # There is no breaking change
    features = feature_helpers.get_features_in_release_notes(milestone=1)
    self.assertEqual(0, len(features))
    cached_result = rediscache.get(cache_key)
    rediscache.delete(cache_key)
    self.assertEqual(cached_result, features)

    # Features 1, 2, 3 and 4 are breaking changes
    self.feature_1.enterprise_impact = ENTERPRISE_IMPACT_LOW
    self.feature_1.put()
    self.feature_2.enterprise_impact = ENTERPRISE_IMPACT_MEDIUM
    self.feature_2.put()
    self.feature_3.enterprise_impact = ENTERPRISE_IMPACT_HIGH
    self.feature_3.put()
    self.feature_4.enterprise_impact = ENTERPRISE_IMPACT_LOW
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
        FeatureEntry.DEFAULT_CACHE_KEY, 'release_notes_milestone', 3)
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
        FeatureEntry.DEFAULT_CACHE_KEY, 'release_notes_milestone', 1)
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
