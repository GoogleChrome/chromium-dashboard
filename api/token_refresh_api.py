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

from __future__ import division
from __future__ import print_function

import logging

from framework import basehandlers
from framework import xsrf
from internals import models


class TokenRefreshAPI(basehandlers.APIHandler):
  """We allow a user to request a new XSRF token so that users may have
     editing sessions much longer than the token expiration time.
     An attacker cannot use this feature to obtain an XSRF token because
       (1) we check that the incoming request has a token that is valid
           for the current user, even if it may be expired,
       (2) CORS prevents the response from being accessed,
       (2) this handler has no side-effects, so an attacker who makes these
           requests without being able to read the response achieves nothing.
  """

  def validate_token(self, token, email):
    """If the token is not valid, raise an exception."""
    # This is a separate method so that the refresh handler can override it.
    xsrf.validate_token(token, email, timeout=xsrf.REFRESH_TOKEN_TIMEOUT_SEC)

  # Note: we use only POST instead of GET to avoid attacks that use GETs.
  def do_post(self):
    """Return a new XSRF token for the current user."""
    user = self.get_current_user()
    result = {
        'token': xsrf.generate_token(user.email()),
        'token_expires_sec': xsrf.token_expires_sec(),
        }
    return result
