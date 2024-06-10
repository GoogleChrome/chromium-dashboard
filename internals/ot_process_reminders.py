# Copyright 2024 Google Inc.
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
import requests
import time
from datetime import datetime, date
from typing import Any

from framework import cloud_tasks_helpers
from framework import origin_trials_client
from internals.core_models import Stage

RELEASE_DATA_URL = 'https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone='

# Cache of release data
# Used to avoid multiple fetches from release data API.
release_cache: dict[str | int, dict[str, str]] = {}
trials = None


def build_trial_data(trial_data: dict[str, Any]) -> dict[str, Any] | None:
  """Find corresponding OT stage and assemble necessary info for reminders."""
  logging.info(f'Building trial data for {trial_data.get("id")}')
  trial_stage: Stage | None = Stage.query(
      Stage.origin_trial_id == trial_data['id']).get()
  if trial_stage is None:
    logging.exception(f'No stage found for trial {trial_data["id"]}')
    return None
  contact_list = trial_stage.ot_emails.copy()
  contact_list.append(trial_stage.ot_owner_email)
  contact_list = [s.strip() for s in contact_list if s]

  # Remove duplicates
  contact_list = list(set(contact_list))

  trial_info = {
    'id': trial_data['id'],
    'name': trial_data['display_name'],
    'start_milestone': int(trial_data['start_milestone']),
    'end_milestone': int(trial_data['end_milestone']),
    'contacts': contact_list,
  }
  return trial_info


def get_trials(release: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
  """Assemble information about trials that are starting or ending this release."""
  trials_list = origin_trials_client.get_trials_list()
  starting_trials = []
  ending_trials = []

  for trial in trials_list:
    start_milestone = int(trial['start_milestone'])
    end_milestone = int(trial['end_milestone'])

    matches_start = start_milestone == release
    matches_end = end_milestone == release
    trial_info = None

    if matches_start or matches_end:
      trial_info = build_trial_data(trial)
      if not trial_info:
        continue

      if matches_start:
        starting_trials.append(trial_info)

      if matches_end:
        ending_trials.append(trial_info)

  return starting_trials, ending_trials


def send_email_reminders() -> str:
  """Main function for sending information about OT process reminders."""
  today = datetime.now().date()
  next_branch_release = get_next_branch_release(today)
  current_stable_release = get_current_stable_release(today)
  next_stable_release = get_release(get_next_release_number(get_milestone(current_stable_release)))

  send_count = 0

  next_branch_date = get_branch_date(next_branch_release)
  time_to_next_branch = diff_weeks(next_branch_date, today)

  if time_to_next_branch == 0:  # The next version is branching
    send_count += send_branch_emails(get_milestone(next_branch_release), next_branch_date)

  time_to_next_beta = diff_weeks(get_beta_date(next_stable_release), today)
  if time_to_next_beta == 0:
    send_count += send_beta_availability_emails(get_milestone(next_stable_release))

  time_since_last_stable = diff_weeks(today, get_stable_date(current_stable_release))
  if time_since_last_stable == 1:
    send_count += send_stable_update_emails(get_milestone(current_stable_release))

  params = {
    'branch_date': format_date_for_email(today),
    'send_count': send_count,
    'next_branch_milestone': get_milestone(next_branch_release),
    'next_branch_date': format_date_for_email(next_branch_date),
    'stable_milestone': get_milestone(current_stable_release),
    'stable_date': format_date_for_email(
        get_stable_date(current_stable_release))
  }
  cloud_tasks_helpers.enqueue_task('/tasks/email-ot-automated-process', params)
  return f'Submitted {send_count} total OT process reminder tasks.'


def send_branch_emails(release: int, next_branch_date: date) -> int:
  """Send reminders about trials that are first branching or are in their last milestone"""
  starting_trials, ending_trials = get_trials(release)
  formatted_branch_date = format_date_for_email(next_branch_date) if next_branch_date else 'soon'
  num_branching_trials = len(starting_trials)

  logging.info('Currently branching - '
               f'{num_branching_trials} emails to send')
  for trial in starting_trials:
    params = {
      'name': trial['name'],
      'release_milestone': release,
      'branch_date': formatted_branch_date,
      'contacts': trial['contacts'],
    }
    cloud_tasks_helpers.enqueue_task(
        '/tasks/email-ot-first-branch', params)

  num_last_release_trials = len(ending_trials)
  logging.info('Entering last release - '
               f'{num_last_release_trials} emails to send')
  for trial in ending_trials:
    params = {
      'name': trial['name'],
      'release_milestone': release,
      'branch_date': formatted_branch_date,
      'contacts': trial['contacts'],
    }
    cloud_tasks_helpers.enqueue_task(
      '/tasks/email-ot-last-branch', params)
  return num_branching_trials + num_last_release_trials


def send_beta_availability_emails(release):
  """Send reminders about trials that are entering beta."""
  trials_entering_beta, _ = get_trials(release)
  for trial in trials_entering_beta:
    params = {
      'name': trial['name'],
      'release_milestone': release,
      'contacts': trial['contacts'],
    }
    cloud_tasks_helpers.enqueue_task(
        '/tasks/email-ot-beta-availability', params)
  send_count = len(trials_entering_beta)
  logging.info(f'sendBetaAvailabilityEmail: {send_count} emails to send')
  return send_count


def send_stable_update_emails(release):
  """Send reminders about trials that are entering stable."""
  trial_end_release = get_next_release_number(get_next_release_number(release))
  after_end_release = get_next_release_number(trial_end_release)
  after_end_branch_date = get_branch_date(get_release(after_end_release))
  formatted_branch_date = format_date_for_email(after_end_branch_date) if after_end_branch_date else 'in 4-6 weeks'

  _, trials_ending_in_next_release = get_trials(trial_end_release)
  for trial in trials_ending_in_next_release:
    params = {
      'name': trial['name'],
      'release_milestone': release,
      'after_end_release': after_end_release,
      'after_end_date': formatted_branch_date,
      'contacts': trial['contacts'],
    }
    cloud_tasks_helpers.enqueue_task(
        '/tasks/email-ot-ending-next-release', params)
  end_in_next_release_count = len(trials_ending_in_next_release)
  logging.info('Ending next release reminders - '
               f'{end_in_next_release_count} emails to send')

  _, trials_ending_this_release = get_trials(release)
  next_release = get_next_release_number(release)
  for trial in trials_ending_this_release:
    params = {
      'name': trial['name'],
      'release_milestone': release,
      'next_release': next_release,
    }
  # TODO(DanielRyanSmith): Determine if this notification should be added.
  #   cloud_tasks_helpers.enqueue_task(
  #       '/tasks/email-ot-ending-this-release', params)
  # close_to_end_count = len(trials_ending_this_release)
  # logging.info('Ending this release reminders - '
  #              f'{close_to_end_count} emails to send')
  return end_in_next_release_count


def get_release(release: str | int) -> dict[str, str]:
  """Get Chromium release information based on a given milestone."""
  if release in release_cache:
    return release_cache[release]

  release_info = fetch_release(f'{RELEASE_DATA_URL}{release}')
  mstone = release_info['mstones'][0]
  release_cache[release] = mstone

  if release == 'current':
    actual_release_number = get_milestone(mstone)
    release_cache[actual_release_number] = mstone

  return mstone


def get_next_branch_release(today: date):
  """Calculate the the next branch release milestone."""
  start = get_release('current')
  start_branch_date = get_branch_date(start)
  start_milestone = get_milestone(start)

  if diff_days(start_branch_date, today) >= 0:
    #  branch date is in the future so this is the next branch
    return start

  version_num = get_next_release_number(start_milestone)
  next_version = get_release(version_num)
  version_branch_date = get_branch_date(next_version)

  while diff_days(version_branch_date, today) < 0:
    version_num = get_next_release_number(version_num)
    next_version = get_release(version_num)
    version_branch_date = get_branch_date(next_version)

  return next_version


def get_current_stable_release(today: date):
  """Calculate the the current stable release milestone."""
  start = get_release('current')
  start_stable_date = get_stable_date(start)
  start_milestone = get_milestone(start)
  if diff_days(start_stable_date, today) <= 0:
    return start

  version_num = get_previous_release_number(start_milestone)
  next_version = get_release(version_num)
  version_stable_date = get_stable_date(next_version)

  while diff_days(version_stable_date, today) > 0:
    version_num = get_previous_release_number(version_num)
    next_version = get_release(version_num)
    version_stable_date = get_stable_date(next_version)

  return next_version


def get_next_release_number(version_num: int) -> int:
  """Get the next milestone number, skipping milestone 82."""
  if version_num == 81:
    return 83
  return version_num + 1


def get_previous_release_number(version_num):
  """Get the previous milestone number, skipping milestone 82."""
  if version_num == 83:
    return 81
  return version_num - 1


def get_branch_date(release_json: dict[str, str]) -> date:
  """Create a datetime object for the branch point of the given release."""
  return datetime.strptime(release_json['branch_point'].split('T')[0],
                           "%Y-%m-%d").date()


def get_beta_date(release_json: dict[str, str]) -> date:
  """Create a datetime object for the earliest beta of the given release."""
  return datetime.strptime(release_json['earliest_beta'].split('T')[0],
                           "%Y-%m-%d").date()


def get_stable_date(release_json: dict[str, str]) -> date:
  """Create a datetime object for the stable date of the given release."""
  return datetime.strptime(release_json['stable_date'].split('T')[0],
                           "%Y-%m-%d").date()


def get_milestone(release_json: dict[str, str]) -> int:
  """Read milestone from release info and convert to integer."""
  return int(release_json['mstone'])


def diff_weeks(t1: date, t2: date) -> int:
  """Get the difference in weeks for two given dates."""
  day_diff = diff_days(t1, t2)
  return day_diff // 7


def diff_days(t1: date, t2: date) -> int:
  """Get the difference in days for two given dates."""
  return (t1 - t2).days


def format_date(time_stamp):
  """Format a datetime object into a date string."""
  if not isinstance(time_stamp, date):
    return ''
  return time_stamp.strftime("%Y-%m-%d")


def format_date_for_email(time_stamp):
  """Format a datetime object into a readable date for emails."""
  if not isinstance(time_stamp, date):
    return ''
  return time_stamp.strftime("%A, %B %d, %Y")


def fetch_release(url, retry=5, timeout=2):
  """Attempt obtaining release information, retrying as needed."""
  if retry == 0:
    raise ValueError(f'Exceeded retry limit for {url}')
  try:
    response = requests.get(url)
    if response.status_code != 200:
      time.sleep(timeout)
      return fetch_release(url, retry - 1, timeout * 2)
    return response.json()
  except requests.RequestException:
    time.sleep(timeout)
    return fetch_release(url, retry - 1, timeout * 2)
  # It should never get this far in practice
