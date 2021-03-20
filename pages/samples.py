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
import models


class SamplesHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'samples.html'

  def get_template_data(self):
    feature_list = models.Feature.get_shipping_samples() # cached

    template_data = {}
    template_data['FEATURES'] = json.dumps(feature_list, separators=(',',':'))
    template_data['CATEGORIES'] = [
      (v, utils.normalized_name(v)) for k,v in
      models.FEATURE_CATEGORIES.iteritems()]
    template_data['categories'] = dict([
      (v, utils.normalized_name(v)) for k,v in
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


routes = [
  ('/samples', SamplesHandler),
  ('/samples.json', SamplesJSONHandler),
  ('/samples.xml', SamplesXMLHandler),
]

app = basehandlers.FlaskApplication(routes, debug=settings.DEBUG)
