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

import testing_config  # Must be imported before the module under test.

import datetime
from unittest import mock
from framework import ramcache
from framework import users

from internals import core_models
from internals import review_models


class ApprovalTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature a', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=3)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.appr_1 = review_models.Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=review_models.Approval.REVIEW_REQUESTED,
        set_on=datetime.datetime.now() - datetime.timedelta(1),
        set_by='one@example.com')
    self.appr_1.put()
    self.appr_2 = review_models.Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=review_models.Approval.APPROVED,
        set_on=datetime.datetime.now(),
        set_by='two@example.com')
    self.appr_2.put()
    self.appr_3 = review_models.Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=review_models.Approval.APPROVED,
        set_on=datetime.datetime.now() + datetime.timedelta(1),
        set_by='three@example.com')
    self.appr_3.put()

  def tearDown(self):
    self.feature_1.key.delete()
    for appr in review_models.Approval.query().fetch(None):
      appr.key.delete()

  def test_get_approvals(self):
    """We can retrieve Approval entities."""
    actual = review_models.Approval.get_approvals(feature_id=self.feature_1_id)
    self.assertEqual(3, len(actual))
    self.assertEqual(review_models.Approval.REVIEW_REQUESTED, actual[0].state)
    self.assertEqual(review_models.Approval.APPROVED, actual[1].state)
    self.assertEqual(
        sorted(actual, key=lambda appr: appr.set_on),
        actual)

    actual = review_models.Approval.get_approvals(field_id=1)
    self.assertEqual(review_models.Approval.REVIEW_REQUESTED, actual[0].state)
    self.assertEqual(review_models.Approval.APPROVED, actual[1].state)

    actual = review_models.Approval.get_approvals(
        states={review_models.Approval.REVIEW_REQUESTED,
                review_models.Approval.REVIEW_STARTED})
    self.assertEqual(1, len(actual))

    actual = review_models.Approval.get_approvals(set_by='one@example.com')
    self.assertEqual(1, len(actual))
    self.assertEqual(review_models.Approval.REVIEW_REQUESTED, actual[0].state)

  def test_is_valid_state(self):
    """We know what approval states are valid."""
    self.assertTrue(
        review_models.Approval.is_valid_state(review_models.Approval.REVIEW_REQUESTED))
    self.assertFalse(review_models.Approval.is_valid_state(None))
    self.assertFalse(review_models.Approval.is_valid_state('not an int'))
    self.assertFalse(review_models.Approval.is_valid_state(999))

  def test_set_approval(self):
    """We can set an Approval entity."""
    review_models.Approval.set_approval(
        self.feature_1_id, 2, review_models.Approval.REVIEW_REQUESTED,
        'owner@example.com')
    self.assertEqual(
        4,
        len(review_models.Approval.query().fetch(None)))

  def test_clear_request(self):
    """We can clear a review request so that it is no longer pending."""
    self.appr_1.state = review_models.Approval.REVIEW_REQUESTED
    self.appr_1.put()

    review_models.Approval.clear_request(self.feature_1_id, 1)

    remaining_apprs = review_models.Approval.get_approvals(
        feature_id=self.feature_1_id, field_id=1,
        states=[review_models.Approval.REVIEW_REQUESTED])
    self.assertEqual([], remaining_apprs)


class CommentTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature a', summary='sum',  owner=['feature_owner@example.com'],
        category=1, visibility=1, standardization=1, web_dev_views=1,
        impl_status_chrome=3)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.comment_1_1 = review_models.Comment(
        feature_id=self.feature_1_id, field_id=1,
        author='one@example.com',
        content='some text')
    self.comment_1_1.put()
    self.comment_1_2 = review_models.Comment(
        feature_id=self.feature_1_id, field_id=2,
        author='one@example.com',
        content='some other text')
    self.comment_1_2.put()

    self.feature_2 = core_models.Feature(
        name='feature b', summary='sum', owner=['feature_owner@example.com'],
        category=1, visibility=1, standardization=1, web_dev_views=1,
        impl_status_chrome=3)
    self.feature_2.put()
    self.feature_2_id = self.feature_2.key.integer_id()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    for comm in review_models.Comment.query().fetch(None):
      comm.key.delete()

  def test_get_comments__none(self):
    """We get [] if feature has no review comments."""
    actual = review_models.Comment.get_comments(self.feature_2_id)
    self.assertEqual([], actual)

  def test_get_comments__some(self):
    """We get review comments if the feature has some."""
    actual = review_models.Comment.get_comments(self.feature_1_id)
    self.assertEqual(2, len(actual))
    self.assertEqual(
        ['some text', 'some other text'],
        [c.content for c in actual])

  def test_get_comments__specific_fields(self):
    """We get review comments for specific approval fields if requested."""
    actual_1 = review_models.Comment.get_comments(self.feature_1_id, 1)
    self.assertEqual(1, len(actual_1))
    self.assertEqual('some text', actual_1[0].content)

    actual_2 = review_models.Comment.get_comments(self.feature_1_id, 2)
    self.assertEqual(1, len(actual_2))
    self.assertEqual('some other text', actual_2[0].content)

    actual_3 = review_models.Comment.get_comments(self.feature_1_id, 3)
    self.assertEqual([], actual_3)


class OwnersFileTest(testing_config.CustomTestCase):

  def setUp(self):
    now = datetime.datetime.now()
    self.owner_file_1 = review_models.OwnersFile(url='abc', raw_content='foo', created_on=now)
    self.owner_file_1.add_owner_file()

    expired = now - datetime.timedelta(hours=3)
    self.owner_file_2 = review_models.OwnersFile(url='def', raw_content='bar', created_on=expired)
    self.owner_file_2.add_owner_file()

  def tearDown(self):
    self.owner_file_1.key.delete()
    self.owner_file_2.key.delete()

  def test_get_raw_owner_file(self):
    raw_content = review_models.OwnersFile.get_raw_owner_file('abc')
    self.assertEqual('foo', raw_content)

    expired_content = review_models.OwnersFile.get_raw_owner_file('def')
    self.assertEqual(None, expired_content)


class ActivityTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature a', summary='sum', owner=['feature_owner@example.com'],
        category=1, visibility=1, standardization=1, web_dev_views=1,
        impl_status_chrome=3)
    self.feature_1.put()

  def tearDown(self):
    feature_id = self.feature_1.key.integer_id()
    activities = review_models.Activity.get_activities(feature_id)
    for activity in activities:
      activity.key.delete()
    self.feature_1.key.delete()

  def test_activities_created(self):
    # stash_values is used to note what the original values of a feature are.
    self.feature_1.stash_values()
    self.feature_1.owner = ["other@example.com"]
    self.feature_1.summary = "new summary"
    self.feature_1.put()

    self.feature_1.stash_values()
    self.feature_1.name = 'Changed name'
    self.feature_1.put()

    feature_id = self.feature_1.key.integer_id()
    activities = review_models.Activity.get_activities(feature_id)
    self.assertEqual(len(activities), 2)
    self.assertEqual(len(activities[0].amendments), 2)
    self.assertEqual(len(activities[1].amendments), 1)

    expected = [
        ('owner', '[\'feature_owner@example.com\']', '[\'other@example.com\']'),
        ('summary', 'sum', 'new summary'),
        ('name', 'feature a', 'Changed name')]
    result = activities[0].amendments + activities[1].amendments

    for i, (field, before, expected) in enumerate(expected):
      self.assertEqual(field, result[i].field_name)
      self.assertEqual(before, result[i].old_value)
      self.assertEqual(expected, result[i].new_value)
  
  def test_activities_created__no_stash(self):
    """stash_values() is not called, so no activity should be logged."""
    self.feature_1.owner = ["other@example.com"]
    self.feature_1.summary = "new summary"
    self.feature_1.put()

    self.feature_1.name = 'Changed name'
    self.feature_1.put()

    feature_id = self.feature_1.key.integer_id()
    activities = review_models.Activity.get_activities(feature_id)
    self.assertEqual(len(activities), 0)

  def test_activities_created__no_changes(self):
    """No Activity should be logged if submitted with no changes."""
    self.feature_1.stash_values()
    self.feature_1.put()

    feature_id = self.feature_1.key.integer_id()
    activities = review_models.Activity.get_activities(feature_id)
    self.assertEqual(len(activities), 0)
