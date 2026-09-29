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

"""Defines the feature launch processes, stages, progress items, and rules for required approvals and fields."""

from dataclasses import asdict, dataclass

from internals import approval_defs, core_enums
from internals.core_models import Stage
from internals.review_models import Gate


@dataclass
class Action:
    """Dataclass for Action, such as requesting a review or OT."""

    name: str
    url: str
    prerequisites: list[str]
    gate_types: list[int]


@dataclass
class ProgressItem:
    """Dataclass for ProgressItem that has details of a prerequisite."""

    name: str
    field: str | None = None
    description: str | None = None
    criteria: str | None = None


# Note: A new feature always starts with intent_stage == INTENT_NONE
# regardless of process.  intent_stage is set to the first stage of
# a specific process when the user clicks a "Start" button and submits
# a form that sets intent_stage.
@dataclass
class ProcessStage:
    """Dataclass for ProcessStage that describes one major step in a process."""

    name: str
    description: str
    # progress_items are defined on the stage that has the relevant fields.
    progress_items: list[ProgressItem]
    # action prerequisites may reference a PI defined in any stage.
    actions: list[Action]
    approvals: list[approval_defs.GateInfo]
    incoming_stage: int
    outgoing_stage: int
    stage_type: int | None


@dataclass
class Process:
    """Dataclass for Process that describes all stages for a given feature type."""

    name: str
    description: str
    applicability: str
    stages: list[ProcessStage]


def process_to_dict(process):
    """Return nested dicts for the nested dataclasses of a process."""
    # asdict() will recursively convert any dataclass props to dicts.
    stages = [asdict(stage) for stage in process.stages]
    process_dict = {
        'name': process.name,
        'description': process.description,
        'applicability': process.applicability,
        'stages': stages,
    }
    return process_dict


# This page generates a preview of an email that can be sent
# to a mailing list to announce an intent.
# {feature_id}, {stage_id}, and {gate_id} are filled in by JS code.
INTENT_EMAIL_URL = '/feature/{feature_id}/gate/{gate_id}/intent'
INTENT_EMAIL_URL_NO_APPROVALS = '/feature/{feature_id}/stage/{stage_id}/intent'
LAUNCH_BUG_TEMPLATE_URL = '/admin/features/launch/{feature_id}?launch=1'
# TODO(jrobbins): Creation of the launch bug has been a TODO for 5 years.

# Metadata progress items
PI_FEATURE_NAME = ProgressItem(
    'Feature name',
    'name',
    'Feature name is clear, accurate, and not a placeholder',
    (
        'Not a bug number, internal codename, or "TBD". '
        'Matches the intent email subject.'
    ),
)

PI_SUMMARY = ProgressItem(
    'Summary',
    'summary',
    'Summary is complete, developer-facing, and ≥ 100 characters',
    (
        'Explains what the feature does, why it matters, and how developers use it. '
        'Not a copy of the spec title.<br>'
        '<br>'
        'Note: The summary should use the present tense for these descriptions '
        '(e.g., "we launch") instead of the future tense. Since these notes are '
        'published at the time of shipment, they should reflect how the product works '
        'at the point of release.'
    ),
)

PI_SUMMARY_POLICY = ProgressItem(
    'Policy in summary',
    'summary',
    'If enterprise policy applies, policy name is stated in the summary',
    (
        'Required when the feature has an enterprise escape-hatch policy. '
        'Name must match the policy registry.'
    ),
)

PI_CATEGORY = ProgressItem(
    'Category',
    'category',
    'Feature category is correctly set (e.g. CSS, JavaScript, Web APIs)',
    (
        'Must match the nature of the feature. Wrong category routes the feature '
        'into the wrong blog section.'
    ),
)

PI_FEATURE_TYPE = ProgressItem(
    'Feature type',
    'feature_type',
    'Feature type matches the feature description',
    'Drives which stages and gates apply. Cannot be changed after creation.',
)

PI_OWNER_EMAILS = ProgressItem(
    'Owner emails',
    'owner_emails',
    'At least one feature owner email is present and valid',
    (
        'Non-empty, valid email format, not a departed owner. '
        'Update if the owner has left.'
    ),
)


PI_INITIAL_PUBLIC_PROPOSAL = ProgressItem(
    'Initial public proposal', 'initial_public_proposal_url'
)
PI_MOTIVATION = ProgressItem('Motivation', 'motivation')

PI_EXPLAINER = ProgressItem(
    'Explainer',
    'explainer_links',
    'Explainer document is linked and resolves (new incubations only)',
    (
        'Required for new feature incubations. Must include use cases, '
        'sample code, and API shape. N/A for standard implementations.'
    ),
)

PI_WEB_FEATURE = ProgressItem(
    'Web feature',
    'web_feature',
    'Web Feature ID (WebDX / web-features ID) is set or confirmed N/A',
    (
        'If a matching WebDX web-features ID exists (e.g. "fetch", "grid"), '
        'it must be set. If no web-features entry exists yet, note this. '
        'Enables Baseline status linking on webstatus.dev, MDN, and Can I Use.'
    ),
)

PI_TRACKING_BUG = ProgressItem(
    'Tracking bug URL',
    'bug_url',
    'Chromium tracking bug URL is present and resolves (HTTP 200)',
    'bugs.chromium.org URL pattern. Must open and reflect current status.',
)

PI_BLINK_COMPONENTS = ProgressItem(
    'Blink components',
    'blink_components',
    'Blink component is not a generic catch-all (e.g. not just "Blink")',
    (
        'Drives reviewer notifications. Verify it maps to the correct owning team.'
    ),
)

PI_SPEC_LINK = ProgressItem(
    'Spec link',
    'spec_link',
    (
        'Specification link is present, resolves (HTTP 200), '
        'and points to the correct section'
    ),
    (
        'Not a redirect to the spec homepage. Expected hosts: '
        'w3.org, whatwg.org, wicg.github.io, tc39.es, khronos.org.'
    ),
)

PI_SPEC_MATURITY = ProgressItem(
    'Spec Maturity',
    'standard_maturity',
    'Specification maturity / standards track status is current and accurate',
    (
        "Should reflect actual status: Editor's Draft, In Development, "
        'Shipped, etc. Not stale.'
    ),
)

PI_SPEC_MENTOR = ProgressItem('Spec mentor', 'spec_mentors')
PI_DRAFT_API_SPEC = ProgressItem('Draft API spec')

PI_SAMPLES = ProgressItem(
    'Samples',
    'sample_links',
    'Sample code or live demo is available',
    (
        'At minimum a basic usage example: CodePen, Glitch, GitHub demo, '
        "or MDN 'Examples' section."
    ),
)

PI_DRAFT_API_OVERVIEW = ProgressItem('Draft API overview (may be on MDN)')
PI_SEC_REVIEW = ProgressItem('Security review issues addressed')
PI_PRI_REVIEW = ProgressItem('Privacy review issues addressed')
# TODO(jrobbins): needs detector.
PI_EXTERNAL_REVIEWS = ProgressItem('External reviews')

PI_TAG_REQUESTED = ProgressItem(
    'TAG review requested',
    'tag_review',
    'TAG review is linked, or explicitly noted as N/A with justification',
    (
        'W3C TAG review link (github.com/w3ctag) should be present. '
        'Missing without justification is a flag.'
    ),
)

PI_DOC_LINKS = ProgressItem('Doc links', 'doc_links')


PI_TAG_ADDRESSED = ProgressItem(
    'TAG review issues addressed', 'tag_review_status'
)

PI_FIREFOX_VIEWS = ProgressItem(
    'Firefox views',
    'ff_views',
    'Gecko (Firefox) signal is recorded and not blank',
    (
        'Valid values: Positive, Neutral, Negative, No signal. Link to '
        'standards-positions issue or intent thread. If N/A, a justification '
        'must be present (e.g. Chrome-specific, no cross-browser relevance).'
    ),
)

PI_SAFARI_VIEWS = ProgressItem(
    'Safari views',
    'safari_views',
    'WebKit (Safari) signal is recorded and not blank',
    (
        'Valid values: Positive, Neutral, Negative, No signal. Link to '
        'standards-positions issue or intent thread. If N/A, a justification '
        'must be present (e.g. Chrome-specific, no cross-browser relevance).'
    ),
)

PI_INTEROP_RISKS = ProgressItem(
    'Interop risks',
    'interop_compat_risks',
    (
        'Interoperability & compatibility risks field is filled in or N/A with '
        'reason provided'
    ),
    'Should reference caniuse signals, or web compat team analysis.',
)

PI_WEB_DEV_VIEWS = ProgressItem(
    'Web developer views',
    'web_dev_views',
    'Web developer views are documented or N/A',
    (
        'Evidence of developer interest: GitHub issues, surveys, origin trial '
        'feedback reports.'
    ),
)

PI_DESKTOP_MILESTONE = ProgressItem(
    'Updated desktop milestone',
    'shipped_milestone',
    (
        'Desktop Chrome milestone is set to a concrete future version '
        'number (not 0 or TBD)'
    ),
    (
        'Verify the milestone is plausible against the current Chrome '
        'release schedule.'
    ),
)

PI_ANDROID_MILESTONE = ProgressItem(
    'Updated android milestone',
    'shipped_android_milestone',
    'Android milestone is set.  Deviation from desktop is justified.',
    'Should match the desktop unless there is an explicit reason documented.',
)

PI_WEBVIEW_MILESTONE = ProgressItem(
    'Updated webview milestone',
    'shipped_webview_milestone',
    'Webview milestone is set, or blank with reason provided.',
    'Blank without justification needs follow-up.',
)

PI_FINCH_FEATURE_OR_JUSTIFY = ProgressItem(
    'Finch feature name or non-finch justification', 'finch_name'
)

PI_CODE_REMOVED = ProgressItem('Code removed')

PI_ROLLOUT_IMPACT = ProgressItem('Rollout impact', 'rollout_impact')
PI_ROLLOUT_MILESTONE = ProgressItem('Rollout milestone', 'rollout_milestone')
PI_ROLLOUT_PLATFORMS = ProgressItem('Rollout platforms', 'rollout_platforms')
PI_ROLLOUT_DETAILS = ProgressItem('Rollout details', 'rollout_details')
PI_ROLLOUT_STAGE_PLAN = ProgressItem('Rollout stage plan', 'rollout_stage_plan')
PI_ENTERPRISE_POLICIES = ProgressItem(
    'Enterprise policies', 'enterprise_policies'
)  # noqa: E501


PI_GROUP_METADATA: list[ProgressItem] = [
    PI_FEATURE_NAME,
    PI_SUMMARY,
    PI_CATEGORY,
    PI_FEATURE_TYPE,
    PI_OWNER_EMAILS,
    PI_BLINK_COMPONENTS,
    PI_WEB_FEATURE,
    PI_SUMMARY_POLICY,
    PI_TRACKING_BUG,
]
PI_GROUP_STANDARDS_PSA: list[ProgressItem] = [
    PI_SPEC_LINK,
    PI_SPEC_MATURITY,
    PI_EXPLAINER,
]
PI_GROUP_STANDARDS: list[ProgressItem] = PI_GROUP_STANDARDS_PSA + [
    PI_TAG_REQUESTED,
]
PI_GROUP_MILESTONES: list[ProgressItem] = [
    PI_DESKTOP_MILESTONE,
    PI_ANDROID_MILESTONE,
    PI_WEBVIEW_MILESTONE,
]
PI_GROUP_INTEROP: list[ProgressItem] = [
    PI_FIREFOX_VIEWS,
    PI_SAFARI_VIEWS,
    PI_INTEROP_RISKS,
    PI_WEB_DEV_VIEWS,
]
PI_GROUP_DOCS: list[ProgressItem] = [
    PI_SAMPLES,
]
DQ_CHECKLIST_BLINK = (
    PI_GROUP_METADATA
    + PI_GROUP_STANDARDS
    + PI_GROUP_MILESTONES
    + PI_GROUP_INTEROP
    + PI_GROUP_DOCS
)
DQ_CHECKLIST_FAST = (
    PI_GROUP_METADATA
    + PI_GROUP_STANDARDS
    + PI_GROUP_MILESTONES
    + PI_GROUP_INTEROP
    + PI_GROUP_DOCS
)
DQ_CHECKLIST_PSA = (
    PI_GROUP_METADATA
    + PI_GROUP_STANDARDS_PSA
    + PI_GROUP_MILESTONES
    + PI_GROUP_INTEROP
    + PI_GROUP_DOCS
)


# This is a stage that can be inserted in the stages of any non-enterprise
# features that are marked as breaking changes.
FEATURE_ROLLOUT_STAGE = ProcessStage(
    'Rollout step',
    '',
    [],
    [],
    [],
    core_enums.INTENT_SHIP,
    core_enums.INTENT_ROLLOUT,
    stage_type=core_enums.STAGE_ENT_ROLLOUT,
)


BLINK_PROCESS_STAGES = [
    ProcessStage(
        'Start incubating',
        'Create an initial WebStatus feature entry and kick off standards '
        'incubation (WICG) to share ideas.',
        PI_GROUP_METADATA
        + [
            PI_MOTIVATION,
            PI_INITIAL_PUBLIC_PROPOSAL,
            PI_EXPLAINER,
        ],
        [],
        [],
        core_enums.INTENT_NONE,
        core_enums.INTENT_INCUBATE,
        stage_type=core_enums.STAGE_BLINK_INCUBATE,
    ),
    ProcessStage(
        'Start prototyping',
        'Share an explainer doc and API. '
        'Start prototyping code in a public repo.',
        [
            PI_SPEC_LINK,
            PI_SPEC_MENTOR,
            PI_SPEC_MATURITY,
            PI_DRAFT_API_SPEC,
        ],
        [
            Action(
                'Draft Intent to Prototype email',
                INTENT_EMAIL_URL,
                [
                    PI_TRACKING_BUG.name,
                    PI_INITIAL_PUBLIC_PROPOSAL.name,
                    PI_MOTIVATION.name,
                    PI_EXPLAINER.name,
                ],
                [core_enums.GATE_API_PROTOTYPE],
            )
        ],
        [approval_defs.PrototypeApproval],
        core_enums.INTENT_INCUBATE,
        core_enums.INTENT_IMPLEMENT,
        stage_type=core_enums.STAGE_BLINK_PROTOTYPE,
    ),
    ProcessStage(
        'Dev trials and iterate on design',
        'Publicize availability for developers to try. '
        'Provide sample code. '
        'Request feedback from browser vendors.',
        [
            PI_SAMPLES,
            PI_DRAFT_API_OVERVIEW,
            PI_SEC_REVIEW,
            PI_PRI_REVIEW,
            PI_EXTERNAL_REVIEWS,
            PI_FIREFOX_VIEWS,
            PI_SAFARI_VIEWS,
            PI_INTEROP_RISKS,
            PI_WEB_DEV_VIEWS,
            PI_FINCH_FEATURE_OR_JUSTIFY,
        ],
        [
            Action(
                'Draft Ready for Developer Testing email',
                INTENT_EMAIL_URL_NO_APPROVALS,  # noqa: E501
                [
                    PI_TRACKING_BUG.name,
                    PI_INITIAL_PUBLIC_PROPOSAL.name,
                    PI_MOTIVATION.name,
                    PI_EXPLAINER.name,
                    PI_SPEC_LINK.name,
                ],
                [],
            )
        ],
        [],
        core_enums.INTENT_IMPLEMENT,
        core_enums.INTENT_EXPERIMENT,
        stage_type=core_enums.STAGE_BLINK_DEV_TRIAL,
    ),
    ProcessStage(
        'Evaluate readiness to ship',
        'Work through a TAG review and gather vendor signals.',
        [
            PI_TAG_REQUESTED,
        ],
        [],
        [],
        core_enums.INTENT_EXPERIMENT,
        core_enums.INTENT_IMPLEMENT_SHIP,
        stage_type=core_enums.STAGE_BLINK_EVAL_READINESS,
    ),
    ProcessStage(
        'Origin Trial',
        '(Optional) Set up and run an origin trial. '
        'Act on feedback from partners and web developers.',
        [],
        [
            Action(
                'Draft Intent to Experiment email',
                INTENT_EMAIL_URL,
                [
                    PI_TRACKING_BUG.name,
                    PI_INITIAL_PUBLIC_PROPOSAL.name,
                    PI_MOTIVATION.name,
                    PI_EXPLAINER.name,
                    PI_SPEC_LINK.name,
                ],
                [core_enums.GATE_API_ORIGIN_TRIAL],
            )
        ],
        [approval_defs.ExperimentApproval],
        core_enums.INTENT_IMPLEMENT_SHIP,
        core_enums.INTENT_ORIGIN_TRIAL,
        stage_type=core_enums.STAGE_BLINK_ORIGIN_TRIAL,
    ),
    ProcessStage(
        'Extend origin trial',
        '(Optional) Extend an existing origin trial.',
        [],
        [
            Action(
                'Draft Intent to Extend Experiment email',
                INTENT_EMAIL_URL,
                [],
                [core_enums.GATE_API_EXTEND_ORIGIN_TRIAL],
            )
        ],
        [approval_defs.ExtendExperimentApproval],
        core_enums.INTENT_ORIGIN_TRIAL,
        core_enums.INTENT_EXTEND_ORIGIN_TRIAL,
        stage_type=core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
    ),
    ProcessStage(
        'Prepare to ship',
        'Lock in shipping milestone. Finalize docs and announcements. '
        'Further standardization.',
        PI_GROUP_METADATA
        + [
            PI_TAG_ADDRESSED,
            PI_DESKTOP_MILESTONE,
            PI_ANDROID_MILESTONE,
            PI_WEBVIEW_MILESTONE,
        ],
        [
            Action(
                'Review data quality',
                INTENT_EMAIL_URL,  # TODO(jrobbins) checklist URL
                [pi.name for pi in DQ_CHECKLIST_BLINK],
                [core_enums.GATE_DQ_SHIP],
            ),
            Action(
                'Draft Intent to Ship email',
                INTENT_EMAIL_URL,
                [
                    PI_INITIAL_PUBLIC_PROPOSAL.name,
                    PI_MOTIVATION.name,
                    PI_EXPLAINER.name,
                    PI_SPEC_LINK.name,
                    PI_WEB_FEATURE.name,
                    PI_TRACKING_BUG.name,
                    PI_FINCH_FEATURE_OR_JUSTIFY.name,
                    PI_FIREFOX_VIEWS.name,
                    PI_SAFARI_VIEWS.name,
                    PI_INTEROP_RISKS.name,
                    PI_WEB_DEV_VIEWS.name,
                    PI_TAG_ADDRESSED.name,
                    PI_DESKTOP_MILESTONE.name,
                ],
                [core_enums.GATE_API_SHIP],
            ),
        ],
        [approval_defs.ShipApproval],
        core_enums.INTENT_IMPLEMENT_SHIP,
        core_enums.INTENT_SHIP,
        stage_type=core_enums.STAGE_BLINK_SHIPPING,
    ),
    ProcessStage(
        'Ship',
        'Update milestones and other information when the feature '
        'actually ships.',
        [],
        [],
        [],
        core_enums.INTENT_SHIP,
        core_enums.INTENT_SHIPPED,
        stage_type=None,
    ),
    FEATURE_ROLLOUT_STAGE,
]


BLINK_LAUNCH_PROCESS = Process(
    'New feature incubation',
    'Description of blink launch process',  # Not used yet.
    'When to use it',  # Not used yet.
    BLINK_PROCESS_STAGES,
)


BLINK_FAST_TRACK_STAGES = [
    ProcessStage(
        'Start prototyping',
        'Write up use cases and scenarios, start coding as a '
        'runtime enabled feature.',
        PI_GROUP_METADATA
        + [
            PI_SPEC_LINK,
            PI_EXPLAINER,
            PI_SPEC_MATURITY,
            PI_TAG_REQUESTED,
        ],
        [
            Action(
                'Draft Intent to Prototype email',
                INTENT_EMAIL_URL,
                [PI_SPEC_LINK.name],
                [core_enums.GATE_API_PROTOTYPE],
            )
        ],
        [approval_defs.PrototypeApproval],
        core_enums.INTENT_NONE,
        core_enums.INTENT_IMPLEMENT,
        stage_type=core_enums.STAGE_FAST_PROTOTYPE,
    ),
    ProcessStage(
        'Dev trials and iterate on implementation',
        'Publicize availability for developers to try. '
        'Provide sample code. '
        'Act on feedback from partners and web developers.',
        [
            PI_SAMPLES,
            PI_DRAFT_API_OVERVIEW,
            PI_FINCH_FEATURE_OR_JUSTIFY,
            PI_FIREFOX_VIEWS,
            PI_SAFARI_VIEWS,
            PI_INTEROP_RISKS,
            PI_WEB_DEV_VIEWS,
        ],
        [
            Action(
                'Draft Ready for Developer Testing email',
                INTENT_EMAIL_URL_NO_APPROVALS,  # noqa: E501
                [
                    PI_TRACKING_BUG.name,
                    PI_SPEC_LINK.name,
                ],
                [],
            )
        ],
        [],
        core_enums.INTENT_IMPLEMENT,
        core_enums.INTENT_EXPERIMENT,
        stage_type=core_enums.STAGE_FAST_DEV_TRIAL,
    ),
    ProcessStage(
        'Origin Trial',
        '(Optional) Set up and run an origin trial. '
        'Act on feedback from partners and web developers.',
        [],
        [
            Action(
                'Draft Intent to Experiment email',
                INTENT_EMAIL_URL,
                [
                    PI_TRACKING_BUG.name,
                    PI_SPEC_LINK.name,
                ],
                [core_enums.GATE_API_ORIGIN_TRIAL],
            )
        ],
        [approval_defs.ExperimentApproval],
        core_enums.INTENT_EXPERIMENT,
        core_enums.INTENT_ORIGIN_TRIAL,
        stage_type=core_enums.STAGE_FAST_ORIGIN_TRIAL,
    ),
    ProcessStage(
        'Extend origin trial',
        '(Optional) Extend an existing origin trial.',
        [],
        [
            Action(
                'Draft Intent to Extend Experiment email',
                INTENT_EMAIL_URL,
                [],
                [core_enums.GATE_API_EXTEND_ORIGIN_TRIAL],
            )
        ],
        [approval_defs.ExtendExperimentApproval],
        core_enums.INTENT_ORIGIN_TRIAL,
        core_enums.INTENT_EXTEND_ORIGIN_TRIAL,
        stage_type=core_enums.STAGE_FAST_EXTEND_ORIGIN_TRIAL,
    ),
    ProcessStage(
        'Prepare to ship',
        'Lock in shipping milestone. Finalize docs and announcements. '
        'Further standardization.',
        PI_GROUP_METADATA
        + [
            PI_DESKTOP_MILESTONE,
            PI_ANDROID_MILESTONE,
            PI_WEBVIEW_MILESTONE,
        ],
        [
            Action(
                'Review data quality',
                INTENT_EMAIL_URL,  # TODO(jrobbins) checklist URL
                [pi.name for pi in DQ_CHECKLIST_FAST],
                [core_enums.GATE_DQ_SHIP],
            ),
            Action(
                'Draft Intent to Ship email',
                INTENT_EMAIL_URL,
                [
                    PI_TRACKING_BUG.name,
                    PI_SPEC_LINK.name,
                    PI_WEB_FEATURE.name,
                    PI_FINCH_FEATURE_OR_JUSTIFY.name,
                    PI_DESKTOP_MILESTONE.name,
                ],
                [core_enums.GATE_API_SHIP],
            ),
        ],
        [approval_defs.ShipApproval],
        core_enums.INTENT_EXPERIMENT,
        core_enums.INTENT_SHIP,
        stage_type=core_enums.STAGE_FAST_SHIPPING,
    ),
    ProcessStage(
        'Ship',
        'Update milestones and other information when the feature '
        'actually ships.',
        [],
        [],
        [],
        core_enums.INTENT_SHIP,
        core_enums.INTENT_SHIPPED,
        stage_type=None,
    ),
    FEATURE_ROLLOUT_STAGE,
]


BLINK_FAST_TRACK_PROCESS = Process(
    'Existing feature implementation',
    'Description of blink fast track process',  # Not used yet.
    'When to use it',  # Not used yet.
    BLINK_FAST_TRACK_STAGES,
)


PSA_ONLY_STAGES = [
    ProcessStage(
        'Implement',
        'Check code into Chromium under a flag.',
        PI_GROUP_METADATA
        + [
            PI_SPEC_LINK,
            PI_EXPLAINER,
            PI_SPEC_MATURITY,
        ],
        [],
        [],
        core_enums.INTENT_NONE,
        core_enums.INTENT_IMPLEMENT,
        stage_type=core_enums.STAGE_PSA_IMPLEMENT,
    ),
    ProcessStage(
        'Dev trials and iterate on implementation',
        '(Optional) Publicize availability for developers to try. '
        'Act on feedback from partners and web developers.',
        [
            PI_FINCH_FEATURE_OR_JUSTIFY,
            PI_FIREFOX_VIEWS,
            PI_SAFARI_VIEWS,
            PI_INTEROP_RISKS,
            PI_WEB_DEV_VIEWS,
            PI_SAMPLES,
        ],
        [
            Action(
                'Draft Ready for Developer Testing email',
                INTENT_EMAIL_URL_NO_APPROVALS,  # noqa: E501
                [
                    PI_TRACKING_BUG.name,
                    PI_SPEC_LINK.name,
                ],
                [],
            )
        ],
        [],
        core_enums.INTENT_IMPLEMENT,
        core_enums.INTENT_EXPERIMENT,
        stage_type=core_enums.STAGE_PSA_DEV_TRIAL,
    ),
    ProcessStage(
        'Prepare to ship',
        'Lock in shipping milestone.',
        PI_GROUP_METADATA
        + [
            PI_DESKTOP_MILESTONE,
            PI_ANDROID_MILESTONE,
            PI_WEBVIEW_MILESTONE,
        ],
        [
            Action(
                'Review data quality',
                INTENT_EMAIL_URL,  # TODO(jrobbins) checklist URL
                [pi.name for pi in DQ_CHECKLIST_PSA],
                [core_enums.GATE_DQ_SHIP],
            ),
            Action(
                'Draft Web-Facing Change PSA email',
                INTENT_EMAIL_URL_NO_APPROVALS,  # noqa: E501
                [
                    PI_TRACKING_BUG.name,
                    PI_SPEC_LINK.name,
                    PI_FINCH_FEATURE_OR_JUSTIFY.name,
                    PI_DESKTOP_MILESTONE.name,
                ],
                [],
            ),
        ],
        [approval_defs.ShipApproval],
        core_enums.INTENT_EXPERIMENT,
        core_enums.INTENT_SHIP,
        stage_type=core_enums.STAGE_PSA_SHIPPING,
    ),
    ProcessStage(
        'Ship',
        'Update milestones and other information when the feature '
        'actually ships.',
        [],
        [],
        [],
        core_enums.INTENT_SHIP,
        core_enums.INTENT_SHIPPED,
        stage_type=None,
    ),
    FEATURE_ROLLOUT_STAGE,
]


PSA_ONLY_PROCESS = Process(
    'Web developer facing change to existing code',
    'Description of PSA process',  # Not used yet.
    'When to use it',  # Not used yet.
    PSA_ONLY_STAGES,
)


DEPRECATION_STAGES = [
    ProcessStage(
        'Write up deprecation plan',
        'Create an initial WebStatus feature entry to deprecate '
        'an existing feature, including motivation and impact. '
        'Then, get approval for your deprecation plans.',
        PI_GROUP_METADATA
        + [
            PI_MOTIVATION,
            PI_SPEC_LINK,
            PI_EXPLAINER,
        ],
        [
            Action(
                'Review data quality',
                INTENT_EMAIL_URL,  # TODO(jrobbins): checklist page URL
                [pi.name for pi in PI_GROUP_METADATA],  # TODO(jrobbins): more
                [core_enums.GATE_DQ_PLAN],
            ),
            Action(
                'Draft Intent to Deprecate and Remove email',
                INTENT_EMAIL_URL,
                [
                    PI_TRACKING_BUG.name,
                    PI_MOTIVATION.name,
                    PI_TRACKING_BUG.name,
                ],
                [core_enums.GATE_API_PLAN],
            ),
        ],
        [approval_defs.PrototypeApproval],
        core_enums.INTENT_NONE,
        core_enums.INTENT_IMPLEMENT,
        stage_type=core_enums.STAGE_DEP_PLAN,
    ),
    # TODO(cwilso): Work out additional steps for flag defaulting to disabled.
    ProcessStage(
        'Dev trial of deprecation',
        'Publicize deprecation and address risks. ',
        [
            PI_FIREFOX_VIEWS,
            PI_SAFARI_VIEWS,
            PI_INTEROP_RISKS,
            PI_WEB_DEV_VIEWS,
            PI_FINCH_FEATURE_OR_JUSTIFY,
        ],
        [
            Action(
                'Draft Ready for Developer Testing email',
                INTENT_EMAIL_URL_NO_APPROVALS,  # noqa: E501
                [
                    PI_TRACKING_BUG.name,
                    PI_MOTIVATION.name,
                    PI_FIREFOX_VIEWS.name,
                    PI_SAFARI_VIEWS.name,
                    PI_INTEROP_RISKS.name,
                    PI_WEB_DEV_VIEWS.name,
                ],
                [],
            )
        ],
        [],
        core_enums.INTENT_IMPLEMENT,
        core_enums.INTENT_EXPERIMENT,
        stage_type=core_enums.STAGE_DEP_DEV_TRIAL,
    ),
    ProcessStage(
        'Prepare for Deprecation Trial',
        '(Optional) Set up and run a deprecation trial. ',
        [],
        [
            Action(
                'Draft Request for Deprecation Trial email',
                INTENT_EMAIL_URL,
                [
                    PI_TRACKING_BUG.name,
                    PI_MOTIVATION.name,
                    PI_FIREFOX_VIEWS.name,
                    PI_SAFARI_VIEWS.name,
                    PI_INTEROP_RISKS.name,
                    PI_WEB_DEV_VIEWS.name,
                ],
                [core_enums.GATE_API_ORIGIN_TRIAL],
            )
        ],
        [approval_defs.ExperimentApproval],
        core_enums.INTENT_EXPERIMENT,
        core_enums.INTENT_ORIGIN_TRIAL,
        stage_type=core_enums.STAGE_DEP_DEPRECATION_TRIAL,
    ),
    ProcessStage(
        'Extend deprecation trial',
        '(Optional) Extend an existing deprecation trial.',
        [],
        [
            Action(
                'Draft Intent to Extend Deprecation Trial email',
                INTENT_EMAIL_URL,
                [],
                [core_enums.GATE_API_EXTEND_ORIGIN_TRIAL],
            )
        ],
        [approval_defs.ExtendExperimentApproval],
        core_enums.INTENT_ORIGIN_TRIAL,
        core_enums.INTENT_EXTEND_ORIGIN_TRIAL,
        stage_type=core_enums.STAGE_DEP_EXTEND_DEPRECATION_TRIAL,
    ),
    ProcessStage(
        'Prepare to ship',
        'Lock in shipping milestone. '
        'Finalize docs and announcements before disabling feature by default. '
        'If there were changes since your plan approvals, get approvals again.',
        [
            PI_DESKTOP_MILESTONE,
        ],
        [
            # There is no I2S for deprecations because it all happens during planning.
            # And thre is no API Owner gate on this stage.
        ],
        [approval_defs.ShipApproval],
        core_enums.INTENT_EXPERIMENT,
        core_enums.INTENT_SHIP,
        stage_type=core_enums.STAGE_DEP_SHIPPING,
    ),
    ProcessStage(
        'Remove code',
        'Once the feature is no longer available, remove the code.',
        [
            PI_CODE_REMOVED,
        ],
        [
            Action(
                'Generate an Intent to Extend Deprecation Trial',
                INTENT_EMAIL_URL,
                [
                    PI_TRACKING_BUG.name,
                    PI_MOTIVATION.name,
                    PI_FIREFOX_VIEWS.name,
                    PI_SAFARI_VIEWS.name,
                    PI_INTEROP_RISKS.name,
                    PI_WEB_DEV_VIEWS.name,
                    PI_DESKTOP_MILESTONE.name,
                ],
                [],
            ),
        ],
        [],
        core_enums.INTENT_SHIP,
        core_enums.INTENT_REMOVED,
        stage_type=core_enums.STAGE_DEP_REMOVE_CODE,
    ),
    FEATURE_ROLLOUT_STAGE,
]

# Thise are the stages for a feature that has the enterprise feature type.
ENTERPRISE_STAGES = [
    ProcessStage(
        'Rollout step',
        '',
        [],
        [],
        [],
        core_enums.INTENT_NONE,
        core_enums.INTENT_ROLLOUT,
        stage_type=core_enums.STAGE_ENT_ROLLOUT,
    ),
]


DEPRECATION_PROCESS = Process(
    'Feature deprecation',
    'Description of deprecation process',  # Not used yet.
    'When to use it',  # Not used yet.
    DEPRECATION_STAGES,
)


ENTERPRISE_PROCESS = Process(
    'New Feature or removal affecting enterprises',
    'Description of enterprise process',  # Not used yet.
    'When to use it',  # Not used yet.
    ENTERPRISE_STAGES,
)


ALL_PROCESSES = {
    core_enums.FEATURE_TYPE_INCUBATE_ID: BLINK_LAUNCH_PROCESS,
    core_enums.FEATURE_TYPE_EXISTING_ID: BLINK_FAST_TRACK_PROCESS,
    core_enums.FEATURE_TYPE_CODE_CHANGE_ID: PSA_ONLY_PROCESS,
    core_enums.FEATURE_TYPE_DEPRECATION_ID: DEPRECATION_PROCESS,
    core_enums.FEATURE_TYPE_ENTERPRISE_ID: ENTERPRISE_PROCESS,
}


def initial_tag_review_status(feature_type):
    """Incubating a new feature requires a TAG review, other types do not."""
    if feature_type == core_enums.FEATURE_TYPE_INCUBATE_ID:
        return core_enums.REVIEW_PENDING
    return core_enums.REVIEW_NA


def write_gates_and_stages_for_feature(
    feature_id: int, feature_type: int
) -> None:
    """Write each Stage and Gate entity for the given feature."""
    # Obtain a list of stages and gates for the given feature type.
    stages_gates = core_enums.STAGES_AND_GATES_BY_FEATURE_TYPE[feature_type]

    for stage_type, gate_types in stages_gates:
        # Don't create a trial extension stage pre-emptively.
        if (
            stage_type
            == core_enums.STAGE_TYPES_EXTEND_ORIGIN_TRIAL[feature_type]
        ):
            continue

        stage = Stage(feature_id=feature_id, stage_type=stage_type)
        stage.put()
        # Stages can have zero or more gates.
        for gate_type in gate_types:
            gate = Gate(
                feature_id=feature_id,
                stage_id=stage.key.integer_id(),
                gate_type=gate_type,
                state=Gate.PREPARING,
            )
            gate.put()
