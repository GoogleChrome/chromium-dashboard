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
from internals import feature_links


class FeatureLinksAPI(basehandlers.APIHandler):
  """FeatureLinksAPI will return the links and its information to the client."""

  def get_feature_links(self, feature_id: int):
    feature = FeatureEntry.get_by_id(feature_id)
    if not feature:
      self.abort(404, msg='Feature not found')
    return feature_links.get_by_feature_id(feature_id)

  def do_get(self, **kwargs):

    feature_id = self.get_int_arg('feature_id', None)
    if feature_id:
      return self.get_feature_links(feature_id)
    else:
      self.abort(400, msg='Missing feature_id')
