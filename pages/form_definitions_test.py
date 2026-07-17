# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

"""Unit tests for form_definitions and form_field_specs modules."""

import unittest

from pages import form_definitions, form_field_specs


class FormDefinitionsTest(unittest.TestCase):
    """Tests for form_definitions module."""

    def test_fields_exist_in_specs(self):
        """All fields referenced in FORMS_BY_STAGE_TYPE must exist in form_field_specs.ALL_FIELDS."""
        for form_def in form_definitions.FORMS_BY_STAGE_TYPE.values():
            for section in form_def['sections']:
                for field in section['fields']:
                    self.assertIn(
                        field,
                        form_field_specs.ALL_FIELDS,
                        f"Field '{field}' not found in form_field_specs.ALL_FIELDS",
                    )

    def test_fast_dev_trial_fields_has_tag_review(self):
        """FAST_DEV_TRIAL_FIELDS should have 'tag_review' in the first section."""
        fast_dev_trial = form_definitions.FAST_DEV_TRIAL_FIELDS
        flat_dev_trial = form_definitions.FLAT_DEV_TRIAL_FIELDS

        self.assertIsNot(fast_dev_trial['sections'], flat_dev_trial['sections'])
        self.assertIsNot(
            fast_dev_trial['sections'][0]['fields'],
            flat_dev_trial['sections'][0]['fields'],
        )

        self.assertIn('tag_review', fast_dev_trial['sections'][0]['fields'])
        self.assertNotIn('tag_review', flat_dev_trial['sections'][0]['fields'])


class FormFieldSpecsTest(unittest.TestCase):
    """Tests for form_field_specs module."""

    def test_all_fields_not_empty(self):
        """ALL_FIELDS should exist and contain field specifications."""
        self.assertTrue(
            len(form_field_specs.ALL_FIELDS) > 0, 'ALL_FIELDS is empty'
        )

    def test_safari_views_link_label(self):
        """Check that safari_views_link uses displayLabel value."""
        spec = form_field_specs.ALL_FIELDS.get('safari_views_link')
        self.assertIsNotNone(spec)
        self.assertEqual(spec['label'], 'WebKit views link')

    def test_shipped_milestone_label(self):
        """Check a standard field like shipped_milestone."""
        spec = form_field_specs.ALL_FIELDS.get('shipped_milestone')
        self.assertIsNotNone(spec)
        self.assertEqual(spec['type'], 'input')
        self.assertEqual(spec['label'], 'Chrome for desktop')

    def test_all_specs_referenced_in_forms(self):
        """Every field in form_field_specs.ALL_FIELDS should be referenced in FORMS_BY_STAGE_TYPE or FLAT_METADATA_FIELDS."""
        referenced_fields = set()
        for form_def in form_definitions.FORMS_BY_STAGE_TYPE.values():
            for section in form_def['sections']:
                for field in section['fields']:
                    referenced_fields.add(field)

        # Also extract fields from metadata forms
        for form_def in [
            form_definitions.FLAT_METADATA_FIELDS,
            form_definitions.FLAT_ENTERPRISE_METADATA_FIELDS,
        ]:
            for section in form_def['sections']:
                for field in section['fields']:
                    referenced_fields.add(field)

        defined_fields = set(form_field_specs.ALL_FIELDS.keys())

        self.assertEqual(
            defined_fields,
            referenced_fields,
            f'Defined fields and referenced fields do not match. Unreferenced: {sorted(list(defined_fields - referenced_fields))}, Missing specs: {sorted(list(referenced_fields - defined_fields))}',
        )


if __name__ == '__main__':
    unittest.main()
