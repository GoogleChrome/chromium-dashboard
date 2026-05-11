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

"""Tests for the link_helpers module, verifying URL validation, classification, and extraction logic."""

import logging
from unittest import mock, skip

import testing_config
from internals.link_helpers import (
    LINK_TYPE_CHROMIUM_BUG,
    LINK_TYPE_GITHUB_ISSUE,
    LINK_TYPE_GITHUB_MARKDOWN,
    LINK_TYPE_GOOGLE_DOCS,
    LINK_TYPE_MDN_DOCS,
    LINK_TYPE_MOZILLA_BUG,
    LINK_TYPE_SPECS,
    LINK_TYPE_WEB,
    Link,
    valid_url,
)


class LinkHelperTest(testing_config.CustomTestCase):
    """Tests for the Link helper class."""

    def setUp(self):
        """Set up the test environment."""
        self.mock_unit_test_mode = mock.patch('settings.UNIT_TEST_MODE', False)
        self.mock_unit_test_mode.start()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Clean up the test environment."""
        self.mock_unit_test_mode.stop()
        logging.disable(logging.NOTSET)

    def test_specs_url(self):
        """Test specs url."""
        urls = [
            'https://w3c.github.io/presentation-api/',
            'https://www.w3.org/TR/css-pseudo-4/#highlight-pseudos',
            'https://dev.w3.org/html5/spec-LC/the-button-element.html',
            'https://drafts.csswg.org/css-conditional-4/#support-definition-ext',
            'https://drafts.csswg.org/css-values-3/#position',
            'https://dom.spec.whatwg.org/#validate',
            'https://html.spec.whatwg.org/multipage/webappapis.html',
            'https://wicg.github.io/keyboard-map/#layoutchange-event',
        ]

        for url in urls:
            with self.subTest(url=url):
                link = Link(url)
                self.assertEqual(link.type, LINK_TYPE_SPECS)
                self.assertEqual(link.url, url)

    def test_mozilla_bug(self):
        """Test mozilla bug."""
        link = Link('https://bugzilla.mozilla.org/show_bug.cgi?id=1314686')
        link.parse()
        self.assertEqual(link.type, LINK_TYPE_MOZILLA_BUG)
        self.assertTrue(link.is_parsed)
        self.assertFalse(
            link.is_error,
            msg=f'Error parsing mozilla bug: {getattr(link, "error", None)}',
        )
        self.assertIsNotNone(link.information.get('title'))
        self.assertIsNotNone(link.information.get('description'))

    def test_google_docs_url(self):
        """Test google docs url."""
        link = Link(
            'https://docs.google.com/document/d/1-M_o-il38aW64Gyk4R23Yaxy1p2Uy7D0i6J5qTWzypU'
        )
        link.parse()
        self.assertEqual(link.type, LINK_TYPE_GOOGLE_DOCS)
        self.assertTrue(link.is_parsed)
        self.assertFalse(link.is_error)
        self.assertIsNotNone(link.information.get('title'))

    def test_mdn_docs_url(self):
        """Test mdn docs url."""
        link = Link('https://developer.mozilla.org/en-US/docs/Web/HTML')
        link.parse()
        self.assertEqual(link.type, LINK_TYPE_MDN_DOCS)
        self.assertEqual(
            link.url, 'https://developer.mozilla.org/en-US/docs/Web/HTML'
        )
        self.assertTrue(link.is_parsed)
        self.assertFalse(link.is_error)
        self.assertIsNotNone(link.information.get('title'))
        self.assertIsNotNone(link.information.get('description'))

    def test_valid_url(self):
        """Test valid url."""
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
    @mock.patch('requests.head')
    def test_mock_not_found_url(self, mock_requests_head, mock_requests_get):
        """Test mock not found url."""
        mock_requests_head.return_value = testing_config.Blank(
            status_code=404, content=''
        )
        mock_requests_get.return_value = testing_config.Blank(
            status_code=404, content=''
        )

        link = Link('https://www.google.com/')
        link.parse()
        self.assertEqual(link.type, LINK_TYPE_WEB)
        self.assertEqual(link.is_error, True)
        self.assertEqual(link.http_error_code, 404)

    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_validate_url_uses_head_success(
        self, mock_requests_head, mock_requests_get
    ):
        """Test that _validate_url uses HEAD and succeeds."""
        mock_requests_head.return_value = testing_config.Blank(
            status_code=200, content=''
        )

        link = Link('https://www.google.com/')
        link.parse()
        self.assertTrue(mock_requests_head.called)
        self.assertFalse(mock_requests_get.called)
        self.assertFalse(link.is_error)

    @mock.patch('requests.get')
    @mock.patch('requests.head')
    def test_validate_url_falls_back_to_get(
        self, mock_requests_head, mock_requests_get
    ):
        """Test that _validate_url falls back to GET on non-200 HEAD."""
        mock_requests_head.return_value = testing_config.Blank(
            status_code=405, content=''
        )
        mock_requests_get.return_value = testing_config.Blank(
            status_code=200, content=''
        )

        link = Link('https://www.google.com/')
        link.parse()
        self.assertTrue(mock_requests_head.called)
        self.assertTrue(mock_requests_get.called)
        self.assertFalse(link.is_error)

    def test_extract_urls_from_value(self):
        """Test extract urls from value."""
        field_value = 'https://www.chromestatus.com/feature/1234'
        urls = Link.extract_urls_from_value(field_value)
        self.assertEqual(urls, [field_value])

        field_value = 'https://w3c.github.io/presentation-api/'
        urls = Link.extract_urls_from_value(field_value)
        self.assertEqual(urls, [field_value])

        field_value = "leadinghttps:https://www.chromestatus.com/feature/1234');, https://www.chromestatus.com/feature/5678 is valid"  # noqa: E501
        urls = Link.extract_urls_from_value(field_value)
        self.assertEqual(
            urls,
            [
                'https://www.chromestatus.com/feature/1234',
                'https://www.chromestatus.com/feature/5678',
            ],
        )

        field_value = [
            'https://www.chromestatus.com/feature/1234',
            'not a valid urlhttps://www.chromestatus.com/feature/',
            None,
        ]  # noqa: E501
        urls = Link.extract_urls_from_value(field_value)
        self.assertEqual(urls, ['https://www.chromestatus.com/feature/1234'])

    def test_link_github_markdown(self):
        """Test link github markdown."""
        urls_to_test = [
            'https://github.com/w3c/reporting/blob/master/EXPLAINER.md#crashes',
            'https://github.com/tc39/proposal-logical-assignment/blob/master/README.md',
            'https://github.com/w3c/reporting/blob/7984341ce9554473fc9487001b169703e9871811/EXPLAINER.md',
        ]
        for url in urls_to_test:
            link = Link(url)
            self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)

    def test_link_parse_github_markdown_with_renamed_branch(self):
        # master branch is renamed to main
        """Test link parse github markdown with renamed branch."""
        link = Link('https://github.com/w3c/reporting/blob/master/EXPLAINER.md')
        link.parse()
        if link.is_error and link.http_error_code == 429:
            return
        info = link.information
        self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(info['_parsed_title'], 'Reporting API')
        print(info)

    def test_link_parse_github_markdown_with_hash(self):
        """Test link parse github markdown with hash."""
        link = Link(
            'https://github.com/vmpstr/web-proposals/blob/b146b4447b3746669000f1abbb5a19d32f508540/explainers/cv-auto-event.md'
        )
        link.parse()
        if link.is_error and link.http_error_code == 429:
            return
        info = link.information
        self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(
            info['_parsed_title'], 'CSS `content-visibility` state change event'
        )

    def test_link_github_issue(self):
        """Test link github issue."""
        urls_to_test = [
            'https://github.com/GoogleChrome/chromium-dashboard/issues/999',
            'https://www.github.com/GoogleChrome/chromium-dashboard/issues/999',
            'https://www.github.com/GoogleChrome/chromium-dashboard/issues/999?params=1#issuecomment-688970447',
        ]
        for url in urls_to_test:
            link = Link(url)
            self.assertEqual(link.type, LINK_TYPE_GITHUB_ISSUE)

    def test_link_non_github_issue(self):
        """Test link non github issue."""
        urls_to_test = [
            'https://fakegithub.com/GoogleChrome/chromium-dashboard/issues/999',
            'https://www.github.com/GoogleChrome/chromium-dashboard/issues/',
        ]
        for url in urls_to_test:
            link = Link(url)
            self.assertNotEqual(link, LINK_TYPE_GITHUB_ISSUE)

    def test_parse_github_issue(self):
        """Test parse github issue."""
        link = Link(
            'https://www.github.com/GoogleChrome/chromium-dashboard/issues/999?params=1#issuecomment-688970447'
        )
        link.parse()
        if link.is_error and link.http_error_code == 429:
            return
        info = link.information
        self.assertEqual(link.type, LINK_TYPE_GITHUB_ISSUE)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(info['title'], 'Comments field is incorrectly escaped')
        self.assertEqual(info['state'], 'closed')
        self.assertEqual(info['state_reason'], 'completed')
        self.assertEqual(info['created_at'], '2020-09-03T18:29:42Z')
        self.assertEqual(info['closed_at'], '2020-12-01T21:50:57Z')
        self.assertEqual(info['labels'], ['bug'])

    @mock.patch('logging.error')
    def test_parse_github_issue_fail_wrong_id_or_no_permission(
        self, mock_error
    ):
        """Test parse github issue fail wrong id or no permission."""
        link = Link(
            'https://www.github.com/GoogleChrome/chromium-dashboard/issues/100000000000000'
        )
        link.parse()
        self.assertEqual(link.type, LINK_TYPE_GITHUB_ISSUE)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(link.is_error, True)
        self.assertEqual(link.http_error_code, 404)

    def test_link_code_google(self):
        """Test link code google."""
        link = Link(
            'https://code.google.com/p/chromium/issues/detail?id=515786'
        )
        self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

    def test_link_crbug(self):
        """Test link crbug."""
        link = Link('https://crbug.com/1352598')
        self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

    def test_link_chromium(self):
        """Test link chromium."""
        link = Link(
            'https://bugs.chromium.org/p/chromium/issues/detail?id=100000'
        )
        self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

    def test_link_non_chromium(self):
        """Test link non chromium."""
        link = Link(
            'https://bugs0chromium.org/p/chromium/issues/detail?id=100000'
        )
        self.assertNotEqual(link.type, LINK_TYPE_CHROMIUM_BUG)

    @skip('Until issues.chromium.org has an API')
    def test_parse_chromium_tracker(self):
        """Test parse chromium tracker."""
        link = Link(
            'https://bugs.chromium.org/p/chromium/issues/detail?id=100000'
        )
        link.parse()
        info = link.information
        self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(
            info['summary'], 'Repeated zooms leave tearing artifact'
        )
        self.assertEqual(info['statusRef']['status'], 'Fixed')
        self.assertEqual(info['ownerRef']['displayName'], 'backer@chromium.org')

    @skip('Until issues.chromium.org has an API')
    @mock.patch('logging.error')
    def test_parse_chromium_tracker_fail_wrong_id(self, mock_error):
        """Test parse chromium tracker fail wrong id."""
        link = Link(
            'https://bugs.chromium.org/p/chromium/issues/detail?id=100000000000000'
        )
        link.parse()
        self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(link.is_error, True)
        self.assertEqual(link.information, None)

    @skip('Until issues.chromium.org has an API')
    @mock.patch('logging.error')
    def test_parse_chromium_tracker_fail_no_permission(self, mock_error):
        """Test parse chromium tracker fail no permission."""
        link = Link('https://bugs.chromium.org/p/chromium/issues/detail?id=1')
        link.parse()
        self.assertEqual(link.type, LINK_TYPE_CHROMIUM_BUG)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(link.is_error, True)
        self.assertEqual(link.information, None)

    def test_extract_invalid_url(self):
        """Test extract invalid url."""
        urls = Link.extract_urls_from_value('Some kind of https://... link.')
        self.assertEqual(len(urls), 0)
