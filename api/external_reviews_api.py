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


import logging
import pprint
from enum import StrEnum

from chromestatus_openapi.models.feature_link import FeatureLink
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

logger = logging.getLogger(__name__)


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


class ExternalReviewsAPI(basehandlers.APIHandler):
  """Implements the OpenAPI /external_reviews path."""

  def do_get(self, **kwargs):
    """Get a list of features with outstanding external reviews from a particular review body.
    """
    review_group: str | None = kwargs.get('review_group', None)
    if review_group not in ['tag', 'gecko', 'webkit']:
      self.abort(404, f'invalid review group {review_group}')

    if review_group == 'tag':
      unreviewed_features = FeatureEntry.query(
        FeatureEntry.tag_review != '', FeatureEntry.tag_review_resolution == None  # noqa: E711
      ).fetch()
      review_link = 'tag_review'
    elif review_group == 'gecko':
      unreviewed_features = FeatureEntry.query(
        FeatureEntry.ff_views_link != '', FeatureEntry.ff_views_link_result == None  # noqa: E711
      ).fetch()
      review_link = 'ff_views_link'
    elif review_group == 'webkit':
      unreviewed_features = FeatureEntry.query(
        FeatureEntry.safari_views_link != '',
        FeatureEntry.safari_views_link_result == None,  # noqa: E711
      ).fetch()
      review_link = 'safari_views_link'

    logger.info(pprint.pformat(unreviewed_features))

    stages = ndb.get_multi(
      [
        ndb.Key('Stage', feature.active_stage_id)
        for feature in unreviewed_features
        if feature.active_stage_id
      ]
    )
    active_stage = {stage.feature_id: stage for stage in stages}

    result = [
      OutstandingReview(
        review_link=getattr(feature, review_link),
        feature=FeatureLink(id=feature.key.id(), name=feature.name),
        current_stage=stage_type(feature, stage),
        estimated_start_milestone=max_of_present(
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
      ).to_dict()
      for feature in unreviewed_features
      for stage in [active_stage.get(feature.key.id(), None)]
    ]

    logger.info(pprint.pformat(result))

    return result
