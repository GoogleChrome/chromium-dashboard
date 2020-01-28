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

import common


class CommonFunctionTests(unittest.TestCase):

  def test_strip_trailing_slash(self):
    self.called_with = []
    def handler(handlerInstance, *args):
      self.called_with = args

    wrapped_handler = common.strip_trailing_slash(handler)

    wrapped_handler('aHandler', '/request/path')
    self.assertEqual(('/request/path',), self.called_with)

    with self.assertRaises(Exception):
      wrapped_handler('aHandler', '/request/path/')
