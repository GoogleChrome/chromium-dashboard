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

from google.cloud import ndb  # type: ignore

from internals import core_enums
from internals.metrics_models import WebDXFeatureObserver


class ProgressVote(ndb.Model):
    """One reviewer's vote on what the state of a progress item should be."""

    NEEDS_REVIEW = 1
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


def review_is_done(status):
    """Determine if a review status indicates the review is complete.

    Args:
        status: The review status code to check.

    Returns:
        True if the review is done or not applicable, False otherwise.
    """
    return status in (core_enums.REVIEW_ISSUES_ADDRESSED, core_enums.REVIEW_NA)


# These functions return a true value when the checkmark should be shown.
# If they return a string, and it starts with "http:" or "https:", it will
# be used as a link URL.
PROGRESS_DETECTORS = {
    'Initial public proposal': lambda f, _: f.initial_public_proposal_url,
    'Explainer': lambda f, _: f.explainer_links and f.explainer_links[0],
    'Web feature': lambda f, _: (
        f.web_feature
        and f.web_feature != WebDXFeatureObserver.MISSING_FEATURE_ID
    ),  # noqa: E501
    'Tracking bug URL': lambda f, _: f.bug_url,
    'Security review issues addressed': lambda f, _: review_is_done(
        f.security_review_status
    ),
    'Privacy review issues addressed': lambda f, _: review_is_done(
        f.privacy_review_status
    ),
    'Intent to Prototype email': lambda f, stages: (
        core_enums.STAGE_TYPES_PROTOTYPE[f.feature_type]
        and stages[core_enums.STAGE_TYPES_PROTOTYPE[f.feature_type]][
            0
        ].intent_thread_url
    ),
    'Intent to Ship email': lambda f, stages: (
        core_enums.STAGE_TYPES_SHIPPING[f.feature_type]
        and stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][
            0
        ].intent_thread_url
    ),
    'Ready for Developer Testing email': lambda f, stages: (
        core_enums.STAGE_TYPES_DEV_TRIAL[f.feature_type]
        and stages[core_enums.STAGE_TYPES_DEV_TRIAL[f.feature_type]][
            0
        ].announcement_url
    ),
    'Intent to Experiment email': lambda f, stages: (
        core_enums.STAGE_TYPES_ORIGIN_TRIAL[f.feature_type]
        and stages[core_enums.STAGE_TYPES_ORIGIN_TRIAL[f.feature_type]][
            0
        ].intent_thread_url
    ),
    'Samples': lambda f, _: f.sample_links and f.sample_links[0],
    'Doc links': lambda f, _: f.doc_links and f.doc_links[0],
    'Spec link': lambda f, _: f.spec_link,
    'Draft API spec': lambda f, _: f.spec_link,
    'API spec': lambda f, _: f.api_spec,
    'Spec mentor': lambda f, _: f.spec_mentor_emails,
    'TAG review requested': lambda f, _: f.tag_review,
    'TAG review issues addressed': lambda f, _: review_is_done(
        f.tag_review_status
    ),
    'Web developer signals': lambda f, _: bool(
        f.web_dev_views and f.web_dev_views != core_enums.DEV_NO_SIGNALS
    ),
    'Vendor signals': lambda f, _: bool(
        f.ff_views != core_enums.NO_PUBLIC_SIGNALS
        or f.safari_views != core_enums.NO_PUBLIC_SIGNALS
    ),
    'Updated vendor signals': lambda f, _: bool(
        f.ff_views != core_enums.NO_PUBLIC_SIGNALS
        or f.safari_views != core_enums.NO_PUBLIC_SIGNALS
    ),
    'Final vendor signals': lambda f, _: bool(
        f.ff_views != core_enums.NO_PUBLIC_SIGNALS
        or f.safari_views != core_enums.NO_PUBLIC_SIGNALS
    ),
    'Estimated target milestone': lambda f, stages: bool(
        core_enums.STAGE_TYPES_SHIPPING[f.feature_type]
        and stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][
            0
        ].milestones  # noqa: E501
        and stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][
            0
        ].milestones.desktop_first
    ),
    'Updated target milestone': lambda f, stages: bool(
        core_enums.STAGE_TYPES_SHIPPING[f.feature_type]
        and stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][
            0
        ].milestones  # noqa: E501
        and stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][
            0
        ].milestones.desktop_first
    ),
    'Final target milestone': lambda f, stages: bool(
        core_enums.STAGE_TYPES_SHIPPING[f.feature_type]
        and stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][
            0
        ].milestones  # noqa: E501
        and stages[core_enums.STAGE_TYPES_SHIPPING[f.feature_type]][
            0
        ].milestones.desktop_first
    ),
    'Finch feature name or non-finch justification': lambda f, stages: bool(
        f.finch_name or f.non_finch_justification
    ),
    'Code in Chromium': lambda f, _: (
        f.impl_status_chrome
        in (
            core_enums.IN_DEVELOPMENT,
            core_enums.BEHIND_A_FLAG,
            core_enums.ENABLED_BY_DEFAULT,
            core_enums.ORIGIN_TRIAL,
        )
    ),
    'Motivation': lambda f, _: bool(f.motivation),
    'Code removed': lambda f, _: f.impl_status_chrome == core_enums.REMOVED,
    'Rollout impact': lambda f, stages: (
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]]
        and stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][
            0
        ].rollout_impact
    ),
    'Rollout milestone': lambda f, stages: (
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]]
        and stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][
            0
        ].rollout_milestone
    ),
    'Rollout platforms': lambda f, stages: (
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]]
        and stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][
            0
        ].rollout_platforms
    ),
    'Rollout details': lambda f, stages: (
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]]
        and stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][
            0
        ].rollout_details
    ),
    'Rollout stage plan': lambda f, stages: (
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]]
        and stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][
            0
        ].rollout_stage_plan
    ),
    'Enterprise policies': lambda f, stages: (
        stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]]
        and stages[core_enums.STAGE_TYPES_ROLLOUT[f.feature_type]][
            0
        ].enterprise_policies
    ),
}
