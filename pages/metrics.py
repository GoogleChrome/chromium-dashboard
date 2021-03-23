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

import json
import logging

import settings
from framework import basehandlers
from framework import utils
from pages import guideforms
import models
import processes
from framework import ramcache
from framework import utils
import util

from google.appengine.api import users



class CssPopularityHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'metrics/css/timeline/popularity.html'

  def get_template_data(self, bucket_id=None):
    # Note: bucket_id is not used, but the JS looks in the URL to get it.
    properties = sorted(
        models.CssPropertyHistogram.get_all().iteritems(), key=lambda x:x[1])
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
        models.FeatureObserverHistogram.get_all().iteritems(), key=lambda x:x[1])
    template_data = {
        'FEATUREOBSERVER_BUCKETS': json.dumps(
            properties, separators=(',',':')),
    }
    return template_data


class OmahaDataHandler(basehandlers.FlaskHandler):

  JSONIFY = True

  def get_template_data(self):
    omaha_data = util.get_omaha_data()
    return omaha_data


# Main URL routes.
routes = [
  ('/metrics', basehandlers.Redirector,
   {'location': '/metrics/css/popularity'}),
  ('/metrics/css', basehandlers.Redirector,
   {'location': '/metrics/css/popularity'}),

  # TODO(jrobbins): These seem like they belong in metrics.py.
  ('/metrics/css/popularity', basehandlers.ConstHandler,
   {'template_path': 'metrics/css/popularity.html'}),
  ('/metrics/css/animated', basehandlers.ConstHandler,
   {'template_path': 'metrics/css/animated.html'}),
  ('/metrics/css/timeline/popularity', CssPopularityHandler),
  ('/metrics/css/timeline/popularity/<int:bucket_id>', CssPopularityHandler),
  ('/metrics/css/timeline/animated', CssAnimatedHandler),
  ('/metrics/css/timeline/animated/<int:bucket_id>', CssAnimatedHandler),
  ('/metrics/feature/popularity', basehandlers.ConstHandler,
   {'template_path': 'metrics/feature/popularity.html'}),
  ('/metrics/feature/timeline/popularity', FeaturePopularityHandler),
  ('/metrics/feature/timeline/popularity/<int:bucket_id>', FeaturePopularityHandler),

  # TODO(jrobbins): util.py has only one thing in it, so maybe move
  # it and this handler to a new omaha.py file.
  ('/omaha_data', OmahaDataHandler),
]

app = basehandlers.FlaskApplication(routes, debug=settings.DEBUG)
