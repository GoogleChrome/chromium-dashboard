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

  @mock.patch('framework.gemini_client.logging')
  def test_get_gemini_response__success(self, mock_logging):
    """The client returns a valid text response."""
    prompt = 'Hello Gemini'
    expected_response = 'Hello there!'

    # Create a mock client to pass into the function
    mock_client = mock.MagicMock()

    # Configure the mock response from the API call
    mock_api_response = mock.MagicMock()
    mock_api_response.text = expected_response
    mock_client.models.generate_content.return_value = mock_api_response

    # Call the function
    actual_response = gemini_client.get_gemini_response(prompt, mock_client)

    # Verify the results
    self.assertEqual(expected_response, actual_response)

    # Verify logging.info was called with the prompt
    mock_logging.info.assert_called_once_with(
        '--- Sending Prompt to Gemini --- \n'
        f'{prompt}\n'
        '---------------------------------')

    # Verify the API was called correctly
    mock_client.models.generate_content.assert_called_once_with(
        model='gemini-2.5-pro',
        contents=prompt
    )
    mock_logging.error.assert_not_called()

  @mock.patch('framework.gemini_client.logging')
  def test_get_gemini_response__no_text_in_response(self, mock_logging):
    """The API returns a response, but it has no 'text' attribute."""
    prompt = 'Hello Gemini'

    # Create a mock client
    mock_client = mock.MagicMock()

    # Configure the mock response to have no .text
    mock_api_response = mock.MagicMock()
    mock_api_response.text = None  # or ""
    mock_client.models.generate_content.return_value = mock_api_response

    # Call the function
    actual_response = gemini_client.get_gemini_response(prompt, mock_client)

    # Verify the error message is returned
    self.assertEqual(
        'Error: No text response received from the API.',
        actual_response
    )

    # Verify logging and API call
    mock_logging.info.assert_called_once()
    mock_client.models.generate_content.assert_called_once()
    mock_logging.error.assert_not_called()

  @mock.patch('framework.gemini_client.logging')
  def test_get_gemini_response__api_exception(self, mock_logging):
    """The API client raises an exception during the request."""
    prompt = 'Hello Gemini'

    # Configure the mock client to raise an exception
    mock_client = mock.MagicMock()
    api_error = Exception('API rate limit exceeded')
    mock_client.models.generate_content.side_effect = api_error

    # Call the function, expecting it to re-raise a RuntimeError
    with self.assertRaisesRegex(
        RuntimeError,
        'Failed to get response from Gemini API: API rate limit exceeded'
    ) as cm:
      gemini_client.get_gemini_response(prompt, mock_client)

    # Verify the exception chaining
    self.assertIs(api_error, cm.exception.__cause__)

    # Verify logging
    mock_logging.info.assert_called_once()
    mock_logging.error.assert_called_once_with(
        f'An error occurred while obtaining Gemini response: {api_error}'
    )

  @mock.patch('framework.gemini_client.settings')
  @mock.patch('framework.gemini_client.genai.Client')
  @mock.patch('framework.gemini_client.logging')
  def test_initialize_gemini__success(
      self, mock_logging, mock_genai_client, mock_settings):
    """The client is initialized correctly with the API key."""
    # Set up mocks
    mock_settings.GEMINI_API_KEY = 'test_api_key_123'
    mock_client_instance = mock.MagicMock()
    mock_genai_client.return_value = mock_client_instance

    # Call the function
    client = gemini_client.initialize_gemini()

    # Verify the result
    self.assertIs(mock_client_instance, client)

    # Verify the genai.Client was called correctly
    mock_genai_client.assert_called_once_with(
        api_key='test_api_key_123'
    )
    mock_logging.error.assert_not_called()

  @mock.patch('framework.gemini_client.settings')
  @mock.patch('framework.gemini_client.genai.Client')
  @mock.patch('framework.gemini_client.logging')
  def test_initialize_gemini__init_exception(
      self, mock_logging, mock_genai_client, mock_settings):
    """The genai.Client raises an exception during initialization."""
    # Set up mocks
    mock_settings.GEMINI_API_KEY = 'bad_key'
    init_error = Exception('Authentication failed')
    mock_genai_client.side_effect = init_error

    # Call the function, expecting it to re-raise a RuntimeError
    with self.assertRaisesRegex(
        RuntimeError,
        'Could not initialize API client: Authentication failed'
    ) as cm:
      gemini_client.initialize_gemini()

    # Verify exception chaining
    self.assertIs(init_error, cm.exception.__cause__)

    # Verify logging
    mock_logging.error.assert_called_once_with(
        f'An unexpected error occurred during client initialization: {init_error}'
    )
