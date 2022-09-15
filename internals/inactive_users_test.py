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
from datetime import datetime

from internals import user_models
from internals.inactive_users import RemoveInactiveUsersHandler

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
