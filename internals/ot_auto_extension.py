# -*- coding: utf-8 -*-
# Copyright 2025 Google Inc.
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

"""Automatic origin trial extensions for features with an approved I2S.

API owners have agreed that once an Intent to Ship is approved, no
additional approval is needed to extend an existing origin trial so that
it covers users on older versions of Chrome while the feature ships
(see GoogleChrome/chromium-dashboard#6875).
"""

import logging
from datetime import datetime

from internals import core_enums, notifier_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote

AUTO_EXTENSION_REASON = (
    'Automatically requested extension. The Intent to Ship for this '
    'feature was approved, and API owners have agreed that no additional '
    'approval is needed to extend an origin trial until the feature has '
    'shipped.'
)


def _get_shipping_milestone(ship_stage: Stage) -> int | None:
    """Return the latest milestone in which the feature starts shipping."""
    milestones: MilestoneSet | None = ship_stage.milestones
    if milestones is None:
        return None
    shipping_milestones = [
        m
        for m in (
            milestones.desktop_first,
            milestones.android_first,
            milestones.ios_first,
            milestones.webview_first,
        )
        if m is not None
    ]
    if not shipping_milestones:
        return None
    return max(shipping_milestones)


def _get_trial_end_milestone(ot_stage: Stage) -> int | None:
    """Return the trial's latest end milestone, considering extensions."""
    end_milestones: list[int] = []
    if ot_stage.milestones and ot_stage.milestones.desktop_last:
        end_milestones.append(ot_stage.milestones.desktop_last)

    extension_stages: list[Stage] = Stage.query(
        Stage.ot_stage_id == ot_stage.key.integer_id()
    ).fetch()
    for es in extension_stages:
        if not es.milestones or not es.milestones.desktop_last:
            continue
        gate: Gate | None = Gate.query(
            Gate.stage_id == es.key.integer_id()
        ).get()
        # Only count extensions that already have the needed approvals.
        if gate and gate.state in Gate.APPROVED_STATES:
            end_milestones.append(es.milestones.desktop_last)

    if not end_milestones:
        return None
    return max(end_milestones)


def _create_extension_stage(
    fe: FeatureEntry,
    ot_stage: Stage,
    ship_stage: Stage,
    end_milestone: int,
    approver_email: str,
    extension_stage_type: int,
) -> None:
    """Create a pre-approved extension stage for the given trial."""
    feature_id = fe.key.integer_id()
    extension_stage = Stage(
        feature_id=feature_id,
        stage_type=extension_stage_type,
        ot_stage_id=ot_stage.key.integer_id(),
        milestones=MilestoneSet(desktop_last=end_milestone),
        experiment_extension_reason=AUTO_EXTENSION_REASON,
        intent_thread_url=ship_stage.intent_thread_url,
        ot_owner_email=ot_stage.ot_owner_email,
        ot_display_name=ot_stage.ot_display_name,
        ot_action_requested=True,
        ot_requester_email=approver_email,
    )
    extension_stage.put()

    # The extension does not need a separate approval, so the gate is
    # created in an already-approved "N/A" state.
    gate = Gate(
        feature_id=feature_id,
        stage_id=extension_stage.key.integer_id(),
        gate_type=core_enums.GATE_API_EXTEND_ORIGIN_TRIAL,
        state=Vote.NA,
    )
    gate.put()
    vote = Vote(
        feature_id=feature_id,
        gate_id=gate.key.integer_id(),
        gate_type=core_enums.GATE_API_EXTEND_ORIGIN_TRIAL,
        state=Vote.NA,
        set_on=datetime.now(),
        set_by=approver_email,
    )
    vote.put()

    logging.info(
        f'Auto-created OT extension stage {extension_stage.key.integer_id()} '
        f'to M{end_milestone} for trial stage {ot_stage.key.integer_id()} '
        f'on feature {feature_id}.'
    )
    notifier_helpers.send_trial_extension_approved_notification(
        fe, extension_stage, gate.key.integer_id()
    )


def maybe_extend_trials_for_shipping(
    fe: FeatureEntry, ship_stage: Stage, approver_email: str
) -> None:
    """Extend active origin trials of a feature with a newly approved I2S.

    For each active origin trial on the feature that ends before the
    approved shipping milestone, create an extension stage that is already
    approved, so that the trial covers users who have not yet updated to
    the shipping milestone.
    """
    # Deprecation trials have a different extension process, and shipping
    # for a deprecation feature means removal, so they are not handled.
    if fe.feature_type == core_enums.FEATURE_TYPE_DEPRECATION_ID:
        return

    extension_stage_type = core_enums.STAGE_TYPES_EXTEND_ORIGIN_TRIAL.get(
        fe.feature_type
    )
    ot_stage_type = core_enums.STAGE_TYPES_ORIGIN_TRIAL.get(fe.feature_type)
    if extension_stage_type is None or ot_stage_type is None:
        return

    shipping_milestone = _get_shipping_milestone(ship_stage)
    if shipping_milestone is None:
        return

    ot_stages: list[Stage] = Stage.query(
        Stage.stage_type == ot_stage_type,
        Stage.feature_id == fe.key.integer_id(),
    ).fetch()
    for ot_stage in ot_stages:
        # Only extend trials that have actually been created.
        if not ot_stage.origin_trial_id:
            continue
        end_milestone = _get_trial_end_milestone(ot_stage)
        if end_milestone is None or end_milestone >= shipping_milestone:
            continue
        _create_extension_stage(
            fe,
            ot_stage,
            ship_stage,
            shipping_milestone,
            approver_email,
            extension_stage_type,
        )
