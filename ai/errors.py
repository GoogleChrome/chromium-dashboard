# Copyright 2026 Google Inc. All rights reserved.
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

"""Error classification and diagnostic utilities for AI generation pipelines.

Provides typed error classification for Google GenAI SDK, Google ADK, and standard
library network exceptions without dynamic reflection or string-matching.

Reference:
    Google Agent Development Kit (ADK) Documentation:
    https://google.github.io/adk-docs/
"""

from __future__ import annotations

import json
import urllib.error

from google.genai import errors

TRANSIENT_HTTP_STATUS_CODES = {429, 503, 504}


def get_error_code(e: Exception) -> int | None:
    """Get the HTTP status code from a typed exception."""
    if isinstance(e, errors.APIError):
        try:
            return int(e.code)
        except (ValueError, TypeError):
            return None
    if isinstance(e, urllib.error.HTTPError):
        return e.code
    return None


def is_transient_error(e: Exception) -> bool:
    """Classifies whether an exception represents a transient/retryable failure.

    Identifies retryable HTTP status codes (429 Rate Limit, 503 Service Unavailable,
    504 Gateway Timeout, 5xx server errors), connection timeouts, and socket drops.
    """
    # 1. Check HTTP status code across typed SDK and HTTP exception models
    status_code = get_error_code(e)
    if status_code is not None:
        return status_code in TRANSIENT_HTTP_STATUS_CODES or (
            500 <= status_code < 600
        )

    # 2. Network timeouts and connection drops
    if isinstance(e, TimeoutError):
        return True
    if isinstance(e, (ConnectionError, OSError)):
        return True
    if isinstance(e, urllib.error.URLError) and isinstance(
        e.reason, (TimeoutError, ConnectionError, OSError)
    ):
        return True

    # 3. Malformed streaming / parse drops
    if isinstance(e, json.JSONDecodeError):
        return True

    return False


def get_error_source_and_message(e: Exception) -> tuple[str, str]:
    """Returns a user-friendly error source title and actionable message for UI presentation.

    Inspects structured exception types and HTTP status codes to generate clean,
    human-readable failure reasons.
    """
    status_code = get_error_code(e)
    if status_code == 429:
        return (
            'Rate Limit Exceeded',
            'Gemini API quota exceeded. Please retry shortly.',
        )
    if status_code in (503, 504) or (
        status_code is not None and 500 <= status_code < 600
    ):
        return (
            'Gemini API Unavailable',
            'Service temporarily unavailable. Please retry.',
        )
    if isinstance(e, errors.APIError):
        msg = e.message or f'API returned error code {e.code}.'
        return ('API Error', msg)
    if isinstance(e, urllib.error.HTTPError):
        return ('HTTP Error', f'HTTP error {e.code}: {e.reason}.')

    if isinstance(e, TimeoutError):
        return (
            'Connection Timeout',
            'Request to Gemini API timed out. Please retry.',
        )

    if isinstance(e, (ConnectionError, OSError, urllib.error.URLError)):
        return (
            'Network Error',
            'Failed to connect to Gemini API. Please check network connectivity.',
        )

    if isinstance(e, json.JSONDecodeError):
        return (
            'JSON Parsing Error',
            f'Failed to parse LLM structured output: {e}',
        )

    return 'Generation Error', f'{e}'
