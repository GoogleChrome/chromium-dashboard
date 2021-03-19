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
import notifier


class StarsAPI(basehandlers.APIHandler):
  """Users can star a feature by clicking a star icon.  The client-side has
  logic to toggle the star icon.  When a user has starred a feature, they
  will be sent notification emails about changes to that feature."""

  def do_get(self):
    """Return a list of all starred feature IDs for the signed-in user."""
    user = self.get_current_user()
    if user:
      feature_ids = notifier.FeatureStar.get_user_stars(user.email())
    else:
      feature_ids = []  # Anon users cannot star features.

    data = {
        'featureIds': feature_ids,
        }
    return data

  def do_post(self):
    """Set or clear a star on the specified feature."""
    json_body = self.request.get_json(force=True)
    feature_id = json_body.get('featureId')
    starred = json_body.get('starred', True)

    if type(feature_id) != int:
      logging.info('Invalid feature_id: %r', feature_id)
      self.abort(400)

    feature = models.Feature.get_feature(feature_id)
    if not feature:
      logging.info('feature not found: %r', feature_id)
      self.abort(404)

    user = self.get_current_user()
    if not user:
      logging.info('User must be signed in before starring')
      self.abort(400)

    notifier.FeatureStar.set_star(user.email(), feature_id, starred)
    # Callers don't use the JSON response for this API call.
    return {'message': 'Done'}
