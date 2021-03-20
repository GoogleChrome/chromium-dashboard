from __future__ import division
from __future__ import print_function

# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc.
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

__author__ = 'ericbidelman@chromium.org (Eric Bidelman)'

import json
import logging

import settings
from framework import basehandlers
from framework import utils
from pages import guideforms
import models
import processes
from framework import ramcache
import util

from google.appengine.api import users


def normalized_name(val):
  return val.lower().replace(' ', '').replace('/', '')


class FeatureDetailHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'feature.html'

  def get_template_data(self, feature_id):
    f = models.Feature.get_by_id(feature_id)
    if f is None:
      self.abort(404)

    if f.deleted:
      # TODO(jrobbins): Check permissions and offer option to undelete.
      self.abort(404)

    feature_process = processes.ALL_PROCESSES.get(
        f.feature_type, processes.BLINK_LAUNCH_PROCESS)
    field_defs = guideforms.DISPLAY_FIELDS_IN_STAGES
    template_data = {
        'process_json': json.dumps(processes.process_to_dict(feature_process)),
        'field_defs_json': json.dumps(field_defs),
        'feature': f.format_for_template(),
        'feature_id': f.key().id(),
        'feature_json': json.dumps(f.format_for_template()),
        'updated_display': f.updated.strftime("%Y-%m-%d"),
        'new_crbug_url': f.new_crbug_url(),
    }
    return template_data



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


class SamplesHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'samples.html'

  def get_template_data(self):
    feature_list = models.Feature.get_shipping_samples() # cached

    template_data = {}
    template_data['FEATURES'] = json.dumps(feature_list, separators=(',',':'))
    template_data['CATEGORIES'] = [
      (v, normalized_name(v)) for k,v in
      models.FEATURE_CATEGORIES.iteritems()]
    template_data['categories'] = dict([
      (v, normalized_name(v)) for k,v in
      models.FEATURE_CATEGORIES.iteritems()])

    return template_data


class SamplesJSONHandler(basehandlers.FlaskHandler):

  JSONIFY = True

  def get_template_data(self):
    feature_list = models.Feature.get_shipping_samples() # cached
    return feature_list


class SamplesXMLHandler(basehandlers.FlaskHandler):

  def get_template_data(self):
    feature_list = models.Feature.get_shipping_samples() # cached

    # Support setting larger-than-default Atom feed sizes so that web
    # crawlers can use this as a full site feed.
    try:
      max_items = int(self.request.args.get(
          'max-items', settings.RSS_FEED_LIMIT))
    except TypeError:
      max_items = settings.RSS_FEED_LIMIT

    return utils.render_atom_feed(self.request, 'Samples', feature_list)


# Main URL routes.
routes = [

  ('/samples', SamplesHandler),
  ('/samples.json', SamplesJSONHandler),
  ('/samples.xml', SamplesXMLHandler),

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
