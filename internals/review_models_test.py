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
from framework import users

from internals import approval_defs, core_models
from internals.review_models import Activity, Approval, Gate, OwnersFile, Vote


class ApprovalTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature a', summary='sum', category=1, impl_status_chrome=3)
    self.feature_1.put()
    self.feature_1_id = self.feature_1.key.integer_id()
    self.appr_1 = Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=Approval.REVIEW_REQUESTED,
        set_on=datetime.datetime.now() - datetime.timedelta(1),
        set_by='one@example.com')
    self.appr_1.put()

    self.appr_2 = Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=Approval.APPROVED,
        set_on=datetime.datetime.now(),
        set_by='two@example.com')
    self.appr_2.put()
    self.appr_3 = Approval(
        feature_id=self.feature_1_id, field_id=1,
        state=Approval.APPROVED,
        set_on=datetime.datetime.now() + datetime.timedelta(1),
        set_by='three@example.com')
    self.appr_3.put()

  def tearDown(self):
    self.feature_1.key.delete()
    for appr in Approval.query().fetch(None):
      appr.key.delete()
    for gate in Gate.query():
      gate.key.delete()
    for vote in Vote.query():
      vote.key.delete()

  def test_get_approvals(self):
    """We can retrieve Approval entities."""
    actual = Approval.get_approvals(feature_id=self.feature_1_id)
    self.assertEqual(3, len(actual))
    self.assertEqual(Approval.REVIEW_REQUESTED, actual[0].state)
    self.assertEqual(Approval.APPROVED, actual[1].state)
    self.assertEqual(
        sorted(actual, key=lambda appr: appr.set_on),
        actual)

    actual = Approval.get_approvals(field_id=1)
    self.assertEqual(Approval.REVIEW_REQUESTED, actual[0].state)
    self.assertEqual(Approval.APPROVED, actual[1].state)

    actual = Approval.get_approvals(
        states={Approval.REVIEW_REQUESTED,
                Approval.REVIEW_STARTED})
    self.assertEqual(1, len(actual))

    actual = Approval.get_approvals(set_by='one@example.com')
    self.assertEqual(1, len(actual))
    self.assertEqual(Approval.REVIEW_REQUESTED, actual[0].state)

  def test_is_valid_state(self):
    """We know what approval states are valid."""
    self.assertTrue(
        Approval.is_valid_state(Approval.REVIEW_REQUESTED))
    self.assertFalse(Approval.is_valid_state(None))
    self.assertFalse(Approval.is_valid_state('not an int'))
    self.assertFalse(Approval.is_valid_state(999))

  def test_set_approval(self):
    """We can set an Approval entity."""
    Approval.set_approval(
        self.feature_1_id, 2, Approval.REVIEW_REQUESTED,
        'owner@example.com')
    self.assertEqual(
        4,
        len(Approval.query().fetch(None)))

  def test_clear_request(self):
    """We can clear a review request so that it is no longer pending."""
    self.appr_1.state = Approval.REVIEW_REQUESTED
    self.appr_1.put()

    Approval.clear_request(self.feature_1_id, 1)

    remaining_apprs = Approval.get_approvals(
        feature_id=self.feature_1_id, field_id=1,
        states=[Approval.REVIEW_REQUESTED])
    self.assertEqual([], remaining_apprs)

class CommentTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature a', summary='sum',  owner=['feature_owner@example.com'],
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

    self.feature_2 = core_models.Feature(
        name='feature b', summary='sum', owner=['feature_owner@example.com'],
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
    self.assertEqual(2, len(actual))
    self.assertEqual(
        ['some text', 'some other text'],
        [c.content for c in actual])

  def test_get_activities__specific_fields(self):
    """We get review comments for specific approval fields if requested."""
    actual_1 = Activity.get_activities(
        self.feature_1_id, 1, comments_only=True)
    self.assertEqual(1, len(actual_1))
    self.assertEqual('some text', actual_1[0].content)

    actual_2 = Activity.get_activities(
        self.feature_1_id, 2, comments_only=True)
    self.assertEqual(1, len(actual_2))
    self.assertEqual('some other text', actual_2[0].content)

    actual_3 = Activity.get_activities(
        self.feature_1_id, 3, comments_only=True)
    self.assertEqual([], actual_3)


class GateTest(testing_config.CustomTestCase):

  def setUp(self):
    self.gate_1 = Gate(feature_id=1, stage_id=1, gate_type=2, state=Vote.NA)
    self.gate_1.put()
    gate_id = self.gate_1.key.integer_id()
    self.votes = []
    # Votes that reference gate_1.
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.APPROVED,
        set_on=datetime.datetime(2020, 1, 1), set_by='user1@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.DENIED, set_on=datetime.datetime(2020, 1, 1),
        set_by='use21@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.REVIEW_REQUESTED, set_on=datetime.datetime(2020, 2, 1),
        set_by='use31@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.REVIEW_REQUESTED, set_on=datetime.datetime(2020, 3, 1),
        set_by='user4@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.REVIEW_REQUESTED, set_on=datetime.datetime(2020, 1, 2),
        set_by='user5@example.com'))

    self.gate_2 = Gate(feature_id=2, stage_id=2, gate_type=2,
        state=Vote.APPROVED)
    self.gate_2.put()
    gate_id = self.gate_2.key.integer_id()
    self.votes.append(Vote(feature_id=1, gate_id=gate_id,
        state=Vote.REVIEW_REQUESTED, set_on=datetime.datetime(2020, 7, 1),
        set_by='user6@example.com'))
    # Votes that reference gate_2.
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.APPROVED,
        set_on=datetime.datetime(2020, 2, 1), set_by='user7@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.APPROVED,
        set_on=datetime.datetime(2020, 4, 10), set_by='user8@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.NA,
        set_on=datetime.datetime(2020, 1, 15), set_by='user9@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.NA,
        set_on=datetime.datetime(2020, 8, 23), set_by='user10@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=gate_id, state=Vote.APPROVED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))

    # Some additional votes that should have no bearing on the gates.
    self.votes.append(Vote(feature_id=2, gate_id=5, state=Vote.DENIED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))
    self.votes.append(Vote(feature_id=3, gate_id=3, state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))
    self.votes.append(Vote(feature_id=2, gate_id=1, state=Vote.REVIEW_REQUESTED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))
    self.votes.append(Vote(feature_id=2, gate_id=1, state=Vote.NA,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))
    self.votes.append(Vote(feature_id=1, gate_id=2, state=Vote.APPROVED,
        set_on=datetime.datetime(2021, 1, 1), set_by='user11@example.com'))

    for vote in self.votes:
      vote.put()

  def tearDown(self):
    self.gate_1.key.delete()
    self.gate_2.key.delete()
    for vote in self.votes:
      vote.key.delete()

  def test_clear_request(self):
    """Once a Gate's outcome is determined, review requests are removed."""
    self.gate_1.clear_request()
    votes = Vote.query(Vote.gate_id == self.gate_1.key.integer_id()).fetch()
    # 5 total votes, 3 with state REVIEW_REQUESTED. Removing them leaves 2.
    self.assertEqual(len(votes), 2)

  def test_update_approval_stage__needs_update(self):
    """Gate's approval state will updated based on votes."""
    # Gate 1 should evaluate to not approved after updating.
    self.assertEqual(approval_defs.update_gate_approval_state(self.gate_1), 6)
    self.assertEqual(self.gate_1.state, 6)

  def test_update_approval_state__no_change(self):
    """Gate's approval state does not change unless it needs to."""
    # Gate 2 is already marked as approved and should not change.
    self.assertEqual(approval_defs.update_gate_approval_state(self.gate_2), 5)
    self.assertEqual(self.gate_2.state, 5)


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


class ActivityTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.FeatureEntry(
        name='feature a', summary='sum', category=1,
        owner_emails=['feature_owner@example.com'])
    self.feature_1.put()
    testing_config.sign_in('one@example.com', 123567890)

  def tearDown(self):
    feature_id = self.feature_1.key.integer_id()
    activities = Activity.get_activities(feature_id)
    for activity in activities:
      activity.key.delete()
    self.feature_1.key.delete()
    testing_config.sign_out()

  def test_activities_created(self):
    # stash_values is used to note what the original values of a feature are.
    self.feature_1.stash_values()
    self.feature_1.owner_emails = ["other@example.com"]
    self.feature_1.summary = "new summary"
    self.feature_1.put()

    self.feature_1.stash_values()
    self.feature_1.name = 'Changed name'
    self.feature_1.put()

    feature_id = self.feature_1.key.integer_id()
    activities = Activity.get_activities(feature_id)
    self.assertEqual(len(activities), 2)
    self.assertEqual(len(activities[0].amendments), 2)
    self.assertEqual(len(activities[1].amendments), 1)

    expected = [
        ('owner_emails', '[\'feature_owner@example.com\']',
            '[\'other@example.com\']'),
        ('summary', 'sum', 'new summary'),
        ('name', 'feature a', 'Changed name')]
    result = activities[0].amendments + activities[1].amendments

    for i, (field, before, expected) in enumerate(expected):
      self.assertEqual(field, result[i].field_name)
      self.assertEqual(before, result[i].old_value)
      self.assertEqual(expected, result[i].new_value)

  def test_activities_created__no_stash(self):
    """If stash_values() is not called, no activity should be logged."""
    self.feature_1.owner_emails = ["other@example.com"]
    self.feature_1.summary = "new summary"
    self.feature_1.put()

    self.feature_1.name = 'Changed name'
    self.feature_1.put()

    feature_id = self.feature_1.key.integer_id()
    activities = Activity.get_activities(feature_id)
    self.assertEqual(len(activities), 0)

  def test_activities_created__no_changes(self):
    """No Activity should be logged if submitted with no changes."""
    self.feature_1.stash_values()
    self.feature_1.put()

    feature_id = self.feature_1.key.integer_id()
    activities = Activity.get_activities(feature_id)
    self.assertEqual(len(activities), 0)
