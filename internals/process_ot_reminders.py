import json
import logging
import requests
import time
from datetime import datetime, date
from typing import Any

from framework import origin_trials_client
from internals.core_models import Stage

RELEASE_DATA_URL = 'https://chromiumdash.appspot.com/fetch_milestone_schedule?mstone='
ORIGIN_TRIALS_TEAM_ADDRESS = 'origin-trials-core+processreminders@google.com'

# Addresses that are copied on all emails.
GLOBAL_CC_LIST = [
  ORIGIN_TRIALS_TEAM_ADDRESS, 'origin-trials-timeline-updates@google.com'
]

# Cache of release data
# Used to avoid multiple fetches from release data API.
release_cache: dict[str | int, dict[str, str]] = {}
trials = None


def build_trial_data(trial_data: dict[str, Any]) -> dict[str, Any] | None:
  trial_stage: Stage | None = Stage.query(
      Stage.origin_trial_id == trial_data['id']).get()
  if trial_stage is None:
    logging.exception(f'No stage found for trial {trial_data["id"]}')
    return None
  contact_list = [trial_stage.ot_owner_email]
  contact_list.extend(trial_stage.ot_emails)
  contact_list = [s.strip() for s in contact_list]

  # Remove duplicates
  contact_list = list(set(contact_list))

  trial_info = {
    'id': trial_data['id'],
    'name': trial_data['display_name'],
    'start_milestone': int(trial_data['start_milestone']),
    'end_milestone': int(trial_data['end_milestone']),
    'contacts': contact_list
  }
  return trial_info


# Assemble information about trials that are starting or ending this release.
def get_trials(release: int) -> dict[str, list[Any]]:
  trials_list = origin_trials_client.get_trials_list()

  release_trials: dict[str, list[Any]] = {
    'starting_trials': [],
    'ending_trials': [],
  }

  for trial in trials_list:
    start_milestone = int(trial['start_milestone'])
    end_milestone = int(trial['end_milestone'])

    if not (start_milestone or end_milestone):
      continue

    matches_start = start_milestone == release
    matches_end = end_milestone == release
    trial_info = None

    if matches_start or matches_end:
      trial_info = build_trial_data(trial)
      if not trial_info:
        continue

      if matches_start:
        release_trials['starting_trials'].append(trial_info)

      if matches_end:
        release_trials['ending_trials'].append(trial_info)

  return release_trials


def send_email_reminders() -> None:
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
    send_count += send_beta_availability_email(get_milestone(next_stable_release))

  time_to_next_stable = diff_weeks(get_stable_date(next_stable_release), today)
  if time_to_next_stable == 0:
    send_count += send_stable_emails(get_milestone(next_stable_release))

  time_since_last_stable = diff_weeks(today, get_stable_date(current_stable_release))
  if time_since_last_stable == 1:
    send_count += send_stable_update_email(get_milestone(current_stable_release))

  subject = 'Origin trials automated process reminder just ran'
  message = """
  Hello! This is your friendly neighborhood <strong>automated reminder script</strong> here. I just ran on {} and
  identified the following facts:
  <ul>
    <li>The next release to branch is <strong>M{}</strong> on {}.</li>
    <li>The current stable release is <strong>M{}</strong> as of {}</li>
    <li>There are <strong>{}</strong> emails to be sent.</li>
  </ul>
  Could you please double check my work and make sure I sent the right emails?
  I'm looking forward to slowly replacing you through the <strong>inexorable tide</strong> of automation!<br /><br />
  <3<br /><br />
  -Your future robot overlord.
  """.format(format_date_for_email(today), get_milestone(next_branch_release), format_date_for_email(next_branch_date),
        get_milestone(current_stable_release), format_date_for_email(get_stable_date(current_stable_release)),
        send_count)

  # MailApp.sendEmail(ORIGIN_TRIALS_TEAM_ADDRESS, subject, '', {'htmlBody': message})
  # TODO(DanielRyanSmith): send actual email.


def send_emails(trials, release, subject_postfix, message_postfix) -> int:
  send_count = 0
  for trial in trials:
    subject = trial['name'] + ' ' + subject_postfix
    message = """
    According to go/chrome-schedule, Chrome {} {}<br /><br />P.S. This email was generated automatically (for
    details, see <a href='http://go/running-an-origin-trial'>go/running-an-origin-trial</a>).
    Please contact origin-trials-core@google.com if this email is incorrect or not useful.
    """.format(release, message_postfix)

    # MailApp.sendEmail(','.join(trial['contacts']), subject, '', {'htmlBody': message, 'cc': GLOBAL_CC_LIST})
    # TODO(DanielRyanSmith): send actual email.
    send_count += 1

  return send_count


def send_branch_emails(release: int, next_branch_date: date):
  all_trials = get_trials(release)
  currently_branching_trials = all_trials['starting_trials']

  formatted_branch_date = format_date_for_email(next_branch_date) if next_branch_date else 'soon'
  subject_postfix = 'origin trial is branching'
  message = """
  Branch is {}. This release will contain your feature as an origin trial.<br /><br />
  You should aim to post a blog post on https://developer.chrome.com/blog/ as
  soon as possible so you can begin to get origin trials sign ups early
  (which means you get feedback earlier!). If you are already working with
  someone from Chrome Web Developer Relations they can help you with this.
  Otherwise, reach out to chrome-devrel-content@google.com for help.
  """.format(formatted_branch_date)

  send_count = send_emails(currently_branching_trials, release, subject_postfix, message)
  logging.info('sendBranchEmails: currently branching - {} emails to send'.format(send_count))

  trials_entering_last_release = all_trials['ending_trials']
  subject_postfix = 'origin trial has branched for its last release'
  message = """
  Is branching {}. This release will be the final one to include your feature as an origin trial.<br /><br />
  Code you land from here on will land in the first release after the origin trial is over.
  """.format(formatted_branch_date)

  last_release_count = send_emails(trials_entering_last_release, release, subject_postfix, message)
  send_count += last_release_count

  logging.info('sendBranchEmails: entering last release - {} emails to send'.format(last_release_count))
  return send_count


def send_beta_availability_email(release):
  trials_entering_beta = get_trials(release)['starting_trials']
  subject_postfix = 'origin trial is entering beta'
  message = """
  Will soon arrive on the beta channel.<br /><br />
  Check that your feature shows up correctly under the origin trials section of
  the roadmap https://chromestatus.com/roadmap. This will automatically get it
  included in the blog post about Chrome {} beta, which will go live on
  https://developer.chrome.com/tags/beta/. If you previously published a blog
  post allowing developers to sign up for tokens for your feature, this will be
  linked in the beta blog post.
  """.format(release)

  send_count = send_emails(trials_entering_beta, release, subject_postfix, message)
  logging.info('sendBetaAvailabilityEmail: {} emails to send'.format(send_count))
  return send_count


def send_stable_emails(release):
  # Currently we don't send any comms around this event
  return 0


def send_stable_update_email(release):
  trial_end_release = get_next_release_number(get_next_release_number(release))
  after_end_release = get_next_release_number(trial_end_release)
  after_end_branch_date = get_branch_date(get_release(after_end_release))

  formatted_branch_date = format_date_for_email(after_end_branch_date) if after_end_branch_date else 'in 4-6 weeks'
  trials_ending_in_next_release = get_trials(trial_end_release)['ending_trials']
  subject_postfix = 'origin trial ship decision approaching'
  message = """
  Landed on the stable channel one week ago. The branch point of Chrome {} occurs {},
  which will be the first release after the end of your trial.<br /><br />
  This is the point to be making the decision about what happens at the end of the
  trial. Options include:
  <ol>
    <li>Ship the feature, which requires an Intent to Ship</li>
    <li>Continue experimenting with the feature in a new trial, which requires an
    Intent to Continue Experimenting</li>
    <li>Let the origin trial finish and be disabled in Chrome {}.</li>
  </ol>
  """.format(after_end_release, formatted_branch_date, after_end_release)

  send_count = send_emails(trials_ending_in_next_release, release, subject_postfix, message)
  logging.info('sendStableUpdateEmail: ending next release - {} emails to send'.format(send_count))

  trials_ending_this_release = get_trials(release)['ending_trials']
  subject_postfix = 'origin trial needs blink-dev update'
  message = """
  Landed on the stable channel one week ago so you should have now shared with blink-dev the things you’ve learned based on the feedback gathered from developers during token renewal.
  Also, you should share your plans for Chrome {}, which will be the first release after the end of your trial.
  """.format(get_next_release_number(release))

  # close_to_end_count = send_emails(trials_ending_this_release, release, subject_postfix, message)
  # send_count += close_to_end_count
  # logging.info('sendStableUpdateEmail: ending this release - {} emails to send'.format(close_to_end_count))
  return send_count


def get_release(release: str | int) -> dict[str, str]:
  if release in release_cache:
    return release_cache[release]

  res = fetch_release(RELEASE_DATA_URL + release)
  mstone = json.loads(res)['mstones'][0]
  release_cache[release] = mstone

  if release == 'current':
    actual_release_number = get_milestone(mstone)
    release_cache[actual_release_number] = mstone

  return mstone


def get_next_branch_release(today: date):
  start = get_release('current')
  start_branch_date = get_branch_date(start)
  start_milestone = get_milestone(start)

  if (start_branch_date - today).days >= 0:
    return start

  version_num = get_next_release_number(start_milestone)
  next_version = get_release(version_num)
  version_branch_date = get_branch_date(next_version)

  while (version_branch_date - today).days < 0:
    version_num = get_next_release_number(version_num)
    next_version = get_release(version_num)
    version_branch_date = get_branch_date(next_version)

  return next_version


def get_current_stable_release(today: date):
  start = get_release('current')
  start_stable_date = get_stable_date(start)
  start_milestone = get_milestone(start)

  if (start_stable_date - today).days <= 0:
    return start

  version_num = get_previous_release_number(start_milestone)
  next_version = get_release(version_num)
  version_stable_date = get_stable_date(next_version)

  while (version_stable_date - today).days > 0:
    version_num = get_previous_release_number(version_num)
    next_version = get_release(version_num)
    version_stable_date = get_stable_date(next_version)

  return next_version


def get_next_release_number(version_num: int) -> int:
  if version_num == 81:
    return 83
  return version_num + 1


def get_previous_release_number(version_num):
  if version_num == 83:
    return 81
  return version_num - 1


def get_branch_date(release_json: dict[str, str]) -> date:
  return datetime.strptime(release_json['branch_point'], "%Y-%m-%d").date()


def get_beta_date(release_json: dict[str, str]) -> date:
  return datetime.strptime(release_json['earliest_beta'], "%Y-%m-%d").date()


def get_stable_date(release_json: dict[str, str]) -> date:
  return datetime.strptime(release_json['stable_date'], "%Y-%m-%d").date()


def get_milestone(release_json: dict[str, str]) -> int:
  return int(release_json['mstone'])


def diff_weeks(t1: date, t2: date) -> int:
  day_diff = diff_days(t1, t2)
  return day_diff // 7


def diff_days(t1: date, t2: date) -> int:
  return (t1 - t2).days


def format_date(time_stamp):
  if not isinstance(time_stamp, datetime):
    return ''
  return time_stamp.strftime("%Y-%m-%d")


def format_date_for_email(time_stamp):
  if not isinstance(time_stamp, datetime):
    return ''
  return time_stamp.strftime("%A, %B %d, %Y")


def fetch_release(url, retry=5, timeout=2):
  if retry == 0:
    raise ValueError(f'Exceeded retry limit for {url}')
  try:
    response = requests.get(url)
    if response.status_code != 200:
      time.sleep(timeout)
      return fetch_release(url, retry - 1, timeout * 2)
    return response.getContentText()
  except requests.RequestException:
    time.sleep(timeout)
    return fetch_release(url, retry - 1, timeout * 2)
  # It should never get this far, in practice
