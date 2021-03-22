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
import flask

from google.appengine.api import users


def require_edit_permission(handler):
  """Handler decorator to require the user have edit permission."""
  def check_login(self, *args, **kwargs):
    user = users.get_current_user()
    if not user:
      return self.redirect(users.create_login_url(self.request.uri))
    elif not self.user_can_edit(user):
      flask.abort(403)
      return

    return handler(self, *args, **kwargs) # Call the handler method
  return check_login
