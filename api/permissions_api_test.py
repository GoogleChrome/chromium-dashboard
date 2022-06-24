# -*- coding: utf-8 -*-
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

import flask

from api import permissions_api
from framework import ramcache

test_app = flask.Flask(__name__)


class PermissionsAPITest(testing_config.CustomTestCase):

  def setUp(self):    
    self.handler = permissions_api.PermissionsAPI()
    self.request_path = f'/api/v0/currentuser/permissions'

  def tearDown(self):
    testing_config.sign_out()
    ramcache.flush_all()
    ramcache.check_for_distributed_invalidation()

  def test_get__anon(self):
    """Returns no user object if not signed in"""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    self.assertEqual({'user': None}, actual_response)

  def test_get__non_googler(self):
    """Non-googlers have no permissions by default"""
    testing_config.sign_in('one@example.com', 12345)
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    expected_response = {
      'user': {
        'can_create_feature': False,
        'can_approve': False,
        'can_edit': False,
        'is_admin': False,
        'email': 'one@example.com'
        }}
    self.assertEqual(expected_response, actual_response)

  def test_get__googler(self):
    """Googlers have default permissions to create feature and edit."""
    testing_config.sign_in('one@google.com', 67890)
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    expected_response = {
      'user': {
        'can_create_feature': True,
        'can_approve': False,
        'can_edit': True,
        'is_admin': False,
        'email': 'one@google.com'
        }}
    self.assertEqual(expected_response, actual_response)