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

import testing_config  # isort: split

from chromestatus_openapi.models import SurveyAnswers as OASurveyAnswers

from internals import self_certify
from internals.core_enums import *
from internals.review_models import Gate, SurveyAnswers


class SelfCertifyFunctionTest(testing_config.CustomTestCase):

  def test_update_survey_answers__no_existing_answers(self):
    """If a gate has no existing answers, we create a blank set."""
    gate = Gate()
    self.assertIsNone(gate.survey_answers)

    self_certify.update_survey_answers(
        gate, OASurveyAnswers(
            is_language_polyfill=True, is_api_polyfill=None,
            is_same_origin_css=None, launch_or_contact=None))

    self.assertIsNotNone(gate.survey_answers)
    self.assertTrue(gate.survey_answers.is_language_polyfill)
    self.assertFalse(gate.survey_answers.is_api_polyfill)
    self.assertFalse(gate.survey_answers.is_same_origin_css)
    self.assertIsNone(gate.survey_answers.launch_or_contact)

  def test_update_survey_answers__has_existing_answers(self):
    """If a gate has existing answers, we just update it."""
    gate = Gate(survey_answers=SurveyAnswers(is_language_polyfill=True))

    self_certify.update_survey_answers(
        gate, OASurveyAnswers(
            is_language_polyfill=None, is_api_polyfill=False,
            is_same_origin_css=None, launch_or_contact=None))

    self.assertIsNotNone(gate.survey_answers)
    self.assertTrue(gate.survey_answers.is_language_polyfill)
    self.assertFalse(gate.survey_answers.is_api_polyfill)
    self.assertFalse(gate.survey_answers.is_same_origin_css)
    self.assertIsNone(gate.survey_answers.launch_or_contact)

  def test_is_security_eligible(self):
    """Security is eligible if any of the booleans is True."""
    self.assertFalse(self_certify.is_security_eligible(
        SurveyAnswers()))
    self.assertFalse(self_certify.is_security_eligible(
        SurveyAnswers(is_language_polyfill=False)))
    self.assertFalse(self_certify.is_security_eligible(
        SurveyAnswers(is_api_polyfill=False)))
    self.assertFalse(self_certify.is_security_eligible(
        SurveyAnswers(is_same_origin_css=False)))
    self.assertFalse(self_certify.is_security_eligible(
        SurveyAnswers(
            is_language_polyfill=False,
            is_api_polyfill=False,
            is_same_origin_css=False)))

    self.assertTrue(self_certify.is_security_eligible(
        SurveyAnswers(is_language_polyfill=True)))
    self.assertTrue(self_certify.is_security_eligible(
        SurveyAnswers(is_api_polyfill=True)))
    self.assertTrue(self_certify.is_security_eligible(
        SurveyAnswers(is_same_origin_css=True)))
    self.assertTrue(self_certify.is_security_eligible(
        SurveyAnswers(
            is_language_polyfill=False, is_api_polyfill=False,
            is_same_origin_css=True)))

  def test_is_eligible(self):
    """Security gates are the only eligible type."""
    self.assertTrue(self_certify.is_eligible(
        Gate(
            gate_type=GATE_SECURITY_ORIGIN_TRIAL,
            survey_answers=SurveyAnswers(is_language_polyfill=True))))

    self.assertFalse(self_certify.is_eligible(
        Gate(
            gate_type=GATE_SECURITY_ORIGIN_TRIAL,
            survey_answers=SurveyAnswers())))

    self.assertFalse(self_certify.is_eligible(
        Gate(
            gate_type=GATE_ENTERPRISE_SHIP,
            survey_answers=SurveyAnswers(is_language_polyfill=True))))
