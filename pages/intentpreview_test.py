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

import datetime
import testing_config  # Must be imported before the module under test.

from flask import render_template

import os
import flask
import settings

from google.cloud import ndb  # type: ignore
from pages import intentpreview
from internals import core_enums
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote

test_app = flask.Flask(__name__,
  template_folder=settings.get_flask_template_path())

# Load testdata to be used across all of the CustomTestCases
TESTDATA = testing_config.Testdata(__file__)


def _create_complete_feature():
  return FeatureEntry(
    id=234,
    # Metadata
    accurate_as_of=datetime.datetime(2025, 10, 11, 12, 0, 0),
    outstanding_notifications=5,
    creator_email='creator.test@example.com',
    updater_email='updater.test@example.com',
    owner_emails=['owner.one@example.com', 'owner.two@example.com'],
    editor_emails=['editor.one@example.com', 'editor.two@example.com'],
    cc_emails=['cc.one@example.com', 'cc.two@example.com'],
    unlisted=False,
    deleted=False,
    name='Test Feature for NDB Constructor',
    summary='This is a detailed summary of the test feature being created. It is designed to populate every possible field for testing purposes.',
    markdown_fields=['summary', 'motivation'],
    category=1,
    enterprise_product_category=2,
    enterprise_feature_categories=['testing', 'developer-tools'],
    blink_components=['Blink>Test', 'Blink>Internals>Test'],
    star_count=42,
    search_tags=['test', 'example', 'constructor'],
    feature_notes='Some internal notes about this feature entry, not typically user-visible.',
    web_feature='test-feature-ndb-constructor',
    webdx_usecounter_enum='TestFeatureNdbConstructor',
    feature_type=0,
    intent_stage=1,
    active_stage_id=1001,
    bug_url='https://bugs.chromium.org/p/chromium/issues/detail?id=12345',
    launch_bug_url='https://buganizer.corp.google.com/issues/67890',
    screenshot_links=['https://example.com/screenshot1.png', 'https://example.com/screenshot2.png'],
    first_enterprise_notification_milestone=130,
    enterprise_impact=2,
    breaking_change=True,
    confidential=False,
    shipping_year=2026,

    # Implementation in Chrome
    impl_status_chrome=3,
    flag_name='enable-test-feature-constructor',
    finch_name='TestFeatureConstructorStudy',
    non_finch_justification='This feature is not suitable for a Finch experiment due to its nature.',
    ongoing_constraints='This feature is only available in secure contexts (HTTPS).',
    rollout_plan=0,

    # Adoption
    motivation='The motivation for this feature is to provide a comprehensive example for developers.',
    devtrial_instructions='To test, navigate to chrome://flags and enable #enable-test-feature-constructor.',
    activation_risks='There are minimal activation risks, primarily related to experimental flag interactions.',
    measurement='Usage will be measured via a UMA histogram named "Test.Feature.Constructor.Usage".',
    availability_expectation='Expected to be available in developer channels by M132.',
    adoption_expectation='We expect 100% adoption within our test suites.',
    adoption_plan='No external adoption plan is necessary as this is for testing.',

    # Standardization & Interop
    initial_public_proposal_url='https://discourse.wicg.io/t/proposal-for-test-feature/9999',
    explainer_links=['https://example.com/explainer.md', 'https://example.com/explainer_slides.pdf'],
    requires_embedder_support=False,
    standard_maturity=2,
    spec_link='https://w3c.github.io/test-feature-spec/',
    api_spec=True,
    automation_spec=True,
    spec_mentor_emails=['spec.mentor@example.com'],
    interop_compat_risks='Low risk. The API surface is small and unlikely to conflict with other browser implementations.',
    prefixed=False,
    all_platforms=True,
    all_platforms_descr='This feature is expected to work on all desktop and mobile platforms.',
    tag_review='https://github.com/w3ctag/design-reviews/issues/999',
    tag_review_status=1,
    non_oss_deps='There are no non-Open-Source dependencies.',
    anticipated_spec_changes='We anticipate minor changes to the spec based on implementer feedback.',

    # Vendor views
    ff_views=2,
    safari_views=3,
    web_dev_views=1,
    ff_views_link='https://github.com/mozilla/standards-positions/issues/999',
    safari_views_link='https://lists.webkit.org/pipermail/webkit-dev/2025-October/subject.html',
    web_dev_views_link='https://developer.chrome.com/blog/test-feature-coming-soon/',
    ff_views_notes='Has expressed cautious optimism.',
    safari_views_notes='Has raised concerns about potential privacy implications.',
    web_dev_views_notes='Positive feedback received from the web developer community via social media.',
    other_views_notes='No signals from other implementers at this time.',

    # Security & Privacy
    security_risks='The main security risk involves ensuring that data is properly sanitized.',
    security_review_status=0,
    privacy_review_status=0,
    security_continuity_id=112233,
    security_launch_issue_id=445566,

    # Testing / Regressions
    ergonomics_risks='The API could be complex for new developers, but documentation should mitigate this.',
    wpt=True,
    wpt_descr='A full suite of Web Platform Tests (WPT) will be developed and upstreamed.',
    webview_risks='No specific WebView risks have been identified.',

    # Devrel & Docs
    devrel_emails=['devrel-lead@example.com'],
    debuggability='The feature is fully debuggable via Chrome DevTools, with a dedicated panel.',
    doc_links=['https://developer.chrome.com/docs/test-feature/'],
    sample_links=['https://github.com/GoogleChrome/samples/tree/gh-pages/test-feature'],
  )


class IntentEmailPreviewTemplateTest(testing_config.CustomTestCase):

  HANDLER_CLASS = intentpreview.IntentEmailPreviewHandler

  def setUp(self):
    super(IntentEmailPreviewTemplateTest, self).setUp()
    self.complete_feature = _create_complete_feature()
    self.complete_feature.put()

    self.feature_2 = FeatureEntry(
        id=456, name='feature two', summary='sum',
        owner_emails=['user1@google.com'], feature_type=2,
        web_feature='WebFeature2',
        category=1, intent_stage=core_enums.INTENT_SHIP)
    self.feature_2.put()


    self.stage_1 = Stage(id=100, feature_id=234, stage_type=150,
                         ot_display_name="Test 123")
    self.stage_1.put()
    self.gate_1 = Gate(id=101, feature_id=234, stage_id=100,
                       gate_type=3, state=Vote.NA)
    self.gate_1.put()

    self.stage_2 = Stage(id=200, feature_id=234, stage_type=120)
    self.stage_2.put()
    self.gate_2 = Gate(id=201, feature_id=234, stage_id=200,
                       gate_type=1, state=Vote.NA)
    self.gate_2.put()

    self.stage_3 = Stage(id=300, feature_id=234, stage_type=160,
                         intent_thread_url='https://example.com/ship')
    self.stage_3.put()
    self.gate_3 = Gate(id=201, feature_id=234, stage_id=300,
                       gate_type=4, state=Vote.APPROVED)
    self.gate_3.put()
    self.stage_2_1 = Stage(id=210, feature_id=456, stage_type=360)
    self.stage_2_1.put()

    self.request_path = '/features/234/stage/300'
    self.intent_preview_path = 'blink/intent_to_implement.html'
    self.handler = self.HANDLER_CLASS()

    with test_app.test_request_context(self.request_path):
      self.template_data = self.handler.get_template_data(
        feature_id=self.complete_feature.key.integer_id(),
        stage_id=self.stage_3.key.integer_id())
      page_data = self.handler.get_page_data(
          self.complete_feature, core_enums.IntentDraftType.SHIP, self.gate_3)

    self.template_data.update(page_data)
    self.template_data['nonce'] = 'fake nonce'
    template_path = self.handler.get_template_path(self.template_data)
    self.full_template_path = os.path.join(template_path)

    self.maxDiff = None

  def tearDown(self):
    for kind in [FeatureEntry, Gate, Stage]:
      for entity in kind.query():
        entity.key.delete()

  def test_template_rendering_prototype(self):
    """We can render the prototype template with valid html."""
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(
          feature_id=self.complete_feature.key.integer_id(),
          stage_id=self.stage_2.key.integer_id(),
          gate_id=self.gate_2.key.integer_id())
      actual_data.update(self.handler.get_common_data())
      actual_data['nonce'] = 'fake nonce'
      actual_data['xsrf_token'] = ''
      actual_data['xsrf_token_expires'] = 0

      body = render_template(self.intent_preview_path, **actual_data)
      testing_config.sign_out()
    # TESTDATA.make_golden(body, 'test_html_prototype_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['test_html_prototype_rendering.html'], body)

  def test_template_rendering_origin_trial(self):
    """We can render the origin trial intent template."""
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(
          feature_id=self.complete_feature.key.integer_id(),
          stage_id=self.stage_1.key.integer_id(),
          gate_id=self.gate_1.key.integer_id())
      actual_data.update(self.handler.get_common_data())
      actual_data['nonce'] = 'fake nonce'
      actual_data['xsrf_token'] = ''
      actual_data['xsrf_token_expires'] = 0

      body = render_template(self.intent_preview_path, **actual_data)
      testing_config.sign_out()
    # TESTDATA.make_golden(body, 'test_html_ot_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['test_html_ot_rendering.html'], body)

  def test_template_rendering_ship(self):
    """We can render the ship intent template."""
    # Add a shipping stage.
    Stage(feature_id=self.complete_feature.key.integer_id(), stage_type=160,
          milestones=MilestoneSet(desktop_first=100),
          intent_thread_url='https://example.com/ship').put()
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(
          feature_id=self.complete_feature.key.integer_id(),
          stage_id=self.stage_3.key.integer_id(),
          gate_id=self.gate_3.key.integer_id())
      actual_data.update(self.handler.get_common_data())
      actual_data['nonce'] = 'fake nonce'
      actual_data['xsrf_token'] = ''
      actual_data['xsrf_token_expires'] = 0

      body = render_template(self.intent_preview_path, **actual_data)
      testing_config.sign_out()
    # TESTDATA.make_golden(body, 'test_html_ship_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['test_html_ship_rendering.html'], body)

  def test_template_rendering_ship__enterprise(self):
    """We can render the ship intent template with enterprise stages."""
    # Add some enterprise stages with milestones.
    Stage(feature_id=self.complete_feature.key.integer_id(), stage_type=1061,
          milestones=MilestoneSet(desktop_first=100)).put()
    Stage(feature_id=self.complete_feature.key.integer_id(), stage_type=1061,
          milestones=MilestoneSet(desktop_first=105)).put()
    Stage(feature_id=self.complete_feature.key.integer_id(),
          stage_type=1061).put()
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(
          feature_id=self.complete_feature.key.integer_id(),
          stage_id=self.stage_3.key.integer_id(),
          gate_id=self.gate_3.key.integer_id())
      actual_data.update(self.handler.get_common_data())
      actual_data['nonce'] = 'fake nonce'
      actual_data['xsrf_token'] = ''
      actual_data['xsrf_token_expires'] = 0

      body = render_template(self.intent_preview_path, **actual_data)
      testing_config.sign_out()
    # TESTDATA.make_golden(body, 'test_html_ship_enterprise_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['test_html_ship_enterprise_rendering.html'], body)

  def test_template_rendering_psa_ship(self):
    """We can render the ship intent template for PSA features."""
    with test_app.test_request_context(self.request_path):
      actual_data = self.handler.get_template_data(
          feature_id=self.feature_2.key.integer_id(),
          stage_id=self.stage_2_1.key.integer_id())
      actual_data.update(self.handler.get_common_data())
      actual_data['nonce'] = 'fake nonce'
      actual_data['xsrf_token'] = ''
      actual_data['xsrf_token_expires'] = 0

      body = render_template(self.intent_preview_path, **actual_data)
      testing_config.sign_out()
    # TESTDATA.make_golden(body, 'test_html_psa_ship_rendering.html')
    self.assertMultiLineEqual(
      TESTDATA['test_html_psa_ship_rendering.html'], body)
