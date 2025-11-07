# Copyright 2025 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testing_config  # Must be imported before the module under test.

from unittest import mock

from framework import gemini_client


class GeminiClientTest(testing_config.CustomTestCase):

  def setUp(self):
    """Set up shared mocks for all tests in this class."""
    # Patch settings for all tests
    self.mock_settings = mock.patch('framework.gemini_client.settings').start()
    self.mock_settings.GEMINI_API_KEY = 'test_api_key_123'

    # Patch genai.Client class
    self.mock_genai_client_class = mock.patch('framework.gemini_client.genai.Client').start()

    # This is the mock *instance* that will be created and assigned to self.client
    self.mock_client_instance = mock.MagicMock()
    self.mock_genai_client_class.return_value = self.mock_client_instance

    # Patch logging
    self.mock_logging = mock.patch('framework.gemini_client.logging').start()

    # Add cleanup to stop all patches
    self.addCleanup(mock.patch.stopall)

  def test_init__success(self):
    """The client is initialized correctly with the API key."""
    # Stop the class-level patch to test __init__ in isolation
    self.mock_genai_client_class.stop()

    # Start a new, fresh patch just for this test
    mock_genai_client = mock.patch('framework.gemini_client.genai.Client').start()
    mock_client_instance = mock.MagicMock()
    mock_genai_client.return_value = mock_client_instance

    client = gemini_client.GeminiClient()

    mock_genai_client.assert_called_once_with(
      api_key='test_api_key_123'
    )
    # Verify the instance's client attribute is the mock
    self.assertIs(client.client, mock_client_instance)
    self.mock_logging.error.assert_not_called()

  def test_init__exception(self):
    """The genai.Client raises an exception during initialization."""
    # Stop the class-level patch to test __init__ in isolation
    self.mock_genai_client_class.stop()

    # Configure a new patch to raise an exception
    mock_genai_client = mock.patch('framework.gemini_client.genai.Client').start()
    init_error = Exception('Authentication failed')
    mock_genai_client.side_effect = init_error

    # Call the constructor, expecting it to re-raise a RuntimeError
    with self.assertRaisesRegex(
      RuntimeError,
      'Could not initialize API client: Authentication failed'
    ) as cm:
      gemini_client.GeminiClient()

    # Verify exception chaining
    self.assertIs(init_error, cm.exception.__cause__)

    # Verify logging
    self.mock_logging.error.assert_called_once_with(
      f'An unexpected error occurred during client initialization: {init_error}'
    )

  def test_get_response__success(self):
    """The client returns a valid text response."""
    prompt = 'Hello Gemini'
    expected_response = 'Hello there!'

    # Configure the mock response from the API call
    mock_api_response = mock.MagicMock()
    mock_api_response.text = expected_response
    self.mock_client_instance.models.generate_content.return_value = mock_api_response

    # Create the client (uses the mocks from setUp)
    client = gemini_client.GeminiClient()

    actual_response = client.get_response(prompt)

    self.assertEqual(expected_response, actual_response)

    # Verify logging.info was called with the prompt
    self.mock_logging.info.assert_called_once_with(
      '--- Sending Prompt to Gemini --- \n'
      f'{prompt}\n'
      '---------------------------------')

    self.mock_client_instance.models.generate_content.assert_called_once_with(
      model=client.GEMINI_MODEL,  # Check it uses the class attribute
      contents=prompt
    )
    self.mock_logging.error.assert_not_called()

  def test_get_response__no_text_in_response(self):
    """The API returns a response, but it has no 'text' attribute."""
    prompt = 'Hello Gemini'

    # Configure the mock response to have no .text
    mock_api_response = mock.MagicMock()
    mock_api_response.text = None  # or ""
    self.mock_client_instance.models.generate_content.return_value = mock_api_response

    client = gemini_client.GeminiClient()

    # Call the method, expecting it to raise the *final* RuntimeError
    with self.assertRaisesRegex(
        RuntimeError,
        'Failed to get response from Gemini API: No text response received from the API.'
    ):
        client.get_response(prompt)

    # Verify logging and API call
    self.mock_logging.info.assert_called_once()
    self.mock_client_instance.models.generate_content.assert_called_once()

    # Verify the error was logged twice, as explained
    self.assertEqual(self.mock_logging.error.call_count, 2)
    self.mock_logging.error.assert_any_call(
        'No text response received from the API.'
    )
    self.mock_logging.error.assert_any_call(
        'An error occurred while obtaining Gemini response: No text response received from the API.'
    )

  def test_get_response__api_exception(self):
    """The API client raises an exception during the request."""
    prompt = 'Hello Gemini'

    # Configure the mock client to raise an exception
    api_error = Exception('API rate limit exceeded')
    self.mock_client_instance.models.generate_content.side_effect = api_error

    client = gemini_client.GeminiClient()

    with self.assertRaisesRegex(
      RuntimeError,
      'Failed to get response from Gemini API: API rate limit exceeded'
    ) as cm:
      client.get_response(prompt)

    # Verify the exception chaining
    self.assertIs(api_error, cm.exception.__cause__)

    # Verify logging
    self.mock_logging.info.assert_called_once()
    self.mock_logging.error.assert_called_once_with(
      f'An error occurred while obtaining Gemini response: {api_error}'
    )

  def test_del__closes_client(self):
    """Tests that the __del__ method calls close() on the client."""
    client = gemini_client.GeminiClient()

    # Grab the internal mock client created in setUp
    mock_internal_client = client.client

    del client

    # Verify close was called on the internal client
    mock_internal_client.close.assert_called_once()
