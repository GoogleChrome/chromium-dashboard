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

from unittest import mock

from google.cloud import secretmanager # type: ignore
from framework import secrets


class SecretsFunctionsTest(testing_config.CustomTestCase):
  """Set of unit tests for accessing server-side secret values."""

  def setUp(self):
    # Store original values to restore them after each test
    self.original_github_token = secrets.settings.GITHUB_TOKEN
    self.original_gemini_api_key = secrets.settings.GEMINI_API_KEY
    self.original_ot_api_key = secrets.settings.OT_API_KEY
    self.original_unit_test_mode = secrets.settings.UNIT_TEST_MODE
    self.original_dev_mode = secrets.settings.DEV_MODE

    # Reset cache and flags before each test
    secrets.settings.GITHUB_TOKEN = None
    secrets.settings.GEMINI_API_KEY = None
    secrets.settings.OT_API_KEY = None
    secrets.settings.UNIT_TEST_MODE = False
    secrets.settings.DEV_MODE = False

  def tearDown(self):
    # Restore original settings
    secrets.settings.GITHUB_TOKEN = self.original_github_token
    secrets.settings.GEMINI_API_KEY = self.original_gemini_api_key
    secrets.settings.OT_API_KEY = self.original_ot_api_key
    secrets.settings.UNIT_TEST_MODE = self.original_unit_test_mode
    secrets.settings.DEV_MODE = self.original_dev_mode

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

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  @mock.patch('builtins.open')
  def test_load_ot_api_key__cached(
      self, mock_open, mock_sm_client):
    """The function returns the cached key if it exists."""
    secrets.settings.OT_API_KEY = 'cached_key'

    secrets.load_ot_api_key()

    self.assertEqual('cached_key', secrets.settings.OT_API_KEY)
    # Ensure no file I/O or API calls were made.
    mock_open.assert_not_called()
    mock_sm_client.assert_not_called()

  @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='ot_file_key\n  ')
  def test_load_ot_api_key__unit_test_mode_file_exists(self, mock_file):
    """In test mode, it reads the key from a local file."""
    secrets.settings.UNIT_TEST_MODE = True

    secrets.load_ot_api_key()

    # Verify the value was cached and stripped.
    self.assertEqual('ot_file_key', secrets.settings.OT_API_KEY)
    mock_file.assert_called_once_with(
        f'{secrets.settings.ROOT_DIR}/ot_api_key.txt', 'r')

  @mock.patch('builtins.open')
  def test_load_ot_api_key__unit_test_mode_file_not_found(self, mock_open):
    """In test mode, it sets the key to None if the file is not found."""
    secrets.settings.UNIT_TEST_MODE = True
    mock_open.side_effect = FileNotFoundError

    secrets.load_ot_api_key()

    # Cache should remain None.
    self.assertIsNone(secrets.settings.OT_API_KEY)

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  def test_load_ot_api_key__prod_mode_secret_exists(self, mock_sm_client_class):
    """In prod mode, it fetches the API key from Secret Manager."""
    mock_client = mock.Mock()
    mock_sm_client_class.return_value = mock_client
    mock_client.secret_path.return_value = 'projects/test-app/secrets/OT_API_KEY'

    mock_response = mock.Mock()
    mock_response.payload.data.decode.return_value = 'prod_secret_ot_key'
    mock_client.access_secret_version.return_value = mock_response

    secrets.load_ot_api_key()

    # Verify the key and that it was cached.
    self.assertEqual('prod_secret_ot_key', secrets.settings.OT_API_KEY)

    # Verify the correct API calls were made.
    mock_sm_client_class.assert_called_once()
    mock_client.access_secret_version.assert_called_once_with(
        request={'name': 'projects/test-app/secrets/OT_API_KEY/versions/latest'})

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  def test_load_ot_api_key__prod_mode_secret_fails_raises_runtimeerror(self, mock_sm_client_class):
    """In prod mode, it raises a RuntimeError if Secret Manager gives no response."""
    mock_client = mock.Mock()
    mock_sm_client_class.return_value = mock_client
    mock_client.secret_path.return_value = 'projects/test-app/secrets/OT_API_KEY'

    # Mock a "falsy" response (e.g., None).
    mock_client.access_secret_version.return_value = None

    with self.assertRaisesRegex(RuntimeError,
        'Failed to obtain the origin trials API key from secrets.'):
      secrets.load_ot_api_key()

    self.assertIsNone(secrets.settings.OT_API_KEY)


  # --- load_github_token tests ---

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  @mock.patch('builtins.open')
  def test_load_github_token__cached(
      self, mock_open, mock_sm_client):
    """The function returns the cached token if it exists."""
    secrets.settings.GITHUB_TOKEN = 'cached_token'

    secrets.load_github_token()

    self.assertEqual('cached_token', secrets.settings.GITHUB_TOKEN)
    # Ensure no file I/O or API calls were made.
    mock_open.assert_not_called()
    mock_sm_client.assert_not_called()

  @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='test_file_token\n  ')
  def test_load_github_token__unit_test_mode_file_exists(self, mock_file):
    """In test mode, it reads the token from a local file."""
    secrets.settings.UNIT_TEST_MODE = True

    secrets.load_github_token()

    # Should be stripped of whitespace.
    self.assertEqual('test_file_token', secrets.settings.GITHUB_TOKEN)
    mock_file.assert_called_once_with(
        f'{secrets.settings.ROOT_DIR}/github_token.txt', 'r')
    # Verify that the value was cached.
    self.assertEqual('test_file_token', secrets.settings.GITHUB_TOKEN)

  @mock.patch('builtins.open')
  def test_load_github_token__unit_test_mode_file_not_found(self, mock_open):
    """In test mode, it sets the token to None if the file is not found."""
    secrets.settings.UNIT_TEST_MODE = True
    mock_open.side_effect = FileNotFoundError

    secrets.load_github_token()

    # Cache should remain None.
    self.assertIsNone(secrets.settings.GITHUB_TOKEN)

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  def test_load_github_token__prod_mode_secret_exists(self, mock_sm_client_class):
    """In prod mode, it fetches the token from Secret Manager."""
    # Mock the client and its response.
    mock_client = mock.Mock()
    mock_sm_client_class.return_value = mock_client
    mock_client.secret_path.return_value = 'projects/test-app/secrets/GITHUB_TOKEN'

    # Mock the response object structure.
    mock_response = mock.Mock()
    mock_response.payload.data.decode.return_value = 'prod_secret_token'
    mock_client.access_secret_version.return_value = mock_response

    secrets.load_github_token()

    # Verify the token and that it was cached.
    self.assertEqual('prod_secret_token', secrets.settings.GITHUB_TOKEN)

    # Verify the correct API calls were made.
    mock_sm_client_class.assert_called_once()
    mock_client.secret_path.assert_called_once_with(
        secrets.settings.APP_ID, 'GITHUB_TOKEN')
    mock_client.access_secret_version.assert_called_once_with(
        request={'name': 'projects/test-app/secrets/GITHUB_TOKEN/versions/latest'})

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  def test_load_github_token__prod_mode_secret_fails_raises_runtimeerror(self, mock_sm_client_class):
    """In prod mode, it raises a RuntimeError if Secret Manager gives no response."""
    mock_client = mock.Mock()
    mock_sm_client_class.return_value = mock_client
    mock_client.secret_path.return_value = 'projects/test-app/secrets/GITHUB_TOKEN'

    # Mock a "falsy" response (e.g., None).
    mock_client.access_secret_version.return_value = None

    with self.assertRaisesRegex(RuntimeError,
        'Failed to obtain the GitHub token from secrets.'):
      secrets.load_github_token()

    self.assertIsNone(secrets.settings.GITHUB_TOKEN)

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  def test_load_github_token__prod_mode_secret_exception(self, mock_sm_client_class):
    """In prod mode, it raises an exception if Secret Manager does."""
    mock_client = mock.Mock()
    mock_sm_client_class.return_value = mock_client
    mock_client.secret_path.return_value = 'projects/test-app/secrets/GITHUB_TOKEN'

    # Mock an exception (e.g., permissions error).
    mock_client.access_secret_version.side_effect = Exception('Permission denied')

    # The function does not catch exceptions in prod mode, so it should propagate.
    with self.assertRaises(Exception, msg='Permission denied'):
      secrets.load_github_token()

    # Cache should not be set.
    self.assertIsNone(secrets.settings.GITHUB_TOKEN)

  # --- load_gemini_api_key tests ---

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  @mock.patch('builtins.open')
  def test_load_gemini_api_key__cached(
      self, mock_open, mock_sm_client):
    """The function returns the cached API key if it exists."""
    secrets.settings.GEMINI_API_KEY = 'cached_api_key'

    secrets.load_gemini_api_key()

    self.assertEqual('cached_api_key', secrets.settings.GEMINI_API_KEY)
    # Ensure no file I/O or API calls were made.
    mock_open.assert_not_called()
    mock_sm_client.assert_not_called()

  @mock.patch('builtins.open', new_callable=mock.mock_open, read_data='test_file_api_key\n  ')
  def test_load_gemini_api_key__unit_test_mode_file_exists(self, mock_file):
    """In test mode, it reads the API key from a local file."""
    secrets.settings.UNIT_TEST_MODE = True

    secrets.load_gemini_api_key()

    # Should be stripped of whitespace.
    self.assertEqual('test_file_api_key', secrets.settings.GEMINI_API_KEY)
    mock_file.assert_called_once_with(
        f'{secrets.settings.ROOT_DIR}/gemini_api_key.txt', 'r')
    # Verify that the value was cached.
    self.assertEqual('test_file_api_key', secrets.settings.GEMINI_API_KEY)

  @mock.patch('builtins.open')
  def test_load_gemini_api_key__unit_test_mode_file_not_found(self, mock_open):
    """In test mode, it sets the API key to None if the file is not found."""
    secrets.settings.UNIT_TEST_MODE = True
    mock_open.side_effect = FileNotFoundError

    secrets.load_gemini_api_key()

    # Cache should remain None.
    self.assertIsNone(secrets.settings.GEMINI_API_KEY)

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  def test_load_gemini_api_key__prod_mode_secret_exists(self, mock_sm_client_class):
    """In prod mode, it fetches the API key from Secret Manager."""
    # Mock the client and its response.
    mock_client = mock.Mock()
    mock_sm_client_class.return_value = mock_client
    mock_client.secret_path.return_value = 'projects/test-app/secrets/GEMINI_API_KEY'

    # Mock the response object structure.
    mock_response = mock.Mock()
    mock_response.payload.data.decode.return_value = 'prod_secret_api_key'
    mock_client.access_secret_version.return_value = mock_response

    secrets.load_gemini_api_key()

    # Verify the key and that it was cached.
    self.assertEqual('prod_secret_api_key', secrets.settings.GEMINI_API_KEY)

    # Verify the correct API calls were made.
    mock_sm_client_class.assert_called_once()
    mock_client.secret_path.assert_called_once_with(
        secrets.settings.APP_ID, 'GEMINI_API_KEY')
    mock_client.access_secret_version.assert_called_once_with(
        request={'name': 'projects/test-app/secrets/GEMINI_API_KEY/versions/latest'})

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  def test_load_gemini_api_key__prod_mode_secret_fails_raises_runtimeerror(self, mock_sm_client_class):
    """In prod mode, it raises a RuntimeError if Secret Manager gives no response."""
    mock_client = mock.Mock()
    mock_sm_client_class.return_value = mock_client
    mock_client.secret_path.return_value = 'projects/test-app/secrets/GEMINI_API_KEY'

    # Mock a "falsy" response (e.g., None).
    mock_client.access_secret_version.return_value = None

    with self.assertRaisesRegex(RuntimeError,
        'Failed to obtain the Gemini API key from secrets.'):
      secrets.load_gemini_api_key()

    self.assertIsNone(secrets.settings.GEMINI_API_KEY)

  @mock.patch('google.cloud.secretmanager.SecretManagerServiceClient')
  def test_load_gemini_api_key__prod_mode_secret_exception(self, mock_sm_client_class):
    """In prod mode, it raises an exception if Secret Manager does."""
    mock_client = mock.Mock()
    mock_sm_client_class.return_value = mock_client
    mock_client.secret_path.return_value = 'projects/test-app/secrets/GEMINI_API_KEY'

    # Mock an exception (e.g., permissions error).
    mock_client.access_secret_version.side_effect = Exception('Permission denied')

    # The function does not catch exceptions in prod mode, so it should propagate.
    with self.assertRaises(Exception, msg='Permission denied'):
      secrets.load_gemini_api_key()

    # Cache should not be set.
    self.assertIsNone(secrets.settings.GEMINI_API_KEY)


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


class ApiCredentialTest(testing_config.CustomTestCase):

  def tearDown(self):
    for old_entity in secrets.ApiCredential.query():
      old_entity.key.delete()

  def test_select_token_for_api__first_use(self):
    """When there are no credientials for an API, it makes one."""
    actual = secrets.ApiCredential.select_token_for_api('foo')

    self.assertEqual('foo', actual.api_name)
    self.assertIsNone(actual.token)
    self.assertEqual(0, actual.failure_timestamp)
    self.assertEqual(
        1, len(list(secrets.ApiCredential.query())))

  def test_select_token_for_api__one_exists(self):
    """When there are no credientials for an API, it makes one."""
    foo_cred = secrets.ApiCredential(api_name='foo', token='token')
    foo_cred.put()

    actual = secrets.ApiCredential.select_token_for_api('foo')

    self.assertEqual('foo', actual.api_name)
    self.assertEqual('token', actual.token)
    self.assertEqual(0, actual.failure_timestamp)
    self.assertEqual(
        1, len(list(secrets.ApiCredential.query())))

  def test_select_token_for_api__three_exist(self):
    """When there are credientials, choose the earliest failure."""
    cred_2 = secrets.ApiCredential(
        api_name='foo', token='token 2', failure_timestamp=2)
    cred_2.put()
    cred_1 = secrets.ApiCredential(
        api_name='foo', token='token 1', failure_timestamp=1)
    cred_1.put()
    cred_3 = secrets.ApiCredential(
        api_name='foo', token='token 3', failure_timestamp=3)
    cred_3.put()

    actual = secrets.ApiCredential.select_token_for_api('foo')

    self.assertEqual('foo', actual.api_name)
    self.assertEqual('token 1', actual.token)
    self.assertEqual(1, actual.failure_timestamp)
    self.assertEqual(
        3, len(list(secrets.ApiCredential.query())))

  def test_get_github_credendial(self):
    """We can get a github token."""
    gh_cred = secrets.ApiCredential(
        api_name=secrets.GITHUB_API_NAME, token='hash')
    gh_cred.put()

    actual = secrets.ApiCredential.get_github_credendial()

    self.assertEqual('github', actual.api_name)
    self.assertEqual('hash', actual.token)
    self.assertEqual(0, actual.failure_timestamp)
    self.assertEqual(
        1, len(list(secrets.ApiCredential.query())))

  def test_record_failure(self):
    """We can record the time of failure for an API token."""
    NOW = 1234567890
    gh_cred = secrets.ApiCredential(
        api_name=secrets.GITHUB_API_NAME, token='hash')
    gh_cred.put()

    gh_cred.record_failure(now=NOW)

    updated_cred = list(secrets.ApiCredential.query())[0]
    self.assertEqual('github', updated_cred.api_name)
    self.assertEqual('hash', updated_cred.token)
    self.assertEqual(NOW, updated_cred.failure_timestamp)
    self.assertEqual(
        1, len(list(secrets.ApiCredential.query())))
