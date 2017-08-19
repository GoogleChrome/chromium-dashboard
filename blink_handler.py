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

import json
import logging
import os
import webapp2
import yaml

# Appengine imports.
from google.appengine.api import memcache

import common
import models
import settings
import util


class PopulateSubscribersHandler(common.ContentHandler):

  def __populate_devrel_owers(self):
    """Seeds the database with the team in devrel_team.yaml and adds the team
      member to the specified blink components in that file. Should only be ran
      if the FeatureOwner database entries have been cleared"""
    f = file('%s/data/devrel_team.yaml' % settings.ROOT_DIR, 'r')
    for profile in yaml.load_all(f):
      blink_components = profile.get('blink_components', [])
      blink_components = [models.BlinkComponent.get_by_name(name).key() for name in blink_components]
      blink_components = filter(None, blink_components) # Filter out None values

      user = models.FeatureOwner(
        name=unicode(profile['name']),
        email=unicode(profile['email']),
        twitter=profile.get('twitter', None),
        blink_components=blink_components
      )
      user.put()
    f.close()

  @common.require_whitelisted_user
  def get(self):
    if settings.PROD:
      return self.response.out.write('Handler not allowed in production.')
    models.BlinkComponent.update_db()
    self.__populate_devrel_owers()
    return self.redirect('/admin/blink')


class BlinkHandler(common.ContentHandler):

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

  @common.require_whitelisted_user
  @common.strip_trailing_slash
  def get(self, path):
    # key = '%s|blinkcomponentowners' % (settings.MEMCACHE_KEY_PREFIX)

    # data = memcache.get(key)
    # if data is None:
    components = models.BlinkComponent.all().order('name').fetch(None)
    subscribers = models.FeatureOwner.all().order('name').fetch(None)

    # Format for django template
    subscribers = [x.format_for_template() for x in subscribers]

    for c in components:
      c.primaries = [o.name for o in c.owners]

    # wf_component_content = models.BlinkComponent.fetch_wf_content_for_components()
    # for c in components:
    #   c.wf_urls = wf_component_content.get(c.name) or []

    data = {
      'subscribers': subscribers,
      'components': components[1:] # ditch generic "Blink" component
    }
    # memcache.set(key, data)

    self.render(data, template_path=os.path.join('admin/blink.html'))

  # Remove user from component subscribers.
  def put(self, path):
    params = json.loads(self.request.body)
    self.__update_subscribers_list(False, user_id=params.get('userId'),
                                   blink_component=params.get('componentName'),
                                   primary=params.get('primary'))
    self.response.set_status(200, message='User removed from subscribers')
    return self.response.write(json.dumps({'done': True}))

  # Add user to component subscribers.
  def post(self, path):
    params = json.loads(self.request.body)

    self.__update_subscribers_list(True, user_id=params.get('userId'),
                                   blink_component=params.get('componentName'),
                                   primary=params.get('primary'))
    # memcache.flush_all()
    # memcache.delete('%s|blinkcomponentowners' % (settings.MEMCACHE_KEY_PREFIX))
    self.response.set_status(200, message='User added to subscribers')
    return self.response.write(json.dumps(params))

app = webapp2.WSGIApplication([
  ('/admin/blink/populate_subscribers', PopulateSubscribersHandler),
  ('(.*)', BlinkHandler),
], debug=settings.DEBUG)

