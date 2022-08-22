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

import testing_config  # Must be imported first
import unittest

from unittest import mock
import html5lib

from django.core.exceptions import ValidationError
from django.template import engines

from pages import guideforms
from internals import models


TestForm = guideforms.define_form_class_using_shared_fields(
    'TestForm', ('name', 'summary', 'category'))

TEST_TEMPLATE = '''
<!DOCTYPE html>

{{form}}
'''

class ChromedashFormTest(unittest.TestCase):

  def render_form(self, feature_dict):
    form = TestForm(feature_dict)
    django_engine = engines['django']
    template = django_engine.from_string(TEST_TEMPLATE)
    rendered_html = template.render({'form': form})
    return rendered_html

  def validate_html(self, rendered_html):
    parser = html5lib.HTMLParser(strict=True)
    document = parser.parse(rendered_html)

  def test__normal(self):
    """Our forms can render some widgets with values."""
    feature_dict = {
        'name': 'this is a feature name',
        'summary': 'this is a summary',
        }
    actual = self.render_form(feature_dict)
    self.validate_html(actual)
    self.assertIn('name="name"', actual)
    self.assertIn('value="this is a feature name"', actual)
    self.assertIn('name="summary"', actual)
    self.assertIn('value="this is a summary"', actual)
    # Initial value MISC (2) is used because feature_dict has no category.
    self.assertIn('name="category" value="2"', actual)

  def test__escaping(self):
    """Our forms render properly even with tricky input."""
    feature_dict = {
        'name': 'name single\' doulble\" angle> amper& comment<!--',
        'summary': 'summary single\' doulble\" angle> amper& comment<!--',
        }
    actual = self.render_form(feature_dict)
    self.validate_html(actual)
    self.assertIn('name="name"', actual)
    self.assertIn(
        'value="name single&#x27; doulble&quot; '
        'angle&gt; amper&amp; comment&lt;!--"',
        actual)
    self.assertIn('name="summary"', actual)
    self.assertIn(
        'value="summary single&#x27; doulble&quot; '
        'angle&gt; amper&amp; comment&lt;!--"',
        actual)


class DisplayFieldsTest(unittest.TestCase):

  def test_make_display_spec(self):
    summary_spec = guideforms.make_display_spec('summary')
    self.assertEqual('summary', summary_spec[0])
    self.assertEqual('Summary', summary_spec[1])
    self.assertEqual('text', summary_spec[2])

    unlisted_spec = guideforms.make_display_spec('unlisted')
    self.assertEqual('unlisted', unlisted_spec[0])
    self.assertEqual('Unlisted', unlisted_spec[1])
    self.assertEqual('bool', unlisted_spec[2])

    i2p_spec = guideforms.make_display_spec('intent_to_implement_url')
    self.assertEqual('intent_to_implement_url', i2p_spec[0])
    self.assertEqual('url', i2p_spec[2])

  def test_make_display_specs(self):
    specs = guideforms.make_display_specs(
        'summary', 'unlisted', 'intent_to_implement_url')
    self.assertEqual(3, len(specs))
    summary_spec, unlisted_spec, i2p_spec = specs
    self.assertEqual('Summary', summary_spec[1])

  def test_DISPLAY_FIELDS_IN_STAGES__no_duplicates(self):
    """Each field appears at most once."""
    fields_seen = set(guideforms.DISPLAY_IN_FEATURE_HIGHLIGHTS +
                      guideforms.DEPRECATED_FIELDS)
    for stage_id, field_spec_list in list(guideforms.DISPLAY_FIELDS_IN_STAGES.items()):
      for field_spec in field_spec_list:
        field_name = field_spec[0]
        self.assertNotIn(
            field_name, fields_seen,
            msg='Field %r is in DISPLAY_FIELDS_IN_STAGES twice' % field_name)
        fields_seen.add(field_name)

  def test_DISPLAY_FIELDS_IN_STAGES__complete_coverage(self):
    """Each field appears at least once."""
    fields_seen = set(guideforms.DISPLAY_IN_FEATURE_HIGHLIGHTS +
                      guideforms.DEPRECATED_FIELDS)
    for stage_id, field_spec_list in list(guideforms.DISPLAY_FIELDS_IN_STAGES.items()):
      for field_spec in field_spec_list:
        field_name = field_spec[0]
        fields_seen.add(field_name)
    for field_name in list(guideforms.ALL_FIELDS.keys()):
      self.assertIn(
          field_name, fields_seen,
          msg='Field %r is missing in DISPLAY_FIELDS_IN_STAGES' % field_name)

  def test_validate_url(self):
    guideforms.validate_url('http://www.google.com')
    guideforms.validate_url('https://www.google.com')
    guideforms.validate_url('https://chromium.org')

    with self.assertRaises(ValidationError):
      # Disallow ftp URLs.
      guideforms.validate_url('ftp://chromium.org')
    with self.assertRaises(ValidationError):
      # Disallow schema-only URLs.
      guideforms.validate_url('http:')
    with self.assertRaises(ValidationError):
      # Disallow schema-less URLs.
      guideforms.validate_url('www.google.com')
