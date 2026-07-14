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

"""SSRF-protected HTTP link verification utilities wrapping `wptgen.context`.

Provides defense-in-depth against Server-Side Request Forgery (SSRF), DNS
rebinding (TOCTOU), and denial-of-service response size exhaustion when fetching
external documentation and web platform specification links. Delegates low-level
socket IP validation and secure connection opening directly to `wptgen.context`.
"""

from __future__ import annotations

import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request

from wptgen.context import (
    _ssrf_safe_opener,
    validate_ip_against_ssrf,
    validate_url_against_ssrf,
)

MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5 MB maximum streaming response ceiling


class SSRFSecurityException(Exception):
    """Raised when a URL or hostname resolves to a prohibited or private IP address."""


def is_private_ip(ip_str: str) -> bool:
    """Check whether an IP address string falls into private or prohibited ranges.

    Delegates to `wptgen.context.validate_ip_against_ssrf` and supplements with
    carrier-grade NAT (`100.64.0.0/10`) and zero-network checking. If `ip_str` is
    not a valid numeric/hex/octal IP literal (e.g., a hostname), returns `False`.
    """
    ip_str = ip_str.strip()
    if not ip_str:
        return False

    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        try:
            if '.' in ip_str and ':' not in ip_str:
                parts = ip_str.split('.')
                if all(
                    p.isdigit() or p.startswith(('0x', '0X')) for p in parts
                ):
                    return True
            val = int(ip_str, 0)
            if 0 <= val <= 0xFFFFFFFF:
                return True
        except (ValueError, OverflowError):
            return False
        return False

    try:
        validate_ip_against_ssrf(str(addr))
        if isinstance(addr, ipaddress.IPv4Address):
            if addr in ipaddress.ip_network(
                '100.64.0.0/10'
            ) or addr in ipaddress.ip_network('0.0.0.0/8'):
                return True
        return False
    except (ValueError, OSError):
        return True


def resolve_hostname_safe(hostname: str) -> list[str]:
    """Resolve a hostname to safe IP addresses, rejecting prohibited targets.

    Inspects all resolved A/AAAA DNS records via `socket.getaddrinfo` and verifies
    each address against `is_private_ip()`. Raises `SSRFSecurityException` if any
    resolved address is prohibited.
    """
    if not hostname or not isinstance(hostname, str):
        raise SSRFSecurityException(
            'Invalid or empty hostname provided for resolution.'
        )
    if is_private_ip(hostname):
        raise SSRFSecurityException(
            f'Target hostname is a prohibited private IP literal: {hostname}'
        )
    try:
        addrinfos = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, UnicodeError) as e:
        raise SSRFSecurityException(
            f'DNS resolution failed for hostname {hostname}: {e}'
        ) from e
    if not addrinfos:
        raise SSRFSecurityException(
            f'No DNS records found for hostname: {hostname}'
        )

    resolved_ips: list[str] = []
    for addrinfo in addrinfos:
        sockaddr = addrinfo[4]
        if sockaddr and len(sockaddr) >= 1:
            ip_str = str(sockaddr[0])
            if is_private_ip(ip_str):
                raise SSRFSecurityException(
                    f'Hostname {hostname} resolved to prohibited private IP address: {ip_str}'
                )
            if ip_str not in resolved_ips:
                resolved_ips.append(ip_str)
    return resolved_ips


def fetch_url_safe(
    url: str,
    max_size: int = MAX_RESPONSE_SIZE,
    timeout: float = 10.0,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    """Fetch an external HTTP/HTTPS URL with SSRF protection and size limits.

    Delegates fast-path URL validation (`validate_url_against_ssrf`) and secure
    connection execution (`_ssrf_safe_opener.open`) directly to `wptgen.context`.
    Streams the response body in 64 KB chunks up to `max_size` bytes to prevent
    memory exhaustion or zip-bomb denial of service.
    """
    try:
        validate_url_against_ssrf(url)
    except (ValueError, OSError) as e:
        raise SSRFSecurityException(
            f'SSRF validation failed for URL {url}: {e}'
        ) from e

    req_headers = headers or {
        'User-Agent': 'Mozilla/5.0 (compatible; WPT-Gen/1.0)'
    }
    req = urllib.request.Request(url, headers=req_headers)

    try:
        with _ssrf_safe_opener.open(req, timeout=timeout) as response:
            status_code = getattr(response, 'status', 200)
            resp_headers = (
                dict(response.info()) if hasattr(response, 'info') else {}
            )
            body_chunks: list[bytes] = []
            total_bytes = 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_size:
                    raise SSRFSecurityException(
                        f'Response body exceeded maximum allowed size of {max_size} bytes.'
                    )
                body_chunks.append(chunk)
            return status_code, resp_headers, b''.join(body_chunks)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        ValueError,
        OSError,
    ) as e:
        if isinstance(e, SSRFSecurityException):
            raise
        raise SSRFSecurityException(
            f'HTTP request failed or blocked for URL {url}: {e}'
        ) from e
