# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
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

import testing_config  # Must be imported before the module under test.

from google.cloud import ndb

from internals import core_models
from internals import html_templates
from internals import user_models


class EstimatedMilestoneTablesTemplateTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature one', summary='sum', owner=['feature_owner@example.com'],
        shipped_milestone=100, ot_milestone_desktop_start=100,
        category=1, standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_1.put()

    self.feature_2 = core_models.Feature(
        name='feature two', summary='sum', owner=['feature_owner@example.com'],
        shipped_milestone=100, ot_milestone_desktop_start=100,
        ot_milestone_android_end=105, ot_milestone_android_start=101,
        category=1, standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_2.put()

    self.feature_3 = core_models.Feature(
        name='feature three', summary='sum', owner=['feature_owner@example.com'],
        ot_milestone_webview_end=99, ot_milestone_webview_start=97,
        shipped_ios_milestone=106, dt_milestone_ios_start=106,
        category=1, standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_3.put()

    self.feature_4 = core_models.Feature(
        name='feature three', summary='sum', owner=['feature_owner@example.com'],
        category=1, standardization=1, web_dev_views=1, impl_status_chrome=1)
    self.feature_4.put()

  def tearDown(self):
    self.feature_1.key.delete()
    self.feature_2.key.delete()
    self.feature_3.key.delete()
    self.feature_4.key.delete()

  def test_estimated_milestone_tables_html__only_desktop(self):
    """We generate an estimated milestone table html with only desktop
    milestone fields."""
    body_html = html_templates.estimated_milestone_tables_html(self.feature_1)
    self.assertIn(
      '<table>\n'
      '  <tr><td>Shipping on desktop</td>\n'
      '  <td>100</td></tr>\n'
      '  <tr><td>OriginTrial desktop first</td>\n'
      '  <td>100</td></tr>\n'
      '</table>\n', body_html)

  def test_estimated_milestone_tables_html__desktop_and_android(self):
    """We generate an estimated milestone table html with desktop and android
    milestone fields."""
    body_html = html_templates.estimated_milestone_tables_html(self.feature_2)
    self.assertIn(
      '<table>\n'
      '  <tr><td>Shipping on desktop</td>\n'
      '  <td>100</td></tr>\n'
      '  <tr><td>OriginTrial desktop first</td>\n'
      '  <td>100</td></tr>\n'
      '</table>\n'
      '<table>\n'
      '  <tr><td>OriginTrial Android last</td>\n'
      '  <td>105</td></tr>\n'
      '  <tr><td>OriginTrial Android first</td>\n'
      '  <td>101</td></tr>\n'
      '</table>\n', body_html)

  def test_estimated_milestone_tables_html__webview_and_ios(self):
    """We generate an estimated milestone table html with webview and ios
    milestone fields."""
    body_html = html_templates.estimated_milestone_tables_html(self.feature_3)
    self.assertIn(
      '<table>\n'
      '  <tr><td>OriginTrial webView last</td>\n'
      '  <td>99</td></tr>\n'
      '  <tr><td>OriginTrial webView first</td>\n'
      '  <td>97</td></tr>\n'
      '</table>\n'
      '<table>\n'
      '  <tr><td>Shipping on iOS</td>\n'
      '  <td>106</td></tr>\n'
      '  <tr><td>DevTrial on iOS</td>\n'
      '  <td>106</td></tr>\n'
      '</table>\n', body_html)

  def test_estimated_milestone_tables_html__no_milestones(self):
    """We generate an estimated milestone table html with no milestone
    fields."""
    body_html = html_templates.estimated_milestone_tables_html(self.feature_4)
    self.assertIn('<p>No milestones specified</p>\n', body_html)


class NewAndUpdatedFeatureTemplateTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = core_models.Feature(
        name='feature one', summary='sum', owner=['feature_owner@example.com'],
        ot_milestone_desktop_start=100,
        editors=['feature_editor@example.com', 'owner_1@example.com'],
        category=1, visibility=1, standardization=1, web_dev_views=1,
        impl_status_chrome=1, created_by=ndb.User(
            email='creator1@gmail.com', _auth_domain='gmail.com'),
        updated_by=ndb.User(
            email='editor1@gmail.com', _auth_domain='gmail.com'),
        blink_components=['Blink'])
    self.feature_1.put()
    self.component_1 = user_models.BlinkComponent(name='Blink')
    self.component_1.put()
    self.component_owner_1 = user_models.FeatureOwner(
        name='owner_1', email='owner_1@example.com',
        primary_blink_components=[self.component_1.key])
    self.component_owner_1.put()
    self.watcher_1 = user_models.FeatureOwner(
        name='watcher_1', email='watcher_1@example.com',
        watching_all_features=True)
    self.watcher_1.put()
    self.changes = [dict(prop_name='test_prop', new_val='test new value',
                    old_val='test old value')]

  def tearDown(self):
    self.feature_1.key.delete()

  def test_format_email_body__new(self):
    """We generate an email body for new features."""
    body_html = html_templates.new_feature_email_html(self.feature_1)
    self.assertIn('Blink', body_html)
    self.assertIn('creator1@gmail.com added', body_html)
    self.assertIn('chromestatus.com/feature/'
      f'{self.feature_1.key.integer_id()}', body_html)
    self.assertNotIn('watcher_1,', body_html)

  def test_format_email_body__update_no_changes(self):
    """We don't crash if the change list is emtpy."""
    body_html = html_templates.update_feature_email_html(self.feature_1, [])
    self.assertIn('Blink', body_html)
    self.assertIn('editor1@gmail.com updated', body_html)
    self.assertNotIn('watcher_1,', body_html)

  def test_format_email_body__update_with_changes(self):
    """We generate an email body for an updated feature."""
    body_html = html_templates.update_feature_email_html(
      self.feature_1, self.changes)
    self.assertIn('test_prop', body_html)
    self.assertIn('chromestatus.com/feature/'
      f'{self.feature_1.key.integer_id()}', body_html)
    self.assertIn('test old value', body_html)
    self.assertIn('test new value', body_html)

  def test_format_email_body__mozdev_links(self):
    """We generate an email body with links to developer.mozilla.org."""
    self.feature_1.doc_links = ['https://developer.mozilla.org/look-here']
    body_html = html_templates.update_feature_email_html(
      self.feature_1, self.changes)
    self.assertIn('look-here', body_html)

    self.feature_1.doc_links = [
        'https://hacker-site.org/developer.mozilla.org/look-here']
    body_html = html_templates.update_feature_email_html(
      self.feature_1, self.changes)
    self.assertNotIn('look-here', body_html)
