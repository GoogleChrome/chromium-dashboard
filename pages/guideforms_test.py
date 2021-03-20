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

import testing_config  # Must be imported first
import unittest

import mock

from pages import guideforms
import models


class DisplayFieldsTest(unittest.TestCase):

  def test_make_display_spec(self):
    summary_spec = guideforms.make_display_spec('summary')
    self.assertEqual('summary', summary_spec[0])
    self.assertEqual('Summary', summary_spec[1])
    self.assertEqual('text', summary_spec[2])

    unlisted_spec = guideforms.make_display_spec('unlisted')
    self.assertEqual('unlisted', unlisted_spec[0])
    self.assertEqual('Unlisted', unlisted_spec[1])
    self.assertEqual('bool', unlisted_spec[2])

    i2p_spec = guideforms.make_display_spec('intent_to_implement_url')
    self.assertEqual('intent_to_implement_url', i2p_spec[0])
    self.assertEqual('Intent to Prototype link', i2p_spec[1])
    self.assertEqual('url', i2p_spec[2])

  def test_make_display_specs(self):
    specs = guideforms.make_display_specs(
        'summary', 'unlisted', 'intent_to_implement_url')
    self.assertEqual(3, len(specs))
    summary_spec, unlisted_spec, i2p_spec = specs
    self.assertEqual('Summary', summary_spec[1])
    self.assertEqual('Unlisted', unlisted_spec[1])
    self.assertEqual('Intent to Prototype link', i2p_spec[1])

  def test_DISPLAY_FIELDS_IN_STAGES__no_duplicates(self):
    """Each field appears at most once."""
    fields_seen = set(guideforms.DISPLAY_IN_FEATURE_HIGHLIGHTS +
                      guideforms.DEPRECATED_FIELDS)
    for stage_id, field_spec_list in guideforms.DISPLAY_FIELDS_IN_STAGES.items():
      for field_spec in field_spec_list:
        field_name = field_spec[0]
        self.assertNotIn(
            field_name, fields_seen,
            msg='Field %r is in DISPLAY_FIELDS_IN_STAGES twice' % field_name)
        fields_seen.add(field_name)

  def test_DISPLAY_FIELDS_IN_STAGES__complete_coverage(self):
    """Each field appears at least once."""
    fields_seen = set(guideforms.DISPLAY_IN_FEATURE_HIGHLIGHTS +
                      guideforms.DEPRECATED_FIELDS)
    for stage_id, field_spec_list in guideforms.DISPLAY_FIELDS_IN_STAGES.items():
      for field_spec in field_spec_list:
        field_name = field_spec[0]
        fields_seen.add(field_name)
    for field_name in guideforms.ALL_FIELDS.keys():
      self.assertIn(
          field_name, fields_seen,
          msg='Field %r is missing in DISPLAY_FIELDS_IN_STAGES' % field_name)
