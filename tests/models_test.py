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

import unittest
import testing_config  # Must be imported before the module under test.

import models


class ModelsFunctionsTest(unittest.TestCase):

  def test_del_none(self):
    d = {}
    self.assertEqual(
        {},
        models.del_none(d))

    d = {1: 'one', 2: None, 3: {33: None}, 4:{44: 44, 45: None}}
    self.assertEqual(
        {1: 'one', 3: {}, 4: {44: 44}},
        models.del_none(d))

  def test_list_to_chunks(self):
    self.assertEqual(
        [],
        list(models.list_to_chunks([], 2)))

    self.assertEqual(
        [[1, 2], [3, 4]],
        list(models.list_to_chunks([1, 2, 3, 4], 2)))

    self.assertEqual(
        [[1, 2], [3, 4], [5], 999],
        list(models.list_to_chunks([1, 2, 3, 4, 5], 2)))
