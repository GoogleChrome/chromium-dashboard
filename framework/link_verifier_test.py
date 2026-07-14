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

"""Tests for SSRF verification and DNS pinning utilities in framework.link_verifier."""

from __future__ import annotations

import socket
from unittest import mock

import testing_config  # Must be imported before the module under test.
from framework import link_verifier


class LinkVerifierTest(testing_config.CustomTestCase):
    """Tests for IP classification, DNS pinning, and SSRF HTTP verification."""

    def test_is_private_ip__loopback_and_rfc1918(self):
        """Verify standard loopback and RFC 1918 private subnets are blocked."""
        self.assertTrue(link_verifier.is_private_ip('127.0.0.1'))
        self.assertTrue(link_verifier.is_private_ip('::1'))
        self.assertTrue(link_verifier.is_private_ip('10.0.0.1'))
        self.assertTrue(link_verifier.is_private_ip('172.16.0.1'))
        self.assertTrue(link_verifier.is_private_ip('192.168.1.100'))
        self.assertFalse(link_verifier.is_private_ip('8.8.8.8'))
        self.assertFalse(link_verifier.is_private_ip('93.184.216.34'))

    def test_is_private_ip__cgnat_link_local_multicast(self):
        """Verify carrier-grade NAT, link-local, and multicast are blocked."""
        self.assertTrue(link_verifier.is_private_ip('100.64.0.1'))
        self.assertTrue(link_verifier.is_private_ip('169.254.169.254'))
        self.assertTrue(link_verifier.is_private_ip('224.0.0.1'))
        self.assertTrue(link_verifier.is_private_ip('0.0.0.0'))

    def test_is_private_ip__non_standard_or_invalid(self):
        """Verify hex, octal, integer literals, and invalid IPs are blocked."""
        self.assertTrue(link_verifier.is_private_ip('0x7f000001'))
        self.assertTrue(link_verifier.is_private_ip('0177.0.0.1'))
        self.assertTrue(link_verifier.is_private_ip('2130706433'))
        self.assertTrue(link_verifier.is_private_ip('256.256.256.256'))
        self.assertFalse(link_verifier.is_private_ip('example.com'))

    @mock.patch('socket.getaddrinfo')
    def test_resolve_hostname_safe__rejects_any_private_ip(
        self, mock_getaddrinfo
    ):
        """Verify DNS rebinding vector with multi-record mix is blocked."""
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80)),
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                '',
                ('169.254.169.254', 80),
            ),
        ]
        with self.assertRaises(link_verifier.SSRFSecurityException) as cm:
            link_verifier.resolve_hostname_safe('attacker-rebind.example.com')
        self.assertIn('prohibited private IP address', str(cm.exception))

    @mock.patch('socket.getaddrinfo')
    def test_resolve_hostname_safe__success(self, mock_getaddrinfo):
        """Verify safe public resolution returns deduplicated IP strings."""
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 80)),
        ]
        ips = link_verifier.resolve_hostname_safe('example.com')
        self.assertEqual(ips, ['93.184.216.34'])

    @mock.patch('wptgen.context._ssrf_safe_opener.open')
    @mock.patch('wptgen.context.validate_url_against_ssrf')
    def test_fetch_url_safe__enforces_size_ceiling(
        self, mock_validate, mock_open
    ):
        """Verify streaming responses exceeding MAX_RESPONSE_SIZE are aborted."""
        mock_validate.return_value = None

        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.info.return_value = {'Content-Type': 'text/html'}
        # Return chunks that cumulatively exceed 5 MB
        chunks = [b'a' * (1024 * 1024)] * 6 + [b'']
        mock_response.read.side_effect = chunks

        mock_open.return_value.__enter__.return_value = mock_response

        with self.assertRaises(link_verifier.SSRFSecurityException) as cm:
            link_verifier.fetch_url_safe('https://example.com/huge-file')
        self.assertIn('exceeded maximum allowed size', str(cm.exception))

    @mock.patch('wptgen.context._ssrf_safe_opener.open')
    @mock.patch('wptgen.context.validate_url_against_ssrf')
    def test_fetch_url_safe__success(self, mock_validate, mock_open):
        """Verify clean URL fetch returns status code, headers, and body bytes."""
        mock_validate.return_value = None

        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.info.return_value = {'Content-Type': 'application/json'}
        mock_response.read.side_effect = [b'{"ok": true}', b'']

        mock_open.return_value.__enter__.return_value = mock_response

        status, headers, body = link_verifier.fetch_url_safe(
            'https://example.com/data'
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers, {'Content-Type': 'application/json'})
        self.assertEqual(body, b'{"ok": true}')
