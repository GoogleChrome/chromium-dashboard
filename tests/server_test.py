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

import unittest
import testing_config  # Must be imported before the module under test.

import server


class ServerFunctionsTest(unittest.TestCase):

  def test_normalized_name(self):
    self.assertEqual('', server.normalized_name(''))
    self.assertEqual('abc', server.normalized_name('abc'))
    self.assertEqual('abc', server.normalized_name('Abc'))
    self.assertEqual('abc', server.normalized_name('ABC'))
    self.assertEqual('abc', server.normalized_name('A BC'))
    self.assertEqual('abc', server.normalized_name('A B/C'))
    self.assertEqual('abc', server.normalized_name(' /A B/C /'))
