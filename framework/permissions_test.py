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

import unittest
import testing_config  # Must be imported before the module under test.

import mock
import werkzeug.exceptions  # Flask HTTP stuff.

# from google.appengine.api import users
from framework import users

from framework import basehandlers
from framework import permissions
from internals import models


class MockHandler(basehandlers.BaseHandler):

  def __init__(self):
    self.called_with = None

  @permissions.require_admin_site
  def do_get(self, *args):
    self.called_with = args
    return {'message': 'did get'}

  @permissions.require_admin_site
  def do_post(self, *args):
    self.called_with = args
    return {'message': 'did post'}


test_app = basehandlers.FlaskApplication(
    [('/path', MockHandler),
     ],
    debug=True)


class PermissionFunctionTests(unittest.TestCase):

  def check_function_results(
      self, func, additional_args,
      normal='missing', special='missing', admin='missing', anon='missing'):
    """Test func under four conditions and check expected results."""
    # Test normal users
    testing_config.sign_in('user@example.com', 123)
    user = users.get_current_user()
    self.assertEqual(normal, func(user, *additional_args))

    # Test special users
    # TODO(jrobbins): generalize this.
    testing_config.sign_in('user@google.com', 123)
    user = users.get_current_user()
    self.assertEqual(special, func(user, *additional_args))
    testing_config.sign_in('user@chromium.org', 123)
    user = users.get_current_user()
    self.assertEqual(special, func(user, *additional_args))

    # Test admin users
    testing_config.sign_in('user@example.com', 123, is_admin=True)
    user = users.get_current_user()
    self.assertEqual(admin, func(user, *additional_args))

    # Test anonymous visitors
    testing_config.sign_out()
    user = users.get_current_user()
    self.assertEqual(anon, func(user, *additional_args))

  def test_can_admin_site(self):
    self.check_function_results(
        permissions.can_admin_site, tuple(),
        normal=False, special=False, admin=True, anon=False)

  def test_can_admin_site__appuser(self):
    """A registered AppUser that has is_admin set can admin the site."""
    email = 'app-admin@example.com'
    testing_config.sign_in(email, 111)
    user = users.get_current_user()

    # Make sure there is no left over entity from past runs.
    query = models.AppUser.query(models.AppUser.email == email)
    for old_app_user in query.fetch(None):
      old_app_user.key.delete()

    self.assertFalse(permissions.can_admin_site(user))

    app_user = models.AppUser(email=email)
    app_user.put()
    self.assertFalse(permissions.can_admin_site(user))

    app_user.is_admin = True
    app_user.put()
    print('user is %r' % user)
    print('get_app_user is %r' % models.AppUser.get_app_user(email))
    print('get_app_user.is_admin is %r' % models.AppUser.get_app_user(email).is_admin)
    self.assertTrue(permissions.can_admin_site(user))

  def test_can_view_feature(self):
    self.check_function_results(
        permissions.can_view_feature, (None,),
        normal=True, special=True, admin=True, anon=True)

  def test_can_create_feature(self):
    self.check_function_results(
        permissions.can_create_feature, tuple(),
        normal=False, special=True, admin=True, anon=False)

  def test_can_edit_any_feature(self):
    self.check_function_results(
        permissions.can_edit_any_feature, tuple(),
        normal=False, special=True, admin=True, anon=False)

  def test_can_edit_feature(self):
    self.check_function_results(
        permissions.can_edit_feature, (None,),
        normal=False, special=True, admin=True, anon=False)

  def test_can_approve_feature(self):
    approvers = []
    self.check_function_results(
        permissions.can_approve_feature, (None, approvers),
        normal=False, special=False, admin=True, anon=False)

    approvers = ['user@example.com']
    self.check_function_results(
        permissions.can_approve_feature, (None, approvers),
        normal=True, special=False, admin=True, anon=False)


class RequireAdminSiteTests(unittest.TestCase):

  def test_require_admin_site__normal_user(self):
    """Wrapped method rejects call from normal user."""
    handler = MockHandler()
    testing_config.sign_in('user@example.com', 123)
    with test_app.test_request_context('/path', method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        handler.do_post()
    self.assertEqual(handler.called_with, None)

  def test_require_admin_site__googler(self):
    """Wrapped method rejects call from googler."""
    handler = MockHandler()
    testing_config.sign_in('user@google.com', 123)
    with test_app.test_request_context('/path', method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        handler.do_post()
    self.assertEqual(handler.called_with, None)

  def test_require_admin_site__admin(self):
    """Wrapped method accepts call from an admin user."""
    handler = MockHandler()
    testing_config.sign_in('admin@example.com', 123, is_admin=True)
    with test_app.test_request_context('/path'):
      actual_response = handler.do_get(123, 234)
    self.assertEqual(handler.called_with, (123, 234))
    self.assertEqual({'message': 'did get'}, actual_response)

    with test_app.test_request_context('/path', method='POST'):
      actual_response = handler.do_post(345, 456)
    self.assertEqual(handler.called_with, (345, 456))
    self.assertEqual({'message': 'did post'}, actual_response)

  def test_require_admin_site__anon(self):
    """Wrapped method rejects call from anon, but offers sign-in."""
    handler = MockHandler()
    testing_config.sign_out()
    with test_app.test_request_context('/path'):
      actual_response = handler.do_get(123, 234)
    self.assertEqual(handler.called_with, None)
    self.assertEqual(302, actual_response.status_code)

    with test_app.test_request_context('/path', method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        handler.do_post(345, 456)
    self.assertEqual(handler.called_with, None)
