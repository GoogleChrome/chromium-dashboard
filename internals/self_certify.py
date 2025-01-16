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

from google.cloud import ndb  # type: ignore

from internals.core_enums import GATE_SECURITY_ORIGIN_TRIAL, GATE_SECURITY_SHIP
from internals.review_models import Gate, SurveyAnswers


def is_security_eligible(answers: SurveyAnswers) -> bool:
  """Return True if the answers allow self-certify for the Security gate."""
  return (
      answers.is_language_polyfill or
      answers.is_api_polyfill or
      answers.is_same_origin_css)


def is_eligible(gate: Gate) -> bool:
  """Return True if the feature owner can self-certify."""
  answers = gate.survey_answers
  if answers is None:
    return False

  if gate.gate_type in [GATE_SECURITY_ORIGIN_TRIAL, GATE_SECURITY_SHIP]:
    return is_security_eligible(answers)

  return False
