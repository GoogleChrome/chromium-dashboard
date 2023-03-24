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

from unittest import mock

import os
import flask
import werkzeug
import html5lib
import settings

from google.cloud import ndb  # type: ignore
from pages import intentpreview
from internals import core_enums
from internals.core_models import FeatureEntry, MilestoneSet, Stage

test_app = flask.Flask(__name__,
  template_folder=settings.get_flask_template_path())

# Load testdata to be used across all of the CustomTestCases
TESTDATA = testing_config.Testdata(__file__)

class IntentEmailPreviewHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = FeatureEntry(
        name='feature one', summary='sum', owner_emails=['user1@google.com'],
        category=1, intent_stage=core_enums.INTENT_IMPLEMENT,
        feature_type=0)
    self.feature_1.put()
    # Write stages for the feature.
    stage_types = [110, 120, 130, 140, 150, 151, 160, 1061]
    for s_type in stage_types:
      s = Stage(feature_id=self.feature_1.key.integer_id(), stage_type=s_type,
          milestones=MilestoneSet(desktop_first=1,
              android_first=1, desktop_last=2),
          intent_thread_url=f'https://example.com/{s_type}')
      # Add stage-specific fields based on the stage ID.
      # 150 is the ID associated with the origin trial stage for feature type 0.
      if s_type == 150:
        s.experiment_goals = 'goals'
        s.experiment_risks = 'risks'
        s.announcement_url = 'https://example.com/announce'
      # 151 is the stage ID associated with the origin trial extension.
      elif s_type == 151:
        s.experiment_extension_reason = 'reason'
      # 151 is the ID associated with the shipping stage.
      elif s_type == 160:
        s.finch_url = 'https://example.com/finch'
      s.put()

    self.request_path = '/admin/features/launch/%d/%d?intent' % (
        core_enums.INTENT_SHIP, self.feature_1.key.integer_id())
    self.handler = intentpreview.IntentEmailPreviewHandler()

  def tearDown(self):
    self.feature_1.key.delete()

  def test_get__anon(self):
    """Anon cannot view this preview features, gets redirected to login."""
    testing_config.sign_out()
    feature_id = self.feature_1.key.integer_id()
    with test_app.test_request_context(self.request_path):
      actual_response = self.handler.get_template_data(feature_id=feature_id)
    self.assertEqual('302 FOUND', actual_response.status)

  def test_get__no_existing(self):
    """Trying to view a feature that does not exist gives a 404."""
    testing_config.sign_in('user1@google.com', 123567890)
    bad_feature_id = self.feature_1.key.integer_id() + 1
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(feature_id=bad_feature_id)

  def test_get__no_stage_specified(self):
    """Allowed user can preview intent email for a feature using an old URL."""
    request_path = (
        '/admin/features/launch/%d?intent' % self.feature_1.key.integer_id())
    testing_config.sign_in('user1@google.com', 123567890)
    feature_id = self.feature_1.key.integer_id()
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(feature_id=feature_id)
    self.assertIn('feature', actual_data)
    self.assertEqual('feature one', actual_data['feature']['name'])

  def test_get__normal(self):
    """Allowed user can preview intent email for a feature."""
    testing_config.sign_in('user1@google.com', 123567890)
    feature_id = self.feature_1.key.integer_id()
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(feature_id=feature_id)
    self.assertIn('feature', actual_data)
    self.assertEqual('feature one', actual_data['feature']['name'])

  def test_get_page_data__implement(self):
    """page_data has correct values."""
    feature_id = self.feature_1.key.integer_id()
    with test_app.test_request_context(self.request_path):
      page_data = self.handler.get_page_data(
          feature_id, self.feature_1, core_enums.INTENT_IMPLEMENT)
    self.assertEqual(
        'http://localhost/feature/%d' % feature_id,
        page_data['default_url'])
    self.assertEqual(
        ['motivation'],
        page_data['sections_to_show'])
    self.assertEqual(
        'Intent to Prototype',
        page_data['subject_prefix'])

  def test_get_page_data__ship(self):
    """page_data has correct values."""
    feature_id = self.feature_1.key.integer_id()
    with test_app.test_request_context(self.request_path):
      page_data = self.handler.get_page_data(
          feature_id, self.feature_1, core_enums.INTENT_SHIP)
    self.assertEqual(
        'http://localhost/feature/%d' % feature_id,
        page_data['default_url'])
    self.assertIn('ship', page_data['sections_to_show'])
    self.assertEqual(
        'Intent to Ship',
        page_data['subject_prefix'])

  def test_compute_subject_prefix__incubate_new_feature(self):
    """We offer users the correct subject line for each intent stage."""
    self.assertEqual(
        'Intent stage "None"',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_NONE))

    self.assertEqual(
        'Intent stage "Start incubating"',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_INCUBATE))

    self.assertEqual(
        'Intent to Prototype',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_IMPLEMENT))

    self.assertEqual(
        'Ready for Trial',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_EXPERIMENT))

    self.assertEqual(
        'Intent stage "Evaluate readiness to ship"',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_IMPLEMENT_SHIP))

    self.assertEqual(
        'Intent to Experiment',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_EXTEND_TRIAL))

    self.assertEqual(
        'Intent to Ship',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_SHIP))

    self.assertEqual(
        'Intent to Extend Deprecation Trial',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_REMOVED))

    self.assertEqual(
        'Intent stage "Shipped"',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_SHIPPED))

    self.assertEqual(
        'Intent stage "Parked"',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_PARKED))

  def test_compute_subject_prefix__deprecate_feature(self):
    """We offer users the correct subject line for each intent stage."""
    self.feature_1.feature_type = core_enums.FEATURE_TYPE_DEPRECATION_ID
    self.assertEqual(
        'Intent stage "None"',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_NONE))

    self.assertEqual(
        'Intent to Deprecate and Remove',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_INCUBATE))

    self.assertEqual(
        'Request for Deprecation Trial',
        self.handler.compute_subject_prefix(
            self.feature_1, core_enums.INTENT_EXTEND_TRIAL))


class IntentEmailPreviewTemplateTest(testing_config.CustomTestCase):

  HANDLER_CLASS = intentpreview.IntentEmailPreviewHandler

  def setUp(self):
    super(IntentEmailPreviewTemplateTest, self).setUp()
    self.feature_1 = FeatureEntry(
        name='feature one', summary='sum', owner_emails=['user1@google.com'],
        category=1, intent_stage=core_enums.INTENT_IMPLEMENT)
    # Hardcode the key for the template test
    self.feature_1.key = ndb.Key('FeatureEntry', 234)
    self.feature_1.put()

    self.request_path = '/admin/features/launch/%d/%d?intent' % (
        core_enums.INTENT_SHIP, self.feature_1.key.integer_id())
    self.handler = self.HANDLER_CLASS()
    self.feature_id = self.feature_1.key.integer_id()

    testing_config.sign_in('user1@google.com', 123567890)
    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data(
        feature_id=self.feature_id)
      page_data = self.handler.get_page_data(
          self.feature_id, self.feature_1, core_enums.INTENT_IMPLEMENT)

    self.template_data.update(page_data)
    self.template_data['nonce'] = 'fake nonce'
    template_path = self.handler.get_template_path(self.template_data)
    self.full_template_path = os.path.join(template_path)

    self.maxDiff = None

  def tearDown(self):
    self.feature_1.key.delete()
    testing_config.sign_out()

  def test_html_rendering(self):
    """We can render the template with valid html."""
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(feature_id=self.feature_id)
      actual_data.update(self.handler.get_common_data())
      actual_data['nonce'] = 'fake nonce'
      actual_data['xsrf_token'] = ''
      actual_data['xsrf_token_expires'] = 0

      template_text = self.handler.render(
          actual_data, self.full_template_path)
      testing_config.sign_out()
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(template_text)
    # TESTDATA.make_golden(template_text, 'test_html_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['test_html_rendering.html'], template_text)
