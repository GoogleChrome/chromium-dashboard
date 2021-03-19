from __future__ import division
from __future__ import print_function

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

import datetime
import mock
import testing_config  # Must be imported before the module under test.
import unittest

from google.appengine.ext import db

from framework import ramcache


KEY_1 = 'cache_key|1'
KEY_2 = 'cache_key|2'
KEY_3 = 'cache_key|3'
KEY_4 = 'cache_key|4'
KEY_5 = 'cache_key|5'
KEY_6 = 'cache_key|6'
KEY_7 = 'cache_key|7'


class RAMCacheFunctionTests(unittest.TestCase):

  def testSetAndGet(self):
    """We can cache a value and retrieve it from the cache."""
    self.assertEquals(None, ramcache.get(KEY_1))

    ramcache.set(KEY_1, 101)
    self.assertEquals(101, ramcache.get(KEY_1))

  def testSetAndGetMulti(self):
    """We can cache values and retrieve them from the cache."""
    self.assertEquals({}, ramcache.get_multi([]))

    self.assertEquals({}, ramcache.get_multi([KEY_2, KEY_3]))

    ramcache.set_multi({KEY_2: 202, KEY_3: 303})
    self.assertEquals(
        {KEY_2: 202, KEY_3: 303},
        ramcache.get_multi([KEY_2, KEY_3]))

    ramcache.set_multi({KEY_2: 202, KEY_3: 303})
    self.assertEquals(
        {KEY_2: 202, KEY_3: 303},
        ramcache.get_multi([KEY_2, KEY_3, KEY_4]))

  @mock.patch('time.time')
  def testExpiration(self, mock_time):
    """If a value is set with an expiration time, it is dropped later."""
    NOW = 1607128969
    mock_time.return_value = NOW
    ramcache.set(KEY_1, 101, time=60)
    self.assertEquals(101, ramcache.get(KEY_1))

    mock_time.return_value = NOW + 59
    self.assertEquals(101, ramcache.get(KEY_1))

    mock_time.return_value = NOW + 61
    self.assertEquals(None, ramcache.get(KEY_1))

    mock_time.return_value = NOW
    ramcache.set_multi({KEY_1 + 'multi': 101}, time=60)
    self.assertEquals(101, ramcache.get(KEY_1 + 'multi'))

    mock_time.return_value = NOW + 59
    self.assertEquals(101, ramcache.get(KEY_1 + 'multi'))

    mock_time.return_value = NOW + 61
    self.assertEquals(None, ramcache.get(KEY_1 + 'multi'))

  @mock.patch('framework.ramcache.SharedInvalidate.invalidate')
  def testDelete_NotFound(self, mock_invalidate):
    """Deleting an item that is not in the cache is a no-op."""
    ramcache.delete(KEY_5)

    mock_invalidate.assert_not_called()

  @mock.patch('framework.ramcache.SharedInvalidate.invalidate')
  def testDelete_Found(self, mock_invalidate):
    """We can delete an item from the cache, causing an invalidation."""
    ramcache.set(KEY_6, 606)
    self.assertEquals(606, ramcache.get(KEY_6))
    ramcache.delete(KEY_6)
    self.assertEquals(None, ramcache.get(KEY_6))

    mock_invalidate.assert_called_once()

  @mock.patch('framework.ramcache.SharedInvalidate.invalidate')
  def testFlushAll(self, mock_invalidate):
    """flush_all simply causes an invalidation."""
    ramcache.flush_all()
    mock_invalidate.assert_called_once()


class SharedInvalidateTests(unittest.TestCase):

  def assertTimestampWasUpdated(self, start_time):
    singleton = ramcache.SharedInvalidate.get(
        ramcache.SharedInvalidate.SINGLETON_KEY,
        read_policy=db.STRONG_CONSISTENCY)
    self.assertTrue(singleton.updated > start_time)

  def testInvalidate(self):
    """Calling invalidate sets a new updated time."""
    start_time = datetime.datetime.now()
    ramcache.SharedInvalidate.invalidate()
    self.assertTimestampWasUpdated(start_time)

  def testCheckForDistributedInvalidation_Unneeded_NoEntity(self):
    """When the system first launches, no need to clear cache."""
    db.delete(ramcache.SharedInvalidate.SINGLETON_KEY)
    ramcache.SharedInvalidate.last_processed_timestamp = None
    ramcache.global_cache = {KEY_7: 777}
    ramcache.SharedInvalidate.check_for_distributed_invalidation()
    self.assertEquals({KEY_7: 777}, ramcache.global_cache)
    self.assertIsNone(ramcache.SharedInvalidate.last_processed_timestamp)

  def testCheckForDistributedInvalidation_Unneeded_Fresh(self):
    """When no other instance has invalidated, this cache is fresh."""
    ramcache.SharedInvalidate.invalidate()
    ramcache.SharedInvalidate.check_for_distributed_invalidation()
    # From this point on there are no invalidations, so our cache is fresh.

    ramcache.global_cache = {KEY_7: 777}
    ramcache.SharedInvalidate.check_for_distributed_invalidation()
    # Since cache is fresh, it is not cleared.
    self.assertEquals({KEY_7: 777}, ramcache.global_cache)

  def testCheckForDistributedInvalidation_Needed_None(self):
    """When needed, we clear our local RAM cache."""
    start_time = datetime.datetime.now()
    ramcache.SharedInvalidate.last_processed_timestamp = None
    ramcache.global_cache = {KEY_7: 777}
    ramcache.flush_all()
    ramcache.SharedInvalidate.check_for_distributed_invalidation()
    self.assertEquals({}, ramcache.global_cache)
    self.assertTimestampWasUpdated(start_time)

  def testCheckForDistributedInvalidation_Needed_Stale(self):
    """When needed, we clear our local RAM cache."""
    start_time = datetime.datetime.now()
    ramcache.SharedInvalidate.last_processed_timestamp = start_time
    ramcache.global_cache = {KEY_7: 777}
    ramcache.flush_all()
    ramcache.SharedInvalidate.check_for_distributed_invalidation()
    self.assertEquals({}, ramcache.global_cache)
    self.assertTimestampWasUpdated(start_time)
