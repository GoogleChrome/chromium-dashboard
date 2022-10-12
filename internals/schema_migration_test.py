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

from google.cloud import ndb as ndb

import testing_config  # Must be imported before the module under test.
from datetime import datetime

from internals.core_models import Feature, FeatureEntry, Stage
from internals.review_models import Activity, Approval, Comment, Gate, Vote
from internals import review_models, schema_migration

class MigrateCommentsToActivitiesTest(testing_config.CustomTestCase):

  def setUp(self):
    comment_1 = Comment(id=1, feature_id=1, field_id=1,
        author='user@example.com', content='some text',
        created=datetime(2020, 1, 1))
    comment_1.put()
    comment_2 = Comment(id=2, feature_id=1, field_id=2,
        author='other_user@example.com', content='some other text',
        created=datetime(2020, 1, 1))
    comment_2.put()

    # Comment 3 is already migrated.
    comment_3 = Comment(id=3, feature_id=2, field_id=1,
        author='user@example.com', content='migrated text')
    comment_3.put()
    activity_3 = Activity(id=3, feature_id=2, gate_id=1,
        author='user@example.com', content='migrated text')
    activity_3.put()

  def tearDown(self):
    for comm in Comment.query().fetch():
      comm.key.delete()
    for activity in Activity.query().fetch():
      activity.key.delete()

  def test_migration__remove_bad_activities(self):
    migration_handler = schema_migration.MigrateCommentsToActivities()
    bad_activity = Activity(id=9, feature_id=1, gate_id=1,
        author='user@example.com', content='some text')
    bad_activity.put()
    result = migration_handler._remove_bad_id_activities()
    # One Activity is from an older version of the migration. Should be removed.
    expected = '1 Activities deleted from previous migration.'
    self.assertEqual(result, expected)
    # One other Activity should still exist.
    activities = Activity.query().fetch()
    self.assertTrue(len(activities) == 1)

  def test_migration(self):
    migration_handler = schema_migration.MigrateCommentsToActivities()
    result = migration_handler.get_template_data()
    # One comment is already migrated, so only 2 need migration.
    expected = '2 Comment entities migrated to Activity entities.'
    self.assertEqual(result, expected)
    activities = Activity.query().fetch()
    self.assertEqual(len(activities), 3)
    self.assertEqual(2020, activities[0].created.year)

    # The migration should be idempotent, so nothing should be migrated twice.
    result_2 = migration_handler.get_template_data()
    expected = '0 Comment entities migrated to Activity entities.'
    self.assertEqual(result_2, expected)

class MigrateEntitiesTest(testing_config.CustomTestCase):

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
      'debuggability', 'doc_links', 'sample_links', 'experiment_timeline']
  
  # (Feature field, FeatureEntry field)
  RENAMED_FIELDS = [('creator', 'creator_email'),
    ('owner', 'owner_emails'),
    ('editors', 'editor_emails'),
    ('cc_recipients', 'cc_emails'),
    ('spec_mentors', 'spec_mentor_emails'),
    ('devrel', 'devrel_emails'),
    ('comments', 'feature_notes')]

  def setUp(self):
    self.feature_1 = Feature(
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
        feature_type=3,
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
        shipped_milestone=105,
        intent_to_ship_url='https://example.com/intentship',
        ot_milestone_desktop_start=101,
        ot_milestone_desktop_end=104,
        ot_milestone_android_start = 102,
        ot_milestone_android_end=104,
        intent_to_experiment_url='https://example.com/intentexperiment',
        finch_url='https://example.com/finch',
        initial_public_proposal_url='proposal.example.com',
        explainer_links=['explainer.example.com'],
        requires_embedder_support=False,
        standard_maturity=1,
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

    self.feature_2 = Feature(
        id=2,
        created=datetime(2020, 4, 1),
        updated=datetime(2020, 7, 1),
        accurate_as_of=datetime(2020, 6, 1),
        created_by=ndb.User(
            _auth_domain='example.com', email='user@example.com'),
        updated_by=ndb.User(
            _auth_domain='example.com', email='editor@example.com'),
        feature_type=0,
        owner=['owner@example.com'],
        editors=['editor@example.com'],
        unlisted=False,
        deleted=False,
        name='feature_two',
        summary='summary',
        category=1,)
    self.feature_2.put()

    # Feature 3 stages are already migrated.
    self.feature_3 = Feature(
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
        summary='summary',
        category=1)
    self.feature_3.put()

    self.feature_4 = Feature(
        id=4,
        created=datetime(2020, 4, 1),
        updated=datetime(2020, 7, 1),
        accurate_as_of=datetime(2020, 6, 1),
        created_by=ndb.User(
            _auth_domain='example.com', email='user@example.com'),
        updated_by=ndb.User(
            _auth_domain='example.com', email='editor@example.com'),
        owner=['owner@example.com'],
        editors=['editor@example.com'],
        feature_type=1,
        unlisted=False,
        deleted=False,
        name='feature_four',
        summary='migrated summary',
        category=1)
    self.feature_4.put()

    self.feature_5 = Feature(
        id=5,
        created=datetime(2020, 4, 1),
        updated=datetime(2020, 7, 1),
        accurate_as_of=datetime(2020, 6, 1),
        created_by=ndb.User(
            _auth_domain='example.com', email='user@example.com'),
        updated_by=ndb.User(
            _auth_domain='example.com', email='editor@example.com'),
        owner=['owner@example.com'],
        editors=['editor@example.com'],
        feature_type=2,
        unlisted=False,
        deleted=False,
        name='feature_five',
        summary='summary',
        category=1)
    self.feature_5.put()

    # Create a "random" number of Approval entities.
    appr_states = [Approval.NA, Approval.NOT_APPROVED, Approval.APPROVED]
    for i in range(20):
      id = i % 5 + 1
      gate_type = i % 4 + 1
      state = appr_states[i % 3]
      set_on = datetime(2020, 1, 1)
      set_by = f'voter{i}@example.com'
      appr = Approval(feature_id=id, field_id=gate_type, state=state,
        set_on=set_on, set_by=set_by)
      appr.put()

  def tearDown(self):
    kinds = [Feature, FeatureEntry, Stage, Gate, Approval, Vote]
    for kind in kinds:
      for entity in kind.query().fetch():
        entity.key.delete()

  def test_migration(self):
    migration_handler = schema_migration.MigrateEntities()
    result = migration_handler.get_template_data()
    # One is already migrated, so only 2 others to migrate.
    expected = '5 Feature entities migrated to FeatureEntry entities.'
    self.assertEqual(result, expected)
    feature_entries = FeatureEntry.query().fetch()
    stages = Stage.query().fetch()
    gates = Gate.query().fetch()
    approvals = Vote.query().fetch()

    self.assertEqual(len(feature_entries), 5)
    self.assertEqual(len(stages), 28)
    self.assertEqual(len(gates), 16)
    self.assertEqual(len(approvals), 16)

    # Check if certain fields were copied over correctly.
    stages = Stage.query(
        Stage.feature_id == self.feature_1.key.integer_id()).fetch()
    self.assertEqual(len(stages), 6)

    # Filter for STAGE_DEP_SHIPPING enum.
    shipping_stage_list = [
      stage for stage in stages if stage.stage_type == 460]
    ot_stage_list = [
        stage for stage in stages if stage.stage_type == 450]
    # Check that 1 Stage exists and the milestone value is correct.
    self.assertEqual(len(shipping_stage_list), 1)
    self.assertEqual(shipping_stage_list[0].milestones.desktop_first, 105)
    self.assertEqual(shipping_stage_list[0].intent_thread_url,
        'https://example.com/intentship')
    self.assertEqual(shipping_stage_list[0].finch_url,
        'https://example.com/finch')
    self.assertEqual(len(ot_stage_list), 1)
    self.assertEqual(ot_stage_list[0].milestones.desktop_first, 101)
    self.assertEqual(ot_stage_list[0].milestones.desktop_last, 104)
    self.assertEqual(ot_stage_list[0].milestones.android_first, 102)
    self.assertEqual(ot_stage_list[0].milestones.android_last, 104)
    self.assertEqual(ot_stage_list[0].intent_thread_url,
        'https://example.com/intentexperiment')

    # Check if all fields have been copied over.
    feature_entry_1 = FeatureEntry.get_by_id(
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
