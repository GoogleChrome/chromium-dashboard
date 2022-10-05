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

from google.cloud import ndb

import testing_config  # Must be imported before the module under test.
from datetime import datetime

from internals import core_models, review_models
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
    expected = '2 Approval entities migrated to Vote entities.'
    self.assertEqual(result, expected)
    approvals = review_models.Approval.query().fetch()
    self.assertEqual(len(approvals), 3)
    self.assertEqual(2020, approvals[0].set_on.year)

    # The migration should be idempotent, so nothing should be migrated twice.
    result_2 = migration_handler.get_template_data()
    expected = '0 Approval entities migrated to Vote entities.'
    self.assertEqual(result_2, expected)

class MigrateFeaturesToFeatureEntriesTest(testing_config.CustomTestCase):

  # Fields that do not require name change or revisions during migration.
  FEATURE_FIELDS = ['created', 'updated', 'accurate_as_of',
      'unlisted', 'deleted', 'name', 'summary', 'category',
      'blink_components', 'star_count', 'search_tags',
      'feature_type', 'intent_stage', 'bug_url', 'launch_bug_url',
      'impl_status_chrome', 'flag_name', 'ongoing_constraints', 'motivation',
      'devtrial_instructions', 'activation_risks', 'measurement',
      'initial_public_proposal_url', 'explainer_links',
      'requires_embedder_support', 'standard_maturity', 'spec_link',
      'api_spec', 'interop_compat_risks',
      'prefixed', 'all_platforms', 'all_platforms_descr', 'tag_review',
      'tag_review_status', 'non_oss_deps', 'anticipated_spec_changes',
      'ff_views', 'safari_views', 'web_dev_views', 'ff_views_link',
      'safari_views_link', 'web_dev_views_link', 'ff_views_notes',
      'safari_views_notes', 'web_dev_views_notes', 'other_views_notes',
      'security_risks', 'security_review_status', 'privacy_review_status',
      'ergonomics_risks', 'wpt', 'wpt_descr', 'webview_risks',
      'debuggability', 'doc_links', 'sample_links']
  
  # (Feature field, FeatureEntry field)
  RENAMED_FIELDS = [('creator', 'creator_email'),
    ('owner', 'owner_emails'),
    ('editors', 'editor_emails'),
    ('cc_recipients', 'cc_emails'),
    ('spec_mentors', 'spec_mentor_emails'),
    ('devrel', 'devrel_emails'),
    ('comments', 'feature_notes')]

  def setUp(self):
    self.feature_1 = core_models.Feature(
        id=1,
        created=datetime(2020, 1, 1),
        updated=datetime(2020, 7, 1),
        accurate_as_of=datetime(2020, 3, 1),
        created_by=ndb.User(
            _auth_domain='example.com', email='user@example.com'),
        updated_by=ndb.User(
            _auth_domain='example.com', email='editor@example.com'),
        owner=['owner@example.com'],
        creator='creator@example.com',
        editors=['editor@example.com'],
        cc_recipients=['cc_user@example.com'],
        unlisted=False,
        deleted=False,
        name='feature_one',
        summary='newly migrated summary',
        comments='Some comments.',
        category=1,
        blink_components=['Blink'],
        star_count=3,
        search_tags=['tag1', 'tag2'],
        feature_type=1,
        intent_stage=1,
        bug_url='https://bug.example.com',
        launch_bug_url='https://bug.example.com',
        impl_status_chrome=1,
        flag_name='flagname',
        ongoing_constraints='constraints',
        motivation='motivation',
        devtrial_instructions='instructions',
        activation_risks='risks',
        measurement=None,
        initial_public_proposal_url='proposal.example.com',
        explainer_links=['explainer.example.com'],
        requires_embedder_support=False,
        standard_maturity=1,
        standardization=1,
        spec_link='spec.example.com',
        api_spec=False,
        spec_mentors=['mentor1', 'mentor2'],
        interop_compat_risks='risks',
        prefixed=True,
        all_platforms=True,
        all_platforms_descr='All platforms',
        tag_review='tag_review',
        tag_review_status=1,
        non_oss_deps='oss_deps',
        anticipated_spec_changes='spec_changes',
        ff_views=1,
        safari_views=1,
        web_dev_views=1,
        ff_views_link='view.example.com',
        safari_views_link='view.example.com',
        web_dev_views_link='view.example.com',
        ff_views_notes='notes',
        safari_views_notes='notes',
        web_dev_views_notes='notes',
        other_views_notes='notes',
        security_risks='risks',
        security_review_status=1,
        privacy_review_status=1,
        ergonomics_risks='risks',
        wpt=True,
        wpt_descr='description',
        webview_risks='risks',
        devrel=['devrel'],
        debuggability='debuggability',
        doc_links=['link1.example.com', 'link2.example.com'],
        sample_links=[])
    self.feature_1.put()

    self.feature_2 = core_models.Feature(
        id=2,
        created=datetime(2020, 4, 1),
        updated=datetime(2020, 7, 1),
        accurate_as_of=datetime(2020, 6, 1),
        created_by=ndb.User(
            _auth_domain='example.com', email='user@example.com'),
        updated_by=ndb.User(
            _auth_domain='example.com', email='editor@example.com'),
        owner=['owner@example.com'],
        editors=['editor@example.com'],
        unlisted=False,
        deleted=False,
        name='feature_one',
        summary='newly migrated summary',
        standardization=1,
        category=1,
        impl_status_chrome=1,
        web_dev_views=1)
    self.feature_2.put()

    self.feature_3 = core_models.Feature(
        id=3,
        created=datetime(2020, 4, 1),
        updated=datetime(2020, 7, 1),
        accurate_as_of=datetime(2020, 6, 1),
        created_by=ndb.User(
            _auth_domain='example.com', email='user@example.com'),
        updated_by=ndb.User(
            _auth_domain='example.com', email='editor@example.com'),
        owner=['owner@example.com'],
        editors=['editor@example.com'],
        unlisted=False,
        deleted=False,
        name='feature_three',
        summary='migrated summary',
        standardization=1,
        category=1,
        impl_status_chrome=1,
        web_dev_views=1)
    self.feature_3.put()

    # Feature 3 is already migrated.
    self.feature_entry_3 = core_models.FeatureEntry(
        id=3,
        created=datetime(2020, 4, 1),
        updated=datetime(2020, 7, 1),
        accurate_as_of=datetime(2020, 6, 1),
        creator_email='user@example.com',
        updater_email='editor@example.com',
        owner_emails=['owner@example.com'],
        editor_emails=['editor@example.com'],
        unlisted=False,
        deleted=False,
        name='feature_three',
        summary='migrated summary',
        standard_maturity=1,
        impl_status_chrome=1,
        category=1,
        ff_views=1,
        safari_views=1,
        web_dev_views=1)
    self.feature_entry_3.put()

  def tearDown(self):
    for feature in core_models.Feature.query().fetch():
      feature.key.delete()
    for feature_entry in core_models.FeatureEntry.query().fetch():
      feature_entry.key.delete()

  def test_migration(self):
    migration_handler = schema_migration.MigrateFeaturesToFeatureEntries()
    result = migration_handler.get_template_data()
    # One is already migrated, so only 2 others to migrate.
    expected = '2 Feature entities migrated to FeatureEntry entities.'
    self.assertEqual(result, expected)
    feature_entries = core_models.FeatureEntry.query().fetch()
    self.assertEqual(len(feature_entries), 3)
    
    # Check if all fields have been copied over.
    feature_entry_1 = core_models.FeatureEntry.get_by_id(
        self.feature_1.key.integer_id())
    self.assertIsNotNone(feature_entry_1)
    # Check that all fields are copied over as expected.
    for field in self.FEATURE_FIELDS:
      self.assertEqual(
          getattr(feature_entry_1, field), getattr(self.feature_1, field))
    for old_field, new_field in self.RENAMED_FIELDS:
      self.assertEqual(
          getattr(feature_entry_1, new_field), getattr(self.feature_1, old_field))
    self.assertEqual(feature_entry_1.updater_email, self.feature_1.updated_by.email())

    # The migration should be idempotent, so nothing should be migrated twice.
    result_2 = migration_handler.get_template_data()
    expected = '0 Feature entities migrated to FeatureEntry entities.'
    self.assertEqual(result_2, expected)
