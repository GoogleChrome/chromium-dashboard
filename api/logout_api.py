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




from google.oauth2 import id_token
from google.auth.transport import requests
from flask import session


from framework import basehandlers
# from framework import permissions
# from framework import ramcache
# from internals import models

class LogoutAPI(basehandlers.APIHandler):
  """Create a session using the id_token generated by Google Sign-In."""

  def do_post(self):
    session.clear()
    return {'message': 'Done'}

