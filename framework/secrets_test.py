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

from framework import secrets


class SecretsFunctionsTest(testing_config.CustomTestCase):
  """Set of unit tests for accessing server-side secret values."""

  def test_make_random_key__long(self):
    """The random keys have the desired length."""
    key = secrets.make_random_key()
    self.assertEqual(secrets.RANDOM_KEY_LENGTH, len(key))

  def test_make_random_key__distinct(self):
    """The random keys are different."""
    key_set = set()
    for _ in range(1000):
      key_set.add(secrets.make_random_key())
    self.assertEqual(1000, len(key_set))

  def test_get_xsrf_secret(self):
    """We can get this secret, and it is the same for repeated calls."""
    s1 = secrets.get_xsrf_secret()
    s2 = secrets.get_xsrf_secret()
    self.assertIsNotNone(s1)
    self.assertEqual(s1, s2)

  def test_get_session_secret(self):
    """We can get this secret, and it is the same for repeated calls."""
    s1 = secrets.get_session_secret()
    s2 = secrets.get_session_secret()
    self.assertIsNotNone(s1)
    self.assertEqual(s1, s2)


class SecretsTest(testing_config.CustomTestCase):
  """Set of unit tests for generating and storing server-side secret values."""

  def delete_all(self):
    for old_entity in secrets.Secrets.query():
      old_entity.key.delete()

  def setUp(self):
    self.delete_all()

  def tearDown(self):
    self.delete_all()

  def test_create_and_persist(self):
    """When a new instance is deployed, it sets up secrets."""
    singleton = secrets.Secrets._get_or_make_singleton()
    self.assertIsInstance(singleton, secrets.Secrets)

    singleton2 = secrets.Secrets._get_or_make_singleton()
    self.assertEqual(singleton.xsrf_secret, singleton2.xsrf_secret)
    self.assertEqual(singleton.session_secret, singleton2.session_secret)

  @mock.patch('framework.secrets.make_random_key')
  def test_upgrade(self, mock_make_random_key):
    """When we add a new secret field, it is added to existing secrets."""
    mock_make_random_key.return_value = 'fake new random'
    singleton = secrets.Secrets(xsrf_secret='old secret field')
    singleton.put()

    singleton2 = secrets.Secrets._get_or_make_singleton()
    mock_make_random_key.assert_called_once_with()
    self.assertEqual(singleton2.xsrf_secret, 'old secret field')
    self.assertEqual(singleton2.session_secret, 'fake new random')
