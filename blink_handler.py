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
from google.appengine.api import urlfetch
from google.appengine.api import users

import common
import models
import settings
import util


class PopulateOwnersHandler(common.ContentHandler):

  def __populate_devrel_owers(self):
    """Seeds the database with the team in devrel_team.yaml and adds the team
      member to the specified blink components in that file. Should only be ran
      if the FeatureOwner database entries have been cleared"""
    f = file('%s/data/devrel_team.yaml' % settings.ROOT_DIR, 'r')
    for profile in yaml.load_all(f):
      blink_components = profile.get('blink_components', [])
      blink_components = [models.BlinkComponent.get_by_name(name).key() for name in blink_components]
      blink_components = filter(None, blink_components) # Filter out None values

      owner = models.FeatureOwner(
        name=unicode(profile['name']),
        email=unicode(profile['email']),
        twitter=profile.get('twitter', None),
        blink_components=blink_components
      )
      owner.put()
    f.close()

  @common.require_whitelisted_user
  def get(self):
    if settings.PROD:
      return self.response.out.write('Handler not allowed in production.')
    models.BlinkComponent.update_db()
    self.__populate_devrel_owers()
    return self.redirect('/admin/blink')


class BlinkHandler(common.ContentHandler):

  def __update_owners_list(self, add=True, user_id=None, blink_component=None):
    if not user_id or not blink_component:
      return False

    owner = models.FeatureOwner.get_by_id(long(user_id))
    if not owner:
      return True

    if add:
      owner.add_as_component_owner(blink_component)
    else:
      owner.remove_from_component_owners(blink_component)

    return True

  @common.require_whitelisted_user
  @common.strip_trailing_slash
  def get(self, path):
    # key = '%s|blinkcomponentowners' % (settings.MEMCACHE_KEY_PREFIX)

    # data = memcache.get(key)
    # if data is None:
    components = models.BlinkComponent.all().order('name').fetch(None)
    owners = models.FeatureOwner.all().order('name').fetch(None)

    # Format for django template
    owners = [x.format_for_template() for x in owners]

    # wf_component_content = models.BlinkComponent.fetch_wf_content_for_components()
    # for c in components:
    #   c.wf_urls = wf_component_content.get(c.name) or []

    data = {
      'owners': owners,
      'components': components[1:] # ditch generic "Blink" component
    }
    # memcache.set(key, data)

    self.render(data, template_path=os.path.join('admin/blink.html'))

  def put(self, path):
    params = json.loads(self.request.body)
    self.__update_owners_list(False, user_id=params.get('userId'),
                              blink_component=params.get('componentName'))
    self.response.set_status(200, message='User removed from owners')
    return self.response.write(json.dumps({'done': True}))

  def post(self, path):
    params = json.loads(self.request.body)
    self.__update_owners_list(True, user_id=params.get('userId'),
                              blink_component=params.get('componentName'))
    # memcache.flush_all()
    # memcache.delete('%s|blinkcomponentowners' % (settings.MEMCACHE_KEY_PREFIX))
    self.response.set_status(200, message='User added to owners')
    return self.response.write(json.dumps(params))

app = webapp2.WSGIApplication([
  ('/admin/blink/populate_owners', PopulateOwnersHandler),
  ('(.*)', BlinkHandler),
], debug=settings.DEBUG)

