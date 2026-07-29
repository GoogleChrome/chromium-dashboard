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
        """Collect text data for h2 and h3 headings."""
        text = data.strip()
        if text and self._current_tag in ('h2', 'h3'):
            self.headings.append(text)


class ReleaseNotesHandlerTest(testing_config.CustomTestCase):
    """Unit tests for ReleaseNotesHandler SSR page controller."""

    def setUp(self):
        """Set up test environment and mock data."""
        super().setUp()
        self.handler = releasenotes.ReleaseNotesHandler()

    def test_http_cache_type_public(self):
        """It configures public HTTP caching for global CDN caching."""
        self.assertEqual(
            'public', releasenotes.ReleaseNotesHandler.HTTP_CACHE_TYPE
        )

    def test_get_template_data__specific_milestone(self):
        """It returns template context data for a specific milestone >= 151."""
        with test_app.test_request_context('/release-notes/151'):
            data = self.handler.get_template_data(milestone=151)
            self.assertEqual(151, data['milestone'])
            self.assertIn('features_by_category', data)
            self.assertIn('milestones_list', data)

    def test_get_template_data__m151_cutoff_redirect(self):
        """It returns an HTTP 302 redirect to developer.chrome.com/release-notes/<milestone> for milestones < 151."""
        with test_app.test_request_context('/release-notes/150'):
            resp = self.handler.get_template_data(milestone=150)
            self.assertEqual(302, resp.status_code)
            self.assertEqual(
                'https://developer.chrome.com/release-notes/150',
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

    def test_get_template_data__string_milestone(self):
        """It accepts string milestone parameters and coerces them to int."""
        with test_app.test_request_context('/release-notes/151'):
            data = self.handler.get_template_data(milestone='151')
            self.assertEqual(151, data['milestone'])

    def test_get_template_data__invalid_milestone_400(self):
        """It aborts HTTP 400 for non-positive milestone values or invalid strings."""
        with test_app.test_request_context('/release-notes/0'):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.get_template_data(milestone=0)
            self.assertEqual(400, cm.exception.code)

        with test_app.test_request_context('/release-notes/abc'):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.get_template_data(milestone='abc')
            self.assertEqual(400, cm.exception.code)

    def test_render_template_html_structure(self):
        """It asserts HTML elements and navigation links using built-in html.parser."""
        with test_app.test_request_context('/release-notes/151'):
            with mock.patch(
                'internals.fetchchannels.get_omaha_data',
                return_value=[
                    {
                        'versions': [
                            {'channel': 'stable', 'version': '150.0'},
                            {'channel': 'beta', 'version': '151.0'},
                            {'channel': 'dev', 'version': '152.0'},
                        ]
                    }
                ],
            ):
                data = self.handler.get_template_data(milestone=151)
                html_str = flask.render_template('release-notes.html', **data)

                parser = ReleaseNotesHTMLParser()
                parser.feed(html_str)

                # Verify subheader title
                self.assertIn('Chrome 151 Release Notes', parser.headings)

                # Verify channel quick-jump href links (stable=150, beta=151, dev=152)
                self.assertIn('/release-notes/151', parser.links)

                # Verify active button class on current milestone pill
                active_buttons = [
                    attrs
                    for tag, attrs in parser.tags
                    if tag == 'a'
                    and 'primary' in attrs.get('class', '').split()
                ]
                self.assertTrue(len(active_buttons) > 0)
