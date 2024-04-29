# Copyright 2024 Google Inc.
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


import math
import re
from enum import StrEnum
from typing import Literal

from chromestatus_openapi.models.external_reviews_response import (
  ExternalReviewsResponse,
)
from chromestatus_openapi.models.feature_link import FeatureLink
from chromestatus_openapi.models.link_preview import LinkPreview
from chromestatus_openapi.models.outstanding_review import OutstandingReview
from google.cloud import ndb  # type: ignore

from framework import basehandlers
from internals.core_enums import (
  ENABLED_BY_DEFAULT,
  STAGE_BLINK_DEV_TRIAL,
  STAGE_BLINK_EVAL_READINESS,
  STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
  STAGE_BLINK_INCUBATE,
  STAGE_BLINK_ORIGIN_TRIAL,
  STAGE_BLINK_PROTOTYPE,
  STAGE_BLINK_SHIPPING,
  STAGE_DEP_DEPRECATION_TRIAL,
  STAGE_DEP_DEV_TRIAL,
  STAGE_DEP_EXTEND_DEPRECATION_TRIAL,
  STAGE_DEP_PLAN,
  STAGE_DEP_REMOVE_CODE,
  STAGE_DEP_SHIPPING,
  STAGE_ENT_ROLLOUT,
  STAGE_ENT_SHIPPED,
  STAGE_FAST_DEV_TRIAL,
  STAGE_FAST_EXTEND_ORIGIN_TRIAL,
  STAGE_FAST_ORIGIN_TRIAL,
  STAGE_FAST_PROTOTYPE,
  STAGE_FAST_SHIPPING,
  STAGE_PSA_DEV_TRIAL,
  STAGE_PSA_IMPLEMENT,
  STAGE_PSA_SHIPPING,
)
from internals.core_models import FeatureEntry, Stage
from internals.feature_links import (
  get_by_feature_ids as get_feature_links_by_feature_ids,
)
from internals.link_helpers import (
  GECKO_REVIEW_URL_PATTERN,
  TAG_REVIEW_URL_PATTERN,
  WEBKIT_REVIEW_URL_PATTERN,
)


class StageType(StrEnum):
  INCUBATING = 'incubating'
  PROTOTYPING = 'prototyping'
  DEV_TRIAL = 'dev-trial'
  WIDE_REVIEW = 'wide-review'
  ORIGIN_TRIAL = 'origin-trial'
  SHIPPING = 'shipping'
  SHIPPED = 'shipped'


STAGE_TYPES: dict[int, StageType] = {
  STAGE_BLINK_INCUBATE: StageType.INCUBATING,
  STAGE_BLINK_PROTOTYPE: StageType.PROTOTYPING,
  STAGE_BLINK_DEV_TRIAL: StageType.DEV_TRIAL,
  STAGE_BLINK_EVAL_READINESS: StageType.WIDE_REVIEW,
  STAGE_BLINK_ORIGIN_TRIAL: StageType.ORIGIN_TRIAL,
  STAGE_BLINK_EXTEND_ORIGIN_TRIAL: StageType.ORIGIN_TRIAL,
  STAGE_BLINK_SHIPPING: StageType.SHIPPING,
  STAGE_FAST_PROTOTYPE: StageType.PROTOTYPING,
  STAGE_FAST_DEV_TRIAL: StageType.DEV_TRIAL,
  STAGE_FAST_ORIGIN_TRIAL: StageType.ORIGIN_TRIAL,
  STAGE_FAST_EXTEND_ORIGIN_TRIAL: StageType.ORIGIN_TRIAL,
  STAGE_FAST_SHIPPING: StageType.SHIPPING,
  STAGE_PSA_IMPLEMENT: StageType.WIDE_REVIEW,
  STAGE_PSA_DEV_TRIAL: StageType.DEV_TRIAL,
  STAGE_PSA_SHIPPING: StageType.SHIPPING,
  STAGE_DEP_PLAN: StageType.INCUBATING,
  STAGE_DEP_DEV_TRIAL: StageType.DEV_TRIAL,
  STAGE_DEP_SHIPPING: StageType.SHIPPING,
  STAGE_DEP_DEPRECATION_TRIAL: StageType.SHIPPED,
  STAGE_DEP_EXTEND_DEPRECATION_TRIAL: StageType.SHIPPED,
  STAGE_DEP_REMOVE_CODE: StageType.SHIPPED,
  STAGE_ENT_ROLLOUT: StageType.SHIPPED,
  STAGE_ENT_SHIPPED: StageType.SHIPPED,
}


def stage_type(feature: FeatureEntry, stage: Stage | None) -> StageType:
  if stage is None:
    return StageType.INCUBATING

  tentative_type = STAGE_TYPES[stage.stage_type]
  if (
    tentative_type == StageType.SHIPPING
    and feature.impl_status_chrome == ENABLED_BY_DEFAULT
  ):
    return StageType.SHIPPED
  return tentative_type


def min_of_present(*args):
  present_args = [arg for arg in args if arg is not None]
  if len(present_args) == 0:
    return None
  return min(present_args)


def max_of_present(*args):
  present_args = [arg for arg in args if arg is not None]
  if len(present_args) == 0:
    return None
  return max(present_args)


class ExternalReviewerInfo:
  unreviewed_features_query: ndb.Query
  """Fetch this to get features for which this group has been asked for a review, and they haven't
  finished it yet."""

  _review_link: str
  """The name of the field in FeatureEntry that holds the review link for review_group."""

  review_pattern: re.Pattern
  """Matches URLs in the reviewer's review repository."""

  group_name: str
  """The name used for this group inside Chrome Status."""

  def __init__(self, group_name: Literal['tag', 'gecko', 'webkit']):
    self.group_name = group_name
    if group_name == 'tag':
      self.unreviewed_features_query = FeatureEntry.query(
        FeatureEntry.has_open_tag_review == True  # noqa: E712
      )
      self._review_link = 'tag_review'
      self.review_pattern = TAG_REVIEW_URL_PATTERN
    elif group_name == 'gecko':
      self.unreviewed_features_query = FeatureEntry.query(
        FeatureEntry.has_open_ff_review == True  # noqa: E712
      )
      self._review_link = 'ff_views_link'
      self.review_pattern = GECKO_REVIEW_URL_PATTERN
    elif group_name == 'webkit':
      self.unreviewed_features_query = FeatureEntry.query(
        FeatureEntry.has_open_safari_review == True  # noqa: E712
      )
      self._review_link = 'safari_views_link'
      self.review_pattern = WEBKIT_REVIEW_URL_PATTERN
    else:
      raise TypeError(f'Invalid group name {group_name!r}')

  def review_link(self, feature: FeatureEntry) -> str:
    """The link to this reviewer's review of `feature`."""
    return getattr(feature, self._review_link)


class ExternalReviewsAPI(basehandlers.APIHandler):
  """Implements the OpenAPI /external_reviews path."""

  def do_get(self, **kwargs):
    """Get a list of features with outstanding external reviews from a particular review body.
    """
    review_group: str | None = kwargs.get('review_group', None)
    if review_group not in ['tag', 'gecko', 'webkit']:
      self.abort(404, f'invalid review group {review_group}')

    reviewer_info = ExternalReviewerInfo(review_group)
    unreviewed_features = reviewer_info.unreviewed_features_query.fetch()

    # Remove features for which the review link isn't a request for the review group to review the
    # feature.
    unreviewed_features = [
      feature
      for feature in unreviewed_features
      if reviewer_info.review_pattern.search(reviewer_info.review_link(feature))
    ]

    # Build a map from each feature ID to its active Stage information.
    active_stage = {
      stage.feature_id: stage
      for stage in ndb.get_multi(
        [
          ndb.Key('Stage', feature.active_stage_id)
          for feature in unreviewed_features
          if feature.active_stage_id
        ]
      )
      if stage
    }

    # Filter to reviews for which we could fetch a preview.
    feature_links, _has_stale_links = get_feature_links_by_feature_ids(
      [feature.key.id() for feature in unreviewed_features], update_stale_links=True
    )
    review_links = {
      reviewer_info.review_link(feature) for feature in unreviewed_features
    }
    previewable_urls = {fl['url'] for fl in feature_links}

    # Build the response objects.
    reviews = [
      OutstandingReview(
        review_link=reviewer_info.review_link(feature),
        feature=FeatureLink(id=feature.key.id(), name=feature.name),
        current_stage=stage_type(feature, stage),
        estimated_start_milestone=min_of_present(
          stage.milestones.desktop_first,
          stage.milestones.android_first,
          stage.milestones.ios_first,
          stage.milestones.webview_first,
        )
        if stage and stage.milestones
        else None,
        estimated_end_milestone=max_of_present(
          stage.milestones.desktop_last,
          stage.milestones.android_last,
          stage.milestones.ios_last,
          stage.milestones.webview_last,
        )
        if stage and stage.milestones
        else None,
      )
      for feature in unreviewed_features
      for stage in [active_stage.get(feature.key.id(), None)]
      if reviewer_info.review_link(feature) in previewable_urls
    ]
    reviews.sort(
      key=lambda review: (
        review.current_stage,
        review.estimated_end_milestone
        if review.estimated_end_milestone is not None
        else math.inf,
        review.estimated_start_milestone
        if review.estimated_start_milestone is not None
        else math.inf,
        review.review_link,
      )
    )

    link_previews = [
      LinkPreview(
        url=feature_link['url'],
        type=feature_link['type'],
        information=feature_link['information'],
        http_error_code=feature_link['http_error_code'],
      )
      for feature_link in feature_links
      if feature_link['url'] in review_links
    ]
    link_previews.sort(key=lambda link: link.url)

    result = ExternalReviewsResponse(reviews=reviews, link_previews=link_previews)
    return result.to_dict()
