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

import asyncio
import calendar
import datetime
import json
import logging
from pathlib import Path
import re
import requests
import time
import traceback
import urllib.request
from base64 import b64decode
from framework import rediscache, secrets
from urllib.parse import urlparse

import settings

CHROME_RELEASE_SCHEDULE_URL = (
    'https://chromiumdash.appspot.com/fetch_milestone_schedule')
CHROMIUM_SCHEDULE_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
WPT_GITHUB_API_URL = 'https://api.github.com/repos/web-platform-tests/wpt/contents/'
WPT_GITHUB_RAW_CONTENTS_URL = 'https://raw.githubusercontent.com/web-platform-tests/wpt/master/'


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


def extract_wpt_fyi_results_urls(text: str) -> list[str]:
  """
  Finds all 'wpt.fyi/results' URLs within a given string and returns
  them without any query parameters.

  Args:
      text: The input string to search for URLs.

  Returns:
      A list of matching URL strings.
  """
  pattern = r"(https?://wpt\.fyi/results[^\s?]+)"
  urls = re.findall(pattern, text)
  return urls


def _get_github_headers(token: str | None = None) -> dict[str, str]:
  """Helper function to construct API headers."""

  headers = {
    'Accept': 'application/vnd.github.v3+json',
    'X-GitHub-Api-Version': '2022-11-28',
  }
  if token:
    headers['Authorization'] = f'Bearer {token}'

  return headers


def reformat_wpt_fyi_url(url: str) -> str:
  """
  Normalizes a WPT URL by converting multi-global test variants back to their
  source ".any.js" file.

  If the URL does not contain ".any.", it is returned unchanged.

  See documentation: https://web-platform-tests.org/writing-tests/testharness.html#tests-for-other-or-multiple-globals-any-js

  Args:
    url: The full wpt.fyi URL (e.g., '.../test.any.worker.html').

  Returns:
    The URL normalized to the source file (e.g., '.../test.any.js').
  """
  substring = ".any."
  if substring in url:
    # Find the index where ".any." ends
    end_index = url.find('.any.') + len(substring)
    # Slice the string up to that point and add "js"
    return url[:end_index] + "js"
  return url


def _parse_wpt_fyi_url(url: str) -> str:
  """
  Parses a wpt.fyi URL to map it to a GitHub repo path.

  Assumes all wpt.fyi URLs map to:
  - owner: 'web-platform-tests'
  - repo: 'wpt'
  - ref: 'master'

  Expected URL format:
  [http|https]://wpt.fyi/results/<path>...
  """
  url = reformat_wpt_fyi_url(url)
  parsed_url = urlparse(url)

  if parsed_url.netloc != 'wpt.fyi':
    raise ValueError('Invalid URL: Not a wpt.fyi URL.')

  path_prefix = '/results/'
  if not parsed_url.path.startswith(path_prefix):
    raise ValueError(f'Invalid URL path: Expected to start with \'{path_prefix}\'.')

  # Extract the file/dir path after '/results/'
  path = parsed_url.path[len(path_prefix):].strip('/')

  if not path:
    raise ValueError('Invalid URL path: No path found after \'/results/\'.')

  return path


def _fetch_file_content(url: str) -> str | None:
  """Helper function to download a single file's content for ThreadPool."""
  try:
    response = requests.get(url)
    response.raise_for_status()
    return response.text
  except requests.exceptions.RequestException as e:
    logging.error(f'Warning: Failed to fetch {url}: {e}')
  # Some tests results are represented with ".html" file extensions, but
  # their test contents are located in an equivalent ".js" file.
  # If we fail to find the html version, instead attempt the js verion.
  if url.endswith('.html'):
    logging.info('Attempting to obtain test file using .js extension')
    url = url.removesuffix('.html') + '.js'
    try:
      response = requests.get(url)
      response.raise_for_status()
      return response.text
    except requests.exceptions.RequestException as e:
      logging.error(f'Failed to fetch alternate URL {url}: {e}')
  return None


def _fetch_dir_listing(url: str, headers: dict[str, str]) -> list[tuple[str, str]]:
  """
  Fetches a GitHub directory listing and extracts all valid file entries.
  Intended to be run in a thread pool.
  """
  try:
    path = _parse_wpt_fyi_url(url)
    endpoint = f'{WPT_GITHUB_API_URL}{path}'
    resp = requests.get(endpoint, headers=headers, params={'ref': 'master'})
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
      return [(i['name'], i['download_url']) for i in data
              if (
                # Ignore YAML files.
                not i.get('name', '').endswith('.yml')
                and not i.get('name', '').endswith('.yaml')
                and i.get('type') == 'file'
                and i.get('download_url'))]
  except Exception as e:
    logging.error(f'Error fetching directory listing for {url}: {e}')
  return []


async def _fetch_and_pair(fname: str, furl: str) -> tuple[str, str | None]:
  """
  Async wrapper for the actual WPT content fetching phase.
  """
  content = await asyncio.to_thread(_fetch_file_content, furl)
  return fname, content


async def get_mixed_wpt_contents_async(
    dir_urls: list[str],
    additional_file_urls: list[str]
) -> dict[str, str]:
  """
  Orchestrates concurrent fetching of complete directories and individual WPT file URLs.

  Args:
    dir_urls: List of WPT directory URLs to scan.
    additional_file_urls: list of individual WPT file URLs.

  Returns:
    Dict mapping filename to raw text content.
  """
  token = secrets.get_github_token()
  if token is None:
    return {}

  headers = _get_github_headers(token)
  all_contents: dict[str, str] = {}

  # PHASE 1: Async Resolution (Directories & Individual Files)

  # 1a. Create tasks to scan directories
  dir_tasks = [
      asyncio.to_thread(_fetch_dir_listing, u, headers)
      for u in dir_urls
  ]
  file_path_info: list[tuple[str, str]] = []
  for furl in additional_file_urls:
    path = _parse_wpt_fyi_url(furl)
    file_path_info.append((
      f'{WPT_GITHUB_RAW_CONTENTS_URL}{path}',
      # Infer the test name by getting the name from a Path object.
      Path(path).name,
    ))

  # Wait for all resolution tasks to complete concurrently
  dir_results = await asyncio.gather(*dir_tasks)

  # Map raw download URLs to filenames. This automatically handles deduplication
  # if the same file appears in a directory and the explicit list.
  files_to_fetch_map: dict[str, str] = {}

  # Process directory results (each result is a list of tuples)
  for dir_list in dir_results:
    for fname, url in dir_list:
      files_to_fetch_map[url] = fname

  # Process individual file results (each result is a single tuple or None)
  for url, fname in file_path_info:
    files_to_fetch_map[url] = fname

  # PHASE 2: Async Content Fetching
  file_tasks = [
      _fetch_and_pair(fname, url)
      for url, fname in files_to_fetch_map.items()
  ]
  file_results = await asyncio.gather(*file_tasks)

  for fname, content in file_results:
    if content is not None:
      all_contents[fname] = content

  return all_contents
