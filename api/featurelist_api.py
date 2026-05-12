# -*- coding: utf-8 -*-
# Copyright 2026 Google Inc.
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


# from google.appengine.api import users
"""Provides the JSON feed handler for the features list page."""

from framework import basehandlers, permissions, users
from internals import feature_helpers


class FeaturesJsonHandler(basehandlers.EntitiesAPIHandler):
    """Handler for returning features list in JSON format."""

    def do_get(self, **kwargs):
        """Returns feature data in JSON format."""
        user = users.get_current_user()
        feature_list = feature_helpers.get_features_by_impl_status(
            show_unlisted=permissions.can_edit_any_feature(user)
        )
        return feature_list
