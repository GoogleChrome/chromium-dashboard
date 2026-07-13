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


"""Unit tests for the core_enums module.

Tests the mapping and conversion functions between enum integers
and their corresponding human-readable or normalized string representations.
"""

import testing_config  # Must be imported before the module under test.
from internals import core_enums


class EnumsFunctionsTest(testing_config.CustomTestCase):
    """Tests for enum functions."""

    def test_convert_enum_int_to_string__not_an_enum(self):
        """If the property is not an enum, just use the property value."""
        actual = core_enums.convert_enum_int_to_string('name', 'not an int')
        self.assertEqual('not an int', actual)

        actual = core_enums.convert_enum_int_to_string(
            'unknown property', 'something'
        )
        self.assertEqual('something', actual)

    def test_convert_enum_int_to_string__not_an_int(self):
        """We don't crash or convert when given non-numeric values."""
        actual = core_enums.convert_enum_int_to_string(
            'impl_status_chrome', {'something': 'non-numeric'}
        )
        self.assertEqual({'something': 'non-numeric'}, actual)

    def test_convert_enum_int_to_string__enum_found(self):
        """We use the human-reable string if it is defined."""
        actual = core_enums.convert_enum_int_to_string(
            'impl_status_chrome', core_enums.NO_ACTIVE_DEV
        )
        self.assertEqual(
            core_enums.IMPLEMENTATION_STATUS[core_enums.NO_ACTIVE_DEV], actual
        )

    def test_convert_enum_int_to_string__enum_not_found(self):
        """If we somehow don't have an emum string, use the ordinal."""
        actual = core_enums.convert_enum_int_to_string('impl_status_chrome', 99)
        self.assertEqual(99, actual)

    def test_normalize_enum_string(self):
        """We can convert enum names to snake_case."""
        self.assertEqual(
            'positive', core_enums.normalize_enum_string('Positive')
        )
        self.assertEqual(
            'mixed_signals', core_enums.normalize_enum_string('Mixed signals')
        )
        self.assertEqual(
            'mixed_signals', core_enums.normalize_enum_string('Mixed_signals')
        )
        self.assertEqual(
            'mixed_signals', core_enums.normalize_enum_string('mixed_signals')
        )
        self.assertEqual(
            'mixed_signals', core_enums.normalize_enum_string('mixed-signals')
        )
        self.assertEqual(
            'in_developer_trial_behind_a_flag',
            core_enums.normalize_enum_string(
                'In developer trial (Behind a flag)'
            ),
        )
        self.assertEqual(
            'in_developer_trial_behind_a_flag',
            core_enums.normalize_enum_string(
                'In_developer_trial_(Behind_a_flag)'
            ),
        )

    def test_convert_enum_string_to_int__already_numeric(self):
        """If the value passed in is already an int, go with it."""
        actual = core_enums.convert_enum_string_to_int(
            'impl_status_chrome', str(core_enums.NO_ACTIVE_DEV)
        )
        self.assertEqual(core_enums.NO_ACTIVE_DEV, actual)

    def test_convert_enum_string_to_int__enum_found(self):
        """We use the enum representation if it is defined."""
        actual = core_enums.convert_enum_string_to_int(
            'impl_status_chrome', 'No active development'
        )
        self.assertEqual(core_enums.NO_ACTIVE_DEV, actual)

        actual = core_enums.convert_enum_string_to_int(
            'impl_status_chrome', 'No_active_development'
        )
        self.assertEqual(core_enums.NO_ACTIVE_DEV, actual)

        actual = core_enums.convert_enum_string_to_int(
            'category', 'Miscellaneous'
        )
        self.assertEqual(core_enums.MISC, actual)

    def test_convert_enum_string_to_int__not_found(self):
        """If enum representation is not defined, return -1."""
        actual = core_enums.convert_enum_string_to_int(
            'impl_status_chrome', 'abc'
        )
        self.assertEqual(-1, actual)


class AIReleaseNotesEnumsTest(testing_config.CustomTestCase):
    """Tests for AI release notes string enums and constants."""

    def test_summary_suggestion_status_members(self):
        """Verify SummarySuggestionStatus string literals and member count."""
        self.assertEqual(core_enums.SummarySuggestionStatus.UNKNOWN, 'UNKNOWN')
        self.assertEqual(
            core_enums.SummarySuggestionStatus.PROPOSED, 'PROPOSED'
        )
        self.assertEqual(core_enums.SummarySuggestionStatus.PENDING, 'PENDING')
        self.assertEqual(core_enums.SummarySuggestionStatus.APPLIED, 'APPLIED')
        self.assertEqual(
            core_enums.SummarySuggestionStatus.REJECTED, 'REJECTED'
        )
        self.assertEqual(
            core_enums.SummarySuggestionStatus.DISCARDED, 'DISCARDED'
        )
        self.assertEqual(
            core_enums.SummarySuggestionStatus.BYPASSED, 'BYPASSED'
        )
        self.assertEqual(core_enums.SummarySuggestionStatus.SKIPPED, 'SKIPPED')
        self.assertEqual(len(core_enums.SummarySuggestionStatus), 8)

    def test_progress_step_status_members(self):
        """Verify ProgressStepStatus string literals and member count."""
        self.assertEqual(core_enums.ProgressStepStatus.UNKNOWN, 'UNKNOWN')
        self.assertEqual(core_enums.ProgressStepStatus.START, 'START')
        self.assertEqual(
            core_enums.ProgressStepStatus.IN_PROGRESS, 'IN_PROGRESS'
        )
        self.assertEqual(core_enums.ProgressStepStatus.SUCCESS, 'SUCCESS')
        self.assertEqual(core_enums.ProgressStepStatus.FAILED, 'FAILED')
        self.assertEqual(core_enums.ProgressStepStatus.RETRYING, 'RETRYING')
        self.assertEqual(len(core_enums.ProgressStepStatus), 6)

    def test_progress_step_id_members(self):
        """Verify ProgressStepId string literals and member count."""
        self.assertEqual(core_enums.ProgressStepId.UNKNOWN, 'UNKNOWN')
        self.assertEqual(core_enums.ProgressStepId.START, 'START')
        self.assertEqual(core_enums.ProgressStepId.SEARCH_MDN, 'SEARCH_MDN')
        self.assertEqual(core_enums.ProgressStepId.READ_SPEC, 'READ_SPEC')
        self.assertEqual(
            core_enums.ProgressStepId.LLM_GENERATION, 'LLM_GENERATION'
        )
        self.assertEqual(core_enums.ProgressStepId.EVALUATION, 'EVALUATION')
        self.assertEqual(core_enums.ProgressStepId.SUCCESS, 'SUCCESS')
        self.assertEqual(len(core_enums.ProgressStepId), 7)

    def test_ai_summary_tool_name_members(self):
        """Verify AISummaryToolName declaration values and member count."""
        self.assertEqual(
            core_enums.AISummaryToolName.SEARCH_MDN, 'search_mdn_tool'
        )
        self.assertEqual(
            core_enums.AISummaryToolName.VERIFY_DOC_LINK, 'verify_doc_link_tool'
        )
        self.assertEqual(
            core_enums.AISummaryToolName.READ_SPEC_LINK, 'read_spec_link_tool'
        )
        self.assertEqual(len(core_enums.AISummaryToolName), 3)

    def test_baseline_status_members(self):
        """Verify BaselineStatus string values and member count."""
        self.assertEqual(core_enums.BaselineStatus.NONE, 'none')
        self.assertEqual(core_enums.BaselineStatus.LIMITED, 'limited')
        self.assertEqual(core_enums.BaselineStatus.NEWLY, 'newly')
        self.assertEqual(core_enums.BaselineStatus.WIDELY, 'widely')
        self.assertEqual(len(core_enums.BaselineStatus), 4)

    def test_string_enums_isinstance_str(self):
        """Confirm our enums inherit from str for seamless API / NDB usage."""
        self.assertIsInstance(core_enums.SummarySuggestionStatus.PROPOSED, str)
        self.assertIsInstance(core_enums.ProgressStepStatus.IN_PROGRESS, str)
        self.assertIsInstance(core_enums.ProgressStepId.LLM_GENERATION, str)
        self.assertIsInstance(core_enums.AISummaryToolName.SEARCH_MDN, str)
        self.assertIsInstance(core_enums.BaselineStatus.WIDELY, str)
