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


def weekdays_since(requested_on: datetime.datetime) -> int:
  """Return the number of weekdays since a review was requested (in UTC)."""
  d = requested_on.astimezone(PACIFIC_TZ)
  today = datetime.datetime.now(tz=PACIFIC_TZ)
  weekday_counter = 0
  while d < today and weekday_counter < MAX_DAYS:
    d = d + timedelta(days=1)
    if is_weekday(d):
      weekday_counter += 1

  return weekday_counter


def is_overdue(requested_on: datetime.datetime, slo_limit: int) -> bool:
  """Return True if a review is overdue."""
  return weekdays_since(requested_on) > slo_limit
