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

"""Unit tests for typed AI error classification and diagnostic helpers."""

from __future__ import annotations

import testing_config  # isort: skip  # Must be imported before other project modules.

import json
import urllib.error

from google.genai import errors

from ai.errors import (
    get_error_code,
    get_error_source_and_message,
    is_transient_error,
)


class AIErrorsTest(testing_config.CustomTestCase):
    """Tests typed transient error detection, status extraction, and diagnostic mapping."""

    def test_get_error_code_extraction(self):
        """Tests that get_error_code extracts HTTP status across typed exception models."""
        # GenAI APIError / ClientError
        client_err = errors.ClientError(
            429, {'error': {'code': 429, 'message': 'Quota exceeded'}}
        )
        self.assertEqual(get_error_code(client_err), 429)

        # GenAI ServerError
        server_err = errors.ServerError(
            503, {'error': {'code': 503, 'message': 'Service unavailable'}}
        )
        self.assertEqual(get_error_code(server_err), 503)

        # Standard library HTTPError
        http_err = urllib.error.HTTPError(
            'https://example.com', 504, 'Gateway Timeout', {}, None
        )
        self.assertEqual(get_error_code(http_err), 504)

        # Plain exception with no code
        self.assertIsNone(get_error_code(ValueError('No code')))

    def test_is_transient_error_identified_correctly(self):
        """Tests that typed GenAI errors, timeouts, and network drops are classified as transient."""
        # Typed GenAI SDK errors
        rate_limit_err = errors.ClientError(
            429, {'error': {'code': 429, 'message': 'Quota exceeded'}}
        )
        self.assertTrue(is_transient_error(rate_limit_err))

        server_err_503 = errors.ServerError(
            503, {'error': {'code': 503, 'message': 'Service unavailable'}}
        )
        self.assertTrue(is_transient_error(server_err_503))

        server_err_504 = errors.ServerError(
            504, {'error': {'code': 504, 'message': 'Gateway timeout'}}
        )
        self.assertTrue(is_transient_error(server_err_504))

        # Network timeouts and drops (standard library)
        self.assertTrue(is_transient_error(TimeoutError('Request timed out')))
        self.assertTrue(
            is_transient_error(ConnectionResetError('Connection reset'))
        )
        self.assertTrue(
            is_transient_error(ConnectionRefusedError('Connection refused'))
        )
        self.assertTrue(
            is_transient_error(ConnectionError('Connection aborted'))
        )
        self.assertTrue(is_transient_error(OSError('Socket read failed')))
        self.assertTrue(
            is_transient_error(
                json.JSONDecodeError('Expecting value', 'doc', 0)
            )
        )
        self.assertTrue(
            is_transient_error(
                urllib.error.URLError(TimeoutError('Socket timeout'))
            )
        )

    def test_is_transient_error_false_for_permanent_failures(self):
        """Tests that non-retryable typed exceptions are identified as permanent."""
        # 400 Bad Request / 404 Not Found from GenAI SDK
        bad_request_err = errors.ClientError(
            400, {'error': {'code': 400, 'message': 'Invalid parameter'}}
        )
        self.assertFalse(is_transient_error(bad_request_err))

        not_found_err = errors.ClientError(
            404, {'error': {'code': 404, 'message': 'Model not found'}}
        )
        self.assertFalse(is_transient_error(not_found_err))

        self.assertFalse(
            is_transient_error(ValueError('Invalid model argument'))
        )
        self.assertFalse(is_transient_error(KeyError('Missing required field')))
        self.assertFalse(
            is_transient_error(TypeError('Unsupported operand type'))
        )

    def test_get_error_source_and_message_mapping(self):
        """Tests that typed exceptions map to user-friendly titles and descriptions."""
        rate_limit_err = errors.ClientError(
            429,
            {
                'error': {
                    'code': 429,
                    'message': 'Quota exceeded for Gemini 2.0',
                }
            },
        )
        source, msg = get_error_source_and_message(rate_limit_err)
        self.assertEqual(source, 'Rate Limit Exceeded')
        self.assertIn('quota exceeded', msg)

        server_err = errors.ServerError(
            503, {'error': {'code': 503, 'message': 'Service temporarily down'}}
        )
        source, msg = get_error_source_and_message(server_err)
        self.assertEqual(source, 'Gemini API Unavailable')
        self.assertIn('temporarily unavailable', msg)

        generic_400_err = errors.ClientError(
            400, {'error': {'code': 400, 'message': 'Field name too long'}}
        )
        source, msg = get_error_source_and_message(generic_400_err)
        self.assertEqual(source, 'API Error')
        self.assertEqual(msg, 'Field name too long')

        http_500_err = urllib.error.HTTPError(
            'https://example.com', 500, 'Internal Server Error', {}, None
        )
        source, msg = get_error_source_and_message(http_500_err)
        self.assertEqual(source, 'Gemini API Unavailable')
        self.assertIn('temporarily unavailable', msg)

        http_404_err = urllib.error.HTTPError(
            'https://example.com', 404, 'Not Found', {}, None
        )
        source, msg = get_error_source_and_message(http_404_err)
        self.assertEqual(source, 'HTTP Error')
        self.assertIn('404: Not Found', msg)

        source, msg = get_error_source_and_message(
            TimeoutError('Socket read timed out')
        )
        self.assertEqual(source, 'Connection Timeout')
        self.assertIn('timed out', msg)

        source, msg = get_error_source_and_message(
            ConnectionError('DNS lookup failed')
        )
        self.assertEqual(source, 'Network Error')
        self.assertIn('check network connectivity', msg)

        source, msg = get_error_source_and_message(
            json.JSONDecodeError('Unterminated string', '{"a": 1', 6)
        )
        self.assertEqual(source, 'JSON Parsing Error')
        self.assertIn('Failed to parse LLM structured output', msg)

        source, msg = get_error_source_and_message(
            ValueError('Custom validation failure')
        )
        self.assertEqual(source, 'Generation Error')
        self.assertEqual(msg, 'Custom validation failure')
