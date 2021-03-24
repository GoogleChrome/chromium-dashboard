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

from framework import permissions


class MockHandler(object):

  def __init__(self):
    self.called_with = None

  @permissions.require_admin_site
  def do_get(self, *args):
    self.called_with = args


class CanAdminSiteTests(unittest.TestCase):

  def test_can_admin_site__normal_user(self):
    """A normal user is not allowed to administer the site."""
    testing_config.sign_in('user@example.com', 123)
    self.assertFalse(permissions.can_admin_site())

  def test_can_admin_site__admin_user(self):
    """An admin user is allowed to administer the site."""
    testing_config.sign_in('user@example.com', 123, is_admin=True)
    self.assertTrue(permissions.can_admin_site())

  def test_can_admin_site__anon(self):
    """An anon visitor is not allowed to administer the site."""
    testing_config.sign_out()
    self.assertFalse(permissions.can_admin_site())


class RequireAdminSiteTests(unittest.TestCase):

  def test_require_admin_site__normal_user(self):
    """Wrapped method rejects call from normal user."""
    handler = MockHandler()
    testing_config.sign_in('user@example.com', 123)
    with self.assertRaises(werkzeug.exceptions.Forbidden):
      handler.do_get()
    self.assertEqual(handler.called_with, None)

  def test_require_admin_site__normal_user(self):
    """Wrapped method rejects call from normal user."""
    handler = MockHandler()
    testing_config.sign_in('admin@example.com', 123, is_admin=True)
    handler.do_get()
    self.assertEqual(handler.called_with, tuple())

  def test_require_admin_site__anon(self):
    """Wrapped method rejects call from anon."""
    handler = MockHandler()
    testing_config.sign_out()
    with self.assertRaises(werkzeug.exceptions.Forbidden):
      handler.do_get()
    self.assertEqual(handler.called_with, None)
