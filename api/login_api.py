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

import logging

from google.oauth2 import id_token
from google.auth.transport import requests
from flask import session

from framework import basehandlers
from framework import xsrf
import settings


class LoginAPI(basehandlers.APIHandler):
  """Create a session using the credential generated by Google Sign-In."""

  def do_post(self):
    # TODO(jrobbins): Remove id_token after next deployment.
    token = (self.get_param('id_token', required=False) or
             self.get_param('credential'))
    message = "Unable to Authenticate"

    try:
      idinfo = id_token.verify_oauth2_token(
          token, requests.Request(),
          settings.GOOGLE_SIGN_IN_CLIENT_ID)
      user_info = {
          'email': idinfo['email'],
          }
      signature = xsrf.generate_token(str(user_info))
      session['signed_user_info'] = user_info, signature
      message = "Done"
      # print(idinfo['email'], file=sys.stderr)
    except ValueError:
      message = "Invalid token"

    return {'message': message}
