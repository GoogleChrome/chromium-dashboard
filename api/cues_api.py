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
import models

# We only accept known cue name strings.
ALLOWED_CUES = ['progress-checkmarks']


class CuesAPI(basehandlers.APIHandler):
  """Cues are UI tips that pop up to teach users about some functionality
  when they first encounter it.   Users can dismiss a cue card by clicking
  an X icon.  We store a list of dismissed cues for each user so that
  we do not show the same cue again to that user."""

  # Note: there is no do_get yet because we decide to show cues
  # based on data that is include in the HTML page.

  def do_post(self):
    """Dismisses a cue card for the signed in user."""
    json_body = self.request.get_json()
    cue = json_body.get('cue')
    if cue not in ALLOWED_CUES:
      logging.info('Unexpected cue: %r', cue)
      self.abort(400)

    user = self.get_current_user()
    if not user:
      logging.info('User must be signed in before dismissing cues')
      self.abort(400)

    models.UserPref.dismiss_cue(cue)
    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}
