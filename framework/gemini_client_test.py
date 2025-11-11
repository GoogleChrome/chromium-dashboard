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

import asyncio
from unittest import mock

from framework import gemini_client
from google.genai import types


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

    # Patch time.sleep to avoid slow tests during retries
    self.mock_sleep = mock.patch('framework.gemini_client.time.sleep').start()

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
    """The client returns a valid text response with correct timeout config."""
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

    # Capture the actual call arguments to verify the config object
    call_args = self.mock_client_instance.models.generate_content.call_args
    self.assertIsNotNone(call_args)

    # Check simple arguments
    self.assertEqual(call_args.kwargs['model'], client.GEMINI_MODEL)
    self.assertEqual(call_args.kwargs['contents'], prompt)

    # Check the nested config object for the timeout
    actual_config = call_args.kwargs['config']
    self.assertIsInstance(actual_config, types.GenerateContentConfig)
    self.assertIsInstance(actual_config.http_options, types.HttpOptions)
    self.assertEqual(
      actual_config.http_options.timeout,
      client.API_TIMEOUT_SECONDS * 1000
    )

    self.mock_logging.error.assert_not_called()
    self.mock_sleep.assert_not_called()

  def test_get_response__retry_success(self):
    """The client fails twice but succeeds on the third attempt."""
    prompt = 'Retry me'
    expected_response = 'Success after retries'

    # Setup: 2 failures (exceptions), then 1 success
    api_error = Exception('Temporary glitch')
    mock_success_response = mock.MagicMock()
    mock_success_response.text = expected_response

    self.mock_client_instance.models.generate_content.side_effect = [
      api_error,
      api_error,
      mock_success_response
    ]

    client = gemini_client.GeminiClient()
    actual_response = client.get_response(prompt)

    self.assertEqual(actual_response, expected_response)
    # Should have called the API 3 times total
    self.assertEqual(self.mock_client_instance.models.generate_content.call_count, 3)
    # Should have slept twice
    self.assertEqual(self.mock_sleep.call_count, 2)
    # Verify backoff times: 2s after 1st fail, 4s after 2nd fail
    self.mock_sleep.assert_has_calls([mock.call(2), mock.call(4)])

  def test_get_response__no_text_in_response(self):
    """The API returns a response, but it has no 'text' attribute."""
    prompt = 'Hello Gemini'

    # Configure the mock response to have no .text
    mock_api_response = mock.MagicMock()
    mock_api_response.text = None  # or ""
    # Fail all 3 times with empty response
    self.mock_client_instance.models.generate_content.return_value = mock_api_response

    client = gemini_client.GeminiClient()

    # Call the method, expecting it to raise the *final* RuntimeError after retries
    with self.assertRaisesRegex(
      RuntimeError,
      'Failed to get valid response after 3 attempts'
    ):
      client.get_response(prompt)

    # Verify logging and API call
    self.mock_client_instance.models.generate_content.assert_called()
    self.assertEqual(self.mock_client_instance.models.generate_content.call_count, 3)

    # Verify it logged an error for each attempt
    self.assertEqual(self.mock_logging.error.call_count, 3)

  def test_get_response__api_exception(self):
    """The API client raises an exception during all retry attempts."""
    prompt = 'Hello Gemini'

    # Configure the mock client to raise an exception every time
    api_error = Exception('API rate limit exceeded')
    self.mock_client_instance.models.generate_content.side_effect = api_error

    client = gemini_client.GeminiClient()

    with self.assertRaisesRegex(
      RuntimeError,
      'Failed to get valid response after 3 attempts'
    ) as cm:
      client.get_response(prompt)

    # Verify the original exception is chained
    self.assertIs(api_error, cm.exception.__cause__)

    # Verify logging
    self.mock_logging.info.assert_called()
    # Should log an error for each of the 3 failed attempts
    self.assertEqual(self.mock_logging.error.call_count, 3)

  def test_get_response__failure_sentinel_retries(self):
    """The model returns 'RESPONSE FAILED', triggering retries."""
    prompt = 'Bad prompt'
    mock_fail_response = mock.MagicMock()
    mock_fail_response.text = 'RESPONSE FAILED: Invalid spec.'

    # Fail all 3 times with the sentinel
    self.mock_client_instance.models.generate_content.return_value = mock_fail_response

    client = gemini_client.GeminiClient()

    with self.assertRaisesRegex(
      RuntimeError,
      'Failed to get valid response after 3 attempts'
    ):
      client.get_response(prompt)

    self.assertEqual(self.mock_client_instance.models.generate_content.call_count, 3)
    # Verify it logged warnings for the sentinel
    self.assertEqual(self.mock_logging.warning.call_count, 3)
    self.mock_logging.warning.assert_any_call(
      f'Model returned failure sentinel on attempt 1: {mock_fail_response.text}'
    )

  def test_del__closes_client(self):
    """Tests that the __del__ method calls close() on the client."""
    client = gemini_client.GeminiClient()

    # Grab the internal mock client created in setUp
    mock_internal_client = client.client

    del client

    # Verify close was called on the internal client
    mock_internal_client.close.assert_called_once()

  def test_get_response_async__success(self):
    """Test that get_response_async correctly wraps the synchronous method."""
    client = gemini_client.GeminiClient()
    expected_response = 'Async response'
    prompt = 'Async prompt'

    # We mock the synchronous get_response method to verify the async wrapper
    # calls it correctly without actually hitting the API or spawning threads.
    with mock.patch.object(
        client, 'get_response', return_value=expected_response
    ) as mock_sync_get:
      # Use asyncio.run to execute the coroutine in a synchronous test method
      result = asyncio.run(client.get_response_async(prompt))

      self.assertEqual(result, expected_response)
      mock_sync_get.assert_called_once_with(prompt)

  def test_get_response_async__timeout(self):
    """Test that the outer async timeout works correctly."""
    client = gemini_client.GeminiClient()

    # Save original timeout to restore later
    original_timeout = gemini_client.GeminiClient.ASYNC_TIMEOUT_SECONDS
    # Set a very short timeout for this test
    gemini_client.GeminiClient.ASYNC_TIMEOUT_SECONDS = 0.1

    # Create a mock for asyncio.to_thread that simulates a slow operation
    # by using asyncio.sleep.
    async def mock_slow_to_thread(func, *args, **kwargs):
      await asyncio.sleep(0.2)
      return "Should not be reached"

    try:
      # Patch asyncio.to_thread specifically within the gemini_client module
      with mock.patch('framework.gemini_client.asyncio.to_thread', side_effect=mock_slow_to_thread):
        with self.assertRaisesRegex(TimeoutError, 'Gemini request timed out after 0.1s'):
          asyncio.run(client.get_response_async('test'))

      self.mock_logging.error.assert_called_with(
        'Gemini request timed out after 0.1 seconds.'
      )
    finally:
      # Always restore the original timeout constant
      gemini_client.GeminiClient.ASYNC_TIMEOUT_SECONDS = original_timeout

  def test_get_response_async__propagates_exception(self):
    """Test that exceptions from the synchronous method propagate asynchronously."""
    client = gemini_client.GeminiClient()
    error_msg = 'Sync failure'

    with mock.patch.object(
        client, 'get_response', side_effect=RuntimeError(error_msg)
    ):
      with self.assertRaisesRegex(RuntimeError, error_msg):
        asyncio.run(client.get_response_async('fail'))

  def test_get_batch_responses_async__success(self):
    """Test that batch processing correctly gathers multiple async results."""
    client = gemini_client.GeminiClient()
    prompts = ['p1', 'p2', 'p3']

    # Mock the single async method to isolate batch logic.
    # We define an async function to use as a side_effect.
    async def mock_async_response(prompt):
      return f'Response for {prompt}'

    with mock.patch.object(
        client, 'get_response_async', side_effect=mock_async_response
    ) as mock_single:
      results = asyncio.run(client.get_batch_responses_async(prompts))

      expected_results = ['Response for p1', 'Response for p2', 'Response for p3']
      self.assertEqual(results, expected_results)
      self.assertEqual(mock_single.call_count, 3)

      # Verify batch logging
      self.mock_logging.info.assert_any_call('Starting batch processing for 3 prompts...')
      self.mock_logging.info.assert_any_call('Batch processing complete for 3 prompts.')

  def test_get_batch_responses_async__mixed_results(self):
    """Test that batch processing handles mixed success and failure (return_exceptions=True)."""
    client = gemini_client.GeminiClient()
    prompts = ['success1', 'fail', 'success2']
    error_msg = 'Task failed'

    async def mixed_side_effect(prompt):
      if prompt == 'fail':
        raise RuntimeError(error_msg)
      return f'Response for {prompt}'

    with mock.patch.object(
        client, 'get_response_async', side_effect=mixed_side_effect
    ):
      results = asyncio.run(client.get_batch_responses_async(prompts))

      self.assertEqual(len(results), 3)
      self.assertEqual(results[0], 'Response for success1')
      # The second result should be the caught exception object.
      self.assertIsInstance(results[1], RuntimeError)
      self.assertEqual(str(results[1]), error_msg)
      self.assertEqual(results[2], 'Response for success2')

  def test_get_batch_responses_async__empty_input(self):
    """Test batch processing with an empty list of prompts."""
    client = gemini_client.GeminiClient()
    results = asyncio.run(client.get_batch_responses_async([]))
    self.assertEqual(results, [])
    self.mock_logging.info.assert_any_call('Starting batch processing for 0 prompts...')
