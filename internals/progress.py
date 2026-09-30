# -*- coding: utf-8 -*-
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

"""Defines models and detectors for evaluating feature progress items."""

import datetime
from collections.abc import Callable
from dataclasses import dataclass

from google.cloud import ndb  # type: ignore

from internals import core_enums
from internals.core_models import FeatureEntry, Stage
from internals.metrics_models import WebDXFeatureObserver
from internals.processes import *


class ProgressVote(ndb.Model):
    """One reviewer's vote on what the state of a progress item should be."""

    NOT_STARTED = 0  # User has not entered enough values to evaluate.
    NEEDS_REVIEW = 1  # Values are ready human or AI review.
    VERIFIED = 2
    NA = 3
    NEEDS_WORK = 4
    VOTE_VALUES = {
        NEEDS_REVIEW: 'needs_review',
        VERIFIED: 'verified',
        NA: 'na',
        NEEDS_WORK: 'needs_work',
    }

    feature_id = ndb.IntegerProperty(required=True)
    progress_item_name = ndb.StringProperty(required=True)
    state = ndb.IntegerProperty(
        required=True,
        choices=[NEEDS_REVIEW, VERIFIED, NA, NEEDS_WORK],
    )
    feedback = ndb.StringProperty()
    set_on = ndb.DateTimeProperty(required=True)
    set_by = ndb.StringProperty(required=True)

    @classmethod
    def is_valid_state(cls, new_state: int) -> bool:
        """Return true if new_state is valid."""
        return new_state in cls.VOTE_VALUES


def set_progress_vote(
    feature_id: int,
    progress_item_name: str,
    state: int,
    set_by: str,
    feedback: str | None = None,
) -> ProgressVote:
    """Store a ProgressVote in ndb, overwriting any existing vote for (feature_id, progress_item_name)."""
    if not ProgressVote.is_valid_state(state):
        raise ValueError('Invalid progress vote state')

    now = datetime.datetime.now()
    existing_votes: list[ProgressVote] = ProgressVote.query(
        ProgressVote.feature_id == feature_id,
        ProgressVote.progress_item_name == progress_item_name,
    ).fetch()

    if existing_votes:
        vote = existing_votes[0]
        vote.state = state
        vote.feedback = feedback
        vote.set_on = now
        vote.set_by = set_by
        vote.put()
        for extra_vote in existing_votes[1:]:
            extra_vote.key.delete()
        return vote

    vote = ProgressVote(
        feature_id=feature_id,
        progress_item_name=progress_item_name,
        state=state,
        feedback=feedback,
        set_on=now,
        set_by=set_by,
    )
    vote.put()
    return vote


def review_is_done(status):
    """Determine if a review status indicates the review is complete.

    Args:
        status: The review status code to check.

    Returns:
        True if the review is done or not applicable, False otherwise.
    """
    return status in (core_enums.REVIEW_ISSUES_ADDRESSED, core_enums.REVIEW_NA)


@dataclass(frozen=True)
class ProgressDetectorResult:
    """Represents the output of a progress detector."""

    state: int
    feedback: str | None = None


def _detect_initial_public_proposal(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.initial_public_proposal_url:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_explainer(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.explainer_links or not fe.explainer_links[0]:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_web_feature(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if (
        not fe.web_feature
        or fe.web_feature == WebDXFeatureObserver.MISSING_FEATURE_ID
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_tracking_bug_url(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.bug_url:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_security_review_issues_addressed(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not review_is_done(fe.security_review_status):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_privacy_review_issues_addressed(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not review_is_done(fe.privacy_review_status):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_samples(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.sample_links or not fe.sample_links[0]:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_doc_links(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.doc_links or not fe.doc_links[0]:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_spec_link(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.spec_link:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_spec_mentor(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.spec_mentor_emails:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_tag_review_requested(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.tag_review:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_tag_review_issues_addressed(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not review_is_done(fe.tag_review_status):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_web_dev_views(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.web_dev_views or fe.web_dev_views == core_enums.DEV_NO_SIGNALS:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_firefox_views(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if fe.ff_views == core_enums.NO_PUBLIC_SIGNALS:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_safari_views(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if fe.safari_views == core_enums.NO_PUBLIC_SIGNALS:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_desktop_milestone(
    fe: FeatureEntry, stages: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    stage_type = core_enums.STAGE_TYPES_SHIPPING[fe.feature_type]
    if (
        not stage_type
        or not stages[stage_type][0].milestones
        or not stages[stage_type][0].milestones.desktop_first
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_android_milestone(
    fe: FeatureEntry, stages: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    stage_type = core_enums.STAGE_TYPES_SHIPPING[fe.feature_type]
    if (
        not stage_type
        or not stages[stage_type][0].milestones
        or (
            not stages[stage_type][0].milestones.android_first
            and not stages[stage_type][0].milestones.desktop_first
        )
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_webview_milestone(
    fe: FeatureEntry, stages: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    stage_type = core_enums.STAGE_TYPES_SHIPPING[fe.feature_type]
    if (
        not stage_type
        or not stages[stage_type][0].milestones
        or (
            not stages[stage_type][0].milestones.webview_first
            and not stages[stage_type][0].milestones.desktop_first
        )
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_finch_feature_name_or_non_finch_justification(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.finch_name and not fe.non_finch_justification:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_motivation(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if not fe.motivation:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_code_removed(
    fe: FeatureEntry, _: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    if fe.impl_status_chrome != core_enums.REMOVED:
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_rollout_impact(
    fe: FeatureEntry, stages: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    stage_type = core_enums.STAGE_TYPES_ROLLOUT[fe.feature_type]
    if (
        not stage_type
        or not stages[stage_type]
        or not stages[stage_type][0].rollout_impact
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_rollout_milestone(
    fe: FeatureEntry, stages: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    stage_type = core_enums.STAGE_TYPES_ROLLOUT[fe.feature_type]
    if (
        not stage_type
        or not stages[stage_type]
        or not stages[stage_type][0].rollout_milestone
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_rollout_platforms(
    fe: FeatureEntry, stages: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    stage_type = core_enums.STAGE_TYPES_ROLLOUT[fe.feature_type]
    if (
        not stage_type
        or not stages[stage_type]
        or not stages[stage_type][0].rollout_platforms
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_rollout_details(
    fe: FeatureEntry, stages: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    stage_type = core_enums.STAGE_TYPES_ROLLOUT[fe.feature_type]
    if (
        not stage_type
        or not stages[stage_type]
        or not stages[stage_type][0].rollout_details
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_rollout_stage_plan(
    fe: FeatureEntry, stages: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    stage_type = core_enums.STAGE_TYPES_ROLLOUT[fe.feature_type]
    if (
        not stage_type
        or not stages[stage_type]
        or not stages[stage_type][0].rollout_stage_plan
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


def _detect_enterprise_policies(
    fe: FeatureEntry, stages: dict[int, list[Stage]]
) -> ProgressDetectorResult:
    stage_type = core_enums.STAGE_TYPES_ROLLOUT[fe.feature_type]
    if (
        not stage_type
        or not stages[stage_type]
        or not stages[stage_type][0].enterprise_policies
    ):
        return ProgressDetectorResult(ProgressVote.NOT_STARTED)
    return ProgressDetectorResult(ProgressVote.NEEDS_REVIEW)


PROGRESS_DETECTORS: dict[
    str,
    Callable[[FeatureEntry, dict[int, list[Stage]]], ProgressDetectorResult],
] = {
    PI_INITIAL_PUBLIC_PROPOSAL.name: _detect_initial_public_proposal,
    PI_EXPLAINER.name: _detect_explainer,
    PI_WEB_FEATURE.name: _detect_web_feature,
    PI_TRACKING_BUG.name: _detect_tracking_bug_url,
    PI_SEC_REVIEW.name: _detect_security_review_issues_addressed,
    PI_PRI_REVIEW.name: _detect_privacy_review_issues_addressed,
    PI_SAMPLES.name: _detect_samples,
    PI_DOC_LINKS.name: _detect_doc_links,
    PI_SPEC_LINK.name: _detect_spec_link,
    PI_SPEC_MENTOR.name: _detect_spec_mentor,
    PI_TAG_REQUESTED.name: _detect_tag_review_requested,
    PI_TAG_ADDRESSED.name: _detect_tag_review_issues_addressed,
    PI_WEB_DEV_VIEWS.name: _detect_web_dev_views,
    PI_FIREFOX_VIEWS.name: _detect_firefox_views,
    PI_SAFARI_VIEWS.name: _detect_safari_views,
    PI_DESKTOP_MILESTONE.name: _detect_desktop_milestone,
    PI_ANDROID_MILESTONE.name: _detect_android_milestone,
    PI_WEBVIEW_MILESTONE.name: _detect_webview_milestone,
    PI_FINCH_FEATURE_OR_JUSTIFY.name: (
        _detect_finch_feature_name_or_non_finch_justification
    ),
    PI_MOTIVATION.name: _detect_motivation,
    PI_CODE_REMOVED.name: _detect_code_removed,
    PI_ROLLOUT_IMPACT.name: _detect_rollout_impact,
    PI_ROLLOUT_MILESTONE.name: _detect_rollout_milestone,
    PI_ROLLOUT_PLATFORMS.name: _detect_rollout_platforms,
    PI_ROLLOUT_DETAILS.name: _detect_rollout_details,
    PI_ROLLOUT_STAGE_PLAN.name: _detect_rollout_stage_plan,
    PI_ENTERPRISE_POLICIES.name: _detect_enterprise_policies,
}
