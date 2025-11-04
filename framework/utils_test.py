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

from unittest import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from framework import utils
import base64
import urllib
import requests  # Added for requests.exceptions.RequestException
import concurrent.futures # Added to mock ThreadPoolExecutor


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


class UtilsGitHubTests(unittest.TestCase):
  """Tests for the GitHub fetching utility functions."""

  def setUp(self):
    # Mock successful file API response
    self.mock_file_api_response = {
      'type': 'file',
      'download_url': 'https://raw.github.com/some/file.html',
      'name': 'file.html'
    }
    # Mock file content response
    self.mock_file_content = '<html>Hello</html>'

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
    self.mock_file1_content = '<html>File 1</html>'
    self.mock_file2_content = 'console.log("File 2");'

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

  @mock.patch('framework.utils.secrets.get_github_token')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  @mock.patch('framework.utils._get_github_headers')
  @mock.patch('framework.utils.requests.get')
  def test_get_file_contents__success(
      self, mock_requests_get, mock_get_headers, mock_parse_url, mock_get_token):
    """Should fetch and return file content on success."""
    mock_get_token.return_value = 'test_token'
    mock_parse_url.return_value = 'dom/file.html'
    mock_get_headers.return_value = {'Authorization': 'Bearer test_token'}

    # Mock API response
    mock_api_response = mock.Mock()
    mock_api_response.json.return_value = self.mock_file_api_response
    mock_api_response.raise_for_status.return_value = None

    # Mock Content download response
    mock_content_response = mock.Mock()
    mock_content_response.text = self.mock_file_content
    mock_content_response.raise_for_status.return_value = None

    mock_requests_get.side_effect = [mock_api_response, mock_content_response]

    content = utils.get_file_contents('https://wpt.fyi/results/dom/file.html')

    self.assertEqual(content, self.mock_file_content)
    mock_get_token.assert_called_once()
    mock_parse_url.assert_called_once_with('https://wpt.fyi/results/dom/file.html')
    mock_get_headers.assert_called_once_with('test_token')

    expected_calls = [
      mock.call(
        f'{utils.WPT_GITHUB_API_URL}dom/file.html',
        headers={'Authorization': 'Bearer test_token'},
        params={'ref': 'master'}
      ),
      mock.call('https://raw.github.com/some/file.html')
    ]
    mock_requests_get.assert_has_calls(expected_calls)

  @mock.patch('framework.utils.secrets.get_github_token')
  def test_get_file_contents__no_token(self, mock_get_token):
    """Should return an empty string if no token is found."""
    mock_get_token.return_value = None
    content = utils.get_file_contents('https://wpt.fyi/results/dom/file.html')
    self.assertEqual(content, '')

  @mock.patch('framework.utils.secrets.get_github_token')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  @mock.patch('framework.utils.logging.error')
  def test_get_file_contents__parse_error(
      self, mock_logging, mock_parse_url, mock_get_token):
    """Should re-raise ValueError and log an error on URL parse failure."""
    mock_get_token.return_value = 'test_token'
    mock_parse_url.side_effect = ValueError('Bad URL')

    with self.assertRaises(ValueError):
      utils.get_file_contents('bad_url')
    mock_logging.assert_called_once()

  @mock.patch('framework.utils.secrets.get_github_token')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils.logging.error')
  def test_get_file_contents__api_request_fails(
      self, mock_logging, mock_requests_get, mock_parse_url, mock_get_token):
    """Should re-raise RequestException and log an error on API failure."""
    mock_get_token.return_value = 'test_token'
    mock_parse_url.return_value = 'dom/file.html'
    mock_requests_get.side_effect = requests.exceptions.RequestException('Failed')

    with self.assertRaises(requests.exceptions.RequestException):
      utils.get_file_contents('https://wpt.fyi/results/dom/file.html')
    mock_logging.assert_called_once()

  @mock.patch('framework.utils.secrets.get_github_token')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  @mock.patch('framework.utils.requests.get')
  def test_get_file_contents__not_a_file(
      self, mock_requests_get, mock_parse_url, mock_get_token):
    """Should raise ValueError if the API response is not type 'file'."""
    mock_get_token.return_value = 'test_token'
    mock_parse_url.return_value = 'dom/dir'

    mock_api_response = mock.Mock()
    mock_api_response.json.return_value = {'type': 'dir'}  # Not 'file'
    mock_api_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_api_response

    with self.assertRaisesRegex(ValueError, 'URL does not point to a file'):
      utils.get_file_contents('https://wpt.fyi/results/dom/dir')

  @mock.patch('framework.utils.secrets.get_github_token')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  @mock.patch('framework.utils.requests.get')
  def test_get_file_contents__no_download_url(
      self, mock_requests_get, mock_parse_url, mock_get_token):
    """Should raise ValueError if the API response lacks a download_url."""
    mock_get_token.return_value = 'test_token'
    mock_parse_url.return_value = 'dom/file.html'

    mock_api_response = mock.Mock()
    mock_api_response.json.return_value = {'type': 'file', 'download_url': None}  # Missing URL
    mock_api_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_api_response

    with self.assertRaisesRegex(ValueError, 'Could not find download_url'):
      utils.get_file_contents('https://wpt.fyi/results/dom/file.html')

  @mock.patch('framework.utils.secrets.get_github_token')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  @mock.patch('framework.utils._get_github_headers')
  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils.concurrent.futures.ThreadPoolExecutor')
  def test_get_directory_contents__success(
      self, mock_executor, mock_requests_get, mock_get_headers, mock_parse_url, mock_get_token):
    """Should fetch and return contents for all files in a directory."""
    mock_get_token.return_value = 'test_token'
    mock_parse_url.return_value = 'dom/events'
    mock_get_headers.return_value = {'Authorization': 'Bearer test_token'}

    # Mock API response for directory listing.
    mock_api_response = mock.Mock()
    mock_api_response.json.return_value = self.mock_dir_api_response
    mock_api_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_api_response

    # Mock the thread pool's map function to return the content.
    # This makes it run sequentially and avoids actual threading.
    mock_map_results = [self.mock_file1_content, self.mock_file2_content]
    mock_executor.return_value.__enter__.return_value.map.return_value = mock_map_results

    contents = utils.get_directory_contents('https://wpt.fyi/results/dom/events')

    # Check results
    expected_contents = {
      'file1.html': self.mock_file1_content,
      'file2.js': self.mock_file2_content
    }
    self.assertEqual(contents, expected_contents)

    # Check calls
    mock_get_token.assert_called_once()
    mock_parse_url.assert_called_once_with('https://wpt.fyi/results/dom/events')
    mock_get_headers.assert_called_once_with('test_token')

    # Check that the API was called for the dir listing
    mock_requests_get.assert_called_once_with(
      f'{utils.WPT_GITHUB_API_URL}dom/events',
      headers={'Authorization': 'Bearer test_token'},
      params={'ref': 'master'}
    )

    # Check that the executor was called with the correct download URLs
    mock_executor.return_value.__enter__.return_value.map.assert_called_once_with(
      utils._fetch_file_content,
      ['https://raw.github.com/some/file1.html', 'https://raw.github.com/some/file2.js']
    )

  @mock.patch('framework.utils.secrets.get_github_token')
  def test_get_directory_contents__no_token(self, mock_get_token):
    """Should return an empty dict if no token is found."""
    mock_get_token.return_value = None
    contents = utils.get_directory_contents('https://wpt.fyi/results/dom/events')
    self.assertEqual(contents, {})

  @mock.patch('framework.utils.secrets.get_github_token')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  @mock.patch('framework.utils.requests.get')
  def test_get_directory_contents__not_a_directory(
      self, mock_requests_get, mock_parse_url, mock_get_token):
    """Should raise ValueError if the API response is not a list."""
    mock_get_token.return_value = 'test_token'
    mock_parse_url.return_value = 'dom/file.html'

    mock_api_response = mock.Mock()
    mock_api_response.json.return_value = {'type': 'file'}  # Not a list
    mock_api_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_api_response

    with self.assertRaisesRegex(ValueError, 'URL does not point to a directory'):
      utils.get_directory_contents('https://wpt.fyi/results/dom/file.html')

  @mock.patch('framework.utils.secrets.get_github_token')
  @mock.patch('framework.utils._parse_wpt_fyi_url')
  @mock.patch('framework.utils.requests.get')
  @mock.patch('framework.utils.concurrent.futures.ThreadPoolExecutor')
  def test_get_directory_contents__partial_failure(
      self, mock_executor, mock_requests_get, mock_parse_url, mock_get_token):
    """Should return only successfully fetched files if some downloads fail."""
    mock_get_token.return_value = 'test_token'
    mock_parse_url.return_value = 'dom/events'

    # Mock API response
    mock_api_response = mock.Mock()
    mock_api_response.json.return_value = self.mock_dir_api_response
    mock_api_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_api_response

    # Mock map results where one file fails (returns None)
    mock_map_results = [self.mock_file1_content, None]
    mock_executor.return_value.__enter__.return_value.map.return_value = mock_map_results

    contents = utils.get_directory_contents('https://wpt.fyi/results/dom/events')

    # Check results, only the successful file should be present
    expected_contents = {
      'file1.html': self.mock_file1_content
    }
    self.assertEqual(contents, expected_contents)
