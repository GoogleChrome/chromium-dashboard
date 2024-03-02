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

from framework import basehandlers
from internals import user_models

# We only accept known cue name strings.
ALLOWED_CUES = ['progress-checkmarks']


class CuesAPI(basehandlers.APIHandler):
  """Cues are UI tips that pop up to teach users about some functionality
  when they first encounter it.   Users can dismiss a cue card by clicking
  an X icon.  We store a list of dismissed cues for each user so that
  we do not show the same cue again to that user."""

  # Note: there is no do_get yet because we decide to show cues
  # based on data that is include in the HTML page.

  def do_post(self, **kwargs):
    """Dismisses a cue card for the signed in user."""
    cue = self.get_param('cue', allowed=ALLOWED_CUES)
    unused_user = self.get_current_user(required=True)

    user_models.UserPref.dismiss_cue(cue)
    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}

  def do_get(self, **kwargs):
    """Return a list of the dismissed cue cards"""
    user_pref = user_models.UserPref.get_signed_in_user_pref()

    dismissed_cues = []
    if user_pref:
      dismissed_cues = user_pref.dismissed_cues

    return dismissed_cues
