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
    comment_1 = review_models.Comment(id=1, feature_id=1, field_id=1,
        author='user@example.com', content='some text',
        created=datetime(2020, 1, 1))
    comment_1.put()
    comment_2 = review_models.Comment(id=2, feature_id=1, field_id=2,
        author='other_user@example.com', content='some other text',
        created=datetime(2020, 1, 1))
    comment_2.put()

    # Comment 3 is already migrated.
    comment_3 = review_models.Comment(id=3, feature_id=2, field_id=1,
        author='user@example.com', content='migrated text')
    comment_3.put()
    activity_3 = review_models.Activity(id=3, feature_id=2, gate_id=1,
        author='user@example.com', content='migrated text')
    activity_3.put()

  def tearDown(self):
    for comm in review_models.Comment.query().fetch():
      comm.key.delete()
    for activity in review_models.Activity.query().fetch():
      activity.key.delete()

  def test_migration__remove_bad_activities(self):
    migration_handler = schema_migration.MigrateCommentsToActivities()
    bad_activity = review_models.Activity(id=9, feature_id=1, gate_id=1,
        author='user@example.com', content='some text')
    bad_activity.put()
    result = migration_handler._remove_bad_id_activities()
    # One Activity is from an older version of the migration. Should be removed.
    expected = '1 Activities deleted from previous migration.'
    self.assertEqual(result, expected)
    # One other Activity should still exist.
    activities = review_models.Activity.query().fetch()
    self.assertTrue(len(activities) == 1)

  def test_migration(self):
    migration_handler = schema_migration.MigrateCommentsToActivities()
    result = migration_handler.get_template_data()
    # One comment is already migrated, so only 2 need migration.
    expected = '2 Comment entities migrated to Activity entities.'
    self.assertEqual(result, expected)
    activities = review_models.Activity.query().fetch()
    self.assertEqual(len(activities), 3)
    self.assertEqual(2020, activities[0].created.year)

    # The migration should be idempotent, so nothing should be migrated twice.
    result_2 = migration_handler.get_template_data()
    expected = '0 Comment entities migrated to Activity entities.'
    self.assertEqual(result_2, expected)

class MigrateApprovalsToVotesTest(testing_config.CustomTestCase):

  def setUp(self):
    approval_1 = review_models.Approval(id=1, feature_id=1, field_id=1,
        state=1, set_on=datetime(2020, 1, 1), set_by='user1@example.com')
    approval_1.put()

    approval_2 = review_models.Approval(id=2, feature_id=1, field_id=2,
        state=2, set_on=datetime(2020, 3, 1), set_by='user2@example.com')
    approval_2.put()

    approval_3 = review_models.Approval(id=3, feature_id=2, field_id=2,
        state=1, set_on=datetime(2022, 7, 1), set_by='user1@example.com')
    approval_3.put()

    vote_3 = review_models.Vote(id=3, feature_id=2, gate_id=2,
        state=1, set_on=datetime(2022, 7, 1), set_by='user1@example.com')
    vote_3.put()

  def tearDown(self):
    for comm in review_models.Approval.query().fetch():
      comm.key.delete()
    for activity in review_models.Vote.query().fetch():
      activity.key.delete()

  def test_migration(self):
    migration_handler = schema_migration.MigrateApprovalsToVotes()
    result = migration_handler.get_template_data()
    # One approval is already migrated, so only 2 need migration.
    expected = '2 approvals migrated to vote entities.'
    self.assertEqual(result, expected)
    approvals = review_models.Approval.query().fetch()
    self.assertEqual(len(approvals), 3)
    self.assertEqual(2020, approvals[0].set_on.year)

    # The migration should be idempotent, so nothing should be migrated twice.
    result_2 = migration_handler.get_template_data()
    expected = '0 approvals migrated to vote entities.'
    self.assertEqual(result_2, expected)
