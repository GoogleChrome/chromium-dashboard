# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
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


from framework import basehandlers
from internals import models


class SettingsAPI(basehandlers.APIHandler):
  """Users can store their settings preferences such as whether to get 
  notification from the features they starred."""

  def do_post(self):
    """Set the user settings (currently only the notify_as_starrer)"""
    user_pref = models.UserPref.get_signed_in_user_pref()
    if not user_pref:
      self.abort(403, msg='User must be signed in')
    new_notify = self.get_bool_param('notify')
    user_pref.notify_as_starrer = new_notify
    user_pref.put()
    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}

  def do_get(self):
    """Return the user settings (currently only the notify_as_starrer)"""
    user_pref = models.UserPref.get_signed_in_user_pref()
    if not user_pref:
      self.abort(404, msg='User preference not found')

    return {'notify_as_starrer': user_pref.notify_as_starrer}