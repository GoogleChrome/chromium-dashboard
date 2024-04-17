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

from datetime import datetime

from unittest import mock
from google.cloud import ndb  # type: ignore

from api import external_reviews_api

from internals.core_enums import STAGE_BLINK_PROTOTYPE
from internals.core_models import FeatureEntry, Stage, MilestoneSet
from internals.review_models import Gate
from internals.feature_links import FeatureLinks
from internals.link_helpers import LINK_TYPE_GITHUB_ISSUE


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
    kinds: list[ndb.Model] = [FeatureEntry, Gate]
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
    tag = 'https://github.com/w3ctag/design_reviews/issues/1'
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
    """Basic success case."""
    tag = 'https://github.com/w3ctag/design_reviews/issues/1'
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
    """Basic success case."""
    gecko = 'https://github.com/mozille/standards-positions/issues/2'
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
    """We take the earliest start milestone and the latest end milestone."""
    tag = 'https://github.com/w3ctag/design_reviews/issues/1'
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

  def test_finished_review_isnt_shown(self):
    """When no reviews have been started, the result is empty."""
    tag = 'https://github.com/w3ctag/design_reviews/issues/1'
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
    """Basic success case."""
    tag = 'https://github.com/w3ctag/design_reviews/issues/1'
    fe = make_feature(
      'Feature one',
      STAGE_BLINK_PROTOTYPE,
      tag=tag,
    )

    result = self.handler.do_get(review_group='tag')
    self.assertEqual(1, len(result['reviews']))
    fe.tag_review = 'https://github.com/w3ctag/design_reviews/issues/2'
    fe.put()
    result = self.handler.do_get(review_group='tag')
    self.assertEqual(0, len(result['reviews']))
