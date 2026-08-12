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

Reference:
    Google Agent Development Kit (ADK) Documentation:
    https://google.github.io/adk-docs/

Follows ADK error handling guidelines:
- Allows standard SDK exceptions to propagate from tools to the application layer.
- Classifies typed RESOURCE_EXHAUSTED (429) and ServerError (5xx) for retry control.
- Avoids over-catching or trapping BaseException.
"""

from __future__ import annotations

import json
import urllib.error

import httpx
from google.genai import errors

TRANSIENT_HTTP_STATUS_CODES = {429, 503, 504}


def is_transient_error(e: Exception) -> bool:
    """Classifies whether an exception represents a transient/retryable failure.

    Identifies retryable HTTP status codes (429 Rate Limit, 503 Service Unavailable,
    504 Gateway Timeout), connection timeouts, and socket dropouts using typed
    exception classes.
    """
    # 1. Google GenAI API typed errors
    if isinstance(e, errors.APIError):
        return e.code in TRANSIENT_HTTP_STATUS_CODES or (
            e.code is not None and 500 <= e.code < 600
        )

    # 2. Network timeouts and connection drops
    if isinstance(e, (httpx.TimeoutException, TimeoutError)):
        return True
    if isinstance(e, (httpx.NetworkError, ConnectionError)):
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
    # 1. Google GenAI SDK typed errors
    if isinstance(e, errors.APIError):
        if e.code == 429:
            return (
                'Rate Limit Exceeded',
                'Gemini API quota exceeded. Please retry shortly.',
            )
        if e.code in (503, 504) or (e.code is not None and 500 <= e.code < 600):
            return (
                'Gemini API Unavailable',
                'Service temporarily unavailable. Please retry.',
            )
        return (
            'API Error',
            e.message or f'Gemini API returned error code {e.code}.',
        )

    # 2. Network timeouts
    if isinstance(e, (httpx.TimeoutException, TimeoutError)):
        return (
            'Connection Timeout',
            'Request to Gemini API timed out. Please retry.',
        )

    # 3. Network connection failures
    if isinstance(
        e, (httpx.NetworkError, ConnectionError, urllib.error.URLError)
    ):
        return (
            'Network Error',
            'Failed to connect to Gemini API. Please check network connectivity.',
        )

    # 4. JSON parsing failures
    if isinstance(e, json.JSONDecodeError):
        return (
            'JSON Parsing Error',
            f'Failed to parse LLM structured output: {e}',
        )

    # 5. Generic fallback
    return 'Generation Error', str(e)
