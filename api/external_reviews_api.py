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


"""API handlers for retrieving the status of external feature reviews (e.g., TAG, Gecko, WebKit)."""

import math
import re
from collections import defaultdict
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
from framework.utils import chunk_list
from internals import core_enums
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
    """Enumeration of feature stage types."""

    INCUBATING = 'incubating'
    PROTOTYPING = 'prototyping'
    DEV_TRIAL = 'dev-trial'
    WIDE_REVIEW = 'wide-review'
    ORIGIN_TRIAL = 'origin-trial'
    SHIPPING = 'shipping'
    SHIPPED = 'shipped'


STAGE_TYPES: dict[int, StageType] = {
    core_enums.STAGE_BLINK_INCUBATE: StageType.INCUBATING,
    core_enums.STAGE_BLINK_PROTOTYPE: StageType.PROTOTYPING,
    core_enums.STAGE_BLINK_DEV_TRIAL: StageType.DEV_TRIAL,
    core_enums.STAGE_BLINK_EVAL_READINESS: StageType.WIDE_REVIEW,
    core_enums.STAGE_BLINK_ORIGIN_TRIAL: StageType.ORIGIN_TRIAL,
    core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL: StageType.ORIGIN_TRIAL,
    core_enums.STAGE_BLINK_SHIPPING: StageType.SHIPPING,
    core_enums.STAGE_FAST_PROTOTYPE: StageType.PROTOTYPING,
    core_enums.STAGE_FAST_DEV_TRIAL: StageType.DEV_TRIAL,
    core_enums.STAGE_FAST_ORIGIN_TRIAL: StageType.ORIGIN_TRIAL,
    core_enums.STAGE_FAST_EXTEND_ORIGIN_TRIAL: StageType.ORIGIN_TRIAL,
    core_enums.STAGE_FAST_SHIPPING: StageType.SHIPPING,
    core_enums.STAGE_PSA_IMPLEMENT: StageType.WIDE_REVIEW,
    core_enums.STAGE_PSA_DEV_TRIAL: StageType.DEV_TRIAL,
    core_enums.STAGE_PSA_SHIPPING: StageType.SHIPPING,
    core_enums.STAGE_DEP_PLAN: StageType.INCUBATING,
    core_enums.STAGE_DEP_DEV_TRIAL: StageType.DEV_TRIAL,
    core_enums.STAGE_DEP_SHIPPING: StageType.SHIPPING,
    core_enums.STAGE_DEP_DEPRECATION_TRIAL: StageType.SHIPPED,
    core_enums.STAGE_DEP_EXTEND_DEPRECATION_TRIAL: StageType.SHIPPED,
    core_enums.STAGE_DEP_REMOVE_CODE: StageType.SHIPPED,
    core_enums.STAGE_ENT_ROLLOUT: StageType.SHIPPED,
    core_enums.STAGE_ENT_SHIPPED: StageType.SHIPPED,
}


def stage_type(feature: FeatureEntry, stage: Stage | None) -> StageType:
    """Determine the stage type for a given feature and stage."""
    if stage is None:
        return StageType.INCUBATING

    tentative_type = STAGE_TYPES[stage.stage_type]
    if (
        tentative_type == StageType.SHIPPING
        and feature.impl_status_chrome == core_enums.ENABLED_BY_DEFAULT
    ):
        return StageType.SHIPPED
    return tentative_type


def _min_of_first(stage: Stage | None) -> int | None:
    """Return the minimum of the first milestones, ignoring None values."""
    if stage is None or stage.milestones is None:
        return None
    return min(
        (
            m
            for m in (
                stage.milestones.desktop_first,
                stage.milestones.android_first,
                stage.milestones.ios_first,
                stage.milestones.webview_first,
            )
            if m is not None
        ),
        default=None
    )


def _max_of_last(stage: Stage | None) -> int | None:
    """Return the maximum of the last milestones, ignoring None values."""
    if stage is None or stage.milestones is None:
        return None
    return max(
        (
            m
            for m in (
                stage.milestones.desktop_last,
                stage.milestones.android_last,
                stage.milestones.ios_last,
                stage.milestones.webview_last,
            )
            if m is not None
        ),
        default=None
    )


class ExternalReviewerInfo:
    """Information about an external reviewer group."""

    unreviewed_features_query: ndb.Query
    """Fetch this to get features for which this group has been asked for a review, and they haven't
  finished it yet."""  # noqa: E501

    _review_link: str
    """The name of the field in FeatureEntry that holds the review link for review_group."""  # noqa: E501

    review_pattern: re.Pattern
    """Matches URLs in the reviewer's review repository."""

    group_name: str
    """The name used for this group inside Chrome Status."""

    def __init__(self, group_name: Literal['tag', 'gecko', 'webkit']):
        """Initialize the external review mapper."""
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
        """Get a list of features with outstanding external reviews from a particular review body."""  # noqa: E501
        review_group: str | None = kwargs.get('review_group', None)
        if review_group not in ['tag', 'gecko', 'webkit']:
            self.abort(404, f'invalid review group {review_group}')

        reviewer_info = ExternalReviewerInfo(review_group)
        unreviewed_features = reviewer_info.unreviewed_features_query.fetch()

        # WP features cannot be confidential, so this should not matter.
        # But if any is ever somehow confidential, remove it.
        unreviewed_features = [
            fe
            for fe in unreviewed_features
            if not fe.confidential and not fe.deleted
        ]

        # Remove features for which the review link isn't a request for the review group to review the  # noqa: E501
        # feature.
        unreviewed_features = [
            fe
            for fe in unreviewed_features
            if reviewer_info.review_pattern.search(
                reviewer_info.review_link(fe)
            )
        ]

        active_stage = self._find_active_stages(unreviewed_features)

        # Filter to reviews for which we could fetch a preview.
        feature_links, _has_stale_links = get_feature_links_by_feature_ids(
            [fe.key.id() for fe in unreviewed_features],
            update_stale_links=True,  # noqa: E501
        )
        review_links = {
            reviewer_info.review_link(fe) for fe in unreviewed_features
        }
        previewable_urls = {fl['url'] for fl in feature_links}

        # Build the response objects.
        reviews = [
            OutstandingReview(
                review_link=reviewer_info.review_link(fe),
                feature=FeatureLink(id=fe.key.id(), name=fe.name),
                current_stage=stage_type(fe, stage),
                estimated_start_milestone=_min_of_first(stage),
                estimated_end_milestone=_max_of_last(stage),
            )
            for fe in unreviewed_features
            for stage in [active_stage.get(fe.key.id(), None)]
            if reviewer_info.review_link(fe) in previewable_urls
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

        result = ExternalReviewsResponse(
            reviews=reviews, link_previews=link_previews
        )  # noqa: E501
        return result.to_dict()

    def _find_active_stages(
        self, unreviewed_features: list[FeatureEntry]
    ) -> dict[int, Stage]:
        """Build a map from each feature ID to the stage with the greatest stage_type that has at least one non-None milestone."""  # noqa: E501
        # Collect all feature IDs.
        feature_ids = [fe.key.id() for fe in unreviewed_features]

        # Fetch all stages for these features in chunks to avoid query limits.
        stages = []
        for chunk in chunk_list(feature_ids, 30):
            stages.extend(Stage.query(Stage.feature_id.IN(chunk)).fetch())
        stages = [s for s in stages if not s.archived]

        # Group stages by feature_id.
        stages_by_fid = defaultdict(list)
        for stage in stages:
            stages_by_fid[stage.feature_id].append(stage)

        # Build a map from each feature ID to the stage with the greatest stage_type
        # that has at least one non-None milestone.
        active_stage = {}
        for fe in unreviewed_features:
            fid = fe.key.id()
            feature_stages = stages_by_fid.get(fid, [])

            # Filter stages that have at least one non-None milestone.
            valid_stages = [
                s
                for s in feature_stages
                if _min_of_first(s) is not None or _max_of_last(s) is not None
            ]

            if valid_stages:
                # Pick the stage with the greatest stage_type, using creation time as a tie-breaker.
                chosen_stage = max(
                    valid_stages,
                    key=lambda s: (s.stage_type, s.created),
                )
                active_stage[fid] = chosen_stage

        return active_stage
