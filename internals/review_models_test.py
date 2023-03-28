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

from internals.core_models import FeatureEntry
from internals.review_models import Activity, Gate, OwnersFile, Vote


class CommentTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        name='feature a', summary='sum',
        owner_emails=['feature_owner@example.com'],
        category=1, impl_status_chrome=3)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.act_1_1 = Activity(
        feature_id=self.feature_1_id, gate_id=1,
        author='one@example.com',
        content='some text')
    self.act_1_1.put()
    self.act_1_2 = Activity(
        feature_id=self.feature_1_id, gate_id=2,
        author='one@example.com',
        content='some other text')
    self.act_1_2.put()
    self.act_1_3 = Activity(
        feature_id=self.feature_1_id,
        author='one@example.com',
        content='random')
    self.act_1_3.put()

    self.feature_2 = FeatureEntry(
        name='feature b', summary='sum',
        owner_emails=['feature_owner@example.com'],
        category=1, impl_status_chrome=3)
    self.feature_2.put()
    self.feature_2_id = self.feature_2.key.integer_id()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    for activity in Activity.query().fetch(None):
      activity.key.delete()

  def test_get_activities__none(self):
    """We get [] if feature has no review comments."""
    actual = Activity.get_activities(self.feature_2_id, comments_only=True)
    self.assertEqual([], actual)

  def test_get_activities__some(self):
    """We get review comments if the feature has some."""
    actual = Activity.get_activities(self.feature_1_id)
    self.assertEqual(3, len(actual))
    self.assertEqual(
        ['some text', 'some other text', 'random'],
        [c.content for c in actual])

  def test_get_activities__specific_fields(self):
    """We get review comments for specific approval fields if requested."""
    actual_1 = Activity.get_activities(
        self.feature_1_id, 1, comments_only=True)
    self.assertEqual(2, len(actual_1))
    self.assertEqual(
        ['some text', 'random'],
        [c.content for c in actual_1])

    actual_2 = Activity.get_activities(
        self.feature_1_id, 2, comments_only=True)
    self.assertEqual(2, len(actual_2))
    self.assertEqual(
        ['some other text', 'random'],
        [c.content for c in actual_2])

    actual_3 = Activity.get_activities(
        self.feature_1_id, 3, comments_only=True)
    self.assertEqual('random', actual_3[0].content)


class GateTest(testing_config.CustomTestCase):
  # TODO(jrobbins): Add tests for is_resolved, is_approved, get_feature_gates.
  pass


class OwnersFileTest(testing_config.CustomTestCase):

  def setUp(self):
    now = datetime.datetime.now()
    self.owner_file_1 = OwnersFile(url='abc', raw_content='foo', created_on=now)
    self.owner_file_1.add_owner_file()

    expired = now - datetime.timedelta(hours=3)
    self.owner_file_2 = OwnersFile(url='def', raw_content='bar', created_on=expired)
    self.owner_file_2.add_owner_file()

  def tearDown(self):
    self.owner_file_1.key.delete()
    self.owner_file_2.key.delete()

  def test_get_raw_owner_file(self):
    raw_content = OwnersFile.get_raw_owner_file('abc')
    self.assertEqual('foo', raw_content)

    expired_content = OwnersFile.get_raw_owner_file('def')
    self.assertEqual(None, expired_content)
