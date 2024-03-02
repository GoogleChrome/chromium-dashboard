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

import logging
from datetime import datetime, timedelta

from framework.basehandlers import FlaskHandler
from internals.user_models import AppUser

class RemoveInactiveUsersHandler(FlaskHandler):
  DEFAULT_LAST_VISIT = datetime(2022, 8, 1)  # 2022-08-01
  INACTIVE_REMOVE_DAYS = 270

  def get_template_data(self, **kwargs):
    """Removes any users that have been inactive for 9 months."""
    self.require_cron_header()
    now = kwargs.get('now', datetime.now())

    q = AppUser.query()
    users: list[AppUser] = q.fetch()
    removed_users = []
    inactive_cutoff = now - timedelta(days=self.INACTIVE_REMOVE_DAYS)
    for user in users:
      # Site admins and editors are not removed for inactivity.
      if user.is_admin or user.is_site_editor:
        continue

      # If the user does not have a last visit, it is assumed the last visit
      # is either the account's creation date or the date the last_visit
      # field was created on the model - whatever is latest.
      last_visit = user.last_visit or self.DEFAULT_LAST_VISIT
      if user.created > last_visit:
        last_visit = user.created
      if last_visit < inactive_cutoff:
        removed_users.append(user.email)
        logging.info(f'User removed: {user.email}')
        user.delete()

    logging.info(f'{len(removed_users)} inactive users removed.')
    removed_users_output = ['Success', 'Removed users:']
    for user in removed_users:
      removed_users_output.append(user)
    return '\n'.join(removed_users_output)
