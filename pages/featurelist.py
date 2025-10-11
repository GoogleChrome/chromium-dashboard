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

import json
import logging

import settings
from framework import basehandlers
from framework import permissions
from framework import utils
from internals import core_enums
from internals import feature_helpers

# from google.appengine.api import users
from framework import users


class FeaturesJsonHandler(basehandlers.FlaskHandler):

  HTTP_CACHE_TYPE = 'private'
  JSONIFY = True

  def get_template_data(self, **kwargs):
    user = users.get_current_user()
    feature_list = feature_helpers.get_features_by_impl_status(
        show_unlisted=permissions.can_edit_any_feature(user))
    return feature_list
