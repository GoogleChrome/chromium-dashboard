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
from datetime import datetime

from internals import review_models
from internals import schema_migration

class MigrateCommentsToActivitiesTest(testing_config.CustomTestCase):

  def setUp(self):
    self.comment_1 = review_models.Comment(feature_id=1, field_id=1,
        author='user@example.com', content='some text',
        created=datetime(2020, 1, 1))
    self.comment_1.put()
    self.comment_2 = review_models.Comment(feature_id=1, field_id=2,
        author='other_user@example.com', content='some other text',
        created=datetime(2020, 1, 1))
    self.comment_2.put()
    self.comment_3 = review_models.Comment(feature_id=2, field_id=1,
        author='user@example.com', content='migrated text',
        migrated=True)
    self.comment_3.put()

  def tearDown(self):
    for comm in review_models.Comment.query().fetch(None):
      comm.key.delete()

  def test_migration(self):
    migration_handler = schema_migration.MigrateCommentsToActivities()
    result = migration_handler.get_template_data()
    # One comment is marked as migrated, so only 2 need migration.
    expected = '2 comments migrated to activity entities.'
    self.assertEqual(result, expected)
    # All comments should now be marked as migrated.
    for comm in review_models.Comment.query().fetch(None):
        self.assertTrue(comm.migrated)

    activities = review_models.Activity.query().fetch(None)
    self.assertEqual(len(activities), 2)
    self.assertEqual(2020, activities[0].created.year)

    # The migration should be idempotent, so nothing should be migrated twice.
    result_2 = migration_handler.get_template_data()
    expected = '0 comments migrated to activity entities.'
    self.assertEqual(result_2, expected)
