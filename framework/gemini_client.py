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

import logging
from google import genai

import settings


def get_gemini_response(prompt: str, client) -> str:
  """
  Sends a prompt to the Gemini 2.5 Pro model and returns the text response.

  Args:
      prompt: The input prompt string.

  Returns:
      The text response from the model, or an error message if the request failed.
  """
  logging.info('--- Sending Prompt to Gemini --- \n'
               f'{prompt}\n'
               '---------------------------------')
  try:
    response = response = client.models.generate_content(
      model='gemini-2.5-pro',
      contents=prompt
    )
    if response.text:
      return response.text
    else:
      return 'Error: No text response received from the API.'
  except Exception as e:
    logging.error(f'An error occurred while obtaining Gemini response: {e}')
    raise RuntimeError(f'Failed to get response from Gemini API: {e}') from e


def initialize_gemini():
  """Configure and initialize Gemini."""
  try:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
  except Exception as e:
    logging.error(f'An unexpected error occurred during client initialization: {e}')
    raise RuntimeError(f'Could not initialize API client: {e}') from e
  return client
