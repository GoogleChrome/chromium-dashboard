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

import testing_config  # Must be imported before the module under test.
import urllib.request, urllib.parse, urllib.error

import os
import flask
import werkzeug
import html5lib

from framework import ramcache
from internals import core_enums
from internals import models
from pages import guide


test_app = flask.Flask(__name__)


class TestWithFeature(testing_config.CustomTestCase):

  REQUEST_PATH_FORMAT = 'subclasses fill this in'
  HANDLER_CLASS = 'subclasses fill this in'

  def setUp(self):
    self.request_path = self.REQUEST_PATH_FORMAT
    self.handler = self.HANDLER_CLASS()

  def tearDown(self):
    ramcache.flush_all()
    ramcache.check_for_distributed_invalidation()


class FeatureNewTest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = guide.FeatureNew()

  def test_get__anon(self):
    """Anon cannot create features, gets a redirect to sign in page."""
    testing_config.sign_out()
    with test_app.test_request_context('/guide/new'):
      actual_response = self.handler.get_template_data()
    self.assertEqual('302 FOUND', actual_response.status)

  def test_get__non_allowed(self):
    """Non-allowed cannot create features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with test_app.test_request_context('/guide/new'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        actual_response = self.handler.get_template_data()

  def test_get__normal(self):
    """Allowed users render a page with a django form."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context('/guide/new'):
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
    with test_app.test_request_context('/guide/new', method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.process_post_data()

  def test_post__non_allowed(self):
    """Non-allowed cannot create features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with test_app.test_request_context('/guide/new', method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.post()

  def test_post__normal_valid(self):
    """Allowed user can create a feature."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        '/guide/new', data={
            'category': '1',
            'name': 'Feature name',
            'summary': 'Feature summary',
        }, method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/guide/edit/'))
    new_feature_id = int(location.split('/')[-1])
    feature = models.Feature.get_by_id(new_feature_id)
    self.assertEqual(1, feature.category)
    self.assertEqual('Feature name', feature.name)
    self.assertEqual('Feature summary', feature.summary)
    feature.key.delete()


class FeatureNewTemplateTest(TestWithFeature):

  HANDLER_CLASS = guide.FeatureNew

  def setUp(self):
    super(FeatureNewTemplateTest, self).setUp()
    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data()

      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      template_path = self.handler.get_template_path(self.template_data)
      self.full_template_path = os.path.join(template_path)

  def test_html_rendering(self):
    """We can render the template with valid html."""
    testing_config.sign_in('user1@google.com', 1234567890)
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)


class ProcessOverviewTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', owner=['user1@google.com'],
        category=1, visibility=1, standardization=1,
        web_dev_views=core_enums.DEV_NO_SIGNALS, impl_status_chrome=1)
    self.feature_1.put()

    self.request_path = '/guide/edit/%d' % self.feature_1.key.integer_id()
    self.handler = guide.ProcessOverview()

  def tearDown(self):
    self.feature_1.key.delete()

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
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.get_template_data(
          self.feature_1.key.integer_id())
    self.assertEqual('302 FOUND', actual_response.status)

  def test_get__non_allowed(self):
    """Non-allowed cannot create features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.get_template_data(self.feature_1.key.integer_id())


  def test_get__not_found(self):
    """Allowed users get a 404 if there is no such feature."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(999)

  def test_get__normal(self):
    """Allowed users render a page with a process overview."""
    testing_config.sign_in('user1@google.com', 1234567890)

    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          self.feature_1.key.integer_id())

    self.assertTrue('overview_form' in template_data)
    self.assertTrue('process_json' in template_data)
    self.assertTrue('progress_so_far' in template_data)


class ProcessOverviewTemplateTest(TestWithFeature):

  HANDLER_CLASS = guide.ProcessOverview

  def setUp(self):
    super(ProcessOverviewTemplateTest, self).setUp()

    self.feature_1 = models.Feature(
        name='feature one', summary='sum', owner=['user1@google.com'],
        category=1, visibility=1, standardization=1,
        web_dev_views=core_enums.DEV_NO_SIGNALS, impl_status_chrome=1)
    self.feature_1.put()
    self.request_path = '/guide/edit/%d' % self.feature_1.key.integer_id()

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data(
        self.feature_1.key.integer_id()
      )

      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      template_path = self.handler.get_template_path(self.template_data)
      self.full_template_path = os.path.join(template_path)

  def test_html_rendering(self):
    """We can render the template with valid html."""
    testing_config.sign_in('user1@google.com', 1234567890)

    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          self.feature_1.key.integer_id())

    template_text = self.handler.render(
        template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)


class FeatureEditStageTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', owner=['user1@google.com'],
        category=1, visibility=1, standardization=1, web_dev_views=1,
        impl_status_chrome=1)
    self.feature_1.put()
    self.stage = core_enums.INTENT_INCUBATE  # Shows first form

    self.request_path = ('/guide/stage/%d/%d' % (
        self.feature_1.key.integer_id(), self.stage))
    self.handler = guide.FeatureEditStage()

  def tearDown(self):
    self.feature_1.key.delete()

  def test_touched(self):
    """We can tell if the user meant to edit a field."""
    with test_app.test_request_context(
        'path', data={'name': 'new name'}):
      self.assertTrue(self.handler.touched('name'))
      self.assertFalse(self.handler.touched('summary'))

  def test_touched__checkboxes(self):
    """For now, any checkbox listed in form_fields is considered touched."""
    with test_app.test_request_context(
        'path', data={'form_fields': 'unlisted, api_spec',
                      'unlisted': 'yes',
                      'wpt': 'yes'}):
      # unlisted is in this form and the user checked the box.
      self.assertTrue(self.handler.touched('unlisted'))
      # api_spec is this form and the user did not check the box.
      self.assertTrue(self.handler.touched('api_spec'))
      # wpt is not part of this form, regardless if a value was given.
      self.assertFalse(self.handler.touched('wpt'))

  def test_touched__selects(self):
    """For now, any select in the form data considered touched if not ''."""
    with test_app.test_request_context(
        'path', data={'form_fields': 'not used for this case',
                      'category': '',
                      'feature_type': '4'}):
      # The user did not choose any value for category.
      self.assertFalse(self.handler.touched('category'))
      # The user did select a value, or one was already set.
      self.assertTrue(self.handler.touched('feature_type'))
      # intent_state is a select, but it was not present in this POST.
      self.assertFalse(self.handler.touched('select'))

  def test_get__anon(self):
    """Anon cannot edit features, gets a redirect to viewing page."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.get_template_data(
          self.feature_1.key.integer_id(), self.stage)
    self.assertEqual('302 FOUND', actual_response.status)

  def test_get__non_allowed(self):
    """Non-allowed cannot edit features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.get_template_data(
            self.feature_1.key.integer_id(), self.stage)

  def test_get__not_found(self):
    """Allowed users get a 404 if there is no such feature."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(999, self.stage)

  def test_get__normal(self):
    """Allowed users render a page with a django form."""
    testing_config.sign_in('user1@google.com', 1234567890)

    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          self.feature_1.key.integer_id(), self.stage)

    self.assertTrue('feature' in template_data)
    self.assertTrue('feature_id' in template_data)
    self.assertTrue('feature_form' in template_data)
    self.assertTrue('already_on_this_stage' in template_data)

  def test_get__not_on_this_stage(self):
    """When feature is not on the stage for the current form, offer checkbox."""
    testing_config.sign_in('user1@google.com', 1234567890)

    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          self.feature_1.key.integer_id(), self.stage)

    self.assertFalse(template_data['already_on_this_stage'])

  def test_get__already_on_this_stage(self):
    """When feature is already on the stage for the current form, say that."""
    self.feature_1.intent_stage = self.stage
    self.feature_1.put()
    testing_config.sign_in('user1@google.com', 1234567890)

    with test_app.test_request_context(self.request_path):
      template_data = self.handler.get_template_data(
          self.feature_1.key.integer_id(), self.stage)

    self.assertTrue(template_data['already_on_this_stage'])

  def test_post__anon(self):
    """Anon cannot edit features, gets a 403."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path, method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.process_post_data(
            self.feature_1.key.integer_id(), self.stage)

  def test_post__non_allowed(self):
    """Non-allowed cannot edit features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with test_app.test_request_context(self.request_path, method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.process_post_data(
            self.feature_1.key.integer_id(), self.stage)

  def test_post__normal_valid(self):
    """Allowed user can edit a feature."""
    testing_config.sign_in('user1@google.com', 1234567890)
    with test_app.test_request_context(
        self.request_path, data={
            'form_fields': 'category, name, summary, shipped_milestone',
            'category': '2',
            'name': 'Revised feature name',
            'summary': 'Revised feature summary',
            'shipped_milestone': '84',
        }):
      actual_response = self.handler.process_post_data(
          self.feature_1.key.integer_id(), self.stage)

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertEqual('/guide/edit/%d' % self.feature_1.key.integer_id(),
                     location)
    revised_feature = models.Feature.get_by_id(self.feature_1.key.integer_id())
    self.assertEqual(2, revised_feature.category)
    self.assertEqual('Revised feature name', revised_feature.name)
    self.assertEqual('Revised feature summary', revised_feature.summary)
    self.assertEqual(84, revised_feature.shipped_milestone)


class FeatureEditStageTemplateTest(TestWithFeature):

  HANDLER_CLASS = guide.FeatureEditStage

  def setUp(self):
    super(FeatureEditStageTemplateTest, self).setUp()
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', owner=['user1@google.com'],
        category=1, visibility=1, standardization=1,
        web_dev_views=core_enums.DEV_NO_SIGNALS, impl_status_chrome=1)
    self.feature_1.put()
    self.stage = core_enums.INTENT_INCUBATE  # Shows first form
    testing_config.sign_in('user1@google.com', 1234567890)

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data(
        self.feature_1.key.integer_id(), self.stage)

      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      template_path = self.handler.get_template_path(self.template_data)
      self.full_template_path = os.path.join(template_path)

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)



class FeatureEditAllFieldsTemplateTest(TestWithFeature):

  HANDLER_CLASS = guide.FeatureEditAllFields

  def setUp(self):
    super(FeatureEditAllFieldsTemplateTest, self).setUp()
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', owner=['user1@google.com'],
        category=1, visibility=1, standardization=1,
        web_dev_views=core_enums.DEV_NO_SIGNALS, impl_status_chrome=1)
    self.feature_1.put()
    self.stage = core_enums.INTENT_INCUBATE  # Shows first form
    testing_config.sign_in('user1@google.com', 1234567890)

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data(
        self.feature_1.key.integer_id())

      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      template_path = self.handler.get_template_path(self.template_data)
      self.full_template_path = os.path.join(template_path)

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)

class FeatureVerifyAccuracyTemplateTest(TestWithFeature):

  HANDLER_CLASS = guide.FeatureVerifyAccuracy

  def setUp(self):
    super(FeatureVerifyAccuracyTemplateTest, self).setUp()
    self.feature_1 = models.Feature(
        name='feature one', summary='sum', owner=['user1@google.com'],
        category=1, visibility=1, standardization=1,
        web_dev_views=core_enums.DEV_NO_SIGNALS, impl_status_chrome=1)
    self.feature_1.put()
    self.stage = core_enums.INTENT_INCUBATE  # Shows first form
    testing_config.sign_in('user1@google.com', 1234567890)

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data(
        self.feature_1.key.integer_id())

      self.template_data.update(self.handler.get_common_data())
      self.template_data['nonce'] = 'fake nonce'
      template_path = self.handler.get_template_path(self.template_data)
      self.full_template_path = os.path.join(template_path)

  def test_html_rendering(self):
    """We can render the template with valid html."""
    template_text = self.handler.render(
        self.template_data, self.full_template_path)
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)
