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

  def test_render_atom_feed__empty(self):
    """It can render a feed with zero items."""
    request = testing_config.Blank(
        scheme='https', host='host',
        path='/samples.xml')
    data = []

    actual_text, actual_headers = utils.render_atom_feed(
        request, 'test feed', data)

    self.assertEqual(
        actual_headers,
        {
            'Strict-Transport-Security':
                'max-age=63072000; includeSubDomains; preload',
            'Content-Type': 'application/atom+xml;charset=utf-8',
        })
    self.assertIn('http://www.w3.org/2005/Atom', actual_text)
    self.assertIn('<title>Local testing - test feed</title>', actual_text)
    self.assertIn('<id>https://host/samples</id>', actual_text)

  def test_render_atom_feed__some(self):
    """It can render a feed with some items."""
    request = testing_config.Blank(
        scheme='https', host='host',
        path='/samples.xml')
    data = [
        {'updated': {'when': '2021-07-27 12:25:00'},
         'name': 'feature one',
         'id': 12345678,
         'summary': 'one for testing',
         'category': 'CSS',
         },
        {'updated': {'when': '2021-06-03 11:22:00'},
         'name': 'feature two',
         'id': 23456789,
         'summary': 'two for testing',
         'category': 'Device',
         },
    ]

    actual_text, actual_headers = utils.render_atom_feed(
        request, 'test feed', data)

    self.assertIn('<title>feature one</title>', actual_text)
    self.assertIn('one for testing</summary>', actual_text)
    self.assertIn('/feature/12345678/</id>', actual_text)
    self.assertIn('<category term="CSS"></category>', actual_text)

    self.assertIn('<title>feature two</title>', actual_text)
    self.assertIn('two for testing</summary>', actual_text)
    self.assertIn('/feature/23456789/</id>', actual_text)
    self.assertIn('<category term="Device"></category>', actual_text)

  def test_get_banner_time__None(self):
    """If no time specified, it returns None."""
    self.assertIsNone(utils.get_banner_time(None))

  def test_get_banner_time__tuple(self):
    """If a time tuple is specified, it returns a timestamp."""
    time_tuple = (2019, 6, 13, 18, 30)
    actual = utils.get_banner_time(time_tuple)
    self.assertEqual(1560450600, actual)
