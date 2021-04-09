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

from __future__ import division
from __future__ import print_function

import datetime
import unittest
import testing_config  # Must be imported before the module under test.

import flask
import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import register
from api import approvals_api
from internals import models


NOW = datetime.datetime.now()

class ApprovalsAPITest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.feature_id = self.feature_1.key().id()
    self.handler = approvals_api.ApprovalsAPI()
    self.request_path = '/api/v0/features/%d/approvals' % self.feature_id

    # These are not in the datastore unless a specific test calls put().
    self.appr_1_1 = models.Approval(
        feature_id=self.feature_id, field_id=1,
        set_by='owner1@example.com', set_on=NOW,
        state=models.Approval.APPROVED)
    self.appr_1_2 = models.Approval(
        feature_id=self.feature_id, field_id=2,
        set_by='owner2@example.com', set_on=NOW,
        state=models.Approval.NEED_INFO)

    self.expected1 = {
        'feature_id': self.feature_id,
        'field_id': 1,
        'set_by': u'owner1@example.com',
        'set_on': str(NOW),
        'state': models.Approval.APPROVED,
        }
    self.expected2 = {
        'feature_id': self.feature_id,
        'field_id': 2,
        'set_by': 'owner2@example.com',
        'set_on': str(NOW),
        'state': models.Approval.NEED_INFO,
        }

  def tearDown(self):
    self.feature_1.delete()
    for appr in models.Approval.all():
      appr.delete()

  def test_get__all_empty(self):
    """We can get all approvals for a given feature, even if there none."""
    testing_config.sign_out()
    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(self.feature_id)
    self.assertEqual({"approvals": []}, actual_response)

  def test_get__all_some(self):
    """We can get all approvals for a given feature."""
    testing_config.sign_out()
    self.appr_1_1.put()
    self.appr_1_2.put()

    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get(self.feature_id)

    self.assertEqual(
        {"approvals": [self.expected1, self.expected2]},
        actual_response)

  def test_get__field_empty(self):
    """We can get approvals for given feature and field, even if there none."""
    testing_config.sign_out()
    with register.app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(self.feature_id, field_id=1)
    self.assertEqual({"approvals": []}, actual_response)

  def test_get__field_some(self):
    """We can get approvals for a given feature and field_id."""
    testing_config.sign_out()
    self.appr_1_1.put()
    self.appr_1_2.put()

    with register.app.test_request_context(self.request_path + '/1'):
      actual_response = self.handler.do_get(self.feature_id, field_id=1)

    self.assertEqual(
        {"approvals": [self.expected1]},
        actual_response)

  # TODO(jrobbins): tests for POST
