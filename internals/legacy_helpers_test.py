
# Copyright 2023 Google Inc.
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

from internals.core_enums import *
from internals import legacy_helpers
from internals.legacy_models import Feature


class LegacyHelpersTest(testing_config.CustomTestCase):

  def setUp(self):
    # Legacy entities for testing legacy functions.
    self.legacy_feature_2 = Feature(
        name='feature b', summary='sum',
        owner=['feature_owner@example.com'], category=1,
        creator="someuser@example.com")
    self.legacy_feature_2.put()

    self.legacy_feature_1 = Feature(
        name='feature a', summary='sum', impl_status_chrome=3,
        owner=['feature_owner@example.com'], category=1)
    self.legacy_feature_1.put()

    self.legacy_feature_4 = Feature(
        name='feature d', summary='sum', category=1, impl_status_chrome=2,
        owner=['feature_owner@example.com'])
    self.legacy_feature_4.put()

    self.legacy_feature_3 = Feature(
        name='feature c', summary='sum', category=1, impl_status_chrome=2,
        owner=['feature_owner@example.com'])
    self.legacy_feature_3.put()

  def tearDown(self):
    for kind in [Feature]:
      for entity in kind.query():
        entity.key.delete()

  def test_get_chronological__normal(self):
    """We can retrieve a list of features."""
    actual = legacy_helpers.get_chronological_legacy()
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature c', 'feature d', 'feature a', 'feature b'],
        names)
    self.assertEqual(True, actual[0]['first_of_milestone'])
    self.assertEqual(False, hasattr(actual[1], 'first_of_milestone'))
    self.assertEqual(True, actual[2]['first_of_milestone'])
    self.assertEqual(False, hasattr(actual[3], 'first_of_milestone'))

  def test_get_chronological__unlisted(self):
    """Unlisted features are not included in the list."""
    self.legacy_feature_2.unlisted = True
    self.legacy_feature_2.put()
    actual = legacy_helpers.get_chronological_legacy(update_cache=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature c', 'feature d', 'feature a'],
        names)

  def test_get_chronological__unlisted_shown(self):
    """Unlisted features are included for users with edit access."""
    self.legacy_feature_2.unlisted = True
    self.legacy_feature_2.put()
    actual = legacy_helpers.get_chronological_legacy(update_cache=True, show_unlisted=True)
    names = [f['name'] for f in actual]
    self.assertEqual(
        ['feature c', 'feature d', 'feature a', 'feature b'],
        names)