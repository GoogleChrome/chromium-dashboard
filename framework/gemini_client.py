# Copyright 2025 Google Inc.
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

import asyncio
import logging
import time
from google import genai
from google.genai import types

import settings


class GeminiClient:
  """Manages client initialization and communication with the Gemini API.

  This class serves as a wrapper for the `google.genai` client,
  handling API key configuration and simplifying content generation requests.
  """

  GEMINI_MODEL = 'gemini-2.5-pro'

  # Retry configuration.
  MAX_RETRIES = 3
  RETRY_BACKOFF_SECONDS = 2

  # Inner timeout: Shorter so the SDK raises its own error first,
  # preventing stuck threads in the background.
  API_TIMEOUT_SECONDS = 175
  # Outer timeout: The absolute max time the async task will wait (9 minutes).
  ASYNC_TIMEOUT_SECONDS = 540

  def __init__(self):
    """Initializes the Gemini client with the API key from settings.

    Raises:
      RuntimeError: If the client could not be initialized due to an
        API key issue or other unexpected error.
    """
    try:
      self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
      logging.error(f'An unexpected error occurred during client initialization: {e}')
      raise RuntimeError(f'Could not initialize API client: {e}') from e

  def __del__(self):
    """Closes the client connection upon object deletion."""
    if hasattr(self, 'client') and self.client:
      self.client.close()

  def get_response(self, prompt: str) -> str:
    """Sends a prompt to the Gemini model and returns the text response.

    Args:
      prompt: The input prompt string to send to the model.

    Returns:
      The text response from the model.

    Raises:
      RuntimeError: If a valid response is not received after all retries.
    """
    logging.info('--- Sending Prompt to Gemini --- \n'
                 f'{prompt}\n'
                 '---------------------------------')
    last_exception = None

    for attempt in range(1, GeminiClient.MAX_RETRIES + 1):
      try:
        if attempt > 1:
          logging.info(f'Starting attempt {attempt}/{GeminiClient.MAX_RETRIES}...')

        response = self.client.models.generate_content(
          model=GeminiClient.GEMINI_MODEL,
          contents=prompt,
          config=types.GenerateContentConfig(
            # timeout is passed to the config using milliseconds.
            http_options=types.HttpOptions(timeout=GeminiClient.API_TIMEOUT_SECONDS * 1000)
          )
        )

        if not response.text:
          raise RuntimeError('No text response received from the API.')

        # Check for the specific failure sentinel in the response.
        # Using lstrip().upper() for robustness against minor formatting variations.
        if response.text.lstrip().upper().startswith("RESPONSE FAILED"):
          # Log the specific failure reason returned by the model
          logging.warning(f'Model returned failure sentinel on attempt {attempt}: {response.text}')
          raise RuntimeError(f'Model reported failure: {response.text}')

        return response.text

      except Exception as e:
        last_exception = e
        logging.error(f'Attempt {attempt}/{GeminiClient.MAX_RETRIES} failed: {e}')

        if attempt < GeminiClient.MAX_RETRIES:
          sleep_time = GeminiClient.RETRY_BACKOFF_SECONDS * attempt
          logging.info(f'Waiting {sleep_time}s before retry...')
          time.sleep(sleep_time)

    # If loop finishes without returning, raise the last error encountered.
    raise RuntimeError(
      f'Failed to get valid response after {GeminiClient.MAX_RETRIES} attempts'
    ) from last_exception

  async def get_response_async(self, prompt: str) -> str:
    """Asynchronously sends a prompt to the Gemini model.

    Wraps the synchronous `get_response` method in a thread, inheriting
    its retry logic.

    Args:
      prompt: The input prompt string.

    Returns:
      The text response from the model.

    Raises:
      TimeoutError: If the total execution time (including retries)
        exceeds ASYNC_TIMEOUT_SECONDS.
    """
    try:
      return await asyncio.wait_for(
        asyncio.to_thread(self.get_response, prompt),
        timeout=GeminiClient.ASYNC_TIMEOUT_SECONDS
      )
    except asyncio.TimeoutError:
      logging.error(f'Gemini request timed out after {GeminiClient.ASYNC_TIMEOUT_SECONDS} seconds.')
      raise TimeoutError(f'Gemini request timed out after {GeminiClient.ASYNC_TIMEOUT_SECONDS}s')

  async def get_batch_responses_async(self, prompts: list[str]) -> list[str|BaseException]:
    """Concurrently sends a list of prompts to the Gemini API.

    Args:
      prompts: A list of prompt strings to send.

    Returns:
      A list containing either the string response or an Exception object
      for each prompt, in the same order as the input list.
    """
    logging.info(f'Starting batch processing for {len(prompts)} prompts...')

    # Create a list of coroutine objects
    tasks = [self.get_response_async(prompt) for prompt in prompts]

    # asyncio.gather runs them concurrently.
    # return_exceptions=True ensures one failure doesn't crash the entire batch.
    results = await asyncio.gather(*tasks, return_exceptions=True)

    logging.info(f'Batch processing complete for {len(prompts)} prompts.')
    return results
