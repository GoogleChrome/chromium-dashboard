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
  def tearDown(self):
    rediscache.flushall()

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

    self.assertEqual({KEY_2: None, KEY_3: None},
                     rediscache.get_multi([KEY_2, KEY_3]))

    rediscache.set_multi({KEY_2: '202', KEY_3: '303'})
    self.assertEqual(
        {KEY_2: '202', KEY_3: '303'},
        rediscache.get_multi([KEY_2, KEY_3]))

    # Ignore non-str types.
    rediscache.set_multi({KEY_2: '202', KEY_3: '303', KEY_5: 111})
    self.assertEqual(
        {KEY_2: '202', KEY_3: '303', KEY_5: 111},
        rediscache.get_multi([KEY_2, KEY_3, KEY_5]))

    rediscache.set_multi({KEY_5: '222'}, 3600)
    self.assertEqual({KEY_5: '222'}, rediscache.get_multi([KEY_5]))

  def test_delete(self):
    rediscache.set(KEY_6, '606')
    self.assertEqual('606', rediscache.get(KEY_6))
    rediscache.delete(KEY_6)
    self.assertEqual(None, rediscache.get(KEY_6))

  def test_delete_keys_with_prefix(self):
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
