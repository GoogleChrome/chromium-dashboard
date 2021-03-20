from __future__ import division
from __future__ import print_function

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
import urllib

import flask
import werkzeug

import models
from pages import guide


class FeatureNewTest(unittest.TestCase):

  def setUp(self):
    self.handler = guide.FeatureNew()

  def test_get__anon(self):
    """Anon cannot create features, gets a redirect to sign in page."""
    testing_config.sign_out()
    with guide.app.test_request_context('/guide/new'):
      actual_response = self.handler.get_template_data()
    self.assertEqual('302 FOUND', actual_response.status)

  def test_get__non_allowed(self):
    """Non-allowed cannot create features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with guide.app.test_request_context('/guide/new'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        actual_response = self.handler.get_template_data()

  def test_get__normal(self):
    """Allowed users render a page with a django form."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with guide.app.test_request_context('/guide/new'):
      template_data = self.handler.get_template_data()

    self.assertTrue('overview_form' in template_data)
    form = template_data['overview_form']
    field = form.fields['owner']
    self.assertEqual(
        'user1@google.com',
        form.get_initial_for_field(field, 'owner'))

  def test_post__anon(self):
    """Anon cannot create features, gets a 403."""
    testing_config.sign_out()
    with guide.app.test_request_context('/guide/new'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.process_post_data()

  def test_post__non_allowed(self):
    """Non-allowed cannot create features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with guide.app.test_request_context('/guide/new'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.post()

  def test_post__normal_valid(self):
    """Allowed user can create a feature."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with guide.app.test_request_context(
        '/guide/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
        }):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/guide/edit/'))
    new_feature_id = int(location.split('/')[-1])
    feature = models.Feature.get_by_id(new_feature_id)
    self.assertEqual(1, feature.category)
    self.assertEqual('Feature name', feature.name)
    self.assertEqual('Feature summary', feature.summary)
    feature.delete()


class ProcessOverviewTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=models.DEV_NO_SIGNALS,
        impl_status_chrome=1)
    self.feature_1.put()

    self.request_path = '/guide/edit/%d' % self.feature_1.key().id()
    self.handler = guide.ProcessOverview()

  def tearDown(self):
    self.feature_1.delete()

  def test_detect_progress__no_progress(self):
    """A new feature has earned no progress items."""
    actual = self.handler.detect_progress(self.feature_1)
    self.assertEqual({}, actual)

  def test_detect_progress__some_progress(self):
    """We can detect some progress."""
    self.feature_1.motivation = 'something'
    actual = self.handler.detect_progress(self.feature_1)
    self.assertEqual({'Motivation': 'True'}, actual)

  def test_detect_progress__progress_item_links(self):
    """Fields with multiple URLs use the first URL in progress item."""
    self.feature_1.doc_links = ['http://one', 'http://two']
    actual = self.handler.detect_progress(self.feature_1)
    self.assertEqual({'Doc links': 'http://one'}, actual)

  def test_get__anon(self):
    """Anon cannot edit features, gets a redirect to viewing page."""
    testing_config.sign_out()
    with guide.app.test_request_context(self.request_path):
      actual_response = self.handler.get_template_data(
          self.feature_1.key().id())
    self.assertEqual('302 FOUND', actual_response.status)

  def test_get__non_allowed(self):
    """Non-allowed cannot create features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with guide.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.get_template_data(self.feature_1.key().id())


  def test_get__not_found(self):
    """Allowed users get a 404 if there is no such feature."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with guide.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(999)

  def test_get__normal(self):
    """Allowed users render a page with a process overview."""
    testing_config.sign_in('user1@google.com', 1234567890)

    with guide.app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          self.feature_1.key().id())

    self.assertTrue('overview_form' in template_data)
    self.assertTrue('process_json' in template_data)
    self.assertTrue('progress_so_far' in template_data)


class FeatureEditStageTest(unittest.TestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()
    self.stage = models.INTENT_INCUBATE  # Shows first form

    self.request_path = ('/guide/stage/%d/%d' % (
        self.feature_1.key().id(), self.stage))
    self.handler = guide.FeatureEditStage()

  def tearDown(self):
    self.feature_1.delete()

  def test_touched(self):
    """We can tell if the user meant to edit a field."""
    with guide.app.test_request_context(
        'path', data={'name': 'new name'}):
      self.assertTrue(self.handler.touched('name'))
      self.assertFalse(self.handler.touched('summary'))

  def test_split_input(self):
    """We can parse items from multi-item text fields"""
    with guide.app.test_request_context(
        'path', data={
            'empty': '',
            'colors': 'yellow\nblue',
            'names': 'alice, bob',
        }):
      self.assertEqual([], self.handler.split_input('missing'))
      self.assertEqual([], self.handler.split_input('empty'))
      self.assertEqual(
          ['yellow', 'blue'],
          self.handler.split_input('colors'))
      self.assertEqual(
          ['alice', 'bob'],
          self.handler.split_input('names', delim=','))

  def test_get__anon(self):
    """Anon cannot edit features, gets a redirect to viewing page."""
    testing_config.sign_out()
    with guide.app.test_request_context(self.request_path):
      actual_response = self.handler.get_template_data(
          self.feature_1.key().id(), self.stage)
    self.assertEqual('302 FOUND', actual_response.status)

  def test_get__non_allowed(self):
    """Non-allowed cannot edit features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with guide.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.get_template_data(
            self.feature_1.key().id(), self.stage)

  def test_get__not_found(self):
    """Allowed users get a 404 if there is no such feature."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with guide.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(999, self.stage)

  def test_get__normal(self):
    """Allowed users render a page with a django form."""
    testing_config.sign_in('user1@google.com', 1234567890)

    with guide.app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          self.feature_1.key().id(), self.stage)

    self.assertTrue('feature' in template_data)
    self.assertTrue('feature_id' in template_data)
    self.assertTrue('feature_form' in template_data)
    self.assertTrue('already_on_this_stage' in template_data)

  def test_get__not_on_this_stage(self):
    """When feature is not on the stage for the current form, offer checkbox."""
    testing_config.sign_in('user1@google.com', 1234567890)

    with guide.app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          self.feature_1.key().id(), self.stage)

    self.assertFalse(template_data['already_on_this_stage'])

  def test_get__already_on_this_stage(self):
    """When feature is already on the stage for the current form, say that."""
    self.feature_1.intent_stage = self.stage
    self.feature_1.put()
    testing_config.sign_in('user1@google.com', 1234567890)

    with guide.app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          self.feature_1.key().id(), self.stage)

    self.assertTrue(template_data['already_on_this_stage'])

  def test_post__anon(self):
    """Anon cannot edit features, gets a 403."""
    testing_config.sign_out()
    with guide.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.process_post_data(
            self.feature_1.key().id(), self.stage)

  def test_post__non_allowed(self):
    """Non-allowed cannot edit features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with guide.app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.process_post_data(
            self.feature_1.key().id(), self.stage)

  def test_post__normal_valid(self):
    """Allowed user can edit a feature."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with guide.app.test_request_context(
        self.request_path, data={
            'category': '2',
            'name': 'Revised feature name',
            'summary': 'Revised feature summary',
            'shipped_milestone': '84',
        }):
      actual_response = self.handler.process_post_data(
          self.feature_1.key().id(), self.stage)

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertEqual('/guide/edit/%d' % self.feature_1.key().id(),
                     location)
    revised_feature = models.Feature.get_by_id(self.feature_1.key().id())
    self.assertEqual(2, revised_feature.category)
    self.assertEqual('Revised feature name', revised_feature.name)
    self.assertEqual('Revised feature summary', revised_feature.summary)
    self.assertEqual(84, revised_feature.shipped_milestone)
