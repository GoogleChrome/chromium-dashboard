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

import datetime
from unittest import mock
from framework import users

from internals import core_enums


class EnumsFunctionsTest(testing_config.CustomTestCase):

  def test_convert_enum_int_to_string__not_an_enum(self):
    """If the property is not an enum, just use the property value."""
    actual = core_enums.convert_enum_int_to_string(
        'name', 'not an int')
    self.assertEqual('not an int', actual)

    actual = core_enums.convert_enum_int_to_string(
        'unknown property', 'something')
    self.assertEqual('something', actual)

  def test_convert_enum_int_to_string__not_an_int(self):
    """We don't crash or convert when given non-numeric values."""
    actual = core_enums.convert_enum_int_to_string(
        'impl_status_chrome', {'something': 'non-numeric'})
    self.assertEqual(
        {'something': 'non-numeric'},
        actual)

  def test_convert_enum_int_to_string__enum_found(self):
    """We use the human-reable string if it is defined."""
    actual = core_enums.convert_enum_int_to_string(
        'impl_status_chrome', core_enums.NO_ACTIVE_DEV)
    self.assertEqual(
        core_enums.IMPLEMENTATION_STATUS[core_enums.NO_ACTIVE_DEV],
        actual)

  def test_convert_enum_int_to_string__enum_not_found(self):
    """If we somehow don't have an emum string, use the ordinal."""
    actual = core_enums.convert_enum_int_to_string(
        'impl_status_chrome', 99)
    self.assertEqual(99, actual)

  def test_convert_enum_string_to_int__already_numeric(self):
    """If the value passed in is already an int, go with it."""
    actual = core_enums.convert_enum_string_to_int(
        'impl_status_chrome', str(core_enums.NO_ACTIVE_DEV))
    self.assertEqual(core_enums.NO_ACTIVE_DEV, actual)

  def test_convert_enum_string_to_int__enum_found(self):
    """We use the enum representation if it is defined."""
    actual = core_enums.convert_enum_string_to_int(
        'impl_status_chrome', 'No active development')
    self.assertEqual(core_enums.NO_ACTIVE_DEV, actual)

    actual = core_enums.convert_enum_string_to_int(
        'category', 'Miscellaneous')
    self.assertEqual(core_enums.MISC, actual)

  def test_convert_enum_string_to_int__not_found(self):
    """If enum representation is not defined, return -1."""
    actual = core_enums.convert_enum_string_to_int(
        'impl_status_chrome', 'abc')
    self.assertEqual(-1, actual)
