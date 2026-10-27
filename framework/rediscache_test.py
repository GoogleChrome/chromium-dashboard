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

"""Unit tests for the rediscache module.

Tests basic caching operations (set, get, multi-get, delete) using
the fake Redis client.
"""

from unittest import mock

import redis

import testing_config  # Must be imported before the module under test.
from framework import rediscache

PREFIX = 'cache_key|'
KEY_1 = 'cache_key|1'
KEY_2 = 'cache_key|2'
KEY_3 = 'cache_key|3'
KEY_4 = 'cache_key|4'
KEY_5 = 'cache_key|5'
KEY_6 = 'cache_key|6'
KEY_7 = 'cache_key|7'


class RedisCacheFunctionTests(testing_config.CustomTestCase):
    """Tests for rediscache functions."""

    def test_set_and_get(self):
        """We can cache a value and retrieve it from the cache."""
        self.assertEqual(None, rediscache.get(KEY_1))

        rediscache.set(KEY_1, '101')
        self.assertEqual('101', rediscache.get(KEY_1))

        rediscache.set(KEY_4, 123)
        self.assertEqual(123, rediscache.get(KEY_4))

        rediscache.set(KEY_4, '123', 3600)
        self.assertEqual('123', rediscache.get(KEY_4))

    def test_set_and_get_multi(self):
        """We can cache values and retrieve them from the cache."""
        self.assertEqual({}, rediscache.get_multi([]))

        self.assertEqual(
            {KEY_2: None, KEY_3: None}, rediscache.get_multi([KEY_2, KEY_3])
        )

        rediscache.set_multi({KEY_2: '202', KEY_3: '303'})
        self.assertEqual(
            {KEY_2: '202', KEY_3: '303'}, rediscache.get_multi([KEY_2, KEY_3])
        )

        # Ignore non-str types.
        rediscache.set_multi({KEY_2: '202', KEY_3: '303', KEY_5: 111})
        self.assertEqual(
            {KEY_2: '202', KEY_3: '303', KEY_5: 111},
            rediscache.get_multi([KEY_2, KEY_3, KEY_5]),
        )

        rediscache.set_multi({KEY_5: '222'}, 3600)
        self.assertEqual({KEY_5: '222'}, rediscache.get_multi([KEY_5]))

    def test_delete(self):
        """Test delete."""
        rediscache.set(KEY_6, '606')
        self.assertEqual('606', rediscache.get(KEY_6))
        rediscache.delete(KEY_6)
        self.assertEqual(None, rediscache.get(KEY_6))

    def test_delete_keys_with_prefix(self):
        """Test delete keys with prefix."""
        for x in range(17):
            key = PREFIX + str(x)
            rediscache.set(key, str(x))
        rediscache.set('random_key', '303')
        rediscache.set('random_key1', '404')
        self.assertEqual('1', rediscache.get(KEY_1))

        rediscache.delete_keys_with_prefix('cache_key')

        self.assertEqual(None, rediscache.get(KEY_1))
        self.assertEqual(None, rediscache.get(KEY_2))
        self.assertEqual('303', rediscache.get('random_key'))
        self.assertEqual('404', rediscache.get('random_key1'))

    def test_delete_multi(self):
        """We can delete several keys at once, leaving other keys alone."""
        rediscache.set(KEY_1, '101')
        rediscache.set(KEY_2, '202')
        rediscache.set(KEY_3, '303')

        rediscache.delete_multi([KEY_1, KEY_2, KEY_7])  # KEY_7 never existed.

        self.assertEqual(None, rediscache.get(KEY_1))
        self.assertEqual(None, rediscache.get(KEY_2))
        self.assertEqual('303', rediscache.get(KEY_3))

    def test_delete_multi__empty(self):
        """Deleting an empty list of keys is a no-op."""
        rediscache.set(KEY_1, '101')
        rediscache.delete_multi([])
        self.assertEqual('101', rediscache.get(KEY_1))

    def test_set_multi__sets_ttl(self):
        """set_multi applies the expiration time to every key."""
        rediscache.set_multi({KEY_1: '101', KEY_2: '202'}, 3600)
        for key in (KEY_1, KEY_2):
            ttl = rediscache.redis_client.ttl(rediscache.add_gae_prefix(key))
            self.assertTrue(0 < ttl <= 3600)

    def test_set_multi__no_ttl(self):
        """set_multi with time=0 stores keys without an expiration time."""
        rediscache.set_multi({KEY_1: '101'}, 0)
        self.assertEqual('101', rediscache.get(KEY_1))
        ttl = rediscache.redis_client.ttl(rediscache.add_gae_prefix(KEY_1))
        self.assertEqual(-1, ttl)

    def test_delete_keys_with_prefix__many_keys(self):
        """All matching keys are deleted, even across many SCAN pages."""
        num_matching = 2500  # More than SCAN_COUNT and DELETE_BATCH_SIZE.
        rediscache.set_multi({f'{PREFIX}{i}': i for i in range(num_matching)})
        rediscache.set_multi({f'other_key|{i}': i for i in range(100)})
        # Keys written by another App Engine version must not be touched.
        rediscache.redis_client.set('otherversion-cache_key|1', b'x')

        num_deleted = rediscache.delete_keys_with_prefix('cache_key')

        self.assertEqual(num_matching, num_deleted)
        self.assertEqual(None, rediscache.get(KEY_1))
        self.assertEqual(None, rediscache.get(f'{PREFIX}{num_matching - 1}'))
        self.assertEqual(99, rediscache.get('other_key|99'))
        self.assertEqual(
            b'x', rediscache.redis_client.get('otherversion-cache_key|1')
        )
        self.assertEqual(101, rediscache.redis_client.dbsize())

    def test_delete_keys_with_prefix__round_trip_budget(self):
        """Prefix deletion takes a small, bounded number of round trips.

        Each Redis round trip from App Engine to Memorystore costs ~1ms, so
        the number of commands sent matters far more than server time.
        """
        num_matching = 2500
        num_other = 5000
        rediscache.set_multi({f'{PREFIX}{i}': i for i in range(num_matching)})
        rediscache.set_multi({f'other_key|{i}': i for i in range(num_other)})
        client = rediscache.redis_client

        with mock.patch.object(
            client, 'execute_command', wraps=client.execute_command
        ) as spy:
            rediscache.delete_keys_with_prefix('cache_key')

        # About (total keys / SCAN_COUNT) SCAN calls plus
        # (matching keys / DELETE_BATCH_SIZE) UNLINK calls. Before this
        # was optimized it took over 3,000 round trips.
        self.assertLessEqual(spy.call_count, 15)
        self.assertEqual(num_other, client.dbsize())

    def test_set_multi__round_trip_budget(self):
        """set_multi sends all keys in a single round trip."""
        client = rediscache.redis_client
        with (
            mock.patch.object(
                client, 'execute_command', wraps=client.execute_command
            ) as spy,
            mock.patch.object(
                redis.client.Pipeline,
                'execute',
                autospec=True,
                side_effect=redis.client.Pipeline.execute,
            ) as pipeline_spy,
        ):
            rediscache.set_multi({f'{PREFIX}{i}': i for i in range(100)})

        self.assertEqual(0, spy.call_count)
        self.assertEqual(1, pipeline_spy.call_count)
        self.assertEqual(99, rediscache.get(f'{PREFIX}99'))
