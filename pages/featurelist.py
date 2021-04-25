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
from framework import permissions
from framework import utils
from internals import models
from framework import ramcache

# from google.appengine.api import users
from framework import users


class FeaturesJsonHandler(basehandlers.FlaskHandler):

  HTTP_CACHE_TYPE = 'private'
  JSONIFY = True

  def get_template_data(self, version=2):
    user = users.get_current_user()
    feature_list = models.Feature.get_chronological(
        version=version,
        show_unlisted=permissions.can_edit_feature(user, None))
    return feature_list


class FeatureListHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'features.html'

  def get_template_data(self, feature_id=None):
    # Note: feature_id is not used here but JS gets it from the URL.

    # This template data is all for filtering.  The actual features
    # are sent by an XHR request for /features.json.

    template_data = {}
    template_data['categories'] = [
      (v, utils.normalized_name(v)) for k,v in
      models.FEATURE_CATEGORIES.iteritems()]
    template_data['IMPLEMENTATION_STATUSES'] = json.dumps([
      {'key': k, 'val': v} for k,v in
      models.IMPLEMENTATION_STATUS.iteritems()])
    template_data['VENDOR_VIEWS'] = json.dumps([
      {'key': k, 'val': v} for k,v in
      models.VENDOR_VIEWS.iteritems()])
    template_data['WEB_DEV_VIEWS'] = json.dumps([
      {'key': k, 'val': v} for k,v in
      models.WEB_DEV_VIEWS.iteritems()])
    template_data['STANDARDS_VALS'] = json.dumps([
      {'key': k, 'val': v} for k,v in
      models.STANDARDIZATION.iteritems()])

    return template_data


class FeatureListXMLHandler(basehandlers.FlaskHandler):

  def get_template_data(self):
    status = self.request.args.get('status', None)
    if status:
      feature_list = models.Feature.get_all_with_statuses(status.split(','))
    else:
      filterby = None
      category = self.request.args.get('category', None)

      # Support setting larger-than-default Atom feed sizes so that web
      # crawlers can use this as a full site feed.
      try:
        max_items = int(self.request.args.get(
            'max-items', settings.RSS_FEED_LIMIT))
      except TypeError:
        max_items = settings.RSS_FEED_LIMIT

      if category is not None:
        for k,v in models.FEATURE_CATEGORIES.iteritems():
          normalized = utils.normalized_name(v)
          if category == normalized:
            filterby = ('category =', k)
            break

      feature_list = models.Feature.get_all( # cached
          limit=max_items,
          filterby=filterby,
          order='-updated')

    return utils.render_atom_feed(self.request, 'Features', feature_list)


routes = [
  # Note: The only requests being made now hit /features.json and
  # /features_v2.json, but both of those cause version == 2.
  # There was logic to accept another version value, but it it was not used.
  (r'/features.json', FeaturesJsonHandler),
  (r'/features_v2.json', FeaturesJsonHandler),

  ('/', basehandlers.Redirector,
   {'location': '/features'}),

  ('/features', FeatureListHandler),
  ('/features/<int:feature_id>', FeatureListHandler),
  ('/features.xml', FeatureListXMLHandler),
]

app = basehandlers.FlaskApplication(routes, debug=settings.DEBUG)
