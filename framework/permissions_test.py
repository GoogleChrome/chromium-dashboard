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

from unittest import mock
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
    __name__,
    [('/path', MockHandler),
     ],
    debug=True)


class PermissionFunctionTests(testing_config.CustomTestCase):

  def setUp(self):
    self.app_user = models.AppUser(email='registered@example.com')
    self.app_user.put()

    self.app_admin = models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

  def tearDown(self):
    self.app_user.delete()
    self.app_admin.delete()

  def check_function_results(
      self, func, additional_args,
      unregistered='missing', registered='missing',
      special='missing', admin='missing', anon='missing'):
    """Test func under four conditions and check expected results."""
    # Test unregistered users
    testing_config.sign_in('unregistered@example.com', 123)
    user = users.get_current_user()
    self.assertEqual(unregistered, func(user, *additional_args))

    # Test registered users
    testing_config.sign_in('registered@example.com', 123)
    user = users.get_current_user()
    self.assertEqual(registered, func(user, *additional_args))

    # Test special users
    # TODO(jrobbins): generalize this.
    testing_config.sign_in('user@google.com', 123)
    user = users.get_current_user()
    self.assertEqual(special, func(user, *additional_args))
    testing_config.sign_in('user@chromium.org', 123)
    user = users.get_current_user()
    self.assertEqual(special, func(user, *additional_args))

    # Test admin users
    testing_config.sign_in('admin@example.com', 123)
    user = users.get_current_user()
    self.assertEqual(admin, func(user, *additional_args))

    # Test anonymous visitors
    testing_config.sign_out()
    user = users.get_current_user()
    self.assertEqual(anon, func(user, *additional_args))

  def test_can_admin_site(self):
    self.check_function_results(
        permissions.can_admin_site, tuple(),
        unregistered=False, registered=False,
        special=False, admin=True, anon=False)

  def test_can_view_feature(self):
    self.check_function_results(
        permissions.can_view_feature, (None,),
        unregistered=True, registered=True,
        special=True, admin=True, anon=True)

  def test_can_create_feature(self):
    self.check_function_results(
        permissions.can_create_feature, tuple(),
        unregistered=False, registered=True,
        special=True, admin=True, anon=False)

  def test_can_edit_any_feature(self):
    self.check_function_results(
        permissions.can_edit_any_feature, tuple(),
        unregistered=False, registered=True,
        special=True, admin=True, anon=False)

  def test_can_edit_feature(self):
    self.check_function_results(
        permissions.can_edit_feature, (None,),
        unregistered=False, registered=True,
        special=True, admin=True, anon=False)

  def test_can_approve_feature(self):
    approvers = []
    self.check_function_results(
        permissions.can_approve_feature, (None, approvers),
        unregistered=False, registered=False,
        special=False, admin=True, anon=False)

    approvers = ['registered@example.com']
    self.check_function_results(
        permissions.can_approve_feature, (None, approvers),
        unregistered=False, registered=True,
        special=False, admin=True, anon=False)


class RequireAdminSiteTests(testing_config.CustomTestCase):

  def setUp(self):
    self.app_user = models.AppUser(email='registered@example.com')
    self.app_user.put()

    self.app_admin = models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

  def tearDown(self):
    self.app_user.delete()
    self.app_admin.delete()

  def test_require_admin_site__unregistered_user(self):
    """Wrapped method rejects call from an unregistered user."""
    handler = MockHandler()
    testing_config.sign_in('unregistered@example.com', 123)
    with test_app.test_request_context('/path', method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        handler.do_post()
    self.assertEqual(handler.called_with, None)

  def test_require_admin_site__registered_user(self):
    """Wrapped method rejects call from registered non-admin user."""
    handler = MockHandler()
    testing_config.sign_in('registered@example.com', 123)
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
    testing_config.sign_in('admin@example.com', 123)
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
