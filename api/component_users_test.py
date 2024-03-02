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
from chromestatus_openapi.models import ComponentUsersRequest
from api import component_users

test_app = flask.Flask(__name__)

class ComponentUsersAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = component_users.ComponentUsersAPI()
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
    self.component_owner_2 = user_models.FeatureOwner(
        name='owner_2', email='owner_2@example.com',
        primary_blink_components=[self.component_1.key, self.component_2.key],
        blink_components=[self.component_1.key, self.component_2.key]
        )
    self.component_owner_2.key = ndb.Key('FeatureOwner', 999)
    self.component_owner_2.put()
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
    

  def tearDown(self):
    self.no_body.key.delete()
    self.watcher_1.key.delete()
    self.component_owner_1.key.delete()
    self.component_owner_2.key.delete()
    self.component_1.key.delete()
    self.component_2.key.delete()
    testing_config.sign_out()
    self.app_admin.key.delete()

  def test_do_put(self):
    request_path = f'/api/v0/components/{self.component_2.key.integer_id()}/users/{self.no_body.key.integer_id()}'
    user = user_models.FeatureOwner.get_by_id(self.no_body.key.integer_id())
    self.assertEqual(user.blink_components, [])
    self.assertEqual(user.primary_blink_components, [])
    # Add user to component
    testing_config.sign_in('admin@example.com', 123567890)
    with test_app.test_request_context(request_path, json=ComponentUsersRequest().to_dict()):
      response = self.handler.do_put(
        component_id=self.component_2.key.integer_id(),
        user_id=self.no_body.key.integer_id())
    self.assertEqual(({}, 200), response)
    user = user_models.FeatureOwner.get_by_id(self.no_body.key.integer_id())
    self.assertEqual(user.blink_components, [self.component_2.key])
    self.assertEqual(user.primary_blink_components, [])

    # Add owner to an existing component user
    with test_app.test_request_context(request_path, json=ComponentUsersRequest(owner=True).to_dict()):
      response = self.handler.do_put(
        component_id=self.component_2.key.integer_id(),
        user_id=self.no_body.key.integer_id())
    self.assertEqual(({}, 200), response)
    user = user_models.FeatureOwner.get_by_id(self.no_body.key.integer_id())
    self.assertEqual(user.blink_components, [self.component_2.key])
    self.assertEqual(user.primary_blink_components, [self.component_2.key])

  def test_do_delete(self):
    request_path = f'/api/v0/components/{self.component_2.key.integer_id()}/users/{self.watcher_1.key.integer_id()}'
    user = user_models.FeatureOwner.get_by_id(self.watcher_1.key.integer_id())
    self.assertEqual(user.blink_components, [self.component_1.key, self.component_2.key])
    self.assertEqual(user.primary_blink_components, [])
    # Remove user from component
    testing_config.sign_in('admin@example.com', 123567890)
    with test_app.test_request_context(request_path, json=ComponentUsersRequest().to_dict()):
      response = self.handler.do_delete(
        component_id=self.component_2.key.integer_id(),
        user_id=self.watcher_1.key.integer_id())
    self.assertEqual(({}, 200), response)
    user = user_models.FeatureOwner.get_by_id(self.watcher_1.key.integer_id())
    self.assertEqual(user.blink_components, [self.component_1.key])
    self.assertEqual(user.primary_blink_components, [])

    request_path = f'/api/v0/components/{self.component_2.key.integer_id()}/users/{self.component_owner_1.key.integer_id()}'
    user = user_models.FeatureOwner.get_by_id(self.component_owner_1.key.integer_id())
    self.assertEqual(user.blink_components, [self.component_1.key, self.component_2.key])
    self.assertEqual(user.primary_blink_components, [self.component_1.key, self.component_2.key])
    # Remove only the owner from component but keep it as a subscriber
    testing_config.sign_in('admin@example.com', 123567890)
    with test_app.test_request_context(request_path, json=ComponentUsersRequest(owner=True).to_dict()):
      response = self.handler.do_delete(
        component_id=self.component_2.key.integer_id(),
        user_id=self.component_owner_1.key.integer_id())
    self.assertEqual(({}, 200), response)
    user = user_models.FeatureOwner.get_by_id(self.component_owner_1.key.integer_id())
    self.assertEqual(user.blink_components, [self.component_1.key, self.component_2.key])
    self.assertEqual(user.primary_blink_components, [self.component_1.key])

    request_path = f'/api/v0/components/{self.component_2.key.integer_id()}/users/{self.component_owner_2.key.integer_id()}'
    user = user_models.FeatureOwner.get_by_id(self.component_owner_2.key.integer_id())
    self.assertEqual(user.blink_components, [self.component_1.key, self.component_2.key])
    self.assertEqual(user.primary_blink_components, [self.component_1.key, self.component_2.key])
    # Remove the user as both and owner and a user from component
    testing_config.sign_in('admin@example.com', 123567890)
    with test_app.test_request_context(request_path, json=ComponentUsersRequest().to_dict()):
      response = self.handler.do_delete(
        component_id=self.component_2.key.integer_id(),
        user_id=self.component_owner_2.key.integer_id())
    self.assertEqual(({}, 200), response)
    user = user_models.FeatureOwner.get_by_id(self.component_owner_2.key.integer_id())
    self.assertEqual(user.blink_components, [self.component_1.key])
    self.assertEqual(user.primary_blink_components, [self.component_1.key])
