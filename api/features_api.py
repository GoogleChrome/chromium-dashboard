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
from framework import permissions
from framework import ramcache
from framework import users
from internals import models

class FeaturesAPI(basehandlers.APIHandler):
  """Features are the the main records that we track."""

  def do_get(self):
    user = users.get_current_user()
    show_unlisted_features = permissions.can_edit_feature(user, None)
    feature_list = None

    # Query-string parameter 'milestone' is provided
    if self.request.args.get('milestone') is not None:
      try:
        milestone = int(self.request.args.get('milestone'))
        feature_list = models.Feature.get_in_milestone(
          show_unlisted=show_unlisted_features, 
          milestone=milestone)
      except ValueError:
        self.abort(400, msg='Invalid  Milestone')

    # No Query-string parameter is provided
    if feature_list is None:
      feature_list = models.Feature.get_chronological(
          version=2,
          show_unlisted=show_unlisted_features)

    return feature_list

  # TODO(jrobbins): do_post

  # TODO(jrobbins): do_patch

  @permissions.require_admin_site
  def do_delete(self, feature_id):
    """Delete the specified feature."""
    # TODO(jrobbins): implement undelete UI.  For now, use cloud console.
    feature = self.get_specified_feature(feature_id=feature_id)
    feature.deleted = True
    feature.put()
    ramcache.flush_all()

    return {'message': 'Done'}
