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
from internals.link_helpers import (
    Link,
    LINK_TYPE_CHROMIUM_BUG,
    LINK_TYPE_GITHUB_ISSUE,
    LINK_TYPE_GITHUB_MARKDOWN,
    LINK_TYPE_WEB
)


class LinkHelperTest(testing_config.CustomTestCase):

  def test_real_server_error_url(self):
    link = Link("http://httpstat.us/503")
    
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_WEB)
    self.assertEqual(link.is_error, True)
    self.assertEqual(link.http_error_code, 503)

    link = Link("https://httpstat.us/400")

    link.parse()
    self.assertEqual(link.type, LINK_TYPE_WEB)
    self.assertEqual(link.is_error, True)
    self.assertEqual(link.http_error_code, 400)

  @mock.patch('requests.get')
  def test_mock_not_found_url(self, mock_requests_get):
    mock_requests_get.return_value = testing_config.Blank(
        status_code=404, content='')  

    link = Link("https://www.google.com/")
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_WEB)
    self.assertEqual(link.is_error, True)
    self.assertEqual(link.http_error_code, 404)
  
  def test_extract_urls_from_value(self):
    field_value = "https://www.chromestatus.com/feature/1234"
    urls = Link.extract_urls_from_value(field_value)
    self.assertEqual(urls, [field_value])

    field_value = "leadinghttps:https://www.chromestatus.com/feature/1234, https://www.chromestatus.com/feature/5678 is valid"
    urls = Link.extract_urls_from_value(field_value)
    self.assertEqual(urls, ["https://www.chromestatus.com/feature/1234", "https://www.chromestatus.com/feature/5678"])

    field_value = ["https://www.chromestatus.com/feature/1234", "not a valid urlhttps://www.chromestatus.com/feature/", None]
    urls = Link.extract_urls_from_value(field_value)
    self.assertEqual(urls, ["https://www.chromestatus.com/feature/1234"])

  def test_link_github_markdown(self):
    urls_to_test = [
        "https://github.com/w3c/reporting/blob/master/EXPLAINER.md#crashes",
        "https://github.com/tc39/proposal-logical-assignment/blob/master/README.md",
        "https://github.com/w3c/reporting/blob/7984341ce9554473fc9487001b169703e9871811/EXPLAINER.md"
    ]
    for url in urls_to_test:
      link = Link(url)
      self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)

  def test_link_parse_github_markdown_with_renamed_branch(self):
    # master branch is renamed to main
    link = Link(
        "https://github.com/w3c/reporting/blob/master/EXPLAINER.md")
    link.parse()
    info = link.information
    self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(info["_parsed_title"], "Reporting API")
    print(info)

  def test_link_parse_github_markdown_with_hash(self):
    link = Link(
        "https://github.com/vmpstr/web-proposals/blob/b146b4447b3746669000f1abbb5a19d32f508540/explainers/cv-auto-event.md")
    link.parse()
    info = link.information
    self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(info["_parsed_title"],
                     "CSS `content-visibility` state change event")

  def test_link_github_issue(self):
    urls_to_test = [
        "https://github.com/GoogleChrome/chromium-dashboard/issues/999",
        "https://www.github.com/GoogleChrome/chromium-dashboard/issues/999",
        "https://www.github.com/GoogleChrome/chromium-dashboard/issues/999?params=1#issuecomment-688970447",
    ]
    for url in urls_to_test:
      link = Link(url)
      self.assertEqual(link.type, LINK_TYPE_GITHUB_ISSUE)

  def test_link_non_github_issue(self):
    urls_to_test = [
        "https://fakegithub.com/GoogleChrome/chromium-dashboard/issues/999",
        "https://www.github.com/GoogleChrome/chromium-dashboard/issues/",
    ]
    for url in urls_to_test:
      link = Link(url)
      self.assertNotEqual(link, LINK_TYPE_GITHUB_ISSUE)

  def test_parse_github_issue(self):
    link = Link(
        "https://www.github.com/GoogleChrome/chromium-dashboard/issues/999?params=1#issuecomment-688970447"
    )
    link.parse()
    info = link.information
    self.assertEqual(link.type, LINK_TYPE_GITHUB_ISSUE)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(info["title"], "Comments field is incorrectly escaped")
    self.assertEqual(info["state"], "closed")
    self.assertEqual(info["state_reason"], "completed")
    self.assertEqual(info["closed_at"], "2020-12-01T21:50:57Z")

  @mock.patch("logging.error")
  def test_parse_github_issue_fail_wrong_id_or_no_permission(self, mock_error):
    link = Link(
        "https://www.github.com/GoogleChrome/chromium-dashboard/issues/100000000000000"
    )
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_GITHUB_ISSUE)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(link.is_error, True)
    self.assertEqual(link.http_error_code, 404)

  def test_link_chromium(self):
    link = Link("https://bugs.chromium.org/p/chromium/issues/detail?id=100000")
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

  def test_link_non_chromium(self):
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

  @mock.patch("logging.error")
  def test_parse_chromium_tracker_fail_wrong_id(self, mock_error):
    link = Link(
        "https://bugs.chromium.org/p/chromium/issues/detail?id=100000000000000"
    )
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(link.is_error, True)
    self.assertEqual(link.information, None)

  @mock.patch("logging.error")
  def test_parse_chromium_tracker_fail_no_permission(self, mock_error):
    link = Link("https://bugs.chromium.org/p/chromium/issues/detail?id=1")
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(link.is_error, True)
    self.assertEqual(link.information, None)
