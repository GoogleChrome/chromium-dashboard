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

import base64
import logging
from unittest import mock, skip
from urllib.error import HTTPError

from fastcore.basics import AttrDict

import testing_config
from internals import link_helpers
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

    def _mock_page_status(self, status_code: int) -> None:
        """Make the github.com page check in _validate_url() see status_code.

        Tests must not depend on github.com, which can rate limit or reject
        requests from CI runners.
        """
        page = testing_config.Blank(status_code=status_code, content='')
        for name in ('requests.head', 'requests.get'):
            patcher = mock.patch(name, return_value=page)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _mock_github_client(self) -> mock.MagicMock:
        """Replace the GitHub API client with a mock and return it."""
        client = mock.MagicMock()
        patcher = mock.patch(
            'internals.link_helpers.get_github_api_client', return_value=client
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        return client

    def _github_file(self, text: str) -> AttrDict:
        """Return a GitHub API file response like ghapi's get_content()."""
        return AttrDict(
            content=base64.b64encode(text.encode('utf-8')).decode('ascii'),
            encoding='base64',
        )

    def _http_error(self, code: int) -> HTTPError:
        """Return an error like the one ghapi raises for an HTTP status."""
        return HTTPError('https://api.github.com/', code, 'error', None, None)  # type: ignore[arg-type]

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
        """A link to a renamed branch (master -> main) reads from the new name."""
        self._mock_page_status(200)
        client = self._mock_github_client()
        client.repos.get_branch.return_value = AttrDict(name='main')
        client.repos.get_content.return_value = self._github_file(
            '# Reporting API\n\nSome text.\n'
        )

        link = Link('https://github.com/w3c/reporting/blob/master/EXPLAINER.md')
        link.parse()

        self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(link.is_error, False)
        self.assertEqual(link.information['_parsed_title'], 'Reporting API')
        client.repos.get_branch.assert_called_once_with(
            owner='w3c', repo='reporting', branch='master'
        )
        client.repos.get_content.assert_called_once_with(
            owner='w3c', repo='reporting', path='EXPLAINER.md', ref='main'
        )

    def test_link_parse_github_markdown_not_found(self):
        """A link to a missing file is an error and skips the GitHub API."""
        self._mock_page_status(404)
        client = self._mock_github_client()

        link = Link('https://github.com/w3c/reporting/blob/master/NOT_FOUND.md')
        link.parse()

        self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(link.is_error, True)
        self.assertEqual(link.http_error_code, 404)
        self.assertEqual(link.information, None)
        client.repos.get_content.assert_not_called()

    def test_link_parse_github_markdown_api_not_found(self):
        """A 404 from the GitHub API is recorded without retrying."""
        self._mock_page_status(200)
        client = self._mock_github_client()
        client.repos.get_branch.return_value = AttrDict(name='main')
        client.repos.get_content.side_effect = self._http_error(404)

        link = Link('https://github.com/w3c/reporting/blob/main/NOT_FOUND.md')
        link.parse()

        self.assertEqual(link.is_parsed, True)
        self.assertEqual(link.is_error, True)
        self.assertEqual(link.http_error_code, 404)
        self.assertEqual(link.information, None)
        client.repos.get_content.assert_called_once()

    def test_link_parse_github_markdown_with_hash(self):
        """A link to a commit hash reads the file at that commit."""
        commit = 'b146b4447b3746669000f1abbb5a19d32f508540'
        self._mock_page_status(200)
        client = self._mock_github_client()
        # A commit hash is not a branch name.
        client.repos.get_branch.side_effect = self._http_error(404)
        client.repos.get_content.return_value = self._github_file(
            '# CSS `content-visibility` state change event\n\nText.\n'
        )

        link = Link(
            f'https://github.com/vmpstr/web-proposals/blob/{commit}/explainers/cv-auto-event.md'
        )
        link.parse()

        self.assertEqual(link.type, LINK_TYPE_GITHUB_MARKDOWN)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(link.is_error, False)
        self.assertEqual(
            link.information['_parsed_title'],
            'CSS `content-visibility` state change event',
        )
        client.repos.get_content.assert_called_once_with(
            owner='vmpstr',
            repo='web-proposals',
            path='explainers/cv-auto-event.md',
            ref=commit,
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
        self._mock_page_status(200)
        client = self._mock_github_client()
        client.issues.get.return_value = {
            'url': 'https://api.github.com/repos/GoogleChrome/chromium-dashboard/issues/999',
            'number': 999,
            'title': 'Comments field is incorrectly escaped',
            'user': {'login': 'someone'},
            'state': 'closed',
            'state_reason': 'completed',
            'assignee': None,
            'created_at': '2020-09-03T18:29:42Z',
            'updated_at': '2020-12-01T21:50:57Z',
            'closed_at': '2020-12-01T21:50:57Z',
            'labels': [{'name': 'bug'}],
        }

        link = Link(
            'https://www.github.com/GoogleChrome/chromium-dashboard/issues/999?params=1#issuecomment-688970447'
        )
        link.parse()

        info = link.information
        self.assertEqual(link.type, LINK_TYPE_GITHUB_ISSUE)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(link.is_error, False)
        self.assertEqual(info['number'], 999)
        self.assertEqual(info['title'], 'Comments field is incorrectly escaped')
        self.assertEqual(info['user_login'], 'someone')
        self.assertEqual(info['state'], 'closed')
        self.assertEqual(info['state_reason'], 'completed')
        self.assertEqual(info['assignee_login'], None)
        self.assertEqual(info['created_at'], '2020-09-03T18:29:42Z')
        self.assertEqual(info['closed_at'], '2020-12-01T21:50:57Z')
        self.assertEqual(info['labels'], ['bug'])
        client.issues.get.assert_called_once_with(
            owner='GoogleChrome', repo='chromium-dashboard', issue_number=999
        )

    def test_parse_github_issue_fail_wrong_id_or_no_permission(self):
        """A 404 from the GitHub API is recorded without retrying."""
        self._mock_page_status(200)
        client = self._mock_github_client()
        client.issues.get.side_effect = self._http_error(404)

        link = Link(
            'https://www.github.com/GoogleChrome/chromium-dashboard/issues/100000000000000'
        )
        link.parse()

        self.assertEqual(link.type, LINK_TYPE_GITHUB_ISSUE)
        self.assertEqual(link.is_parsed, True)
        self.assertEqual(link.is_error, True)
        self.assertEqual(link.http_error_code, 404)
        self.assertEqual(link.information, None)
        client.issues.get.assert_called_once()

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


class LinkFormattingHelpersTest(testing_config.CustomTestCase):
    """Unit tests for centralized URL formatting functions in link_helpers."""

    def test_format_chromium_bug_url__numeric_id(self):
        """It parses numeric bug IDs and creates issues.chromium.org URLs."""
        url, title = link_helpers.format_chromium_bug_url('40731275')
        self.assertEqual('https://issues.chromium.org/issues/40731275', url)
        self.assertEqual('Tracking bug #40731275', title)

    def test_format_chromium_bug_url__crbug_shortlink(self):
        """It parses crbug shortlinks and extracts bug IDs."""
        url, title = link_helpers.format_chromium_bug_url(
            'https://crbug.com/123456'
        )
        self.assertEqual('https://crbug.com/123456', url)
        self.assertEqual('Tracking bug #123456', title)

    def test_format_chromium_bug_url__issues_chromium_org(self):
        """It parses full issues.chromium.org URLs."""
        url, title = link_helpers.format_chromium_bug_url(
            'https://issues.chromium.org/issues/40146374'
        )
        self.assertEqual('https://issues.chromium.org/issues/40146374', url)
        self.assertEqual('Tracking bug #40146374', title)

    def test_format_chromium_bug_url__empty_and_non_matching(self):
        """It handles empty input and unrecognized bug URLs gracefully."""
        self.assertEqual(
            (None, None), link_helpers.format_chromium_bug_url(None)
        )
        self.assertEqual(
            (None, None), link_helpers.format_chromium_bug_url('  ')
        )
        url, title = link_helpers.format_chromium_bug_url(
            'https://bugs.example.com/123'
        )
        self.assertEqual('https://bugs.example.com/123', url)
        self.assertEqual('Tracking bug', title)

    def test_format_feature_url(self):
        """It generates canonical relative ChromeStatus feature permalinks."""
        self.assertEqual(
            '/feature/12345', link_helpers.format_feature_url(12345)
        )
        self.assertEqual(
            '/feature/54321', link_helpers.format_feature_url('54321')
        )
        self.assertIsNone(link_helpers.format_feature_url(None))

    def test_format_origin_trial_url(self):
        """It generates canonical origin trial view URLs from OT IDs or stage IDs."""
        self.assertEqual(
            'https://origintrials-staging.corp.google.com/origintrials#/view_trial/4199606652522987521',
            link_helpers.format_origin_trial_url(
                origin_trial_id='4199606652522987521'
            ),
        )
        self.assertEqual(
            'https://origintrials-staging.corp.google.com/origintrials#/view_trial/105',
            link_helpers.format_origin_trial_url(stage_id=105),
        )
        with mock.patch('settings.PROD', True):
            self.assertEqual(
                'https://developer.chrome.com/origintrials#/view_trial/4199606652522987521',
                link_helpers.format_origin_trial_url(
                    origin_trial_id='4199606652522987521'
                ),
            )
            self.assertEqual(
                'https://developer.chrome.com/origintrials#/view_trial/105',
                link_helpers.format_origin_trial_url(stage_id=105),
            )
        self.assertIsNone(link_helpers.format_origin_trial_url())
