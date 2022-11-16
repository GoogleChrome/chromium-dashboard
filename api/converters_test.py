# Copyright 2022 Google Inc.
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


from api import converters
from internals.core_models import FeatureEntry

from google.cloud import ndb  # type: ignore

class ConvertersTest(testing_config.CustomTestCase):

  def setUp(self):
    self.fe_1 = FeatureEntry(
        id=123, name='feature template', summary='sum',
        owner_emails=['feature_owner@example.com'],
        editor_emails=['feature_editor@example.com', 'owner_1@example.com'],
        category=1, creator_email='creator_template@example.com',
        updater_email='editor_template@example.com',
        blink_components=['Blink'])
    self.fe_1.put()
    self.maxDiff = None

  def tearDown(self) -> None:
    self.fe_1.key.delete()

  def test_feature_entry_to_json_basic__bad_view_field(self):
    """Function handles if any views fields have deprecated values."""
    # Deprecated views enum value.
    self.fe_1.ff_views = 4
    self.fe_1.safari_views = 4
    self.fe_1.put()
    result = converters.feature_entry_to_json_basic(self.fe_1)
    self.assertEqual(5, result['browsers']['safari']['view']['val'])
    self.assertEqual(5, result['browsers']['ff']['view']['val'])

  def test_feature_entry_to_jason_verbose__bad_view_field(self):
    """Function handles if any views fields have deprecated values."""
    # Deprecated views enum value.
    self.fe_1.safari_views = 4
    self.fe_1.ff_views = 4
    self.fe_1.put()
    result = converters.feature_entry_to_json_verbose(self.fe_1)
    self.assertEqual(5, result['browsers']['safari']['view']['val'])
    self.assertEqual(5, result['browsers']['ff']['view']['val'])
