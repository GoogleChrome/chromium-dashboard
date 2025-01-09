# Copyright 2023 Google Inc.
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

import datetime
import logging
import pytz

from framework import permissions
from framework.users import User
from internals.core_models import FeatureEntry
from internals.review_models import Gate, Vote

PACIFIC_TZ = pytz.timezone('US/Pacific')
MAX_DAYS = 30


def is_weekday(d: datetime.datetime) -> bool:
  """Return True if d is a weekday: Monday through Friday."""
  return d.weekday() < 5


def weekdays_between(start: datetime.datetime, end: datetime.datetime) -> int:
  """Return the number of Pacific timezone weekdays between two UTC dates."""
  # If the difference is big, just approximate.
  calendar_days = (end - start).days
  if calendar_days > MAX_DAYS:
    return calendar_days * 5 // 7

  d_ptz = start.astimezone(PACIFIC_TZ)
  # The day of the request does not count.
  d_ptz = d_ptz.replace(hour=23, minute=59, second=59)
  end_ptz = end.astimezone(tz=PACIFIC_TZ)
  weekday_counter = 0
  while d_ptz < end_ptz and weekday_counter < MAX_DAYS:
    d_ptz = d_ptz + datetime.timedelta(days=1)
    if is_weekday(d_ptz):
      weekday_counter += 1

  return weekday_counter


def now_utc() -> datetime.datetime:
  """A mockable version of datetime.datetime.now()."""
  return datetime.datetime.now()


def remaining_days(requested_on: datetime.datetime, slo_limit: int) -> int:
  """Return the number of weekdays before the SLO deadline is reached."""
  # Positive: There are days remaining.
  # Zero: The review is due today.
  # Negative: The review is overdue.
  return slo_limit - weekdays_between(requested_on, now_utc())


def record_vote(gate: Gate, votes: list[Vote], old_gate_state: int) -> bool:
  """Record a Gate SLO response time if needed.  Return True if changed."""
  if not votes:
    return False
  latest_vote = sorted(votes, key=lambda v: v.set_on)[-1]
  latest_state = latest_vote.state

  if latest_state == Vote.NO_RESPONSE:
    return False  # NO_RESPONSE never changes SLO state.

  changed = False
  if latest_state in Vote.REQUESTING_STATES:
    if gate.requested_on is None:
      logging.info('SLO: Someone requested a new review')
      gate.requested_on = latest_vote.set_on
      changed = True

  if latest_state in Vote.RESPONSE_STATES:
    if gate.responded_on is None:
      logging.info('SLO: Got reviewer vote as initial response')
      gate.responded_on = latest_vote.set_on
      if gate.requested_on is None:
        logging.info('SLO: Reviewer is the person initiating the review')
        gate.requested_on = latest_vote.set_on
      changed = True

  sent_back_for_rework = (
      old_gate_state != Vote.NEEDS_WORK and
      gate.state == Vote.NEEDS_WORK and
      gate.needs_work_started_on is None)
  finished_rework = (
      old_gate_state == Vote.NEEDS_WORK and
      gate.state != Vote.NEEDS_WORK and
      gate.needs_work_started_on is not None)
  resolved = (
      old_gate_state not in Vote.FINAL_STATES and
      gate.state in Vote.FINAL_STATES and
      gate.resolved_on is None)

  if finished_rework:
      logging.info('SLO: It is the reviewers turn again')
      # We count any time spent in NEEDS_WORK state as being
      # at least one weekday.
      turn_length_weekdays = max(1, weekdays_between(
          gate.needs_work_started_on, latest_vote.set_on))
      gate.needs_work_elapsed = (
          (gate.needs_work_elapsed or 0) + turn_length_weekdays)
      gate.needs_work_started_on = None
      changed = True

  if sent_back_for_rework:
      logging.info('SLO: It is now the feature owners turn')
      gate.needs_work_started_on = latest_vote.set_on
      changed = True

  if resolved:
    if gate.resolved_on is None:
      logging.info('SLO: This review is done')
      gate.resolved_on = latest_vote.set_on
      changed = True

  return changed


def record_comment(
    feature: FeatureEntry, gate: Gate, user: User,
    approvers: list[str]) -> bool:
  """Record Gate SLO response time if needed. Return True if changed."""
  if gate.requested_on is None:
    return False  # Review has not been requested yet.
  elif gate.responded_on is not None:
    return False  # We already recorded the time of the initial response.
  else:
    is_approver = permissions.can_review_gate(user, feature, gate, approvers)
    if is_approver:
      logging.info('SLO: Got reviewer comment as initial response')
      gate.responded_on = now_utc()
      return True

  return False


def get_active_gates() -> list[Gate]:
  """Return a list of gates with active reviews."""
  active_gates = Gate.query(Gate.state.IN(Gate.PENDING_STATES)).fetch()
  return active_gates
