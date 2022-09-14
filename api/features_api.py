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
from framework import permissions
from framework import rediscache
from framework import users
from internals import core_models
from internals import search


class FeaturesAPI(basehandlers.APIHandler):
  """Features are the the main records that we track."""

  def get_one_feature(self, feature_id):
    features = core_models.Feature.get_by_ids([feature_id])
    if not features:
      self.abort(404, msg='Feature %r not found' % feature_id)
    return features[0]

  def do_search(self):
    user = users.get_current_user()
    # Show unlisted features to site editors or admins.
    show_unlisted_features = permissions.can_edit_any_feature(user)
    features_on_page = None

    # Query-string parameter 'milestone' is provided
    if self.request.args.get('milestone') is not None:
      try:
        milestone = int(self.request.args.get('milestone'))
        features_by_type = core_models.Feature.get_in_milestone(
          show_unlisted=show_unlisted_features,
          milestone=milestone)
        total_count = sum(len(features_by_type[t]) for t in features_by_type)
        return {
            'features_by_type': features_by_type,
            'total_count': total_count,
            }
      except ValueError:
        self.abort(400, msg='Invalid  Milestone')

    user_query = self.request.args.get('q', '')
    sort_spec = self.request.args.get('sort')
    features_on_page, total_count = search.process_query(
        user_query, sort_spec=sort_spec, show_unlisted=show_unlisted_features)

    return {
        'total_count': total_count,
        'features': features_on_page,
        }

  def do_get(self, feature_id=None):
    """Handle GET requests for a single feature or a search."""
    if feature_id:
      return self.get_one_feature(feature_id)
    else:
      return self.do_search()

  # TODO(jrobbins): do_post

  # TODO(jrobbins): do_patch

  @permissions.require_admin_site
  def do_delete(self, feature_id):
    """Delete the specified feature."""
    # TODO(jrobbins): implement undelete UI.  For now, use cloud console.
    feature = self.get_specified_feature(feature_id=feature_id)
    feature.deleted = True
    feature.put()
    rediscache.delete_keys_with_prefix(core_models.feature_cache_prefix())

    return {'message': 'Done'}
