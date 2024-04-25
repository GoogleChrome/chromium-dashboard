# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testing_config  # isort: split

import json
import logging
import os.path
import re
from typing import NotRequired, TypedDict
from unittest import mock

import flask
from google.cloud import ndb  # type: ignore

from api import external_reviews_api
from api.api_specs import MILESTONESET_FIELD_DATA_TYPES
from api.features_api import FeaturesAPI
from internals.core_enums import (
  ENABLED_BY_DEFAULT,
  FEATURE_TYPE_EXISTING_ID,
  FEATURE_TYPE_INCUBATE_ID,
  IN_DEV,
  IN_DEVELOPMENT,
  MISC,
  NEUTRAL,
  NO_PUBLIC_SIGNALS,
  PROPOSED,
  SHIPPED,
  SIGNALS_NA,
  STAGE_BLINK_DEV_TRIAL,
  STAGE_BLINK_ORIGIN_TRIAL,
  STAGE_BLINK_PROTOTYPE,
  STAGE_FAST_SHIPPING,
  UNSET_STD,
)
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.feature_links import FeatureLinks
from internals.link_helpers import LINK_TYPE_GITHUB_ISSUE, Link
from internals.review_models import Gate
from internals.user_models import AppUser

test_app = flask.Flask(__name__)


def make_feature(
  name: str,
  active_stage: int,
  tag: str | None = None,
  webkit: str | None = None,
  gecko: str | None = None,
  milestones: MilestoneSet = MilestoneSet(),
) -> FeatureEntry:
  fe = FeatureEntry(
    name=name,
    category=1,
    summary='Summary',
    tag_review=tag,
    tag_review_resolution=None,
    ff_views_link=gecko,
    ff_views_link_result=None,
    safari_views_link=webkit,
    safari_views_link_result=None,
  )
  fe.put()
  fe_id = fe.key.integer_id()
  stage = Stage(feature_id=fe_id, stage_type=active_stage, milestones=milestones)
  stage.put()
  fe.active_stage_id = stage.key.id()
  fe.put()
  if tag:
    fl = FeatureLinks(
      feature_ids=[fe_id], url=tag, type=LINK_TYPE_GITHUB_ISSUE, information={}
    )
    fl.put()
  if webkit:
    fl = FeatureLinks(
      feature_ids=[fe_id], url=webkit, type=LINK_TYPE_GITHUB_ISSUE, information={}
    )
    fl.put()
  if gecko:
    fl = FeatureLinks(
      feature_ids=[fe_id], url=gecko, type=LINK_TYPE_GITHUB_ISSUE, information={}
    )
    fl.put()
  return fe


class ExternalReviewsAPITest(testing_config.CustomTestCase):
  def setUp(self):
    self.handler = external_reviews_api.ExternalReviewsAPI()
    self.request_path = '/api/v0/external_reviews'
    self.maxDiff = None

  def tearDown(self):
    kinds: list[ndb.Model] = [FeatureEntry, FeatureLinks, Stage, Gate]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_no_reviews(self):
    """When no reviews have been started, the result is empty."""
    make_feature('Feature one', STAGE_BLINK_PROTOTYPE)

    actual = self.handler.do_get(review_group='tag')
    self.assertEqual({'reviews': [], 'link_previews': []}, actual)

  def test_one_unfinished_tag_review(self):
    """Basic success case."""
    tag = 'https://github.com/w3ctag/design-reviews/issues/1'
    webkit = 'https://github.com/WebKit/standards-positions/issues/3'
    fe = make_feature(
      'Feature one',
      STAGE_BLINK_PROTOTYPE,
      tag=tag,
      webkit=webkit,
    )

    result = self.handler.do_get(review_group='tag')
    self.assertEqual(
      {
        'reviews': [
          dict(
            feature=dict(id=fe.key.id(), name='Feature one'),
            review_link=tag,
            current_stage='prototyping',
            estimated_start_milestone=None,
            estimated_end_milestone=None,
          )
        ],
        'link_previews': [
          dict(
            url=tag, type=LINK_TYPE_GITHUB_ISSUE, information={}, http_error_code=None
          )
        ],
      },
      result,
    )

  def test_one_unfinished_webkit_review(self):
    tag = 'https://github.com/w3ctag/design-reviews/issues/1'
    webkit = 'https://github.com/WebKit/standards-positions/issues/3'
    fe = make_feature(
      'Feature one',
      STAGE_BLINK_PROTOTYPE,
      tag=tag,
      webkit=webkit,
    )

    result = self.handler.do_get(review_group='webkit')
    self.assertEqual(
      {
        'reviews': [
          dict(
            feature=dict(id=fe.key.id(), name='Feature one'),
            review_link=webkit,
            current_stage='prototyping',
            estimated_start_milestone=None,
            estimated_end_milestone=None,
          )
        ],
        'link_previews': [
          dict(
            url=webkit, type=LINK_TYPE_GITHUB_ISSUE, information={}, http_error_code=None
          )
        ],
      },
      result,
    )

  def test_one_unfinished_gecko_review(self):
    gecko = 'https://github.com/mozilla/standards-positions/issues/2'
    webkit = 'https://github.com/WebKit/standards-positions/issues/3'
    fe = make_feature(
      'Feature one',
      STAGE_BLINK_PROTOTYPE,
      gecko=gecko,
      webkit=webkit,
    )

    result = self.handler.do_get(review_group='gecko')
    self.assertEqual(
      {
        'reviews': [
          dict(
            feature=dict(id=fe.key.id(), name='Feature one'),
            review_link=gecko,
            current_stage='prototyping',
            estimated_start_milestone=None,
            estimated_end_milestone=None,
          )
        ],
        'link_previews': [
          dict(
            url=gecko, type=LINK_TYPE_GITHUB_ISSUE, information={}, http_error_code=None
          )
        ],
      },
      result,
    )

  def test_milestones_summarize(self):
    """We take the earliest start milestone and the latest end milestone.

    This isn't quite right for sorting urgency, since a later start milestone for some platforms
    probably indicates that the feature will ship later, but it makes more sense in the UI.
    """
    tag = 'https://github.com/w3ctag/design-reviews/issues/1'
    webkit = 'https://github.com/WebKit/standards-positions/issues/3'
    fe = make_feature(
      'Feature one',
      STAGE_BLINK_PROTOTYPE,
      tag=tag,
      webkit=webkit,
      milestones=MilestoneSet(
        desktop_first=93, android_first=94, ios_last=95, webview_last=96
      ),
    )

    result = self.handler.do_get(review_group='tag')
    self.assertEqual(
      {
        'reviews': [
          dict(
            feature=dict(id=fe.key.id(), name='Feature one'),
            review_link=tag,
            current_stage='prototyping',
            estimated_start_milestone=93,
            estimated_end_milestone=96,
          )
        ],
        'link_previews': [
          dict(
            url=tag, type=LINK_TYPE_GITHUB_ISSUE, information={}, http_error_code=None
          )
        ],
      },
      result,
    )

  def test_omit_non_review_links(self):
    """Vendor positions of 'shipping', 'in development', and 'na' shouldn't be returned, even if
    they link to a standards-positions repository.
    """
    webkit = 'https://github.com/WebKit/standards-positions/issues/3'
    fe = make_feature('Feature one', STAGE_BLINK_PROTOTYPE, webkit=webkit)
    result = self.handler.do_get(review_group='webkit')
    self.assertEqual(1, len(result['reviews']))
    for view in [SHIPPED, IN_DEV, SIGNALS_NA]:
      fe.safari_views = view
      fe.put()
      result = self.handler.do_get(review_group='webkit')
      self.assertEqual(0, len(result['reviews']))

  def test_omit_review_links_to_non_review_repo(self):
    """Links that aren't to the reviewer's positions repository shouldn't be returned."""
    webkit = 'https://github.com/WebKit/standards-positions/issues/3'
    fe = make_feature('Feature one', STAGE_BLINK_PROTOTYPE, webkit=webkit)
    result = self.handler.do_get(review_group='webkit')
    self.assertEqual(1, len(result['reviews']))
    fe.safari_views_link = (
      'https://github.com/whatwg/html/pull/10139#pullrequestreview-1966263347'
    )
    fe.put()
    result = self.handler.do_get(review_group='webkit')
    self.assertEqual(0, len(result['reviews']))

  def test_finished_review_isnt_shown(self):
    tag = 'https://github.com/w3ctag/design-reviews/issues/1'
    webkit = 'https://github.com/WebKit/standards-positions/issues/3'
    fe = make_feature(
      'Feature one',
      STAGE_BLINK_PROTOTYPE,
      tag=tag,
      webkit=webkit,
    )
    fe.tag_review_resolution = 'unsatisfied'
    fe.put()

    result = self.handler.do_get(review_group='tag')
    self.assertEqual(
      {
        'reviews': [],
        'link_previews': [],
      },
      result,
    )

  def test_feature_without_a_crawled_link_isnt_shown(self):
    tag = 'https://github.com/w3ctag/design-reviews/issues/1'
    fe = make_feature(
      'Feature one',
      STAGE_BLINK_PROTOTYPE,
      tag=tag,
    )

    result = self.handler.do_get(review_group='tag')
    self.assertEqual(1, len(result['reviews']))
    fe.tag_review = 'https://github.com/w3ctag/design-reviews/issues/2'
    fe.put()
    result = self.handler.do_get(review_group='tag')
    self.assertEqual(0, len(result['reviews']))

  class FeatureDict(TypedDict):
    name: str
    summary: NotRequired[str]
    blink_components: NotRequired[str]
    owner_emails: NotRequired[str]
    category: NotRequired[int]
    feature_type: NotRequired[int]
    standard_maturity: NotRequired[int]
    impl_status_chrome: int
    ff_views: int
    ff_views_link: str | None
    safari_views: NotRequired[int]
    web_dev_views: NotRequired[int]
    safari_views_link: NotRequired[str]

  def _use_ui_to_create_feature(
    self,
    fe: FeatureDict,
    active_stage_type: int,
    milestones: MilestoneSet | None = None,
  ) -> FeatureEntry:
    """Uses the same path as the web UI to create a feature.

    This is slower than directly .put()ing FeatureEntries, but ensures at least 1 test makes no
    assumptions about what the UI actually does.
    """
    name = fe['name']
    patch_update: dict[str, object] = dict(fe)
    # Only set the minimum set of fields in the initial POST. The FeaturesAPI expects to handle
    # most updates in the later PATCH call.
    initial_fields = dict(
      blink_components=patch_update.pop('blink_components', 'Blink'),
      category=patch_update.pop('category', MISC),
      feature_type=patch_update.pop('feature_type', FEATURE_TYPE_INCUBATE_ID),
      ff_views=patch_update.pop('ff_views'),
      impl_status_chrome=patch_update.pop('impl_status_chrome'),
      name=patch_update.pop('name'),
      safari_views=patch_update.pop('safari_views', NO_PUBLIC_SIGNALS),
      standard_maturity=patch_update.pop('standard_maturity', UNSET_STD),
      summary=patch_update.pop('summary', f'Summary for {name}'),
      web_dev_views=patch_update.pop('web_dev_views', NO_PUBLIC_SIGNALS),
    )
    with test_app.test_request_context('/api/v0/features/create', json=initial_fields):
      response = FeaturesAPI().do_post()
    # A new feature ID should be returned.
    self.assertIsInstance(response['feature_id'], int)
    # New feature should exist.
    new_feature = FeatureEntry.get_by_id(response['feature_id'])
    self.assertIsNotNone(new_feature)
    feature_id = new_feature.key.id()

    # Now that the feature and its stages are created, update the rest of the fields, and the active
    # stage, using a PATCH.
    active_stage = Stage.query(
      Stage.feature_id == feature_id, Stage.stage_type == active_stage_type
    ).fetch(keys_only=True)
    self.assertEqual(1, len(active_stage), active_stage)
    patch_update.update(id=feature_id, active_stage_id=active_stage[0].id())

    class FeatureUpdate(TypedDict):
      feature_changes: dict[str, object]
      stages: list[dict[str, object]]

    update: FeatureUpdate = dict(feature_changes=patch_update, stages=[])
    if milestones is not None:
      stage_info = dict(id=active_stage[0].id())
      for field_name, _type in MILESTONESET_FIELD_DATA_TYPES:
        value = getattr(milestones, field_name, None)
        if value is not None:
          stage_info[field_name] = dict(form_field_name=field_name, value=value)
      update['stages'].append(stage_info)

    with test_app.test_request_context(f'/api/v0/features/{feature_id}', json=update):
      response = FeaturesAPI().do_patch()
    self.assertEqual(f'Feature {feature_id} updated.', response['message'])

    return new_feature

  @mock.patch.object(Link, '_parse_github_issue', autospec=True)
  def test_e2e_features_that_need_review_are_included(self, mockParse: mock.MagicMock):
    """This one test goes through the same path as the UI to create features, to catch if other
    tests have made incorrect assumptions about how that flow works. This is slower, so it shouldn't
    be used to test every part of the feature.

    This test also checks that a JSON file used by the Playwright tests is actually the output
    format for this API, which allows a test on the Playwright side to also check its assumptions
    about the output format.
    """
    # Create a feature using the admin user.
    app_admin = AppUser(email='admin@example.com')
    app_admin.is_admin = True
    app_admin.put()

    testing_config.sign_in(app_admin.email, app_admin.key.id())

    unexpected_links: list[str] = []

    def github_result(link):
      result = dict(
        url=re.sub(r'github\.com', 'api.github.com', link.url),
        number=1,
        title='A Title',
        user_login=None,
        state='open',
        state_reason=None,
        assignee_login=None,
        created_at='2024-04-15T08:30:42',
        updated_at='2024-04-15T10:30:43',
        closed_at=None,
        labels=[],
      )
      if link.url == 'https://github.com/mozilla/standards-positions/issues/1':
        result.update(
          number=1, labels=['position: oppose'], title="Opposed review isn't shown"
        )
      elif link.url == 'https://github.com/mozilla/standards-positions/issues/2':
        result.update(number=2)
      elif link.url == 'https://github.com/mozilla/standards-positions/issues/3':
        result.update(number=3)
      elif link.url == 'https://github.com/mozilla/standards-positions/issues/4':
        result.update(number=4)
      elif link.url == 'https://github.com/mozilla/standards-positions/issues/5':
        result.update(number=5)
      elif link.url == 'https://github.com/WebKit/standards-positions/issues/6':
        result.update(number=6)
      elif link.url == 'https://github.com/mozilla/standards-positions/issues/8':
        raise Exception(f'Expected fetch error for {link.url=}')
      elif link.url == 'https://github.com/mozilla/standards-positions/issues/9':
        result.update(number=4, state='closed', closed_at='2024-04-20T07:15:34')
      else:
        unexpected_links.append(link.url)
      return result

    mockParse.side_effect = github_result

    _f1 = self._use_ui_to_create_feature(
      dict(
        name='Feature 1',
        impl_status_chrome=IN_DEVELOPMENT,
        ff_views=NEUTRAL,
        ff_views_link='https://github.com/mozilla/standards-positions/issues/1',
      ),
      active_stage_type=STAGE_BLINK_DEV_TRIAL,
    )
    f2 = self._use_ui_to_create_feature(
      dict(
        name='Feature 2',
        feature_type=FEATURE_TYPE_EXISTING_ID,
        impl_status_chrome=ENABLED_BY_DEFAULT,
        ff_views=NEUTRAL,
        ff_views_link='https://github.com/mozilla/standards-positions/issues/2',
      ),
      active_stage_type=STAGE_FAST_SHIPPING,
    )
    f3 = self._use_ui_to_create_feature(
      dict(
        name='Feature 3',
        impl_status_chrome=PROPOSED,
        ff_views=NO_PUBLIC_SIGNALS,
        ff_views_link='https://github.com/mozilla/standards-positions/issues/3',
      ),
      active_stage_type=STAGE_BLINK_PROTOTYPE,
      milestones=MilestoneSet(desktop_first=101, desktop_last=103),
    )
    f4 = self._use_ui_to_create_feature(
      dict(
        name='Feature 4',
        impl_status_chrome=ENABLED_BY_DEFAULT,
        ff_views=NO_PUBLIC_SIGNALS,
        ff_views_link='https://github.com/mozilla/standards-positions/issues/4',
      ),
      active_stage_type=STAGE_BLINK_PROTOTYPE,
    )
    f5 = self._use_ui_to_create_feature(
      dict(
        name='Feature 5',
        impl_status_chrome=PROPOSED,
        ff_views=NO_PUBLIC_SIGNALS,
        ff_views_link='https://github.com/mozilla/standards-positions/issues/5',
      ),
      active_stage_type=STAGE_BLINK_PROTOTYPE,
      milestones=MilestoneSet(desktop_first=100, desktop_last=104),
    )
    _f6 = self._use_ui_to_create_feature(
      dict(
        name='Feature 6',
        impl_status_chrome=PROPOSED,
        ff_views=SHIPPED,
        ff_views_link=None,
        # Not a Firefox view, so this won't be included in the results.
        safari_views_link='https://github.com/WebKit/standards-positions/issues/6',
      ),
      active_stage_type=STAGE_BLINK_DEV_TRIAL,
    )
    f7 = self._use_ui_to_create_feature(
      dict(
        name='Feature 7 shares a review with Feature 5',
        impl_status_chrome=PROPOSED,
        ff_views=NO_PUBLIC_SIGNALS,
        ff_views_link='https://github.com/mozilla/standards-positions/issues/5',
      ),
      active_stage_type=STAGE_BLINK_ORIGIN_TRIAL,
      milestones=MilestoneSet(desktop_first=100, desktop_last=104),
    )
    with self.assertLogs(level=logging.ERROR):  # So the log doesn't echo.
      _f8 = self._use_ui_to_create_feature(
        dict(
          name='Feature 8 has a nonexistent standards-position link',
          impl_status_chrome=PROPOSED,
          ff_views=NO_PUBLIC_SIGNALS,
          ff_views_link='https://github.com/mozilla/standards-positions/issues/8',
        ),
        active_stage_type=STAGE_BLINK_PROTOTYPE,
      )
    _f9 = self._use_ui_to_create_feature(
      dict(
        name='Feature 9 is closed without a position',
        impl_status_chrome=PROPOSED,
        ff_views=NO_PUBLIC_SIGNALS,
        ff_views_link='https://github.com/mozilla/standards-positions/issues/9',
      ),
      active_stage_type=STAGE_BLINK_PROTOTYPE,
    )

    testing_config.sign_out()

    result = self.handler.do_get(review_group='gecko')

    # This test expectation is saved to a JSON file so the
    # Playwright tests can use it as a mock API response. Because the real feature IDs are
    # dynamically generated, we have to slot them into the right places here.
    with open(
      os.path.join(
        os.path.dirname(__file__),
        '../packages/playwright/tests/external_reviews_api_result.json',
      )
    ) as f:
      expected_response = json.load(f)
    expected_response['reviews'][0]['feature']['id'] = f7.key.id()
    expected_response['reviews'][1]['feature']['id'] = f3.key.id()
    expected_response['reviews'][2]['feature']['id'] = f5.key.id()
    expected_response['reviews'][3]['feature']['id'] = f4.key.id()
    expected_response['reviews'][4]['feature']['id'] = f2.key.id()

    self.assertEqual(expected_response, result)
    self.assertEqual([], unexpected_links)
