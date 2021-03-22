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

from __future__ import division
from __future__ import print_function

import unittest
import testing_config  # Must be imported before the module under test.

import mock
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


class CommonFunctionTests(unittest.TestCase):

  def test_format_feature_url(self):
    self.assertEqual(
        '/feature/123',
        utils.format_feature_url(123))

  @mock.patch('time.sleep')  # Run test full speed.
  def testRetryDecorator_ExceedFailures(self, mock_sleep):
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
    self.assertEquals(3, tracker.func_called)
    self.assertEqual(2, len(mock_sleep.mock_calls))

  @mock.patch('time.sleep')  # Run test full speed.
  def testRetryDecorator_EventuallySucceed(self, mock_sleep):
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
    self.assertEquals(2, tracker.func_called)
    self.assertEqual(1, len(mock_sleep.mock_calls))

  def test_strip_trailing_slash(self):
    handlerInstance = MockHandler('/request/path')
    handlerInstance.handlerMethod('/request/path')
    self.assertEqual(('/request/path',), handlerInstance.handler_called_with)
    self.assertIsNone(handlerInstance.redirected_to)

    handlerInstance = MockHandler('/request/path/')
    handlerInstance.handlerMethod('/request/path/')
    self.assertIsNone(handlerInstance.handler_called_with)
    self.assertEqual('/request/path', handlerInstance.redirected_to)
