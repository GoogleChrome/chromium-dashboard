# Copyright 2020 Google Inc.
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

import unittest
import testing_config  # Must be imported before the module under test.

import asyncio
from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from framework import utils
import base64
import urllib
import requests  # Added for requests.exceptions.RequestException


class MockHandler(object):

  def __init__(self, path):
    self.handler_called_with = None
    self.redirected_to = None
    self.request = self
    self.path = path

  @utils.strip_trailing_slash
  def handlerMethod(self, *args):
    self.handler_called_with = args

  def redirect(self, new_path):
    self.redirected_to = new_path


class UtilsFunctionTests(unittest.TestCase):

  def setUp(self):
    self.url = 'https://example.com/file.txt'
    self.content = 'This is the file content.'
    # Encode content into bytes, then base64 encode it.
    self.encoded_content = base64.b64encode(self.content.encode('utf-8'))

  def test_normalized_name(self):
    self.assertEqual('', utils.normalized_name(''))
    self.assertEqual('abc', utils.normalized_name('abc'))
    self.assertEqual('abc', utils.normalized_name('Abc'))
    self.assertEqual('abc', utils.normalized_name('ABC'))
    self.assertEqual('abc', utils.normalized_name('A BC'))
    self.assertEqual('abc', utils.normalized_name('A B/C'))
    self.assertEqual('abc', utils.normalized_name(' /A B/C /'))

  def test_format_feature_url(self):
    self.assertEqual(
        '/feature/123',
        utils.format_feature_url(123))

  @mock.patch('logging.error')
  @mock.patch('logging.warning')
  @mock.patch('time.sleep')  # Run test full speed.
  def testRetryDecorator_ExceedFailures(
      self, mock_sleep, mock_warn, mock_err):
    class Tracker(object):
      func_called = 0
    tracker = Tracker()

    # Use a function that always fails.
    @utils.retry(2, delay=1, backoff=2)
    def testFunc(tracker):
      tracker.func_called += 1
      raise Exception('Failed')

    with self.assertRaises(Exception):
      testFunc(tracker)
    self.assertEqual(3, tracker.func_called)
    self.assertEqual(2, len(mock_sleep.mock_calls))
    self.assertEqual(2, len(mock_warn.mock_calls))
    self.assertEqual(1, len(mock_err.mock_calls))

  @mock.patch('logging.warning')
  @mock.patch('time.sleep')  # Run test full speed.
  def testRetryDecorator_EventuallySucceed(self, mock_sleep, mock_warn):
    class Tracker(object):
      func_called = 0
    tracker = Tracker()

    # Use a function that succeeds on the 2nd attempt.
    @utils.retry(2, delay=1, backoff=2)
    def testFunc(tracker):
      tracker.func_called += 1
      if tracker.func_called < 2:
        raise Exception('Failed')

    testFunc(tracker)
    self.assertEqual(2, tracker.func_called)
    self.assertEqual(1, len(mock_sleep.mock_calls))
    self.assertEqual(1, len(mock_warn.mock_calls))

  def test_strip_trailing_slash(self):
    handlerInstance = MockHandler('/request/path')
    handlerInstance.handlerMethod('/request/path')
    self.assertEqual(('/request/path',), handlerInstance.handler_called_with)
    self.assertIsNone(handlerInstance.redirected_to)

    handlerInstance = MockHandler('/request/path/')
    handlerInstance.handlerMethod('/request/path/')
    self.assertIsNone(handlerInstance.handler_called_with)
    self.assertEqual('/request/path', handlerInstance.redirected_to)

  def test_get_banner_time__None(self):
    """If no time specified, it returns None."""
    self.assertIsNone(utils.get_banner_time(None))

  def test_get_banner_time__tuple(self):
    """If a time tuple is specified, it returns a timestamp."""
    time_tuple = (2019, 6, 13, 18, 30)
    actual = utils.get_banner_time(time_tuple)
    self.assertEqual(1560450600, actual)

  @mock.patch('framework.utils.rediscache')
  @mock.patch('urllib.request.urlopen')
  def test_get_chromium_file__cache_hit(self, mock_urlopen, mock_rediscache):
    """When the content is cached, it is returned directly."""
    mock_rediscache.get.return_value = self.content

    result = utils.get_chromium_file(self.url)

    self.assertEqual(result, self.content)
    mock_rediscache.get.assert_called_once_with(self.url)
    mock_urlopen.assert_not_called()
    mock_rediscache.set.assert_not_called()

  @mock.patch('logging.info')
  @mock.patch('framework.utils.rediscache')
  @mock.patch('urllib.request.urlopen')
  def test_get_chromium_file__cache_miss_success(
      self, mock_urlopen, mock_rediscache, mock_logging_info):
    """When not cached, the file is fetched, decoded, cached, and returned."""
    mock_rediscache.get.return_value = None
    mock_conn = mock.MagicMock()
    mock_conn.read.return_value = self.encoded_content
    # Mock the context manager
    mock_urlopen.return_value.__enter__.return_value = mock_conn

    result = utils.get_chromium_file(self.url)

    self.assertEqual(result, self.content)
    mock_rediscache.get.assert_called_once_with(self.url)
    mock_logging_info.assert_called_once_with(f'Fetching and caching file: {self.url}')
    mock_urlopen.assert_called_once_with(self.url, timeout=60)
    mock_rediscache.set.assert_called_once_with(self.url, self.content, time=1800)

  @mock.patch('logging.error')
  @mock.patch('framework.utils.rediscache')
  @mock.patch('urllib.request.urlopen')
  def test_get_chromium_file__fetch_error(
      self, mock_urlopen, mock_rediscache, mock_logging_error):
    """If fetching fails with a URLError, return an empty string."""
    mock_rediscache.get.return_value = None
    mock_urlopen.side_effect = urllib.error.URLError('test error')

    result = utils.get_chromium_file(self.url)

    self.assertEqual(result, "")
    mock_rediscache.get.assert_called_once_with(self.url)
    mock_urlopen.assert_called_once_with(self.url, timeout=60)
    mock_logging_error.assert_called_once()
    mock_rediscache.set.assert_not_called()

  @mock.patch('logging.error')
  @mock.patch('framework.utils.rediscache')
  @mock.patch('urllib.request.urlopen')
  def test_get_chromium_file__parsing_error(
      self, mock_urlopen, mock_rediscache, mock_logging_error):
    """If decoding the fetched content fails, return an empty string."""
    mock_rediscache.get.return_value = None
    mock_conn = mock.MagicMock()
    # Provide content that is not valid base64, causing a ValueError on decode.
    mock_conn.read.return_value = b'this is not valid base64'
    mock_urlopen.return_value.__enter__.return_value = mock_conn

    result = utils.get_chromium_file(self.url)

    self.assertEqual(result, "")
    mock_rediscache.get.assert_called_once_with(self.url)
    mock_urlopen.assert_called_once_with(self.url, timeout=60)
    mock_logging_error.assert_called_once()
    mock_rediscache.set.assert_not_called()

  def test_extract_wpt_fyi_results_urls(self):
    """Tests the regex for finding wpt.fyi/results URLs."""
    test_cases = {
      # Input string (key): expected list of URLs (value)
      'Example string with no URLs': [],
      'Empty string': [],
      'Invalid domain: https://google.com/results/foo': [],
      'Invalid path: https://wpt.fyi/wrong/path/foo': [],
      'Protocol relative: //wpt.fyi/results/foo': [],
      'Malformed: https:wpt.fyi/results/foo': [],
      'Path-less URL: https://wpt.fyi/results': [],

      # Case: One URL with query
      'https://wpt.fyi/results/fedcm/fedcm-error-attribute?label=experimental':
        ['https://wpt.fyi/results/fedcm/fedcm-error-attribute'],

      # Case: One URL, no query, embedded
      'Random characters https://wpt.fyi/results/dom/historical.html other':
        ['https://wpt.fyi/results/dom/historical.html'],

      # Case: Two URLs, mixed http/https, one with query string
      'https://wpt.fyi/results/a?q=1 and http://wpt.fyi/results/b':
        ['https://wpt.fyi/results/a', 'http://wpt.fyi/results/b'],

      # Case: URL at end of string
      'Here is the URL: http://wpt.fyi/results/css/foo.css':
        ['http://wpt.fyi/results/css/foo.css'],

      # Case: URL with hash fragment
      'Check https://wpt.fyi/results/css/bar.html#section1 for details':
        ['https://wpt.fyi/results/css/bar.html#section1'],

      # Case: Multiple URLs complex
      ('See https://wpt.fyi/results/a?q=1 http://wpt.fyi/results/b and '
       "'https://wpt.fyi/results/c.html?foo=bar#hash for info."):
        ['https://wpt.fyi/results/a',
         'http://wpt.fyi/results/b',
         'https://wpt.fyi/results/c.html'],
    }

    for input_str, expected in test_cases.items():
      with self.subTest(input=input_str):
        actual = utils.extract_wpt_fyi_results_urls(input_str)
        self.assertEqual(expected, actual)


class UtilsGitHubTests(unittest.TestCase):
  """Tests for the GitHub fetching utility functions (synchronous helpers)."""

  def setUp(self):
    self.mock_headers = {'Authorization': 'Bearer test_token'}
    # Mock successful file API response
    self.mock_file_api_response = {
      'type': 'file',
      'download_url': 'https://raw.github.com/some/file.html',
      'name': 'file.html'
    }
    # Mock successful directory API response
    self.mock_dir_api_response = [
      {
        'type': 'file',
        'name': 'file1.html',
        'download_url': 'https://raw.github.com/some/file1.html'
      },
      {
        'type': 'dir',
        'name': 'subdir',
        'download_url': None
      },
      {
        'type': 'file',
        'name': 'file2.js',
        'download_url': 'https://raw.github.com/some/file2.js'
      }
    ]

  def test_get_github_headers__with_token(self):
    """Headers should include Authorization when a token is provided."""
    headers = utils._get_github_headers('test_token')
    self.assertIn('Authorization', headers)
    self.assertEqual(headers['Authorization'], 'Bearer test_token')
    self.assertIn('Accept', headers)
    self.assertIn('X-GitHub-Api-Version', headers)

  def test_get_github_headers__no_token(self):
    """Headers should not include Authorization when token is None."""
    headers = utils._get_github_headers(None)
    self.assertNotIn('Authorization', headers)
    self.assertIn('Accept', headers)
    self.assertIn('X-GitHub-Api-Version', headers)

  def test_parse_wpt_fyi_url__valid_cases(self):
    """Should correctly parse valid wpt.fyi URLs."""
    urls = {
      'https://wpt.fyi/results/dom/historical.html': 'dom/historical.html',
      'http://wpt.fyi/results/dom/events': 'dom/events',
      'https://wpt.fyi/results/dom/events?label=master': 'dom/events',
      'https://wpt.fyi/results/dom/events/': 'dom/events',
    }
    for url, expected_path in urls.items():
      with self.subTest(url=url):
        self.assertEqual(expected_path, utils._parse_wpt_fyi_url(url))

  def test_parse_wpt_fyi_url__invalid_cases(self):
    """Should raise ValueError for invalid URLs."""
    invalid_urls = [
      'https://google.com/results/dom/events',  # Invalid domain
      'https://wpt.fyi/something/dom/events',  # Invalid prefix
      'https://wpt.fyi/results/',  # Empty path
      'https://wpt.fyi/results',  # Empty path
    ]
    for url in invalid_urls:
      with self.subTest(url=url):
        with self.assertRaises(ValueError):
          utils._parse_wpt_fyi_url(url)

  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils.logging.error')
  def test_fetch_file_content__success(self, mock_logging, mock_requests_get):
    """Should return file text on successful download."""
    mock_response = mock.Mock()
    mock_response.text = 'file content'
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    content = utils._fetch_file_content('http://example.com/file.txt')

    self.assertEqual(content, 'file content')
    mock_requests_get.assert_called_once_with('http://example.com/file.txt')
    mock_logging.assert_not_called()

  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils.logging.error')
  def test_fetch_file_content__failure(self, mock_logging, mock_requests_get):
    """Should return None and log an error on download failure."""
    mock_requests_get.side_effect = requests.exceptions.RequestException('Failed')

    content = utils._fetch_file_content('http://example.com/file.txt')

    self.assertIsNone(content)
    mock_requests_get.assert_called_once_with('http://example.com/file.txt')
    mock_logging.assert_called_once()

  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  def test_fetch_dir_listing__success(self, mock_parse_url, mock_requests_get):
    """Should return a list of (name, url) tuples for files only."""
    mock_parse_url.return_value = 'dom/events'
    mock_response = mock.Mock()
    mock_response.json.return_value = self.mock_dir_api_response
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    result = utils._fetch_dir_listing('https://wpt.fyi/results/dom/events', self.mock_headers)

    expected = [
        ('file1.html', 'https://raw.github.com/some/file1.html'),
        ('file2.js', 'https://raw.github.com/some/file2.js')
    ]
    self.assertEqual(result, expected)
    mock_requests_get.assert_called_once()

  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils.logging.error')
  def test_fetch_dir_listing__failure(self, mock_logging, mock_requests_get):
    """Should return an empty list and log error on failure."""
    mock_requests_get.side_effect = Exception('API Error')
    result = utils._fetch_dir_listing('https://bad.url', self.mock_headers)
    self.assertEqual(result, [])
    mock_logging.assert_called_once()

  @mock.patch('framework.utils.requests.get')
  def test_fetch_dir_listing__not_a_list(self, mock_requests_get):
    """Should return empty list if response is not a list (e.g. it's a file)."""
    mock_response = mock.Mock()
    mock_response.json.return_value = {'type': 'file'}  # Not a list
    mock_requests_get.return_value = mock_response

    result = utils._fetch_dir_listing('https://wpt.fyi/results/somefile', self.mock_headers)
    self.assertEqual(result, [])

  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  def test_resolve_file_url__success(self, mock_parse_url, mock_requests_get):
    """Should resolve a single file URL to (name, download_url)."""
    mock_parse_url.return_value = 'dom/file.html'
    mock_response = mock.Mock()
    mock_response.json.return_value = self.mock_file_api_response
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    result = utils._resolve_file_url('https://wpt.fyi/results/dom/file.html', self.mock_headers)
    self.assertEqual(result, ('file.html', 'https://raw.github.com/some/file.html'))

  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils.logging.warning')
  def test_resolve_file_url__not_a_file(self, mock_warning, mock_requests_get):
    """Should return None and log warning if URL is not a valid file."""
    mock_response = mock.Mock()
    # Missing download_url or wrong type
    mock_response.json.return_value = {'type': 'dir'}
    mock_requests_get.return_value = mock_response

    result = utils._resolve_file_url('https://wpt.fyi/results/dom/dir', self.mock_headers)
    self.assertIsNone(result)
    mock_warning.assert_called_once()

  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils.logging.error')
  def test_resolve_file_url__failure(self, mock_error, mock_requests_get):
    """Should return None and log error on API failure."""
    mock_requests_get.side_effect = Exception('Net Error')
    result = utils._resolve_file_url('https://wpt.fyi/results/fail', self.mock_headers)
    self.assertIsNone(result)
    mock_error.assert_called_once()


class AsyncUtilsGitHubTests(unittest.IsolatedAsyncioTestCase):
  """Tests for the async GitHub orchestration functions."""

  async def test_fetch_and_pair(self):
    """Should pair filename with fetched content asynchronously."""
    fname = 'test.html'
    furl = 'http://example.com/test.html'
    expected_content = '<html>content</html>'

    # We use a patch on the sync function it wraps with to_thread
    with mock.patch('framework.utils._fetch_file_content', return_value=expected_content) as mock_fetch:
      result = await utils._fetch_and_pair(fname, furl)
      self.assertEqual(result, (fname, expected_content))
      mock_fetch.assert_called_once_with(furl)

  @mock.patch('framework.utils.secrets.get_github_token', return_value='token')
  @mock.patch('framework.utils._fetch_dir_listing')
  @mock.patch('framework.utils._resolve_file_url')
  @mock.patch('framework.utils._fetch_file_content')
  async def test_get_mixed_wpt_contents_async__success(
      self, mock_fetch_content, mock_resolve_file, mock_fetch_dir, _mock_token):
    """Test full orchestration with mixed directory and file URLs."""
    # Setup Inputs
    dir_urls = ['https://wpt.fyi/results/dir1']
    file_urls = ['https://wpt.fyi/results/extra.js']

    # Dir 1 contains file A and file B
    mock_fetch_dir.return_value = [
        ('a.html', 'http://dl/a.html'),
        ('b.css', 'http://dl/b.css')
    ]
    # Individual file resolves to file C
    mock_resolve_file.return_value = ('c.js', 'http://dl/c.js')

    # Content fetching returns a simple string based on the URL for verification
    mock_fetch_content.side_effect = lambda url: f'content of {url}'

    # Execute
    results = await utils.get_mixed_wpt_contents_async(dir_urls, file_urls)

    # Assertions
    expected_results = {
        'a.html': 'content of http://dl/a.html',
        'b.css': 'content of http://dl/b.css',
        'c.js': 'content of http://dl/c.js',
    }
    self.assertEqual(results, expected_results)
    self.assertEqual(mock_fetch_dir.call_count, 1)
    self.assertEqual(mock_resolve_file.call_count, 1)
    # Should have fetched content for all 3 unique files
    self.assertEqual(mock_fetch_content.call_count, 3)

  @mock.patch('framework.utils.secrets.get_github_token', return_value='token')
  @mock.patch('framework.utils._fetch_dir_listing')
  @mock.patch('framework.utils._resolve_file_url')
  @mock.patch('framework.utils._fetch_file_content')
  async def test_get_mixed_wpt_contents_async__deduplication(
      self, mock_fetch_content, mock_resolve_file, mock_fetch_dir, _mock_token):
    """If the same file is in a dir and explicitly listed, fetch only once."""
    dir_urls = ['https://wpt.fyi/results/dir1']
    # This file URL will resolve to the same download URL as one in the directory
    file_urls = ['https://wpt.fyi/results/dir1/a.html']

    mock_fetch_dir.return_value = [('a.html', 'http://dl/a.html')]
    mock_resolve_file.return_value = ('a.html', 'http://dl/a.html')
    mock_fetch_content.return_value = 'content'

    results = await utils.get_mixed_wpt_contents_async(dir_urls, file_urls)

    self.assertEqual(len(results), 1)
    self.assertEqual(results['a.html'], 'content')
    # Crucial: content fetch should only happen once despite appearing twice in resolution phase
    mock_fetch_content.assert_called_once_with('http://dl/a.html')

  @mock.patch('framework.utils.secrets.get_github_token', return_value='token')
  @mock.patch('framework.utils._fetch_dir_listing')
  @mock.patch('framework.utils._resolve_file_url')
  @mock.patch('framework.utils._fetch_file_content')
  async def test_get_mixed_wpt_contents_async__partial_failures(
      self, mock_fetch_content, mock_resolve_file, mock_fetch_dir, _mock_token):
    """Should gracefully handle failures in resolution or fetching phases."""
    dir_urls = ['https://wpt.fyi/results/dir1', 'https://wpt.fyi/results/fail_dir']
    file_urls = ['https://wpt.fyi/results/fail_file']

    # One dir fails (returns empty list), one succeeds
    mock_fetch_dir.side_effect = [[('a.html', 'http://dl/a.html')], []]
    # Individual file resolution fails (returns None)
    mock_resolve_file.return_value = None

    # Content fetch succeeds for the one valid file
    mock_fetch_content.return_value = 'content_a'

    results = await utils.get_mixed_wpt_contents_async(dir_urls, file_urls)

    self.assertEqual(results, {'a.html': 'content_a'})

  @mock.patch('framework.utils.secrets.get_github_token', return_value=None)
  async def test_get_mixed_wpt_contents_async__no_token(self, _mock_token):
    """Should return empty dict immediately if no GitHub token is available."""
    results = await utils.get_mixed_wpt_contents_async(['url1'], ['url2'])
    self.assertEqual(results, {})
