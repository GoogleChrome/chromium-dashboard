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

import flask
import werkzeug
from google.cloud import ndb  # type: ignore

from framework import rediscache
from internals import core_enums
from internals import stage_helpers
from internals.core_models import Feature, FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate
from pages import guide


test_app = flask.Flask(__name__)


class TestWithFeature(testing_config.CustomTestCase):

  REQUEST_PATH_FORMAT = 'subclasses fill this in'
  HANDLER_CLASS = 'subclasses fill this in'

  def setUp(self):
    self.request_path = self.REQUEST_PATH_FORMAT
    self.handler = self.HANDLER_CLASS()

  def tearDown(self):
    rediscache.flushall()


class FeatureCreateTest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = guide.FeatureCreateHandler()

  def tearDown(self) -> None:
    kinds: list[ndb.Model] = [Feature, FeatureEntry, Stage, Gate]
    for kind in kinds:
      entities = kind.query().fetch()
      for entity in entities:
        entity.key.delete()

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
            'feature_type': '0'
        }, method='POST'):
      actual_response = self.handler.process_post_data()

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertTrue(location.startswith('/guide/edit/'))
    new_feature_id = int(location.split('/')[-1])
    feature = Feature.get_by_id(new_feature_id)
    self.assertEqual(1, feature.category)
    self.assertEqual('Feature name', feature.name)
    self.assertEqual('Feature summary', feature.summary)

    # Ensure FeatureEntry entity was also created.
    feature_entry = FeatureEntry.get_by_id(new_feature_id)
    self.assertEqual(1, feature_entry.category)
    self.assertEqual('Feature name', feature_entry.name)
    self.assertEqual('Feature summary', feature_entry.summary)
    self.assertEqual('user1@google.com', feature_entry.creator_email)

    # Ensure Stage and Gate entities were also created.
    stages = Stage.query().fetch()
    gates = Gate.query().fetch()
    self.assertEqual(len(stages), 7)
    self.assertEqual(len(gates), 4)


class FeatureEditHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = Feature(
        name='feature one', summary='sum', owner=['user1@google.com'],
        category=1)
    self.feature_1.put()
    self.stage = core_enums.INTENT_INCUBATE  # Shows first form

    self.fe_1 = FeatureEntry(
        id=self.feature_1.key.integer_id(), name='feature one',
        summary='sum', owner_emails=['user1@google.com'], category=1,
        standard_maturity=1, ff_views=1, safari_views=1, web_dev_views=1,
        impl_status_chrome=1)
    self.fe_1.put()

    feature_id = self.fe_1.key.integer_id()
    # Shipping stage is not created, and should be created on edit.
    stage_types = [core_enums.STAGE_BLINK_INCUBATE,
        core_enums.STAGE_BLINK_PROTOTYPE,
        core_enums.STAGE_BLINK_DEV_TRIAL,
        core_enums.STAGE_BLINK_EVAL_READINESS,
        core_enums.STAGE_BLINK_ORIGIN_TRIAL,
        core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL]
    for stage_type in stage_types:
      stage = Stage(feature_id=feature_id, stage_type=stage_type,
          milestones=MilestoneSet())
      stage.put()

    self.request_path = ('/guide/stage/%d/%d' % (
        self.feature_1.key.integer_id(), self.stage))
    self.handler = guide.FeatureEditHandler()

  def tearDown(self):
    self.feature_1.key.delete()
    self.fe_1.key.delete()
    for stage in Stage.query():
      stage.key.delete()

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

  def test_post__anon(self):
    """Anon cannot edit features, gets a 403."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path, method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.process_post_data(
            feature_id=self.feature_1.key.integer_id(), stage_id=self.stage)

  def test_post__non_allowed(self):
    """Non-allowed cannot edit features, gets a 403."""
    testing_config.sign_in('user1@example.com', 1234567890)
    with test_app.test_request_context(self.request_path, method='POST'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.process_post_data(
            feature_id=self.feature_1.key.integer_id(), stage_id=self.stage)

  def test_post__normal_valid(self):
    """Allowed user can edit a feature."""
    testing_config.sign_in('user1@google.com', 1234567890)

    # Fields changed.
    form_fields = ('category, name, summary, shipped_milestone, '
        'intent_to_experiment_url, experiment_risks, experiment_reason, '
        'origin_trial_feedback_url, intent_to_ship_url')
    # Expected stage change items.
    new_shipped_milestone = '84'
    new_ready_for_trial_url = 'https://example.com/trial'
    new_intent_to_experiment_url = 'https://example.com/intent'
    new_experiment_risks = 'Some pretty risky business'
    new_experiment_extension_reason = 'It would be fun'
    new_origin_trial_feedback_url = 'https://example.com/ot_intent'
    new_intent_to_ship_url = 'https://example.com/shipping'

    with test_app.test_request_context(
        self.request_path, data={
            'form_fields': form_fields,
            'category': '2',
            'name': 'Revised feature name',
            'summary': 'Revised feature summary',
            'shipped_milestone': new_shipped_milestone,
            'ready_for_trial_url': new_ready_for_trial_url,
            'intent_to_experiment_url': new_intent_to_experiment_url,
            'experiment_risks': new_experiment_risks,
            'experiment_extension_reason': new_experiment_extension_reason,
            'origin_trial_feedback_url': new_origin_trial_feedback_url,
            'intent_to_ship_url': new_intent_to_ship_url,
            'feature_type': '1'
        }):
      actual_response = self.handler.process_post_data(
          feature_id=self.fe_1.key.integer_id(), stage_id=self.stage)

    self.assertEqual('302 FOUND', actual_response.status)
    location = actual_response.headers['location']
    self.assertEqual('/guide/edit/%d' % self.feature_1.key.integer_id(),
                     location)
    revised_feature = Feature.get_by_id(
        self.feature_1.key.integer_id())
    self.assertEqual(2, revised_feature.category)
    self.assertEqual('Revised feature name', revised_feature.name)
    self.assertEqual('Revised feature summary', revised_feature.summary)
    self.assertEqual(84, revised_feature.shipped_milestone)

    # Ensure changes were also made to FeatureEntry entity
    revised_entry = FeatureEntry.get_by_id(
        self.feature_1.key.integer_id())
    self.assertEqual(2, revised_entry.category)
    self.assertEqual('Revised feature name', revised_entry.name)
    self.assertEqual('Revised feature summary', revised_entry.summary)

    # Ensure changes were also made to Stage entities
    stages = stage_helpers.get_feature_stages(
        self.feature_1.key.integer_id())
    self.assertEqual(len(stages.keys()), 7)
    dev_trial_stage = stages.get(130)
    origin_trial_stages = stages.get(150)
    ot_extension_stages = stages.get(151)
    # Stage for shipping should have been created.
    shipping_stages = stages.get(160)
    self.assertIsNotNone(origin_trial_stages)
    self.assertIsNotNone(shipping_stages)
    self.assertIsNotNone(ot_extension_stages)
    # Check that correct stage fields were changed.
    self.assertEqual(dev_trial_stage[0].announcement_url,
                     new_ready_for_trial_url)
    self.assertEqual(origin_trial_stages[0].experiment_risks,
        new_experiment_risks)
    self.assertEqual(origin_trial_stages[0].intent_thread_url,
        new_intent_to_experiment_url)
    self.assertEqual(origin_trial_stages[0].origin_trial_feedback_url,
        new_origin_trial_feedback_url)
    self.assertEqual(ot_extension_stages[0].experiment_extension_reason,
        new_experiment_extension_reason)
    self.assertEqual(shipping_stages[0].milestones.desktop_first,
        int(new_shipped_milestone))
    self.assertEqual(shipping_stages[0].intent_thread_url,
        new_intent_to_ship_url)
