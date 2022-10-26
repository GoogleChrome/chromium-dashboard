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
from internals import core_models
from internals import core_enums

# from google.appengine.api import users
from framework import users


class FeaturesJsonHandler(basehandlers.FlaskHandler):

  HTTP_CACHE_TYPE = 'private'
  JSONIFY = True

  def get_template_data(self, **kwargs):
    user = users.get_current_user()
    feature_list = core_models.Feature.get_chronological(
        show_unlisted=permissions.can_edit_any_feature(user))
    return feature_list


class FeatureListHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'features.html'

  def get_template_data(self, **kwargs):
    # Note: feature_id is not used here but JS gets it from the URL.

    # This template data is all for filtering.  The actual features
    # are sent by an XHR request for /features.json.

    template_data = {}
    template_data['categories'] = [
      (v, utils.normalized_name(v)) for k,v in
      list(core_enums.FEATURE_CATEGORIES.items())]
    template_data['IMPLEMENTATION_STATUSES'] = json.dumps([
      {'key': k, 'val': v} for k,v in
      list(core_enums.IMPLEMENTATION_STATUS.items())])
    template_data['VENDOR_VIEWS'] = json.dumps([
      {'key': k, 'val': v} for k,v in
      list(core_enums.VENDOR_VIEWS.items())])
    template_data['WEB_DEV_VIEWS'] = json.dumps([
      {'key': k, 'val': v} for k,v in
      list(core_enums.WEB_DEV_VIEWS.items())])
    template_data['STANDARDS_VALS'] = json.dumps([
      {'key': k, 'val': v} for k,v in
      list(core_enums.STANDARDIZATION.items())])

    return template_data
