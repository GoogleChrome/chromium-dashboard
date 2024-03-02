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
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import accounts_api
from internals import user_models

test_app = flask.Flask(__name__)


class AccountsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

    self.app_editor = user_models.AppUser(email='editor@example.com')
    self.app_editor.is_site_editor = True
    self.app_editor.put()

    self.appuser_1 = user_models.AppUser(email='user@example.com')
    self.appuser_1.put()
    self.appuser_id = self.appuser_1.key.integer_id()

    self.request_path = '/api/v0/accounts/%d' % self.appuser_id
    self.handler = accounts_api.AccountsAPI()

  def tearDown(self):
    self.appuser_1.key.delete()
    self.app_admin.key.delete()
    self.app_editor.key.delete()

  def test_create__normal_valid(self):
    """Admin wants to register a normal account."""
    testing_config.sign_in('admin@example.com', 123567890)

    json_data = {
      'email': 'new_user@example.com',
      'isAdmin': False, 'isSiteEditor': False}
    with test_app.test_request_context(self.request_path, json=json_data):
      actual_json = self.handler.do_post()
    self.assertEqual('new_user@example.com', actual_json['email'])
    self.assertFalse(actual_json['is_site_editor'])
    self.assertFalse(actual_json['is_admin'])

    new_appuser = (user_models.AppUser.query(
        user_models.AppUser.email == 'new_user@example.com').get())
    result_email = new_appuser.email
    result_is_admin = new_appuser.is_admin
    new_appuser.key.delete()
    self.assertEqual('new_user@example.com', result_email)
    self.assertFalse(result_is_admin)

  def test_create__site_editor_valid(self):
    """Admin wants to register a new site editor account."""
    testing_config.sign_in('admin@example.com', 123567890)

    json_data = {
      'email': 'new_site_editor@example.com',
      'isAdmin': False, 'isSiteEditor': True}
    with test_app.test_request_context(self.request_path, json=json_data):
      actual_json = self.handler.do_post()
    self.assertEqual('new_site_editor@example.com', actual_json['email'])
    self.assertFalse(actual_json['is_admin'])
    self.assertTrue(actual_json['is_site_editor'])

    new_appuser = user_models.AppUser.query(
        user_models.AppUser.email == 'new_site_editor@example.com').get()
    self.assertEqual('new_site_editor@example.com', new_appuser.email)
    self.assertTrue(new_appuser.is_site_editor)
    self.assertFalse(new_appuser.is_admin)

    # Clean up
    new_appuser.key.delete()

  def test_create__admin_valid(self):
    """Admin wants to register a new admin account."""
    testing_config.sign_in('admin@example.com', 123567890)

    json_data = {
      'email': 'new_admin@example.com',
      'isAdmin': True, 'isSiteEditor': True}
    with test_app.test_request_context(self.request_path, json=json_data):
      actual_json = self.handler.do_post()
    self.assertEqual('new_admin@example.com', actual_json['email'])
    self.assertTrue(actual_json['is_site_editor'])
    self.assertTrue(actual_json['is_admin'])

    new_appuser = user_models.AppUser.query(
        user_models.AppUser.email == 'new_admin@example.com').get()
    self.assertEqual('new_admin@example.com', new_appuser.email)
    self.assertTrue(new_appuser.is_admin)

    # Clean up
    new_appuser.key.delete()

  def test_create__forbidden(self):
    """Regular user cannot create an account."""
    testing_config.sign_in('one@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(self.appuser_id)

    new_appuser = user_models.AppUser.query(
        user_models.AppUser.email == 'new@example.com').get()
    self.assertIsNone(new_appuser)

  def test_create__site_editor_forbidden(self):
    """Site editors cannot create an account."""
    testing_config.sign_in('editor@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

    new_appuser = user_models.AppUser.query(
        user_models.AppUser.email == 'new@example.com').get()
    self.assertIsNone(new_appuser)

  def test_create__invalid(self):
    """We cannot create an account without an email address."""
    testing_config.sign_in('admin@example.com', 123567890)

    json_data = {'isAdmin': False}  # No email
    with test_app.test_request_context(self.request_path, json=json_data):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    new_appuser = user_models.AppUser.query(
        user_models.AppUser.email == 'new@example.com').get()
    self.assertIsNone(new_appuser)

  def test_create__duplicate(self):
    """We cannot create an account with a duplicate email."""
    testing_config.sign_in('admin@example.com', 123567890)

    json_data = {'email': 'user@example.com'}
    with test_app.test_request_context(self.request_path, json=json_data):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    unrevised_appuser = user_models.AppUser.get_by_id(self.appuser_id)
    self.assertEqual('user@example.com', unrevised_appuser.email)

  def test_delete__valid(self):
    """Admin wants to delete an account."""
    testing_config.sign_in('admin@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      actual_json = self.handler.do_delete(account_id=self.appuser_id)
    self.assertEqual({'message': 'Done'}, actual_json)

    revised_appuser = user_models.AppUser.get_by_id(self.appuser_id)
    self.assertIsNone(revised_appuser)

  def test_delete__forbidden(self):
    """Regular user cannot delete an account."""
    testing_config.sign_in('one@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_delete(account_id=self.appuser_id)

    unrevised_appuser = user_models.AppUser.get_by_id(self.appuser_id)
    self.assertEqual('user@example.com', unrevised_appuser.email)

  def test_delete__invalid(self):
    """We cannot delete an account without an account_id."""
    testing_config.sign_in('admin@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_delete()

    unrevised_appuser = user_models.AppUser.get_by_id(self.appuser_id)
    self.assertEqual('user@example.com', unrevised_appuser.email)


  def test_delete__not_found(self):
    """We cannot delete an account with the wrong account_id."""
    testing_config.sign_in('admin@example.com', 123567890)

    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_delete(account_id=self.appuser_id + 1)

    unrevised_appuser = user_models.AppUser.get_by_id(self.appuser_id)
    self.assertEqual('user@example.com', unrevised_appuser.email)
