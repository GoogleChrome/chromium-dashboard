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

from datetime import datetime

from api import converters
from framework import basehandlers
from framework import permissions
from framework import rediscache
from framework import users
from internals.core_enums import *
from internals.core_models import FeatureEntry
from internals.data_types import VerboseFeatureDict
from internals import feature_helpers
from internals import search


class FeaturesAPI(basehandlers.APIHandler):
  """Features are the the main records that we track."""

  def get_one_feature(self, feature_id: int) -> VerboseFeatureDict:
    feature = FeatureEntry.get_by_id(feature_id)
    if not feature:
      self.abort(404, msg='Feature %r not found' % feature_id)
    return converters.feature_entry_to_json_verbose(feature)

  def do_search(self):
    user = users.get_current_user()
    # Show unlisted features to site editors or admins.
    show_unlisted_features = permissions.can_edit_any_feature(user)
    features_on_page = None

    # Query-string parameter 'milestone' is provided
    milestone = self.get_int_arg('milestone')
    if milestone:
      features_by_type = feature_helpers.get_in_milestone(
        show_unlisted=show_unlisted_features, milestone=milestone)
      total_count = sum(len(features_by_type[t]) for t in features_by_type)
      return {
          'features_by_type': features_by_type,
          'total_count': total_count,
          }

    user_query = self.request.args.get('q', '')
    sort_spec = self.request.args.get('sort')
    num = self.get_int_arg('num', search.DEFAULT_RESULTS_PER_PAGE)
    start = self.get_int_arg('start', 0)

    show_enterprise = 'feature_type' in user_query
    try:
      features_on_page, total_count = search.process_query(
          user_query, sort_spec=sort_spec, show_unlisted=show_unlisted_features,
          show_enterprise=show_enterprise, start=start, num=num)
    except ValueError:
      self.abort(400, msg=str(ValueError))

    return {
        'total_count': total_count,
        'features': features_on_page,
        }

  def do_get(self, **kwargs):
    """Handle GET requests for a single feature or a search."""
    # TODO(danielrsmith): This request gives two independent return types
    # based on whether a feature_id was specified. Determine the best
    # way to handle this in a strictly-typed manner and implement it.
    feature_id = kwargs.get('feature_id', None)
    if feature_id:
      return self.get_one_feature(feature_id)
    return self.do_search()

  # TODO(jrobbins): do_post

  def do_patch(self, **kwargs):
    """Handle PATCH requests to update fields in a single feature."""
    feature_id = kwargs['feature_id']
    body = self.get_json_param_dict()

    # update_fields represents which fields will be updated by this request.
    fields_to_update = body.get('update_fields', [])
    feature: FeatureEntry | None = FeatureEntry.get_by_id(feature_id)
    if feature is None:
      self.abort(404, msg=f'Feature {feature_id} not found')

    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    # Update each field specified in the field mask.
    for field in fields_to_update:
      # Each field specified should be a valid field that exists on the entity.
      if not hasattr(feature, field):
        self.abort(400, msg=f'FeatureEntry has no attribute {field}.')
      if field in FeatureEntry.FIELDS_IMMUTABLE_BY_USER:
        self.abort(400, f'FeatureEntry field {field} is immutable.')
      setattr(feature, field, body.get(field, None))

    feature.updater_email = self.get_current_user().email()
    feature.updated = datetime.now()
    feature.put()
    return {'message': f'Feature {feature_id} updated.'}

  @permissions.require_admin_site
  def do_delete(self, **kwargs) -> dict[str, str]:
    """Delete the specified feature."""
    # TODO(jrobbins): implement undelete UI.  For now, use cloud console.
    feature_id = kwargs.get('feature_id', None)
    feature = self.get_specified_feature(feature_id=feature_id)
    if feature is None:
      return {'message': 'ID does not match any feature.'}
    feature.deleted = True
    feature.put()
    rediscache.delete_keys_with_prefix(FeatureEntry.feature_cache_prefix())

    # Write for new FeatureEntry entity.
    feature_entry: FeatureEntry | None = (
        FeatureEntry.get_by_id(feature_id))
    if feature_entry:
      feature_entry.deleted = True
      feature_entry.put()

    return {'message': 'Done'}
