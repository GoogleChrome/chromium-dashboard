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

import guideforms
import models


class DisplayFieldsTest(unittest.TestCase):

  def testAllFieldsInStages_NoDuplicates(self):
    """Each field appears at most once."""
    fields_seen = set(guideforms.METADATA_FIELDS +
                      guideforms.DEPRECATED_FIELDS)
    for stage_id, field_spec_list in guideforms.DISPLAY_FIELDS_IN_STAGES.items():
      for field_spec in field_spec_list:
        field_name = field_spec[0]
        self.assertNotIn(
            field_name, fields_seen,
            msg='Field %r is in DISPLAY_FIELDS_IN_STAGES twice' % field_name)
        fields_seen.add(field_name)

  def testDisplayFields_CompleteCoverage(self):
    """Each field appears at least once."""
    fields_seen = set(guideforms.METADATA_FIELDS +
                      guideforms.DEPRECATED_FIELDS)
    for stage_id, field_spec_list in guideforms.DISPLAY_FIELDS_IN_STAGES.items():
      for field_spec in field_spec_list:
        field_name = field_spec[0]
        fields_seen.add(field_name)
    for field_name in guideforms.ALL_FIELDS.keys():
      self.assertIn(
          field_name, fields_seen,
          msg='Field %r is missing in DISPLAY_FIELDS_IN_STAGES' % field_name)
