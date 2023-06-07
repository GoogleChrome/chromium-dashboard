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

PACIFIC_TZ = pytz.timezone('US/Pacific')
MAX_DAYS = 9999

def is_weekday(d: datetime.datetime) -> bool:
  """Return True if d is a weekday: Monday through Friday."""
  return d.weekday() < 5


def weekdays_between(start: datetime.datetime, end: datetime.datetime) -> int:
  """Return the number of Pacific timezone weekdays between two UTC dates."""
  d_ptz = start.astimezone(PACIFIC_TZ)
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


def is_overdue(requested_on: datetime.datetime, slo_limit: int) -> bool:
  """Return True if a review is overdue."""
  return remaining_days(requested_on, slo_limit) < 0
