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

from framework import basehandlers
from internals import metrics_models
from internals import fetchchannels


class CssPopularityHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'metrics/css/timeline/popularity.html'

  def get_template_data(self, bucket_id=None):
    # Note: bucket_id is not used, but the JS looks in the URL to get it.
    properties = sorted(
        list(metrics_models.CssPropertyHistogram.get_all().items()),
        key=lambda x:x[1])
    template_data = {
        'CSS_PROPERTY_BUCKETS': json.dumps(
            properties, separators=(',',':')),
        }
    return template_data


class CssAnimatedHandler(CssPopularityHandler):

  TEMPLATE_PATH = 'metrics/css/timeline/animated.html'
  # The logic and data is the same, but it is filtered differenly in JS.


class FeaturePopularityHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'metrics/feature/timeline/popularity.html'

  def get_template_data(self, bucket_id=None):
    # Note: bucket_id is not used, but the JS looks in the URL to get it.
    properties = sorted(
        metrics_models.FeatureObserverHistogram.get_all().items(),
        key=lambda x:x[1])
    template_data = {
        'FEATUREOBSERVER_BUCKETS': json.dumps(
            properties, separators=(',',':')),
    }
    return template_data


class OmahaDataHandler(basehandlers.FlaskHandler):

  JSONIFY = True

  def get_template_data(self):
    omaha_data = fetchchannels.get_omaha_data()
    return omaha_data
