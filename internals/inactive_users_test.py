import collections
import json
import testing_config  # Must be imported before the module under test.
from datetime import datetime

import flask
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.
from google.cloud import ndb

from framework import users

from internals import approval_defs
from internals import core_enums
from internals import core_models
from internals import notifier
from internals import user_models
from internals.inactive_users import RemoveInactiveUsersHandler
import settings

class RemoveInactiveUsersHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.users = []
    active_user = user_models.AppUser(
      email="active_user@example.com", is_admin=False, is_site_editor=False,
      last_visit=datetime(2023, 8, 30))
    active_user.put()
    self.users.append(active_user)

    inactive_user = user_models.AppUser(
      email="inactive_user@example.com", is_admin=False, is_site_editor=False,
      last_visit=datetime(2023, 2, 20))
    inactive_user.put()
    self.users.append(inactive_user)

    really_inactive_user = user_models.AppUser(
      email="really_inactive_user@example.com", is_admin=False,
      is_site_editor=False, last_visit=datetime(2022, 10, 1))
    really_inactive_user.put()
    self.users.append(really_inactive_user)

    active_admin = user_models.AppUser(
      email="active_admin@example.com", is_admin=True, is_site_editor=True,
      last_visit=datetime(2023, 9, 30))
    active_admin.put()
    self.users.append(active_admin)

    inactive_admin = user_models.AppUser(
      email="inactive_admin@example.com", is_admin=True, is_site_editor=True,
      last_visit=datetime(2023, 3, 1))
    inactive_admin.put()
    self.users.append(inactive_admin)

    active_site_editor = user_models.AppUser(
      email="active_site_editor@example.com", is_admin=False,
      is_site_editor=True, last_visit=datetime(2023, 7, 30))
    active_site_editor.put()
    self.users.append(active_site_editor)

    inactive_site_editor = user_models.AppUser(
      email="inactive_site_editor@example.com", is_admin=False,
      is_site_editor=True, last_visit=datetime(2023, 2, 9))
    inactive_site_editor.put()
    self.users.append(inactive_site_editor)

  def tearDown(self):
    for user in self.users:
      user.key.delete()

  def test_remove_inactive_users(self):
    inactive_remover = RemoveInactiveUsersHandler()
    result = inactive_remover.get_template_data(now=datetime(2023, 9, 1))
    expected = 'Success\nRemoved users:\nreally_inactive_user@example.com'
    self.assertEqual(result, expected)
