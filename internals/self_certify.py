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

"""Provides logic for checking if a feature owner can self-certify a review gate."""

from chromestatus_openapi.models import SurveyAnswers as OASurveyAnswers

from internals import core_enums
from internals.review_models import Gate, SurveyAnswers

CERTIFIABLE_GATE_TYPES = [
    core_enums.GATE_PRIVACY_ORIGIN_TRIAL,
    core_enums.GATE_PRIVACY_SHIP,
    core_enums.GATE_TESTING_PLAN,
    core_enums.GATE_TESTING_SHIP,
    core_enums.GATE_ADOPTION_PLAN,
    core_enums.GATE_ADOPTION_SHIP,
]


def update_survey_answers(gate: Gate, new_answers: OASurveyAnswers):
    """Modify the given SurveyAnswers with user-requested changes."""
    if gate.survey_answers is None:
        gate.survey_answers = SurveyAnswers()
    answers = gate.survey_answers

    if new_answers.is_language_polyfill is not None:
        answers.is_language_polyfill = new_answers.is_language_polyfill
    if new_answers.is_api_polyfill is not None:
        answers.is_api_polyfill = new_answers.is_api_polyfill
    if new_answers.is_same_origin_css is not None:
        answers.is_same_origin_css = new_answers.is_same_origin_css

    if new_answers.covers_existence is not None:
        answers.covers_existence = new_answers.covers_existence
    if new_answers.covers_common_cases is not None:
        answers.covers_common_cases = new_answers.covers_common_cases
    if new_answers.covers_errors is not None:
        answers.covers_errors = new_answers.covers_errors
    if new_answers.covers_invalidation is not None:
        answers.covers_invalidation = new_answers.covers_invalidation
    if new_answers.covers_integration is not None:
        answers.covers_integration = new_answers.covers_integration

    if new_answers.adoption_fields_up_to_date is not None:
        answers.adoption_fields_up_to_date = (
            new_answers.adoption_fields_up_to_date
        )
    if new_answers.adoption_style_aligned is not None:
        answers.adoption_style_aligned = new_answers.adoption_style_aligned
    if new_answers.adoption_lead_time is not None:
        answers.adoption_lead_time = new_answers.adoption_lead_time
    if new_answers.adoption_mdn_drafted is not None:
        answers.adoption_mdn_drafted = new_answers.adoption_mdn_drafted

    if new_answers.launch_or_contact is not None:
        answers.launch_or_contact = new_answers.launch_or_contact
    if new_answers.explanation is not None:
        answers.explanation = new_answers.explanation


def is_privacy_eligible(answers: SurveyAnswers) -> bool:
    """Return True if the answers allow self-certify for the Privacy gate."""
    return answers.explanation and (
        answers.is_language_polyfill
        or answers.is_api_polyfill
        or answers.is_same_origin_css
    )


def is_testing_eligible(answers: SurveyAnswers) -> bool:
    """Return True if the answers allow self-certify for the Testing gate."""
    return (
        answers.covers_existence
        and answers.covers_common_cases
        and answers.covers_errors
        and answers.covers_invalidation
        and answers.covers_integration
    )


def is_adoption_eligible(answers: SurveyAnswers) -> bool:
    """Return True if the answers allow self-certify for the Adoption gate."""
    return (
        answers.adoption_fields_up_to_date
        and answers.adoption_style_aligned
        and answers.adoption_lead_time
        and answers.adoption_mdn_drafted
    )


def is_eligible(gate: Gate) -> bool:
    """Return True if the feature owner can self-certify the gate now."""
    answers = gate.survey_answers
    if answers is None:
        return False

    if gate.gate_type in [
        core_enums.GATE_PRIVACY_ORIGIN_TRIAL,
        core_enums.GATE_PRIVACY_SHIP,
    ]:
        return is_privacy_eligible(answers)
    if gate.gate_type in [
        core_enums.GATE_TESTING_PLAN,
        core_enums.GATE_TESTING_SHIP,
    ]:
        return is_testing_eligible(answers)
    if gate.gate_type in [
        core_enums.GATE_ADOPTION_PLAN,
        core_enums.GATE_ADOPTION_SHIP,
    ]:
        return is_adoption_eligible(answers)

    return False


def is_possible(gate: Gate) -> bool:
    """Return True if the feature owner can ever self-certify this gate."""
    return gate.gate_type in CERTIFIABLE_GATE_TYPES
