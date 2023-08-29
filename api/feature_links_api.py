# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
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
from internals.core_enums import *
from internals.core_models import FeatureEntry
from internals.feature_links import get_feature_links_summary, get_by_feature_id, get_feature_links_samples
from framework import permissions

class FeatureLinksAPI(basehandlers.APIHandler):
  """FeatureLinksAPI will return the links and its information to the client."""

  def get_feature_links(self, feature_id: int, update_stale_links: bool):
    feature = FeatureEntry.get_by_id(feature_id)
    if not feature:
      self.abort(404, msg='Feature not found')
    return get_by_feature_id(feature_id, update_stale_links)

  def do_get(self, **kwargs):

    feature_id = self.get_int_arg('feature_id', None)
    update_stale_links = self.get_bool_arg('update_stale_links', True)
    if feature_id:
      data, has_stale_links = self.get_feature_links(
          feature_id, update_stale_links)
      return {
          "data": data,
          "has_stale_links": has_stale_links
      }
    else:
      self.abort(400, msg='Missing feature_id')


class FeatureLinksSummaryAPI(basehandlers.APIHandler):
  """FeatureLinksSummaryAPI will return summary of links to the client."""

  @permissions.require_admin_site
  def do_get(self, **kwargs):
    return get_feature_links_summary()

class FeatureLinksSamplesAPI(basehandlers.APIHandler):
  """FeatureLinksSamplesAPI will return sample links to the client."""

  @permissions.require_admin_site
  def do_get(self, **kwargs):
    domain = self.request.args.get('domain', None)
    type = self.request.args.get('type', None)
    is_error = self.get_bool_arg('is_error', None)
    if domain:
      return get_feature_links_samples(domain, type, is_error)