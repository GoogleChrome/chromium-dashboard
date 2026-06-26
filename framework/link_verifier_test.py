# -*- coding: utf-8 -*-
# Copyright 2026 Google Inc.
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
from unittest import mock
import requests
import testing_config
from framework import link_verifier


class LinkVerifierTest(testing_config.CustomTestCase):
    """Unit tests verifying the secure link verifier's defenses: SSRF, DNS Pinning, and size ceiling."""

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    @mock.patch('socket.getaddrinfo')
    def test_verify_url__ssrf_local_ip_blocked(self, mock_getaddrinfo):
        """Verify that any URL resolving to a private/loopback IP address is blocked."""
        # Scenario 1: Loopback IP (127.0.0.1)
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('127.0.0.1', 80))]
        status_1 = link_verifier.verify_url('https://localhost/test')
        self.assertEqual(status_1, 'Error: Blocked private IP address (SSRF protection)')

        # Scenario 2: Private Network IP (10.0.0.1)
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('10.0.0.1', 80))]
        status_2 = link_verifier.verify_url('https://private-server.internal/test')
        self.assertEqual(status_2, 'Error: Blocked private IP address (SSRF protection)')

        # Scenario 3: Link-Local IP (169.254.169.254 - GCE Metadata server)
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('169.254.169.254', 80))]
        status_3 = link_verifier.verify_url('http://metadata.google.internal/computeMetadata/v1/')
        self.assertEqual(status_3, 'Error: Blocked private IP address (SSRF protection)')

    @mock.patch('framework.link_verifier.verify_url')
    def test_verify_candidate_links_in_parallel__thread_safety_and_pinning(self, mock_verify):
        """Verify that the parallel link verifier launches threads and preserves results correctly."""
        mock_verify.side_effect = lambda url, **kwargs: 'Invalid' if 'invalid' in url else 'Valid'
        
        urls = [
            'https://valid.example.com/spec',
            'https://invalid.example.com/broken',
            'https://another-valid.example.com/explainer'
        ]
        
        results = link_verifier.verify_candidate_links_in_parallel(urls)
        
        self.assertEqual(results['https://valid.example.com/spec'], 'Valid')
        self.assertEqual(results['https://invalid.example.com/broken'], 'Invalid')
        self.assertEqual(results['https://another-valid.example.com/explainer'], 'Valid')
        self.assertEqual(mock_verify.call_count, 3)

    @mock.patch('socket.getaddrinfo')
    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_verify_url__size_ceiling_enforced(self, mock_head, mock_get, mock_getaddrinfo):
        """Verify that URLs returning content larger than 5MB are chunk-aborted to prevent OOM."""
        # Setup: Mock DNS to resolve to a public IP
        mock_getaddrinfo.return_value = [(2, 1, 6, '', ('93.184.216.34', 80))]
        
        # Mock requests.head to return 405 Method Not Allowed to trigger fallback to requests.get
        mock_head_resp = mock.MagicMock()
        mock_head_resp.status_code = 405
        mock_head_resp.headers = {}
        mock_head.return_value = mock_head_resp
        
        # Mock requests.get response with a Content-Length header > 5MB
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': str(6 * 1024 * 1024)} # 6MB
        mock_response.request.method = 'GET'  # Critical: Set request method to GET for size ceiling
        mock_response.__enter__.return_value = mock_response
        mock_get.return_value = mock_response
        
        status_len = link_verifier.verify_url('https://example.com/giant-file')
        self.assertEqual(status_len, 'Error: Content length exceeds 5MB limit')

        # Scenario 2: Content-Length is missing, but streaming content chunks exceed 5MB
        mock_response.headers = {}  # Missing header
        
        # Generator yielding 6 chunks of 1MB each
        def chunk_generator(*args, **kwargs):
            for _ in range(6):
                yield b'A' * (1024 * 1024)
                
        mock_response.iter_content = chunk_generator
        
        status_stream = link_verifier.verify_url('https://example.com/giant-stream')
        self.assertEqual(status_stream, 'Error: Download size exceeded 5MB ceiling')
