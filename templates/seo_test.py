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

"""Unit tests for shared SEO sub-templates (templates/seo/)."""

import testing_config  # noqa: F401, I001

from html.parser import HTMLParser

import flask

from framework import seo

test_app = flask.Flask(__name__, template_folder='../templates')


class SEOHTMLParser(HTMLParser):
    """Collector parser using Python's built-in html.parser library."""

    def __init__(self) -> None:
        """Initialize parser attributes."""
        super().__init__()
        self.tags: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        """Collect start tags and attributes."""
        attr_dict = {k: (v or '') for k, v in attrs}
        self.tags.append((tag, attr_dict))


class SEOSubTemplatesTest(testing_config.CustomTestCase):
    """Unit tests for reusable SEO Jinja2 sub-templates."""

    def _get_meta_content(
        self, html_str: str, property_name: str
    ) -> str | None:
        """Helper to extract <meta property="..."> content attribute."""
        parser = SEOHTMLParser()
        parser.feed(html_str)
        for tag, attrs in parser.tags:
            if tag == 'meta' and attrs.get('property') == property_name:
                return attrs.get('content')
        return None

    def test_open_graph_sub_template(self):
        """It renders Open Graph meta tags cleanly with custom context inputs."""
        meta = seo.Metadata(
            canonical_url='https://chromestatus.com/feature/123',
            seo_title='Custom Title',
            seo_description='Custom Description',
            site_logo_url='https://chromestatus.com/static/img/crstatus_192.png',
        )
        with test_app.test_request_context('/'):
            html_str = flask.render_template(
                'seo/_open_graph.html', seo=meta.to_dict()
            )
            self.assertEqual(
                'Custom Title', self._get_meta_content(html_str, 'og:title')
            )
            self.assertEqual(
                'https://chromestatus.com/feature/123',
                self._get_meta_content(html_str, 'og:url'),
            )

    def test_open_graph_fallbacks(self):
        """It falls back to page_title when seo.seo_title is omitted."""
        with test_app.test_request_context('/'):
            html_str = flask.render_template(
                'seo/_open_graph.html', page_title='Page Title Fallback'
            )
            self.assertEqual(
                'Page Title Fallback',
                self._get_meta_content(html_str, 'og:title'),
            )

    def test_json_ld_sub_template(self):
        """It renders Schema.org JSON-LD structured data on custom inputs."""
        meta = seo.Metadata(
            canonical_url='https://chromestatus.com/feature/123',
            seo_title='Feature Detail',
            seo_description='Feature Description',
            schema_type='SoftwareApplication',
        )
        with test_app.test_request_context('/'):
            html_str = flask.render_template(
                'seo/_json_ld.html', seo=meta.to_dict()
            )
            self.assertIn('"@context": "https://schema.org"', html_str)
            self.assertIn('"@type": "SoftwareApplication"', html_str)
            self.assertIn('"name": "Feature Detail"', html_str)

    def test_primary_meta_sub_template(self):
        """It renders canonical link and includes open graph and json-ld sub-templates."""
        meta = seo.Metadata(
            canonical_url='https://chromestatus.com/release-notes/151',
            seo_title='Release Notes',
            seo_description='Release Notes Description',
        )
        with test_app.test_request_context('/'):
            html_str = flask.render_template(
                'seo/_meta.html', seo=meta.to_dict()
            )
            self.assertIn(
                '<link rel="canonical" href="https://chromestatus.com/release-notes/151">',
                html_str,
            )
            self.assertEqual(
                'Release Notes', self._get_meta_content(html_str, 'og:title')
            )
            self.assertIn('"@context": "https://schema.org"', html_str)
