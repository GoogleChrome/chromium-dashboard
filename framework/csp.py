# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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

import base64
import copy
import logging
import os
import six

import flask

import settings


REPORT_ONLY = False
USE_NONCE_ONLY_POLICY = True  # Recommended
REPORT_URI = '/csp'
NONCE_LENGTH = 30

# Note: This is an addition beyond the reference csp.py example code.
HOST_SOURCES = [
    'https://www.gstatic.com',
    'https://accounts.google.com',
    ]

DEFAULT_POLICY = {
    # Disallow base tags.
    'base-uri': ["'none'"],
    # Disallow Flash, etc.
    'object-src': ["'none'"],
    # Strict CSP with fallbacks for browsers not supporting CSP v3.
    # Nonces or hashes must be enabled in order for this CSP to be effective.
    'script-src': [
        # Propagate trust to dynamically created scripts.
        "'strict-dynamic'",
        # Fallback. Ignored in presence of a nonce
        "'unsafe-inline'",
        # Fallback. Ignored in presence of strict-dynamic.
        'https:',
        'http:'
    ] + HOST_SOURCES,
}

# This is a stricter version of the DEFAULT_POLICY.
NONCE_ONLY_POLICY = {
    # Disallow base tags.
    'base-uri': ["'none'"],
    # Disallow Flash, etc.
    'object-src': ["'none'"],
    # Strict CSP with fallbacks for browsers not supporting CSP v3.
    # Nonces or hashes must be enabled in order for this CSP to be effective.
    'script-src': [
        # Fallback. Ignored in presence of a nonce (which is added below).
        "'unsafe-inline'"
    ] + HOST_SOURCES,
}

HEADER_KEY_ENFORCE = 'Content-Security-Policy'
HEADER_KEY_REPORT_ONLY = 'Content-Security-Policy-Report-Only'


def get_nonce():
  """Returns a random nonce."""
  length = NONCE_LENGTH
  b_nonce = base64.b64encode(os.urandom(length * 2))[:length]
  return b_nonce.decode()


def get_default_policy(nonce=None):
  """Returns a copy of the default CSP directives."""
  if USE_NONCE_ONLY_POLICY:
    policy = copy.deepcopy(NONCE_ONLY_POLICY)
  else:
    policy = copy.deepcopy(DEFAULT_POLICY)

  if nonce:
    policy['script-src'].append('\'nonce-%s\'' % nonce)

  return policy


def get_csp_header_key():
  """Returns the right CSP header key (report-only or enforcing mode)."""
  if REPORT_ONLY:
    return HEADER_KEY_REPORT_ONLY
  else:
    return HEADER_KEY_ENFORCE


def build_policy(policy):
  """Builds the CSP policy string from the internal representation."""
  csp_directives = [
      k + ' ' + ' '.join(v) for k, v in six.iteritems(policy) if v is not None
  ]
  if REPORT_URI:
    csp_directives.append('report-uri %s' % REPORT_URI)
  return '; '.join(csp_directives)


def get_headers(nonce):
  """Return a dict of CSP headers."""
  csp_header_key = get_csp_header_key()
  csp_directives = build_policy(get_default_policy(nonce=nonce))
  return {csp_header_key: csp_directives}


def report_handler():
  """Log any CSP violations that are reported to our app."""
  logging.error('CSP Violation: %s' %
                repr(flask.request.data)[:settings.MAX_LOG_LINE])
  return ''
