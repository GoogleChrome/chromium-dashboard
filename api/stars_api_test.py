# Copyright 2020 Google Inc.
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

import unittest
import testing_config  # Must be imported before the module under test.

import flask
import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from api import register
from api import stars_api
from internals import models
from internals import notifier



class StarsAPITest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.handler = stars_api.StarsAPI()
    self.request_path = '/api/v0/currentuser/stars'

  def tearDown(self):
    self.feature_1.delete()
    for star in notifier.FeatureStar.all():
      star.delete()

  def test_get__anon(self):
    """Anon should always have an empty list of stars."""
    testing_config.sign_out()
    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    self.assertEqual({"featureIds": []}, actual_response)

  def test_get__no_stars(self):
    """User has not starred any features."""
    testing_config.sign_in('user7@example.com', 123567890)
    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    self.assertEqual({"featureIds": []}, actual_response)

  def test_get__some_stars(self):
    """User has starred some features."""
    email = 'user8@example.com'
    feature_1_id = self.feature_1.key().id()
    testing_config.sign_in(email, 123567890)
    notifier.FeatureStar.set_star(email, feature_1_id)
    with register.app.test_request_context(self.request_path):
      actual_response = self.handler.do_get()
    self.assertEqual(
        {"featureIds": [feature_1_id]},
        actual_response)

  def test_post__invalid_feature_id(self):
    """We reject star requests that don't have an int featureId."""
    params = {}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

    params = {"featureId": "not an int"}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post()

  def test_post__feature_id_not_found(self):
    """We reject star requests for features that don't exist."""
    params = {"featureId": 999}
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.do_post()

  def test_post__anon(self):
    """We reject anon star requests."""
    feature_id = self.feature_1.key().id()
    params = {"featureId": feature_id}
    testing_config.sign_out()
    with register.app.test_request_context(self.request_path, json=params):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()
    

  def test_post__duplicate(self):
    """User sends a duplicate request, which should be a no-op."""
    testing_config.sign_in('user7@example.com', 123567890)

    feature_id = self.feature_1.key().id()
    params = {"featureId": feature_id}
    with register.app.test_request_context(self.request_path, json=params):
      self.handler.do_post()  # Original request

    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(1, updated_feature.star_count)

    with register.app.test_request_context(self.request_path, json=params):
      self.handler.do_post()  # Duplicate request
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(1, updated_feature.star_count)  # Still 1, not 2.

    params = {"featureId": feature_id, "starred": False}
    with register.app.test_request_context(self.request_path, json=params):
      self.handler.do_post()  # Original request
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)

    with register.app.test_request_context(self.request_path, json=params):
      self.handler.do_post()  # Duplicate request
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)  # Still 0, not negative.

  def test_post__unmatched_unstar(self):
    """User tries to unstar feature that they never starred: no-op."""
    testing_config.sign_in('user8@example.com', 123567890)

    feature_id = self.feature_1.key().id()
    # User never stars the feature in the first place.

    params = {"featureId": feature_id, "starred": False}
    with register.app.test_request_context(self.request_path, json=params):
      self.handler.do_post()  # Out-of-step request
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)  # Still 0, not negative.

  def test_post__normal(self):
    """User can star and unstar."""
    testing_config.sign_in('user6@example.com', 123567890)

    feature_id = self.feature_1.key().id()
    params = {"featureId": feature_id}
    with register.app.test_request_context(self.request_path, json=params):
      self.handler.do_post()
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(1, updated_feature.star_count)

    params = {"featureId": feature_id, "starred": False}
    with register.app.test_request_context(self.request_path, json=params):
      self.handler.do_post()
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)
