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

import unittest
import testing_config  # Must be imported before the module under test.
import webapp2
from webob import exc

import models
import notifier



class NotifierFunctionsTest(unittest.TestCase):

  def test_list_diff__empty(self):
    self.assertEqual([], notifier.list_diff([], []))


class FeatureStarTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.feature_2 = models.Feature(
        name='feature two', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_2.put()

  def test_get_star__no_existing(self):
    """User has never starred the given feature."""
    email = 'user1@example.com'
    feature_id = self.feature_1.key().id()
    actual = notifier.FeatureStar.get_star(email, feature_id)
    self.assertEqual(None, actual)

  def test_get_and_set_star(self):
    """User can star and unstar a feature."""
    email = 'user2@example.com'
    feature_id = self.feature_1.key().id()
    notifier.FeatureStar.set_star(email, feature_id)
    actual = notifier.FeatureStar.get_star(email, feature_id)
    self.assertEqual(email, actual.email)
    self.assertEqual(feature_id, actual.feature_id)
    self.assertTrue(actual.starred)
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(1, updated_feature.star_count)

    notifier.FeatureStar.set_star(email, feature_id, starred=False)
    actual = notifier.FeatureStar.get_star(email, feature_id)
    self.assertEqual(email, actual.email)
    self.assertEqual(feature_id, actual.feature_id)
    self.assertFalse(actual.starred)
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)

  def test_get_user_star__no_stars(self):
    """User has never starred any features."""
    email = 'user4@example.com'
    actual = notifier.FeatureStar.get_user_stars(email)
    self.assertEqual([], actual)

  def test_get_user_star(self):
    """User has starred two features."""
    email = 'user5@example.com'
    feature_1_id = self.feature_1.key().id()
    feature_2_id = self.feature_2.key().id()
    notifier.FeatureStar.set_star(email, feature_1_id)
    notifier.FeatureStar.set_star(email, feature_2_id)

    actual = notifier.FeatureStar.get_user_stars(email)
    self.assertItemsEqual(
        [feature_1_id, feature_2_id],
        actual)


class SetStarHandlerTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.handler = notifier.SetStarHandler()
    self.handler.request = webapp2.Request.blank('/features/star/set')
    self.handler.response = webapp2.Response()

  def test_post__invalid_feature_id(self):
    """We reject star requests that don't have an int featureId."""
    self.handler.request.body = '{}'
    with self.assertRaises(exc.HTTPClientError):
      self.handler.post()

    self.handler.request.body = '{"featureId":"not an int"}'
    with self.assertRaises(exc.HTTPClientError):
      self.handler.post()

  def test_post__feature_id_not_found(self):
    """We reject star requests for features that don't exist."""
    self.handler.request.body = '{"featureId": 999}'
    with self.assertRaises(exc.HTTPClientError):
      self.handler.post()

  def test_post__anon(self):
    """We reject anon star requests."""
    feature_id = self.feature_1.key().id()
    self.handler.request.body = '{"featureId": %d}' % feature_id
    testing_config.ourTestbed.setup_env(
            user_email='', user_id='', overwrite=True)
    with self.assertRaises(exc.HTTPClientError):
      self.handler.post()

  def test_post__normal(self):
    """User can star and unstar."""
    testing_config.ourTestbed.setup_env(
            user_email='user6@example.com',
            user_id='123567890',
            overwrite=True)

    feature_id = self.feature_1.key().id()
    self.handler.request.body = '{"featureId": %d}' % feature_id
    self.handler.post()
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(1, updated_feature.star_count)

    self.handler.request.body = (
        '{"featureId": %d, "starred": false}' % feature_id)
    self.handler.post()
    updated_feature = models.Feature.get_by_id(feature_id)
    self.assertEqual(0, updated_feature.star_count)


class GetUserStarsHandlerTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.handler = notifier.GetUserStarsHandler()
    self.handler.request = webapp2.Request.blank('/features/star/list')
    self.handler.response = webapp2.Response()

  def test_post__anon(self):
    """Anon should always have an empty list of stars."""
    testing_config.ourTestbed.setup_env(
            user_email='', user_id='', overwrite=True)
    self.handler.post()
    self.assertEqual(
        '{"featureIds":[]}',
        self.handler.response.body)

  def test_post__no_stars(self):
    """User has not starred any features."""
    testing_config.ourTestbed.setup_env(
            user_email='user7@example.com',
            user_id='123567890',
            overwrite=True)
    self.handler.post()
    self.assertEqual(
        '{"featureIds":[]}',
        self.handler.response.body)

  def test_post__some_stars(self):
    """User has not starred any features."""
    email = 'user8@example.com'
    feature_1_id = self.feature_1.key().id()
    testing_config.ourTestbed.setup_env(
            user_email=email,
            user_id='123567890',
            overwrite=True)
    notifier.FeatureStar.set_star(email, feature_1_id)
    self.handler.post()
    self.assertEqual(
        '{"featureIds":[%d]}' % feature_1_id,
        self.handler.response.body)
