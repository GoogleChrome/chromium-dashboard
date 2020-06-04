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

import mock

import processes


class HelperFunctionsTest(unittest.TestCase):

  def test_process_to_dict(self):
    process = processes.Process(
        'Baking',
        'This is how you make bread',
        'Make it before you are hungry',
        [processes.ProcessStage(
            'Make dough',
            'Mix it and kneed',
            ['Cold dough'],
            0, 1),
         processes.ProcessStage(
             'Bake it',
             'Heat at 375 for 40 minutes',
             ['A loaf', 'A dirty pan'],
             1, 2),
         ])
    expected = {
        'name': 'Baking',
        'description': 'This is how you make bread',
        'applicability': 'Make it before you are hungry',
        'stages': [
            {'name': 'Make dough',
             'description': 'Mix it and kneed',
             'progress_items': ['Cold dough'],
             'incoming_stage': 0,
             'outgoing_stage': 1},
            {'name': 'Bake it',
             'description': 'Heat at 375 for 40 minutes',
             'progress_items': ['A loaf', 'A dirty pan'],
             'incoming_stage': 1,
             'outgoing_stage': 2},
        ]
    }
    actual = processes.process_to_dict(process)
    self.assertEqual(expected, actual)
