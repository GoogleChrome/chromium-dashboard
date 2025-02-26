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

from chromestatus_openapi.models import SurveyAnswers as OASurveyAnswers

from internals.core_enums import GATE_PRIVACY_ORIGIN_TRIAL, GATE_PRIVACY_SHIP
from internals.review_models import Gate, SurveyAnswers


CERTIFIABLE_GATE_TYPES = [GATE_PRIVACY_ORIGIN_TRIAL, GATE_PRIVACY_SHIP]


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

  if new_answers.launch_or_contact is not None:
    answers.launch_or_contact = new_answers.launch_or_contact
  if new_answers.explanation is not None:
    answers.explanation = new_answers.explanation


def is_privacy_eligible(answers: SurveyAnswers) -> bool:
  """Return True if the answers allow self-certify for the Privacy gate."""
  return answers.explanation and (
      answers.is_language_polyfill or
      answers.is_api_polyfill or
      answers.is_same_origin_css)


def is_eligible(gate: Gate) -> bool:
  """Return True if the feature owner can self-certify the gate now."""
  answers = gate.survey_answers
  if answers is None:
    return False

  if gate.gate_type in [GATE_PRIVACY_ORIGIN_TRIAL, GATE_PRIVACY_SHIP]:
    return is_privacy_eligible(answers)

  return False


def is_possible(gate: Gate) -> bool:
  """Return True if the feature owner can ever self-certify this gate."""
  return gate.gate_type in CERTIFIABLE_GATE_TYPES
