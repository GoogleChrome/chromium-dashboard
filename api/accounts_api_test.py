# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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
import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import accounts_api
from api import register
from internals import models


class AccountsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.app_admin = models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()
    self.appuser_1 = models.AppUser(email='user@example.com')
    self.appuser_1.put()
    self.appuser_id = self.appuser_1.key.integer_id()

    self.request_path = '/api/v0/accounts/%d' % self.appuser_id
    self.handler = accounts_api.AccountsAPI()

  def tearDown(self):
    self.appuser_1.key.delete()
    self.app_admin.key.delete()

  def test_create__normal_valid(self):
    """Admin wants to register a normal account."""
    testing_config.sign_in('admin@example.com', 123567890)

    json_data = {'email': 'new@example.com', 'isAdmin': False}
    with register.app.test_request_context(self.request_path, json=json_data):
      actual_json = self.handler.do_post()
    self.assertEqual('new@example.com', actual_json['email'])
    self.assertFalse(actual_json['is_admin'])

    new_appuser = (models.AppUser.query(models.AppUser.email == 'new@example.com').get())
    self.assertEqual('new@example.com', new_appuser.email)
    self.assertFalse(new_appuser.is_admin)

  def test_create__admin_valid(self):
    """Admin wants to register a new admin account."""
    testing_config.sign_in('admin@example.com', 123567890)

    json_data = {'email': 'new_admin@example.com', 'isAdmin': True}
    with register.app.test_request_context(self.request_path, json=json_data):
      actual_json = self.handler.do_post()
    self.assertEqual('new_admin@example.com', actual_json['email'])
    self.assertTrue(actual_json['is_admin'])

    new_appuser = (models.AppUser.query(models.AppUser.email == 'new_admin@example.com').get())
    self.assertEqual('new_admin@example.com', new_appuser.email)
    self.assertTrue(new_appuser.is_admin)

  def test_create__forbidden(self):
    """Regular user cannot create an account."""
    testing_config.sign_in('one@example.com', 123567890)

    with register.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(self.appuser_id)

    new_appuser = (models.AppUser.query(models.AppUser.email == 'new@example.com').get())
    self.assertIsNone(new_appuser)

  def test_create__invalid(self):
    """We cannot create an account without an email address."""
    testing_config.sign_in('admin@example.com', 123567890)

    json_data = {'isAdmin': False}  # No email
    with register.app.test_request_context(self.request_path, json=json_data):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    new_appuser = (models.AppUser.query(models.AppUser.email == 'new@example.com').get())
    self.assertIsNone(new_appuser)

  def test_create__duplicate(self):
    """We cannot create an account with a duplicate email."""
    testing_config.sign_in('admin@example.com', 123567890)

    json_data = {'email': 'user@example.com'}
    with register.app.test_request_context(self.request_path, json=json_data):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    unrevised_appuser = models.AppUser.get_by_id(self.appuser_id)
    self.assertEqual('user@example.com', unrevised_appuser.email)

  def test_delete__valid(self):
    """Admin wants to delete an account."""
    testing_config.sign_in('admin@example.com', 123567890)

    with register.app.test_request_context(self.request_path):
      actual_json = self.handler.do_delete(self.appuser_id)
    self.assertEqual({'message': 'Done'}, actual_json)

    revised_appuser = models.AppUser.get_by_id(self.appuser_id)
    self.assertIsNone(revised_appuser)

  def test_delete__forbidden(self):
    """Regular user cannot delete an account."""
    testing_config.sign_in('one@example.com', 123567890)

    with register.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_delete(self.appuser_id)

    unrevised_appuser = models.AppUser.get_by_id(self.appuser_id)
    self.assertEqual('user@example.com', unrevised_appuser.email)

  def test_delete__invalid(self):
    """We cannot delete an account without an account_id."""
    testing_config.sign_in('admin@example.com', 123567890)

    with register.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_delete(None)

    unrevised_appuser = models.AppUser.get_by_id(self.appuser_id)
    self.assertEqual('user@example.com', unrevised_appuser.email)


  def test_delete__not_found(self):
    """We cannot delete an account with the wrong account_id."""
    testing_config.sign_in('admin@example.com', 123567890)

    with register.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_delete(self.appuser_id + 1)

    unrevised_appuser = models.AppUser.get_by_id(self.appuser_id)
    self.assertEqual('user@example.com', unrevised_appuser.email)
