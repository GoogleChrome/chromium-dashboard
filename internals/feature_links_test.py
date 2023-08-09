# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
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

import testing_config
from unittest import mock
from internals.core_models import FeatureEntry
from internals.feature_links import FeatureLinks, update_feature_links, get_domain_with_scheme, get_feature_links_summary
from internals.link_helpers import LINK_TYPE_CHROMIUM_BUG, LINK_TYPE_WEB


class LinkTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature = FeatureEntry(
        name='feature a', summary='sum', category=1,
        owner_emails=['feature_owner@example.com'],
    )
    self.feature.put()
    self.feature_id = self.feature.key.integer_id()

    self.feature2 = FeatureEntry(
        name='feature b', summary='sum', category=1,
    )
    self.feature2.put()
    self.feature2_id = self.feature2.key.integer_id()

  def tearDown(self):
    for feature_links in FeatureLinks.query():
      feature_links.key.delete()
    self.feature.key.delete()
    self.feature2.key.delete()
    pass

  def mock_user_change_fields(self, changed_fields, target_feature=None):
    if not target_feature:
      target_feature = self.feature
    for field_name, old_val, new_val in changed_fields:
      setattr(target_feature, field_name, new_val)
    self.feature.put()

    update_feature_links(target_feature, changed_fields)

  def test_get_domain_and_scheme__valid(self):
    self.assertEqual(
        'https://example.com',
        get_domain_with_scheme('https://example.com'))
    self.assertEqual(
        'https://example.com',
        get_domain_with_scheme('https://example.com/'))
    self.assertEqual(
        'https://example.com',
        get_domain_with_scheme('https://example.com/something?foo=bar#baz'))
    self.assertEqual(
        'https://localhost',
        get_domain_with_scheme('https://localhost'))
    self.assertEqual(
        'https://localhost:8080',
        get_domain_with_scheme('https://localhost:8080'))
    self.assertEqual(
        'https://192.168.0.1',
        get_domain_with_scheme('https://192.168.0.1/'))
    self.assertEqual(
        'https://[2a01:5cc0:1:2::4]',
        get_domain_with_scheme('https://[2a01:5cc0:1:2::4]/something'))

  def test_get_domain_and_scheme__invalid(self):
    self.assertEqual(
        'Invalid: https://[2a01:5cc0:1:2:$::4]/s',
        get_domain_with_scheme('https://[2a01:5cc0:1:2:$::4]/something'))
    self.assertEqual(
        'Invalid: http://[::1.2.3',
        get_domain_with_scheme('http://[::1.2.3'))

  def test_get_feature_links_summary(self):
    links = [
      FeatureLinks(url='https://bugs.chromium.org/p/chromium/issues/detail?id=100000', type=LINK_TYPE_CHROMIUM_BUG),
      FeatureLinks(url='https://docs.google.com/document/d/xxx', type=LINK_TYPE_WEB),
      FeatureLinks(url='https://docs.google.com/spreadsheets/d/xxx', type=LINK_TYPE_WEB),
      FeatureLinks(url='https://www.google.com', type=LINK_TYPE_WEB),
    ]
    for link in links:
      link.put()
    summary = get_feature_links_summary()

    self.assertEqual(
          summary,
          {
              "total_count": 4,
              "covered_count": 1,
              "uncovered_count": 3,
              "link_types": [
                  {"key": "web", "count": 3},
                  {"key": "chromium_bug", "count": 1},
              ],
              "uncovered_link_domains": [
                {"key": "https://docs.google.com", "count": 2},
                {"key": "https://www.google.com", "count": 1},
              ],
          },
      )

  def test_feature_changed_add_and_remove_url(self):
    url = "https://bugs.chromium.org/p/chromium/issues/detail?id=100000"
    query = FeatureLinks.query(FeatureLinks.url == url)

    changed_fields = [
      ('bug_url', None, url),
      ('launch_bug_url', None, url),
    ]

    # add two same links in a feature fields
    self.mock_user_change_fields(changed_fields)
    link = query.get()
    self.assertEqual(link.url, url)
    self.assertIn(self.feature_id, link.feature_ids)
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
    self.assertIsNotNone(link.information)
    self.assertEqual(link.information["summary"],
                     "Repeated zooms leave tearing artifact")

    # remove bug_url field, the link should still exist
    # because launch_bug_url field is still using it
    changed_fields_remove = [('bug_url', url, None)]
    self.mock_user_change_fields(changed_fields_remove)
    link = query.get()
    self.assertIsNotNone(link)

    # remove launch_bug_url field, the link should be deleted
    changed_fields_remove = [
      ('launch_bug_url', url, None)]
    self.mock_user_change_fields(changed_fields_remove)
    link = query.get()
    self.assertIsNone(link)

  @mock.patch('logging.error')
  def test_feature_changed_invalid_url(self, mock_error):
    url = "https://bugs.chromium.org/p/chromium/issues/detail?id=100000000000"
    query = FeatureLinks.query(FeatureLinks.url == url)
    changed_fields = [
      ('bug_url', None, url),
    ]

    # add invalid url to feature
    self.mock_user_change_fields(changed_fields)
    link = query.get()
    self.assertIsNone(link)

  def test_features_with_same_link(self):
    url = "https://bugs.chromium.org/p/chromium/issues/detail?id=100000"
    query = FeatureLinks.query(FeatureLinks.url == url)
    changed_fields = [
      ('bug_url', None, url),
    ]
    # add same link to both features
    self.mock_user_change_fields(changed_fields)
    self.mock_user_change_fields(changed_fields, self.feature2)
    link = query.get()
    self.assertIsNotNone(link)
    self.assertIn(self.feature_id, link.feature_ids)
    self.assertIn(self.feature2_id, link.feature_ids)

    # remove link from one feature
    changed_fields_remove = [
      ('bug_url', url, None)]
    self.mock_user_change_fields(changed_fields_remove)
    link = query.get()
    self.assertNotIn(self.feature_id, link.feature_ids)
    self.assertIn(self.feature2_id, link.feature_ids)
