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

"""Tests for the review_models module, verifying activity retrieval and owners file freshness logic."""

import datetime

from google.cloud import ndb  # type: ignore

import testing_config  # Must be imported before the module under test.
from framework import rediscache
from internals.core_models import FeatureEntry
from internals.review_models import Activity, Gate, OwnersFile, Vote


class ActivityTest(testing_config.CustomTestCase):
    """Tests for Activity."""

    def setUp(self):
        """Set up the test environment."""
        self.feature_1 = FeatureEntry(
            name='feature a',
            summary='sum',
            owner_emails=['feature_owner@example.com'],
            category=1,
            impl_status_chrome=3,
        )
        self.feature_1.put()
        self.feature_1_id = self.feature_1.key.integer_id()
        self.act_1_1 = Activity(
            log_type=Activity.USER_COMMENT,
            feature_id=self.feature_1_id,
            gate_id=1,
            author='one@example.com',
            content='some text',
        )
        self.act_1_1.put()
        self.act_1_2 = Activity(
            log_type=Activity.USER_COMMENT,
            feature_id=self.feature_1_id,
            gate_id=2,
            author='one@example.com',
            content='some other text',
        )
        self.act_1_2.put()
        self.act_1_3 = Activity(
            log_type=Activity.USER_COMMENT,
            feature_id=self.feature_1_id,
            author='one@example.com',
            content='random',
        )
        self.act_1_3.put()

        self.feature_2 = FeatureEntry(
            name='feature b',
            summary='sum',
            owner_emails=['feature_owner@example.com'],
            category=1,
            impl_status_chrome=3,
        )
        self.feature_2.put()
        self.feature_2_id = self.feature_2.key.integer_id()

    def test_get_activities__none(self):
        """We get [] if feature has no review comments."""
        actual = Activity.get_activities(self.feature_2_id, comments_only=True)
        self.assertEqual([], actual)

    def test_get_activities__some(self):
        """We get review comments if the feature has some."""
        actual = Activity.get_activities(self.feature_1_id)
        self.assertEqual(3, len(actual))
        self.assertEqual(
            ['some text', 'some other text', 'random'],
            [c.content for c in actual],
        )

    def test_get_activities__specific_fields(self):
        """We get review comments for specific gates if requested."""
        actual_1 = Activity.get_activities(
            self.feature_1_id, 1, comments_only=True
        )
        self.assertEqual(1, len(actual_1))
        self.assertEqual(['some text'], [c.content for c in actual_1])

        actual_2 = Activity.get_activities(
            self.feature_1_id, 2, comments_only=True
        )
        self.assertEqual(1, len(actual_2))
        self.assertEqual(['some other text'], [c.content for c in actual_2])

        actual_3 = Activity.get_activities(
            self.feature_1_id, 3, comments_only=True
        )
        self.assertEqual([], actual_3)

    def test_log_types(self):
        """Verifies Activity log type constants."""
        self.assertEqual(1, Activity.USER_CHANGE)
        self.assertEqual(2, Activity.MILESTONE_RESET)
        self.assertEqual(3, Activity.USER_COMMENT)
        self.assertEqual(4, Activity.SYSTEM_CHANGE)
        self.assertEqual(5, Activity.BYPASS_APPLIED)
        self.assertEqual(6, Activity.BYPASS_REVERTED)


class GateTest(testing_config.CustomTestCase):
    """Tests for Gate."""

    # TODO(jrobbins): Add tests for get_feature_gates.
    pass


class GateAndVoteCacheInvalidationTest(testing_config.CustomTestCase):
    """Tests that Gate and Vote writes invalidate cached search results."""

    def setUp(self):
        """Populate feature and search cache entries."""
        self.feature_id = 12345
        self.entry_key = FeatureEntry.feature_cache_key(
            FeatureEntry.DEFAULT_CACHE_KEY, self.feature_id
        )
        self.name_key = FeatureEntry.feature_cache_key(
            FeatureEntry.FEATURE_NAME_CACHE_KEY, self.feature_id
        )
        self.search_key = f'{FeatureEntry.SEARCH_CACHE_KEY}|test_query'
        for key in (self.entry_key, self.name_key, self.search_key):
            rediscache.set(key, 'cached')

    def tearDown(self):
        """Clean up entities and cache."""
        for gate in Gate.query():
            gate.key.delete()
        for vote in Vote.query():
            vote.key.delete()
        rediscache.flushall()

    def make_gate(self):
        """Return an unsaved Gate."""
        return Gate(
            feature_id=self.feature_id,
            stage_id=1,
            gate_type=1,
            state=Gate.PREPARING,
        )

    def make_vote(self):
        """Return an unsaved Vote."""
        return Vote(
            feature_id=self.feature_id,
            gate_id=2,
            gate_type=1,
            state=Vote.APPROVED,
            set_on=datetime.datetime.now(),
            set_by='reviewer@example.com',
        )

    def assert_only_search_invalidated(self):
        """Search results are invalidated; per-feature caches are kept."""
        self.assertIsNone(rediscache.get(self.search_key))
        # Cached feature data does not include gates or votes.
        self.assertEqual('cached', rediscache.get(self.entry_key))
        self.assertEqual('cached', rediscache.get(self.name_key))

    def test_gate_put(self):
        """Saving a gate invalidates search results only."""
        self.make_gate().put()
        self.assert_only_search_invalidated()

    def test_gate_put_multi(self):
        """ndb.put_multi() of gates invalidates search results only."""
        ndb.put_multi([self.make_gate(), self.make_gate()])
        self.assert_only_search_invalidated()

    def test_gate_delete(self):
        """Deleting a gate invalidates search results only."""
        key = self.make_gate().put()
        rediscache.set(self.search_key, 'cached')
        key.delete()
        self.assert_only_search_invalidated()

    def test_vote_put(self):
        """Saving a vote invalidates search results only."""
        self.make_vote().put()
        self.assert_only_search_invalidated()

    def test_vote_delete(self):
        """Deleting a vote invalidates search results only."""
        key = self.make_vote().put()
        rediscache.set(self.search_key, 'cached')
        key.delete()
        self.assert_only_search_invalidated()


class OwnersFileTest(testing_config.CustomTestCase):
    """Tests for OwnersFile."""

    def setUp(self):
        """Set up the test environment."""
        now = datetime.datetime.now()
        self.owner_file_1 = OwnersFile(
            url='abc', raw_content='foo', created_on=now
        )
        self.owner_file_1.add_owner_file()

        expired = now - datetime.timedelta(hours=3)
        self.owner_file_2 = OwnersFile(
            url='def', raw_content='bar', created_on=expired
        )
        self.owner_file_2.add_owner_file()

    def test_get_raw_owner_file(self):
        """Test get raw owner file."""
        owners_file = OwnersFile.get_raw_owner_file('abc')
        self.assertEqual('foo', owners_file.raw_content)
        self.assertTrue(owners_file.is_fresh())

        expired_owners_file = OwnersFile.get_raw_owner_file('def')
        self.assertFalse(expired_owners_file.is_fresh())
