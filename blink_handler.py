from __future__ import division
from __future__ import print_function

# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc.
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

import collections
import json
import logging
import os
import yaml

import common
import models
import ramcache
import settings
import util
from schedule import construct_chrome_channels_details


class BlinkHandler(common.FlaskHandler):

  TEMPLATE_PATH = 'admin/blink.html'

  def __update_subscribers_list(self, add=True, user_id=None, blink_component=None, primary=False):
    if not user_id or not blink_component:
      return False

    user = models.FeatureOwner.get_by_id(long(user_id))
    if not user:
      return True

    if primary:
      if add:
        user.add_as_component_owner(blink_component)
      else:
        user.remove_as_component_owner(blink_component)
    else:
      if add:
        user.add_to_component_subscribers(blink_component)
      else:
        user.remove_from_component_subscribers(blink_component)

    return True

  @common.require_edit_permission
  def get_template_data(self):
    components = models.BlinkComponent.all().order('name').fetch(None)
    subscribers = models.FeatureOwner.all().order('name').fetch(None)

    # Format for django template
    subscribers = [x.format_for_template() for x in subscribers]

    for c in components:
      c.primaries = [o.name for o in c.owners]

    # wf_component_content = models.BlinkComponent.fetch_wf_content_for_components()
    # for c in components:
    #   c.wf_urls = wf_component_content.get(c.name) or []

    template_data = {
      'subscribers': subscribers,
      'components': components[1:] # ditch generic "Blink" component
    }
    return templatedata

  # Remove user from component subscribers.
  @common.require_edit_permission
  def put(self):
    params = self.request.json
    self.__update_subscribers_list(False, user_id=params.get('userId'),
                                   blink_component=params.get('componentName'),
                                   primary=params.get('primary'))
    return {'done': True}

  # Add user to component subscribers.
  @common.require_edit_permission
  def process_post_data(self):
    params = self.request.json

    self.__update_subscribers_list(True, user_id=params.get('userId'),
                                   blink_component=params.get('componentName'),
                                   primary=params.get('primary'))
    return params


class SubscribersHandler(common.FlaskHandler):

  TEMPLATE_PATH = 'admin/subscribers.html'

  @common.require_edit_permission
  def get_template_data(self):
    users = models.FeatureOwner.all().order('name').fetch(None)
    feature_list = models.Feature.get_chronological()

    milestone = self.request.args.get('milestone') or None
    if milestone:
      milestone = int(milestone)
      feature_list = filter(lambda f: (f['shipped_milestone'] or f['shipped_android_milestone']) == milestone, feature_list)

    list_features_per_owner = 'showFeatures' in self.request.args
    for user in users:
      # user.subscribed_components = [models.BlinkComponent.get(key) for key in user.blink_components]
      user.owned_components = [models.BlinkComponent.get(key) for key in user.primary_blink_components]
      for component in user.owned_components:
        component.features = []
        if list_features_per_owner:
          component.features = filter(lambda f: component.name in f['blink_components'], feature_list)

    details = construct_chrome_channels_details()

    template_data = {
      'subscribers': users,
      'channels': collections.OrderedDict([
        ('stable', details['stable']),
        ('beta', details['beta']),
        ('dev', details['dev']),
        ('canary', details['canary']),
      ]),
      'selected_milestone': int(milestone) if milestone else None
    }
    return template_data


app = common.FlaskApplication([
  ('/admin/subscribers', SubscribersHandler),
  ('/admin/blink', BlinkHandler),
], debug=settings.DEBUG)
