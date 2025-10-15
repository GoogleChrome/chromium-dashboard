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
