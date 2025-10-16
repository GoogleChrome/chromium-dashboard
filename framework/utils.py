# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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

import calendar
import datetime
import json
import logging
import requests
import time
import traceback
import urllib.request
from base64 import b64decode
from framework import rediscache

import settings

CHROME_RELEASE_SCHEDULE_URL = (
    'https://chromiumdash.appspot.com/fetch_milestone_schedule')
CHROMIUM_SCHEDULE_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'


def normalized_name(val):
  return val.lower().replace(' ', '').replace('/', '')


def format_feature_url(feature_id):
  """Return the feature detail page URL for the specified feature."""
  return '/feature/%d' % feature_id


def retry(tries, delay=1, backoff=2):
  """A retry decorator with exponential backoff.

  Functions are retried when Exceptions occur.

  Args:
    tries: int Number of times to retry, set to 0 to disable retry.
    delay: float Initial sleep time in seconds.
    backoff: float Must be greater than 1, further failures would sleep
             delay*=backoff seconds.
  """
  if backoff <= 1:
    raise ValueError("backoff must be greater than 1")
  if tries < 0:
    raise ValueError("tries must be 0 or greater")
  if delay <= 0:
    raise ValueError("delay must be greater than 0")

  def decorator(func):
    def wrapper(*args, **kwargs):
      _tries, _delay = tries, delay
      _tries += 1  # Ensure we call func at least once.
      while _tries > 0:
        try:
          ret = func(*args, **kwargs)
          return ret
        except Exception:
          _tries -= 1
          if _tries == 0:
            logging.error('Exceeded maximum number of retries for %s.',
                          func.__name__)
            raise
          trace_str = traceback.format_exc()
          logging.warning('Retrying %s due to Exception: %s',
                          func.__name__, trace_str[:settings.MAX_LOG_LINE])
          time.sleep(_delay)
          _delay *= backoff  # Wait longer the next time we fail.
    return wrapper
  return decorator


def strip_trailing_slash(handler):
  """Strips the trailing slash on the URL."""
  def remove_slash(self, *args, **kwargs):
    path = args[0]
    if path[-1] == '/':
      return self.redirect(self.request.path.rstrip('/'))

    return handler(self, *args, **kwargs) # Call the handler method
  return remove_slash


_ZERO = datetime.timedelta(0)

class _UTCTimeZone(datetime.tzinfo):
    """UTC"""
    def utcoffset(self, _dt):
        return _ZERO
    def tzname(self, _dt):
        return "UTC"
    def dst(self, _dt):
        return _ZERO

_UTC = _UTCTimeZone()


def get_banner_time(timestamp):
  """Converts a timestamp into data so it can appear in the banner.
  Args:
    timestamp: timestamp expressed in the following format:
         [year,month,day,hour,minute,second]
         e.g. [2009,3,20,21,45,50] represents March 20 2009 9:45:50 PM
  Returns:
    EZT-ready data used to display the time inside the banner message.
  """
  if timestamp is None:
    return None
  ts = datetime.datetime(*timestamp, tzinfo=_UTC)
  return calendar.timegm(ts.timetuple())


def dedupe(list_with_duplicates):
  """Return a list without duplicates, in the original order."""
  return list(dict.fromkeys(list_with_duplicates))


def get_chromium_milestone_info(milestone: int) -> dict:
  try:
    response = requests.get(
      'https://chromiumdash.appspot.com/fetch_milestone_schedule'
      f'?mstone={milestone}')
    response.raise_for_status()
  except requests.exceptions.RequestException as e:
    logging.exception('Failed to get response from Chromium schedule API.')
    raise e
  return response.json()


def get_current_milestone_info(anchor_channel: str):
  """Return a dict of info about the next milestone reaching anchor_channel."""
  try:
    resp = requests.get(f'{CHROME_RELEASE_SCHEDULE_URL}?mstone={anchor_channel}')
  except requests.RequestException as e:
    raise e
  mstone_info = json.loads(resp.text)
  return mstone_info['mstones'][0]


def get_chromium_file(url: str) -> str:
  """Fetches a file from Chromium source, caching the result for 1 hour."""
  content = rediscache.get(url)
  if content is None:
    logging.info(f'Fetching and caching file: {url}')
    try:
      with urllib.request.urlopen(url, timeout=60) as conn:
        content = b64decode(conn.read()).decode('utf-8')
        # Cache page for 30 minutes.
        rediscache.set(url, content, time=1800)
    except (urllib.error.URLError, TypeError, ValueError) as e:
      logging.error(f'Could not fetch or parse file at {url}: {e}')
      return ""
  return content
