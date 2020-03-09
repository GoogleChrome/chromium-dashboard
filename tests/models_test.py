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

  def test_convert_enum_int_to_string__not_an_enum(self):
    """If the property is not an enum, just use the property value."""
    actual = models.convert_enum_int_to_string(
        'name', 'not an int')
    self.assertEqual('not an int', actual)

    actual = models.convert_enum_int_to_string(
        'unknown property', 'something')
    self.assertEqual('something', actual)

  def test_convert_enum_int_to_string__not_an_int(self):
    """We don't crash or convert when given non-numeric values."""
    actual = models.convert_enum_int_to_string(
        'impl_status_chrome', {'something': 'non-numeric'})
    self.assertEqual(
        {'something': 'non-numeric'},
        actual)

  def test_convert_enum_int_to_string__enum_found(self):
    """We use the human-reable string if it is defined."""
    actual = models.convert_enum_int_to_string(
        'impl_status_chrome', models.NO_ACTIVE_DEV)
    self.assertEqual(
        models.IMPLEMENTATION_STATUS[models.NO_ACTIVE_DEV],
        actual)

  def test_convert_enum_int_to_string__enum_not_found(self):
    """If we somehow don't have an emum string, use the ordinal."""
    actual = models.convert_enum_int_to_string(
        'impl_status_chrome', 99)
    self.assertEqual(99, actual)


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
        [[1, 2], [3, 4], [5]],
        list(models.list_to_chunks([1, 2, 3, 4, 5], 2)))
