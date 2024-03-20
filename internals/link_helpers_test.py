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
from unittest import skip
from internals.link_helpers import (
    Link,
    LINK_TYPE_CHROMIUM_BUG,
    LINK_TYPE_GITHUB_ISSUE,
    LINK_TYPE_GITHUB_MARKDOWN,
    LINK_TYPE_WEB,
    LINK_TYPE_MDN_DOCS,
    LINK_TYPE_GOOGLE_DOCS,
    LINK_TYPE_MOZILLA_BUG,
    LINK_TYPE_SPECS,
    valid_url
)


class LinkHelperTest(testing_config.CustomTestCase):
  def test_specs_url(self):
    urls = [
      "https://w3c.github.io/presentation-api/",
      "https://www.w3.org/TR/css-pseudo-4/#highlight-pseudos",
      "https://dev.w3.org/html5/spec-LC/the-button-element.html",
      "https://drafts.csswg.org/css-conditional-4/#support-definition-ext",
      "https://drafts.csswg.org/css-values-3/#position",
      "https://dom.spec.whatwg.org/#validate",
      "https://html.spec.whatwg.org/multipage/webappapis.html",
      "https://wicg.github.io/keyboard-map/#layoutchange-event",
    ]

    for url in urls:
      with self.subTest(url=url):
        link = Link(url)
        self.assertEqual(link.type, LINK_TYPE_SPECS)
        self.assertEqual(link.url, url)
  def test_mozilla_bug(self):
    link = Link("https://bugzilla.mozilla.org/show_bug.cgi?id=1314686")
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_MOZILLA_BUG)
    self.assertTrue(link.is_parsed)
    self.assertFalse(link.is_error)
    self.assertIsNotNone(link.information.get('title'))
    self.assertIsNotNone(link.information.get('description'))

  def test_google_docs_url(self):
    link = Link("https://docs.google.com/document/d/1-M_o-il38aW64Gyk4R23Yaxy1p2Uy7D0i6J5qTWzypU")
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_GOOGLE_DOCS)
    self.assertTrue(link.is_parsed)
    self.assertFalse(link.is_error)
    self.assertIsNotNone(link.information.get('title'))

  def test_mdn_docs_url(self):
    link = Link("https://developer.mozilla.org/en-US/docs/Web/HTML")
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_MDN_DOCS)
    self.assertEqual(link.url, "https://developer.mozilla.org/en-US/docs/Web/HTML")
    self.assertTrue(link.is_parsed)
    self.assertFalse(link.is_error)
    self.assertIsNotNone(link.information.get('title'))
    self.assertIsNotNone(link.information.get('description'))

  def test_valid_url(self):
    invalid_urls = [
        'http://',
        'http://.',
        'https://invalid',
    ]
    valid_urls = [
        'http://www.google.com/',
        'https://www.google.com/',
        'http://www.google.com',
        'https://www.google.com',
    ]
    for url in invalid_urls:
      with self.subTest(url=url):
        self.assertFalse(valid_url(url))
    for url in valid_urls:
      with self.subTest(url=url):
        self.assertTrue(valid_url(url))

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

    field_value = "https://w3c.github.io/presentation-api/"
    urls = Link.extract_urls_from_value(field_value)
    self.assertEqual(urls, [field_value])

    field_value = "leadinghttps:https://www.chromestatus.com/feature/1234');, https://www.chromestatus.com/feature/5678 is valid"
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
    if link.is_error and "rate limit" in str(link.error):
      return
    info = link.information
    self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(info["_parsed_title"], "Reporting API")
    print(info)

  def test_link_parse_github_markdown_with_hash(self):
    link = Link(
        "https://github.com/vmpstr/web-proposals/blob/b146b4447b3746669000f1abbb5a19d32f508540/explainers/cv-auto-event.md")
    link.parse()
    if link.is_error and "rate limit" in str(link.error):
      return
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
    if link.is_error and "rate limit" in str(link.error):
      return
    info = link.information
    self.assertEqual(link.type, LINK_TYPE_GITHUB_ISSUE)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(info["title"], "Comments field is incorrectly escaped")
    self.assertEqual(info["state"], "closed")
    self.assertEqual(info["state_reason"], "completed")
    self.assertEqual(info["created_at"], "2020-09-03T18:29:42Z")
    self.assertEqual(info["closed_at"], "2020-12-01T21:50:57Z")
    self.assertEqual(info["labels"], ["bug"])

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

  def test_link_code_google(self):
    link = Link("https://code.google.com/p/chromium/issues/detail?id=515786")
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

  def test_link_crbug(self):
    link = Link("https://crbug.com/1352598")
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

  def test_link_chromium(self):
    link = Link("https://bugs.chromium.org/p/chromium/issues/detail?id=100000")
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

  def test_link_non_chromium(self):
    link = Link("https://bugs0chromium.org/p/chromium/issues/detail?id=100000")
    self.assertNotEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

  @skip('Until issues.chromium.org has an API')
  def test_parse_chromium_tracker(self):
    link = Link("https://bugs.chromium.org/p/chromium/issues/detail?id=100000")
    link.parse()
    info = link.information
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(info["summary"], "Repeated zooms leave tearing artifact")
    self.assertEqual(info["statusRef"]["status"], "Fixed")
    self.assertEqual(info["ownerRef"]["displayName"], "backer@chromium.org")

  @skip('Until issues.chromium.org has an API')
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

  @skip('Until issues.chromium.org has an API')
  @mock.patch("logging.error")
  def test_parse_chromium_tracker_fail_no_permission(self, mock_error):
    link = Link("https://bugs.chromium.org/p/chromium/issues/detail?id=1")
    link.parse()
    self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
    self.assertEqual(link.is_parsed, True)
    self.assertEqual(link.is_error, True)
    self.assertEqual(link.information, None)

  def test_extract_invalid_url(self):
    urls = Link.extract_urls_from_value('Some kind of https://... link.')
    self.assertEqual(len(urls), 0)
