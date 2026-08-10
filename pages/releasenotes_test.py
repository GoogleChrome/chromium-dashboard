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

"""Tests for pages/releasenotes module."""

from html.parser import HTMLParser
from unittest import mock

import flask
import werkzeug.exceptions

import testing_config
from pages import releasenotes

test_app = flask.Flask(__name__, template_folder='../templates')


class ReleaseNotesHTMLParser(HTMLParser):
    """Collector parser using Python's built-in html.parser library."""

    def __init__(self) -> None:
        """Initialize parser attributes."""
        super().__init__()
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.links: list[str] = []
        self.headings: list[str] = []
        self._current_tag: str | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        """Collect start tags, attributes, and href links."""
        attr_dict = {k: (v or '') for k, v in attrs}
        self.tags.append((tag, attr_dict))
        if tag == 'a' and 'href' in attr_dict:
            self.links.append(attr_dict['href'])
        self._current_tag = tag

    def handle_data(self, data: str) -> None:
        """Collect text data for h1, h2, and h3 headings."""
        text = data.strip()
        if text and self._current_tag in ('h1', 'h2', 'h3'):
            self.headings.append(text)


class ReleaseNotesHandlerTest(testing_config.CustomTestCase):
    """Unit tests for ReleaseNotesHandler SSR page controller."""

    def setUp(self):
        """Set up test environment and mock data."""
        super().setUp()
        self.handler = releasenotes.ReleaseNotesHandler()
        self.mock_features = [
            {
                'id': 101,
                'name': 'Sample CSS Feature',
                'summary': 'Summary of CSS feature',
                'category_name': 'CSS',
                'doc_links': ['https://example.com/spec'],
            }
        ]
        patcher = mock.patch(
            'internals.feature_helpers.get_developer_release_notes_features',
            return_value=self.mock_features,
        )
        self.addCleanup(patcher.stop)
        self.mock_get_features = patcher.start()

    def test_http_cache_type_private(self):
        """It configures private HTTP caching to prevent CDN caching of XSRF tokens."""
        self.assertEqual(
            'private', releasenotes.ReleaseNotesHandler.HTTP_CACHE_TYPE
        )

    def test_get_template_data__specific_milestone(self):
        """It returns template context data for a specific milestone >= 151."""
        with test_app.test_request_context('/release-notes/151'):
            data = self.handler.get_template_data(milestone=151)
            self.assertEqual(151, data['milestone'])
            self.assertEqual(150, data['prev_milestone'])
            self.assertEqual(152, data['next_milestone'])
            self.assertTrue(data['is_min_ssr_milestone'])
            self.assertIn('features_by_category', data)
            self.assertIn('milestones_list', data)
            self.assertEqual(124, data['milestones_list'][-1])
            self.assertIn('seo', data)
            self.assertEqual(
                'Chrome 151 Release Notes', data['seo']['seo_title']
            )

    def test_get_template_data__m124_to_m150_redirect(self):
        """It returns an HTTP 302 redirect to developer.chrome.com/release-notes/<milestone> for 124 <= m < 151."""
        with test_app.test_request_context('/release-notes/150'):
            resp = self.handler.get_template_data(milestone=150)
            self.assertEqual(302, resp.status_code)
            self.assertEqual(
                'https://developer.chrome.com/release-notes/150',
                resp.headers['Location'],
            )

        with test_app.test_request_context('/release-notes/124'):
            resp = self.handler.get_template_data(milestone=124)
            self.assertEqual(302, resp.status_code)
            self.assertEqual(
                'https://developer.chrome.com/release-notes/124',
                resp.headers['Location'],
            )

    def test_get_template_data__pre_m124_archive_redirect(self):
        """It returns an HTTP 302 redirect to developer.chrome.com/release-notes archive root for m < 124."""
        for pre_124_m in (1, 100, 120, 123):
            with test_app.test_request_context(f'/release-notes/{pre_124_m}'):
                resp = self.handler.get_template_data(milestone=pre_124_m)
                self.assertEqual(302, resp.status_code)
                self.assertEqual(
                    'https://developer.chrome.com/release-notes',
                    resp.headers['Location'],
                )

    def test_get_template_data__default_milestone(self):
        """It defaults to current stable milestone when no milestone param is provided."""
        with test_app.test_request_context('/release-notes'):
            with mock.patch(
                'internals.fetchchannels.get_current_stable_milestone',
                return_value=151,
            ):
                data = self.handler.get_template_data()
                self.assertEqual(151, data['milestone'])

    def test_get_template_data__upstream_omaha_downtime_fallback(self):
        """It gracefully falls back to MIN_SSR_RELEASE_NOTES_MILESTONE if Omaha returns 0."""
        with test_app.test_request_context('/release-notes'):
            with mock.patch(
                'internals.fetchchannels.get_current_stable_milestone',
                return_value=0,
            ):
                data = self.handler.get_template_data()
                self.assertEqual(151, data['milestone'])
                self.assertEqual(151, data['stable_milestone'])
                self.assertEqual(153, data['milestones_list'][0])
                self.assertEqual(124, data['milestones_list'][-1])

    def test_get_template_data__string_milestone(self):
        """It accepts string milestone parameters and coerces them to int."""
        with test_app.test_request_context('/release-notes/151'):
            data = self.handler.get_template_data(milestone='151')
            self.assertEqual(151, data['milestone'])

    def test_get_template_data__invalid_milestone_400(self):
        """It aborts HTTP 400 for non-positive milestone values or invalid strings."""
        for invalid_val in (0, -1, -150, '-5', 'abc'):
            with test_app.test_request_context(f'/release-notes/{invalid_val}'):
                with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                    self.handler.get_template_data(milestone=invalid_val)
                self.assertEqual(400, cm.exception.code)

    def test_get_template_data__out_of_range_milestone_404(self):
        """It aborts HTTP 404 for excessively large out-of-range future milestones."""
        with test_app.test_request_context('/release-notes/9999'):
            with mock.patch(
                'internals.fetchchannels.get_current_stable_milestone',
                return_value=151,
            ):
                with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                    self.handler.get_template_data(milestone=9999)
                self.assertEqual(404, cm.exception.code)

    def test_render_template_html_structure(self):
        """It asserts HTML elements, steppers, and jump box using built-in html.parser."""
        with test_app.test_request_context('/release-notes/151'):
            data = self.handler.get_template_data(milestone=151)
            html_str = flask.render_template('release-notes.html', **data)

            parser = ReleaseNotesHTMLParser()
            parser.feed(html_str)

            # Verify subheader title (rendered as h1)
            self.assertIn('Chrome 151 Release Notes', parser.headings)

            # Verify previous and next stepper links
            self.assertIn('/release-notes/150', parser.links)
            self.assertIn('/release-notes/152', parser.links)

            # Verify archival notice link on M151
            self.assertIn(
                'https://developer.chrome.com/release-notes', parser.links
            )
