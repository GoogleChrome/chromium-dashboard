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
from internals.link_helpers import Link, LINK_TYPE_CHROMIUM_BUG


class LinkHelperTest(testing_config.CustomTestCase):
  def test_link_with_wrong_host(self):
    link = Link("https://bugs0chromium.org/p/chromium/issues/detail?id=100000")
    self.assertNotEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

  def test_parse_chromium_tracker(self):
    link = Link("https://bugs.chromium.org/p/chromium/issues/detail?id=100000")
    link.parse()
    info = link.information
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(info["summary"], "Repeated zooms leave tearing artifact")
    self.assertEqual(info["statusRef"]["status"], "Fixed")
    self.assertEqual(info["ownerRef"]["displayName"], "backer@chromium.org")

  @mock.patch('logging.error')
  def test_parse_chromium_tracker_fail_wrong_id(self, mock_error):
    link = Link(
        "https://bugs.chromium.org/p/chromium/issues/detail?id=100000000000000"
    )
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(link.is_error, True)
    self.assertEqual(link.information, None)

  @mock.patch('logging.error')
  def test_parse_chromium_tracker_fail_no_permission(self, mock_error):
    link = Link("https://bugs.chromium.org/p/chromium/issues/detail?id=1")
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(link.is_error, True)
    self.assertEqual(link.information, None)
