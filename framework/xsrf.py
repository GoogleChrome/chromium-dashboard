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
import hmac
import logging
import random
import string
import time
import hashlib

from framework import constants
from framework import secrets


# TODO(jrobbins): 2 hours is too short for usability, but a longer value
# is not secure enough.  So, we will go with 2 hours and also implement
# token refresh as done in Monorail.

# This is how long tokens are valid.
TOKEN_TIMEOUT_SEC = 2 * constants.SECS_PER_HOUR

# The token refresh servlet accepts old tokens to generate new ones, but
# we still impose a limit on how old they can be.
REFRESH_TOKEN_TIMEOUT_SEC = 10 * constants.SECS_PER_DAY

# When the JS on a page decides whether or not it needs to refresh the
# XSRF token before submitting a form, there could be some clock skew,
# so we subtract a little time to avoid having the JS use an existing
# token that the server might consider expired already.
TOKEN_TIMEOUT_MARGIN_SEC = 5 * constants.SECS_PER_MINUTE

# When checking that the token is not from the future, allow a little
# margin for the possibliity that the clock of the GAE instance that
# generated the token could be a little ahead of the one checking.
CLOCK_SKEW_SEC = 5

DELIMITER = ':'.encode()


def generate_token(user_email, token_time=None):
  """Return a security token specifically for the given user.
  Args:
    user_email: email addr of the user viewing an HTML form.  This can
        be None for anon vistors.
    token_time: Time at which the token is generated in seconds since the epoch.
  Returns:
    A url-safe security token.  The token is a string with the digest
    the email and time, followed by plain-text copy of the time that is
    used in validation.
  Raises:
    ValueError: if the XSRF secret was not configured.
  """
  token_time = token_time or int(time.time())
  token_time = str(token_time).encode()
  digester = hmac.new(secrets.get_xsrf_secret().encode(), digestmod=hashlib.sha256)
  digester.update(user_email.encode() if user_email else b'')
  digester.update(DELIMITER)
  digester.update(token_time)
  digest = digester.digest()
  binary_token = base64.urlsafe_b64encode(digest+ DELIMITER + token_time)
  token = binary_token.decode()
  return token


def validate_token(
    token, user_email, timeout=TOKEN_TIMEOUT_SEC):
  """Return True if the given token is valid for the given scope.
  Args:
    token: String token that was presented by the user.
    user_email: user email addr.
    timeout: int max token age in seconds.
  Raises:
    TokenIncorrect: if the token is missing or invalid.
  """
  if not token:
    raise TokenIncorrect('missing token')
  try:
    decoded = base64.urlsafe_b64decode(token)
    token_time = int(decoded.split(DELIMITER)[-1])
  except (TypeError, ValueError):
    raise TokenIncorrect('could not decode token')
  now = int(time.time())

  # The given token should match the generated one with the same time.
  expected_token = generate_token(user_email, token_time=token_time)
  if len(token) != len(expected_token):
    raise TokenIncorrect('presented token is wrong size')

  # Perform constant time comparison to avoid timing attacks
  different = 0
  for res in zip(str(token), str(expected_token)):
    different |= ord(res[0]) ^ ord(res[1])
  if different:
    raise TokenIncorrect(
        'presented token does not match expected token: %r != %r' % (
            token, expected_token))

  # We reject tokens from the future.
  if token_time > now + CLOCK_SKEW_SEC:
    raise TokenIncorrect('token is from future')

  # We check expiration last so that we only raise the expriration error
  # if the token would have otherwise been valid.
  if now - token_time > timeout:
    raise TokenIncorrect('token has expired')


def token_expires_sec():
  """Return timestamp when current tokens will expire, minus a safety margin."""
  now = int(time.time())
  return now + TOKEN_TIMEOUT_SEC - TOKEN_TIMEOUT_MARGIN_SEC


class Error(Exception):
  """Base class for errors from this module."""
  pass


# Caught separately in servlet.py
class TokenIncorrect(Error):
  """The POST body has an incorrect URL Command Attack token."""
  pass
