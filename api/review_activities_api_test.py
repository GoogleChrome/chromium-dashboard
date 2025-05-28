# Copyright 2025 Google Inc.
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

from datetime import datetime
from unittest import mock

import flask
import werkzeug
from chromestatus_openapi.models import (
  ReviewActivity as ReviewActivityModel,
  GetReviewActivitiesResponse,
)

import testing_config  # Must be imported before the module under test.
from api import review_activities_api
from internals.core_models import FeatureEntry
from internals.review_models import Activity, Amendment, Gate, Vote

test_app = flask.Flask(__name__)


class ReviewActivitiesAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.request_path = 'api/v0/activities'
    self.handler = review_activities_api.ReviewActivitiesAPI()

    self.activity_1 = Activity(
      feature_id=1, gate_id=11, author='user1@example.com',
      created=datetime(2020, 1, 1, 11), content='test comment', amendments=[])
    self.activity_1.put()
    
    self.activity_2 = Activity(
      feature_id=1, gate_id=11, created=datetime(2020, 1, 2, 9),
      author='user1@example.com', content=None,
      amendments=[Amendment(
          field_name='review_status', old_value='na', new_value='no_response')
      ])
    self.activity_2.put()

    self.activity_3 = Activity(
      feature_id=1, gate_id=11, author='user2@example.com',
      created=datetime(2020, 1, 3, 8), content='test comment 2', amendments=[])
    self.activity_3.put()

    self.activity_4 = Activity(
      feature_id=1, gate_id=11, created=datetime(2020, 1, 4, 12),
      author='user1@example.com', content=None,
      amendments=[Amendment(
          field_name='review_status', old_value='na', new_value='needs_work')
      ])
    self.activity_4.put()

    # Deleted comment.
    self.activity_5 = Activity(
      feature_id=1, gate_id=11, author='user2@example.com',
      created=datetime(2020, 1, 11, 8), content='test comment 3', amendments=[],
      deleted_by='user2@example.com')
    self.activity_5.put()

    self.activity_6 = Activity(
      feature_id=1, gate_id=11, created=datetime(2020, 1, 6, 12),
      author='user2@example.com', content=None,
      amendments=[Amendment(
          field_name='review_status', old_value='needs_work',
          new_value='approved')
      ])
    self.activity_6.put()

    # Comment with no gate ID.
    self.activity_7 = Activity(
      feature_id=2, gate_id=None, author='user3@example.com',
      created=datetime(2020, 1, 10, 8), content='test comment 4', amendments=[])
    self.activity_7.put()


    self.activity_8 = Activity(
      feature_id=2, gate_id=12, author='user3@example.com',
      created=datetime(2020, 1, 11, 9), content=None,
      amendments=[Amendment(
          field_name='review_status', old_value='needs_work',
          new_value='approved')
      ])
    self.activity_8.put()

    self.activity_9 = Activity(
      feature_id=2, gate_id=12, author='user4@example.com',
      created=datetime(2020, 1, 12, 10), content=None,
      amendments=[Amendment(
          field_name='review_assignee', old_value='',
          new_value='user3@example.com')
      ])
    self.activity_9.put()

    self.activity_10 = Activity(
      feature_id=2, gate_id=12, author='user3@example.com',
      created=datetime(2020, 1, 15, 8), content='test comment 5', amendments=[])
    self.activity_10.put()

  def tearDown(self):
    for kind in [Activity]:
      for entity in kind.query():
        entity.key.delete()

  @mock.patch('flask.abort')
  def test_get__no_start_time(self, mock_abort):
    """Raises 400 if no start time is provided."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_get()
    mock_abort.assert_called_once_with(
      400, description='No start timestamp provided.')

  @mock.patch('flask.abort')
  def test_get__bad_start_time(self, mock_abort):
    """Raises 400 if a malformed start time is provided."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest
    with test_app.test_request_context(f'{self.request_path}?start=oops'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_get()
    mock_abort.assert_called_once_with(
      400, description='Bad date format. Format should be YYYY-MM-DD')

  def test_get__valid(self):
    """Returns activity data if a valid start date is given"""
    with test_app.test_request_context(f'{self.request_path}?start=2020-01-10'):
      actual = self.handler.do_get()

    self.assertIsNotNone(actual.activities)
    activities = actual.activities
    # All activity returned should be after the given start time.
    self.assertTrue(all(
      datetime.strptime(
        a.event_date,
        self.handler.RESPONSE_DATETIME_FORMAT) >= datetime(2020, 1, 10)
      for a in activities))

    self.assertEqual(len(activities), 3)
    # One comment activity should exist in the result
    comment_activity = list(filter(
      lambda a: a.content is not None, activities))
    self.assertEqual(len(comment_activity), 1)
    self.assertEqual(comment_activity[0].content, 'test comment 5')
    # One review status change activity should exist in the result
    review_status_activity = list(filter(
      lambda a: a.review_status is not None, activities))
    self.assertEqual(len(review_status_activity), 1)
    self.assertEqual(review_status_activity[0].review_status, 'approved')
    # One review assignee change activity should exist in the result
    review_assignee_activity = list(filter(
      lambda a: a.review_assignee is not None, activities))
    self.assertEqual(len(review_assignee_activity), 1)
    self.assertEqual(review_assignee_activity[0].review_assignee,
                     'user3@example.com')
