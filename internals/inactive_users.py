import logging
from datetime import datetime, timedelta

from framework.basehandlers import FlaskHandler
from internals.user_models import AppUser

class RemoveInactiveUsersHandler(FlaskHandler):
  DEFAULT_LAST_VISIT = (2022, 8, 1)  # 2022-08-01
  INACTIVE_REMOVE_DAYS = 270

  def get_template_data(self, now=None):
    """Removes any users that have been inactive for 9 months."""
    self.require_cron_header()
    if now is None:
      now = datetime.now()

    q = AppUser.query()
    users = q.fetch()
    removed_users = []
    inactive_cutoff = now - timedelta(days=self.INACTIVE_REMOVE_DAYS)
    for user in users:
      # Site admins and editors are not removed for inactivity.
      if user.is_admin or user.is_site_editor:
        continue

      last_visit = user.last_visit
      # If the user does not have a last visit, it is assumed the last visit
      # is roughly the date the last_visit field was added.
      if last_visit is None:
        y, m, d = self.DEFAULT_LAST_VISIT
        last_visit = datetime(y, m, d)
      if last_visit < inactive_cutoff:
        removed_users.append(user.email)
        user.delete()

    logging.info(f'{len(removed_users)} inactive users removed.')
    removed_users_output = ['Success', 'Removed users:']
    for user in removed_users:
      removed_users_output.append(user)
    return '\n'.join(removed_users_output)
