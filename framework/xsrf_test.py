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




import testing_config  # Must be imported before the module under test.

import mock

from framework import xsrf


class XsrfTest(testing_config.CustomTestCase):
  """Set of unit tests for blocking XSRF attacks."""

  def test_generate_token__anon(self):
    """Anon users get a real token."""
    self.assertNotEqual('', xsrf.generate_token(None))

  def test_generate_token__distinct(self):
    """Each user gets their own distinct token."""
    self.assertNotEqual(
        xsrf.generate_token('user1@example.com'),
        xsrf.generate_token('user2@example.com'))

    self.assertNotEqual(
        xsrf.generate_token('user1@example.com'),
        xsrf.generate_token(None))

  def test_validate_token__normal(self):
    """We accept valid tokens."""
    token = xsrf.generate_token('user1@example.com')
    xsrf.validate_token(token, 'user1@example.com')  # no exception raised

  def test_validate_token__malformed_token(self):
    """We reject missing or non-matching tokens."""
    with self.assertRaises(xsrf.TokenIncorrect):
      xsrf.validate_token('bad', 'user1@example.com')

    with self.assertRaises(xsrf.TokenIncorrect):
      xsrf.validate_token('', 'user1@example.com')

    with self.assertRaises(xsrf.TokenIncorrect):
      xsrf.validate_token(
          '098a08fe08b08c08a05e:9721973123',
          'user1@example.com')

  def test_validate_token__wrong_user(self):
    """We reject a user attempting to use a different user's token."""
    token = xsrf.generate_token('user1@example.com')
    with self.assertRaises(xsrf.TokenIncorrect):
      xsrf.validate_token(token, 'user2@example.com')
    with self.assertRaises(xsrf.TokenIncorrect):
      xsrf.validate_token(token, None)

  @mock.patch('time.time')
  def test_validate_token__expiration(self, mock_time):
    """We accept non-expired tokens and reject expired ones."""
    test_time = 1526671379
    mock_time.return_value = test_time
    token = xsrf.generate_token('user1@example.com')

    xsrf.validate_token(token, 'user1@example.com')

    mock_time.return_value = test_time + 1
    xsrf.validate_token(token, 'user1@example.com')

    mock_time.return_value = test_time + xsrf.TOKEN_TIMEOUT_SEC
    xsrf.validate_token(token, 'user1@example.com')

    mock_time.return_value = test_time + xsrf.TOKEN_TIMEOUT_SEC + 1
    with self.assertRaises(xsrf.TokenIncorrect):
      xsrf.validate_token(token, 'user1@example.com')

  @mock.patch('time.time')
  def test_validate_token__future(self, mock_time):
    """We reject tokens from the future."""
    test_time = 1526671379
    mock_time.return_value = test_time
    token = xsrf.generate_token('user1@example.com')

    xsrf.validate_token(token, 'user1@example.com')

    # The clock of the GAE instance doing the checking might be slightly slow.
    mock_time.return_value = test_time - 1
    xsrf.validate_token(token, 'user1@example.com')

    # But, if the difference is too much, someone is trying to fake a token.
    mock_time.return_value = test_time - xsrf.CLOCK_SKEW_SEC - 1
    with self.assertRaises(xsrf.TokenIncorrect):
      xsrf.validate_token(token, 'user1@example.com')