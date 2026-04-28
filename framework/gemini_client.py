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

"""Client module for interacting with the Google GenAI API.

This module provides the `GeminiClient` class, which serves as a wrapper
around the `google.genai` SDK. It handles API key configuration, retry logic
for transient errors, asynchronous batch processing of prompts, and token
limit validation.
"""

import asyncio
import logging

from google import genai
from google.genai import types

import settings
from framework import utils


class GeminiClient:
    """Manages client initialization and communication with the Gemini API.

    This class serves as a wrapper for the `google.genai` client,
    handling API key configuration and simplifying content generation requests.
    """

    GEMINI_MODEL = 'gemini-3.1-pro-preview'

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
        api_key = settings.GEMINI_API_KEY
        # This error should only be raised locally. The application will already
        # raise this type of error when trying to load the Gemini API key in a
        # non-local environment.
        if api_key is None:
            raise RuntimeError('No Gemini API key found.')

        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            logging.error(
                f'An unexpected error occurred during client initialization: {e}'
            )  # noqa: E501
            raise RuntimeError(f'Could not initialize API client: {e}') from e

    def __del__(self):
        """Closes the client connection upon object deletion."""
        if hasattr(self, 'client') and self.client:
            self.client.close()

    @utils.retry(MAX_RETRIES, delay=RETRY_BACKOFF_SECONDS)
    def prompt_exceeds_input_token_limit(self, prompt: str) -> bool:
        """Checks the token size of a prompt and checks if it exceeds the input
           limit of the Gemini model.

        Args:
          prompt: The input prompt string.

        Returns:
          Boolean value of whether the input token limit is exceedded.
        """  # noqa: D205
        response = self.client.models.count_tokens(
            model=GeminiClient.GEMINI_MODEL, contents=prompt
        )
        model_info = self.client.models.get(model=self.GEMINI_MODEL)
        logging.info(f'Prompt token count: {response.total_tokens}')
        logging.info(
            f"Model's context limit token count: {model_info.input_token_limit}"
        )  # noqa: E501
        return response.total_tokens > model_info.input_token_limit

    @utils.retry(MAX_RETRIES, delay=RETRY_BACKOFF_SECONDS)
    def get_response(
        self, prompt: str, temperature: float | None = None
    ) -> str:
        """Sends a prompt to the Gemini model and returns the text response.

        Args:
          prompt: The input prompt string to send to the model.
          temperature: Controls the randomness of the output.

        Returns:
          The text response from the model.

        Raises:
          RuntimeError: If a valid response is not received after all retries.
        """
        logging.info(
            '--- Sending Prompt to Gemini --- \n'
            f'{prompt}\n'
            '---------------------------------'
        )

        response = self.client.models.generate_content(
            model=GeminiClient.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                # timeout is passed to the config using milliseconds.
                http_options=types.HttpOptions(
                    timeout=GeminiClient.API_TIMEOUT_SECONDS * 1000
                ),  # noqa: E501
            ),
        )

        if not response.text:
            raise RuntimeError('No text response received from the API.')

        # Check for the specific failure sentinel in the response.
        # Using lstrip().upper() for robustness against minor formatting variations.
        if response.text.lstrip().upper().startswith('RESPONSE FAILED'):
            # Log the specific failure reason returned by the model
            logging.warning(f'Model returned failure sentinel: {response.text}')
            raise RuntimeError(f'Model reported failure: {response.text}')

        return response.text

    async def get_response_async(
        self, prompt: str, temperature: float | None = None
    ) -> str:  # noqa: E501
        """Asynchronously sends a prompt to the Gemini model.

        Wraps the synchronous `get_response` method in a thread, inheriting
        its retry logic.

        Args:
          prompt: The input prompt string.
          temperature: Controls the randomness of the output.

        Returns:
          The text response from the model.

        Raises:
          TimeoutError: If the total execution time (including retries)
            exceeds ASYNC_TIMEOUT_SECONDS.
        """
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self.get_response, prompt, temperature),
                timeout=GeminiClient.ASYNC_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logging.error(
                f'Gemini request timed out after {GeminiClient.ASYNC_TIMEOUT_SECONDS} seconds.'
            )  # noqa: E501
            raise TimeoutError(
                f'Gemini request timed out after {GeminiClient.ASYNC_TIMEOUT_SECONDS}s'
            )  # noqa: E501

    async def get_batch_responses_async(
        self, prompts: list[str], temperature: float | None = None
    ) -> list[str | BaseException]:  # noqa: E501
        """Concurrently sends a list of prompts to the Gemini API.

        Args:
          prompts: A list of prompt strings to send.
          temperature: Controls the randomness of the output.

        Returns:
          A list containing either the string response or an Exception object
          for each prompt, in the same order as the input list.
        """
        logging.info(f'Starting batch processing for {len(prompts)} prompts...')

        # Create a list of coroutine objects
        tasks = [
            self.get_response_async(prompt, temperature) for prompt in prompts
        ]

        # asyncio.gather runs them concurrently.
        # return_exceptions=True ensures one failure doesn't crash the entire batch.
        results = await asyncio.gather(*tasks, return_exceptions=True)

        logging.info(f'Batch processing complete for {len(prompts)} prompts.')
        return results


class DummyGeminiClient:
    """A dummy client for local development without credentials."""

    GEMINI_MODEL = 'gemini-3.1-pro-preview'

    def __init__(self):
        """Initializes the dummy Gemini client."""
        logging.info('DummyGeminiClient initialized.')

    def __del__(self):
        """No-op cleanup for the dummy client."""
        pass

    def prompt_exceeds_input_token_limit(self, prompt: str) -> bool:
        """Always returns False for the dummy client."""
        logging.info('Dummy Gemini Client checking token limit.')
        return False

    def get_response(
        self, prompt: str, temperature: float | None = None
    ) -> str:
        """Returns a fake string response."""
        logging.info(
            f'Dummy Gemini Client returning fake response for prompt of length {len(prompt)}.'
        )
        return 'This is a dummy response from DummyGeminiClient.'

    async def get_response_async(
        self, prompt: str, temperature: float | None = None
    ) -> str:
        """Returns a fake string response asynchronously."""
        logging.info(
            f'Dummy Gemini Client returning fake async response for prompt of length {len(prompt)}.'
        )
        return 'This is a dummy async response from DummyGeminiClient.'

    async def get_batch_responses_async(
        self, prompts: list[str], temperature: float | None = None
    ) -> list[str | BaseException]:
        """Returns a list of fake string responses asynchronously."""
        logging.info(
            f'Dummy Gemini Client returning fake batch responses for {len(prompts)} prompts.'
        )
        return [
            'This is a dummy async batch response from DummyGeminiClient.'
        ] * len(prompts)


_client_instance: GeminiClient | DummyGeminiClient | None = None


def initialize_client() -> None:
    """Initializes the active Gemini client at startup."""
    global _client_instance
    if settings.GEMINI_API_KEY is None and settings.DEV_MODE:
        logging.info('Using DummyGeminiClient for local development.')
        _client_instance = DummyGeminiClient()
    else:
        _client_instance = GeminiClient()


def get_client() -> GeminiClient | DummyGeminiClient:
    """Returns the globally configured Gemini client."""
    if _client_instance is None:
        # Fallback if not initialized explicitly
        initialize_client()
    if _client_instance is None:  # This should not happen, but for type checker
        raise RuntimeError('Gemini Client not initialized.')
    return _client_instance
