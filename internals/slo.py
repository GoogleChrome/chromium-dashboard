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
MAX_DAYS = 9999


def is_weekday(d: datetime.datetime) -> bool:
  """Return True if d is a weekday: Monday through Friday."""
  return d.weekday() < 5


def weekdays_between(start: datetime.datetime, end: datetime.datetime) -> int:
  """Return the number of Pacific timezone weekdays between two UTC dates."""
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


def record_vote(gate: Gate, votes: list[Vote]) -> bool:
  """Record a Gate SLO response time if needed.  Return True if changed."""
  if gate.requested_on is None:
    return False  # Review has not been requested yet.
  elif gate.responded_on is not None:
    return False  # We already recorded the time of the initial response.
  elif not votes:
    return False  # No votes yet
  else:
    recent_vote_time = max(v.set_on for v in votes)
    if recent_vote_time > gate.requested_on:
      logging.info('SLO: Got reviewer vote as initial response')
      gate.responded_on = recent_vote_time
      return True

  return False


def record_comment(
    feature: FeatureEntry, gate: Gate, user: User,
    approvers: list[str]) -> bool:
  """Record Gate SLO response time if needed. Return True if changed."""
  if gate.requested_on is None:
    return False  # Review has not been requested yet.
  elif gate.responded_on is not None:
    return False  # We already recorded the time of the initial response.
  else:
    is_approver = permissions.can_approve_feature(user, feature, approvers)
    if is_approver:
      logging.info('SLO: Got reviewer comment as initial response')
      gate.responded_on = now_utc()
      return True

  return False


def is_gate_overdue(gate, appr_fields, default_slo_limit) -> bool:
  """Return True if a gate's review is overdue."""
  if gate.requested_on is None or gate.responded_on is not None:
    return False
  appr_def = appr_fields.get(gate.gate_type)
  slo_limit = (appr_def.slo_initial_response
               if appr_def else default_slo_limit)
  return remaining_days(gate.requested_on, slo_limit) < 0


def get_overdue_gates(appr_fields, default_slo_limit):
  """Return a list of gates with overdue reviews."""
  active_gates = Gate.query(Gate.state.IN(Gate.PENDING_STATES))
  overdue_gates = [g for g in active_gates
                   if is_gate_overdue(g, appr_fields, default_slo_limit)]
  return overdue_gates
