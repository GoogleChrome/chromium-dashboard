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

from framework import basehandlers
from framework import permissions
from internals import core_models
from internals import user_models
import settings
from api.channels_api import construct_chrome_channels_details


class BlinkHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'admin/blink.html'

  def __update_subscribers_list(
      self, add=True, user_id=None, blink_component=None, primary=False):
    if not user_id or not blink_component:
      return False

    user = user_models.FeatureOwner.get_by_id(int(user_id))
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

  @permissions.require_admin_site
  def get_template_data(self, **kwargs):
    components = user_models.BlinkComponent.query().order(
        user_models.BlinkComponent.name).fetch(None)
    possible_subscribers = user_models.FeatureOwner.query().order(
        user_models.FeatureOwner.name).fetch(None)

    # Format for django template
    possible_subscriber_dicts = [
        {'id': fo.key.integer_id(), 'email': fo.email}
        for fo in possible_subscribers]

    component_to_subscribers = {c.key: [] for c in components}
    component_to_owners = {c.key: [] for c in components}
    for ps in possible_subscribers:
      for subed_component_key in ps.blink_components:
        component_to_subscribers[subed_component_key].append(ps)
      for owned_component_key in ps.primary_blink_components:
        component_to_owners[owned_component_key].append(ps.name)

    for c in components:
      c.computed_subscribers = component_to_subscribers[c.key]
      c.computed_owners = component_to_owners[c.key]

    template_data = {
      'possible_subscribers': possible_subscriber_dicts,
      'components': components[1:] # ditch generic "Blink" component
    }
    return template_data

  # Remove user from component subscribers.
  @permissions.require_admin_site
  def put(self):
    params = self.request.get_json(force=True)
    self.__update_subscribers_list(False, user_id=params.get('userId'),
                                   blink_component=params.get('componentName'),
                                   primary=params.get('primary'))
    return {'done': True}

  # Add user to component subscribers.
  @permissions.require_admin_site
  def process_post_data(self, **kwargs):
    params = self.request.get_json(force=True)
    self.__update_subscribers_list(True, user_id=params.get('userId'),
                                   blink_component=params.get('componentName'),
                                   primary=params.get('primary'))
    return params


class SubscribersHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'admin/subscribers.html'

  @permissions.require_admin_site
  def get_template_data(self, **kwargs):
    users = user_models.FeatureOwner.query().order(
        user_models.FeatureOwner.name).fetch(None)
    feature_list = core_models.Feature.get_chronological()

    milestone = self.get_int_arg('milestone')
    if milestone is not None:
      feature_list = [
          f for f in feature_list
          if (f['shipped_milestone'] or
              f['shipped_android_milestone']) == milestone]

    list_features_per_owner = 'showFeatures' in self.request.args
    for user in users:
      # user.subscribed_components = [key.get() for key in user.blink_components]
      user.owned_components = [
          key.get() for key in user.primary_blink_components]
      for component in user.owned_components:
        component.features = []
        if list_features_per_owner:
          component.features = [
              f for f in feature_list
              if component.name in f['blink_components']]

    details = construct_chrome_channels_details()

    template_data = {
      'subscribers': users,
      'channels': collections.OrderedDict([
        ('stable', details['stable']),
        ('beta', details['beta']),
        ('dev', details['dev']),
        ('canary', details['canary']),
      ]),
      'selected_milestone': milestone
    }
    return template_data
