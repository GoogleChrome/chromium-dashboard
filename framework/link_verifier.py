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

"""Thread-safe, SSRF-protected, and DNS-pinned HTTP link verifier."""

import socket
import urllib.parse
import ipaddress
import requests
import urllib3
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress insecure request warnings due to our intentional DNS IP-pinning (virtual host TLS mismatch)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Private IP ranges (SSRF block targets)
PRIVATE_NETWORKS = [
    ipaddress.ip_network('127.0.0.0/8'),       # Loopback
    ipaddress.ip_network('10.0.0.0/8'),        # RFC 1918
    ipaddress.ip_network('172.16.0.0/12'),     # RFC 1918
    ipaddress.ip_network('192.168.0.0/16'),    # RFC 1918
    ipaddress.ip_network('169.254.0.0/16'),    # Link-local / GCP Metadata
    ipaddress.ip_network('0.0.0.0/8'),         # Current network
    ipaddress.ip_network('::1/128'),           # IPv6 Loopback
    ipaddress.ip_network('fe80::/10'),         # IPv6 Link-local
    ipaddress.ip_network('fc00::/7'),          # IPv6 Unique local
]

_dns_pinning_state = threading.local()

def get_thread_dns_pins():
    if not hasattr(_dns_pinning_state, 'pins'):
        _dns_pinning_state.pins = {}
    return _dns_pinning_state.pins

_original_getaddrinfo = socket.getaddrinfo

def secure_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host:
        normalized_host = host.lower().strip()
        pins = get_thread_dns_pins()
        if normalized_host in pins:
            return _original_getaddrinfo(pins[normalized_host], port, family, type, proto, flags)
    return _original_getaddrinfo(host, port, family, type, proto, flags)

# Monkey-patch socket.getaddrinfo globally to intercept and pin DNS resolutions safely!
socket.getaddrinfo = secure_getaddrinfo


def is_private_ip(ip_str: str) -> bool:
    """Returns True if the IP address belongs to a private or loopback range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in PRIVATE_NETWORKS)
    except ValueError:
        return True  # Treat invalid IPs as unsafe


def resolve_hostname_safe(hostname: str) -> str | None:
    """Resolves a hostname to an IP address, checking it against the SSRF blacklist."""
    try:
        # Use original getaddrinfo to resolve the actual IP before pinning
        addr_info = _original_getaddrinfo(hostname, None)
        for family, socktype, proto, canonname, sockaddr in addr_info:
            ip = sockaddr[0]
            if not is_private_ip(ip):
                return ip
        return None
    except socket.gaierror:
        return None


class SafeDNSPinner:
    def __init__(self, hostname: str, safe_ip: str):
        self.hostname = hostname.lower().strip()
        self.safe_ip = safe_ip
    def __enter__(self):
        get_thread_dns_pins()[self.hostname] = self.safe_ip
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        get_thread_dns_pins().pop(self.hostname, None)


def verify_url(url: str, max_redirects: int = 5, timeout: int = 5) -> str:
    """Verifies a single documentation link safely, protecting against SSRF and OOM."""
    current_url = url
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChromeStatus-LinkVerifier/2.0'
    }
    MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5MB size ceiling

    for redirect_count in range(max_redirects + 1):
        try:
            parsed = urllib.parse.urlparse(current_url)
            if parsed.scheme not in ('http', 'https'):
                return 'Error: Blocked untrusted URL (unallowed scheme)'
                
            hostname = parsed.hostname
            if not hostname:
                return 'Error: Invalid hostname'
                
            # 1. Resolve and validate IP (SSRF Block)
            ip = resolve_hostname_safe(hostname)
            if not ip:
                return 'Error: Blocked private IP address (SSRF protection)'
                
            # 2. DNS Pinning: Reconstruct URL with IP address to prevent DNS rebinding
            with SafeDNSPinner(hostname, ip):
                # 3. Perform HTTP HEAD request
                try:
                    response = requests.head(
                        current_url,
                        headers=headers,
                        allow_redirects=False,
                        timeout=timeout,
                        verify=False
                    )
                    # Fall back to GET if HEAD is not allowed (common on some doc sites)
                    if response.status_code in (405, 501, 403):
                        response = requests.get(
                            current_url,
                            headers=headers,
                            allow_redirects=False,
                            timeout=timeout,
                            stream=True,
                            verify=False
                        )
                except requests.RequestException as e:
                    return f'Error: {e}'
                    
            # Check for redirect (3xx)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get('Location')
                if not location:
                    return 'Error: Missing redirect Location header'
                
                # Resolve relative redirects
                current_url = urllib.parse.urljoin(current_url, location)
                continue
                
            # Check for size ceiling on GET requests
            if response.status_code == 200:
                cl = response.headers.get('Content-Length')
                if cl and int(cl) > MAX_RESPONSE_SIZE:
                    return 'Error: Content length exceeds 5MB limit'
                
                # Stream content chunks to prevent OOM on missing Content-Length
                if response.request.method == 'GET':
                    downloaded_bytes = 0
                    try:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                            if chunk:
                                downloaded_bytes += len(chunk)
                                if downloaded_bytes > MAX_RESPONSE_SIZE:
                                    return 'Error: Download size exceeded 5MB ceiling'
                    except Exception as e:
                        return f'Error reading stream: {e}'
            
            # Check for success (2xx)
            if 200 <= response.status_code < 300:
                return 'Valid'
                
            return f'Invalid status: {response.status_code}'
            
        except Exception as e:
            return f'Error: {e}'
            
    return f'Error: Exceeded max redirects ({max_redirects})'


def verify_candidate_links_in_parallel(urls: list[str], max_workers: int = 5, timeout: int = 5) -> dict[str, str]:
    """Verifies multiple links concurrently using a thread pool."""
    results = {}
    if not urls:
        return results
    unique_urls = list(set(urls))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(verify_url, url, timeout=timeout): url
            for url in unique_urls
        }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception as e:
                results[url] = f'Error: {e}'
    # Preserve duplicate input URLs in the output map
    return {url: results.get(url, 'Error: Unknown') for url in urls}
