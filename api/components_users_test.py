# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
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

import testing_config  # Must be imported before the module under test.

import datetime
import flask

from google.cloud import ndb  # type: ignore
from internals import user_models
from api import components_users

test_app = flask.Flask(__name__)

class ComponentsUsersAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = components_users.ComponentsUsersAPI()
    self.app_admin = user_models.AppUser(email='admin@example.com')
    self.app_admin.is_admin = True
    self.app_admin.put()

    created = datetime.datetime(2022, 10, 28, 0, 0, 0)

    self.component_1 = user_models.BlinkComponent(name='Blink', created=created, updated=created)
    self.component_1.key = ndb.Key('BlinkComponent', 123)
    self.component_1.put()
    self.component_2 = user_models.BlinkComponent(name='Blink>Accessibility', created=created, updated=created)
    self.component_2.key = ndb.Key('BlinkComponent', 234)
    self.component_2.put()
    self.component_owner_1 = user_models.FeatureOwner(
        name='owner_1', email='owner_1@example.com',
        primary_blink_components=[self.component_1.key, self.component_2.key],
        blink_components=[self.component_1.key, self.component_2.key]
        )
    self.component_owner_1.key = ndb.Key('FeatureOwner', 111)
    self.component_owner_1.put()
    self.watcher_1 = user_models.FeatureOwner(
        name='watcher_1', email='watcher_1@example.com',
        blink_components=[self.component_1.key, self.component_2.key],
        watching_all_features=True)
    self.watcher_1.key = ndb.Key('FeatureOwner', 222)
    self.watcher_1.put()

    self.no_body = user_models.FeatureOwner(
        name='no_body', email='no_body@example.com',
        watching_all_features=True)
    self.no_body.key = ndb.Key('FeatureOwner', 444)
    self.no_body.put()

    self.request_path = '/api/v0/componentsusers'

  def tearDown(self):
    self.no_body.key.delete()
    self.watcher_1.key.delete()
    self.component_owner_1.key.delete()
    self.component_1.key.delete()
    self.component_2.key.delete()
    testing_config.sign_out()
    self.app_admin.key.delete()

  def test_do_get(self):
    testing_config.sign_in('admin@example.com', 123567890)
    with test_app.test_request_context(self.request_path):
      response = self.handler.do_get()
    expected = {
      # Should not see the generic Blink
      'components': [
        {'id': 234,'name': 'Blink>Accessibility', 'owner_ids': [111], 'subscriber_ids': [111, 222]}],
      'users': [{'email': 'no_body@example.com', 'id': 444, 'name': 'no_body'},
            {'email': 'owner_1@example.com', 'id': 111, 'name': 'owner_1'},
            {'email': 'watcher_1@example.com', 'id': 222, 'name': 'watcher_1'}]}
    self.assertEqual(expected, response)