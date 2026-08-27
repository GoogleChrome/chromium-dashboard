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

"""Tests for the FeatureDetailHandler in pages/featuredetail.py."""

# ruff: noqa: I001
import testing_config  # isort: split
import flask
import werkzeug.exceptions

from internals import core_enums
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from pages import featuredetail

import settings

test_app = flask.Flask(
    __name__,
    template_folder=settings.get_flask_template_path(),
)
test_app.secret_key = 'test_session_secret'


class FeatureDetailHandlerTest(testing_config.CustomTestCase):
    """Tests for the FeatureDetailHandler."""

    def setUp(self) -> None:
        """Set up a test feature and its stages."""
        self.handler = featuredetail.FeatureDetailHandler()

        # 1. Create a feature with basic metadata.
        self.fe = FeatureEntry(
            name='SSR Test Feature',
            summary='Detailed test summary for SSR',
            category=1,
            feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
            intent_stage=core_enums.INTENT_IMPLEMENT,
            motivation='Strong motivation for testing',
            spec_link='https://example.com/spec',
            owner_emails=['test_owner@example.com'],
            editor_emails=['test_editor@example.com'],
            cc_emails=['test_cc@example.com'],
            devrel_emails=['test_devrel@example.com'],
            feature_notes='Internal feature notes',
            unlisted=False,
            breaking_change=False,
            confidential=False,
        )
        self.fe.put()
        self.feature_id = self.fe.key.integer_id()

        # 2. Add an Origin Trial Stage with extensions and milestones.
        self.ot_stage = Stage(
            feature_id=self.feature_id,
            stage_type=core_enums.STAGE_BLINK_ORIGIN_TRIAL,
            display_name='Testing Origin Trial',
            intent_thread_url='https://example.com/intent-ot',
            milestones=MilestoneSet(
                desktop_first=110,
                desktop_last=115,
                android_first=110,
                android_last=115,
                webview_first=110,
                webview_last=115,
            ),
            experiment_goals='Test OT goals',
            experiment_risks='Test OT risks',
        )
        self.ot_stage.put()
        self.ot_stage_id = self.ot_stage.key.integer_id()

        self.ot_extension = Stage(
            feature_id=self.feature_id,
            stage_type=core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
            ot_stage_id=self.ot_stage_id,
            intent_thread_url='https://example.com/intent-extend',
            milestones=MilestoneSet(
                desktop_last=120,
            ),
            experiment_extension_reason='Need more time to test OT extension',
        )
        self.ot_extension.put()

        # 3. Add a Prototype Stage.
        self.proto_stage = Stage(
            feature_id=self.feature_id,
            stage_type=core_enums.STAGE_BLINK_PROTOTYPE,
            display_name='Testing Prototype Step',
        )
        self.proto_stage.put()

        # 4. Add a Prepare to Ship Stage.
        self.ship_stage = Stage(
            feature_id=self.feature_id,
            stage_type=core_enums.STAGE_BLINK_SHIPPING,
            display_name='Testing Ship Step',
            intent_thread_url='https://example.com/intent-ship',
            milestones=MilestoneSet(
                desktop_first=125,
                android_first=125,
                ios_first=125,
                webview_first=125,
            ),
        )
        self.ship_stage.put()

        self.request_path = f'/feature-ssr/{self.feature_id}'

    def tearDown(self) -> None:
        """Clean up the seeded datastore entities."""
        for stage in Stage.query(Stage.feature_id == self.feature_id):
            stage.key.delete()
        self.fe.key.delete()

    def test_get_template_data__success(self) -> None:
        """Retrieve and validate the aggregated SSR template data dictionary."""
        with test_app.test_request_context(self.request_path):
            data = self.handler.get_template_data(feature_id=self.feature_id)

        self.assertIsInstance(data, dict)
        self.assertIn('metadata', data)
        self.assertIn('metadata_form', data)
        self.assertIn('stages', data)
        self.assertIn('field_specs', data)

        # Validate Metadata section
        meta = data['metadata']
        self.assertNotIn('metadata_form', meta)
        self.assertNotIn('form', meta)
        self.assertEqual(data['metadata_form']['name'], 'Feature metadata')

        self.assertEqual(meta['id'], self.feature_id)
        self.assertEqual(meta['name'], 'SSR Test Feature')
        self.assertEqual(meta['summary'], 'Detailed test summary for SSR')
        self.assertEqual(meta['owner'], ['test_owner@example.com'])
        self.assertEqual(meta['editors'], ['test_editor@example.com'])
        self.assertEqual(meta['cc_recipients'], ['test_cc@example.com'])
        self.assertEqual(meta['devrel'], ['test_devrel@example.com'])
        self.assertEqual(meta['comments'], 'Internal feature notes')
        self.assertEqual(
            meta['feature_type_int'], core_enums.FEATURE_TYPE_INCUBATE_ID
        )
        self.assertEqual(meta['intent_stage_int'], core_enums.INTENT_IMPLEMENT)

        # Validate Stages list
        stages = data['stages']
        self.assertEqual(len(stages), 4)

        # Stage 1: Origin Trial
        ot = next(
            s
            for s in stages
            if s['stage_type'] == core_enums.STAGE_BLINK_ORIGIN_TRIAL
        )
        self.assertIn('stage_form', ot)
        self.assertNotIn('form', ot)
        self.assertEqual(ot['stage_form']['name'], 'Origin trial')

        self.assertEqual(ot['display_name'], 'Testing Origin Trial')
        self.assertEqual(
            ot['intent_to_experiment_url'], 'https://example.com/intent-ot'
        )
        self.assertEqual(ot['experiment_goals'], 'Test OT goals')
        self.assertEqual(ot['experiment_risks'], 'Test OT risks')
        self.assertEqual(ot['ot_milestone_desktop_start'], 110)
        self.assertEqual(ot['ot_milestone_desktop_end'], 115)
        self.assertEqual(ot['ot_milestone_android_start'], 110)
        self.assertEqual(ot['ot_milestone_android_end'], 115)
        self.assertEqual(ot['ot_milestone_webview_start'], 110)
        self.assertEqual(ot['ot_milestone_webview_end'], 115)

        # Stage 2: OT Extension
        ext = next(
            s
            for s in stages
            if s['stage_type'] == core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL
        )
        self.assertIn('stage_form', ext)
        self.assertEqual(ext['stage_form']['name'], 'Trial extension')

        self.assertEqual(
            ext['experiment_extension_reason'],
            'Need more time to test OT extension',
        )
        self.assertEqual(
            ext['intent_to_extend_experiment_url'],
            'https://example.com/intent-extend',
        )
        self.assertEqual(ext['extension_desktop_last'], 120)

        # Stage 3: Prepare to Ship
        ship = next(
            s
            for s in stages
            if s['stage_type'] == core_enums.STAGE_BLINK_SHIPPING
        )
        self.assertIn('stage_form', ship)
        self.assertEqual(ship['stage_form']['name'], 'Prepare to ship')

        self.assertEqual(ship['display_name'], 'Testing Ship Step')
        self.assertEqual(
            ship['intent_to_ship_url'], 'https://example.com/intent-ship'
        )
        self.assertEqual(ship['shipped_milestone'], 125)
        self.assertEqual(ship['shipped_android_milestone'], 125)
        self.assertEqual(ship['shipped_ios_milestone'], 125)
        self.assertEqual(ship['shipped_webview_milestone'], 125)

        # Stage 4: Prototype
        proto = next(
            s
            for s in stages
            if s['stage_type'] == core_enums.STAGE_BLINK_PROTOTYPE
        )
        self.assertIn('stage_form', proto)
        self.assertEqual(proto['stage_form']['name'], 'Prototype a solution')

        self.assertEqual(proto['display_name'], 'Testing Prototype Step')
        self.assertEqual(proto['motivation'], 'Strong motivation for testing')
        self.assertEqual(proto['spec_link'], 'https://example.com/spec')

    def test_get_template_data__not_found(self) -> None:
        """Querying a non-existent feature ID aborts with 404."""
        with test_app.test_request_context('/feature-ssr/99999'):
            with self.assertRaises(werkzeug.exceptions.NotFound):
                self.handler.get_template_data(feature_id=99999)

    def test_get_http_integration(self) -> None:
        """A GET request successfully server-side renders the feature-detail.html Jinja2 template."""
        with test_app.test_request_context(self.request_path):
            rendered_html, status, headers = self.handler.get(
                feature_id=self.feature_id
            )

        self.assertEqual(status, 200)
        self.assertIsInstance(rendered_html, str)

        # Validate that the Overview section is rendered and open
        self.assertIn('<details open>', rendered_html)
        self.assertIn('<summary>Overview</summary>', rendered_html)
        self.assertIn('Detailed test summary for SSR', rendered_html)
        self.assertIn('test_owner@example.com', rendered_html)

        # Validate Metadata form is rendered
        self.assertIn(
            '<summary>Feature metadata</summary>',
            rendered_html,
        )

        # Validate each of the Stage Forms are rendered with their ordered fields
        self.assertIn(
            '<summary>Prototype a solution</summary>',
            rendered_html,
        )
        self.assertIn('<summary>Origin trial</summary>', rendered_html)
        self.assertIn('<summary>Trial extension</summary>', rendered_html)
        self.assertIn('<summary>Prepare to ship</summary>', rendered_html)

        # Validate stage-specific field values and ordered dt/dd rendering
        self.assertIn('Test OT goals', rendered_html)
        self.assertIn('Need more time to test OT extension', rendered_html)
        self.assertIn('https://example.com/intent-ship', rendered_html)
        self.assertIn('125', rendered_html)

        # Validate that ChromeStatus base template shell components are included
        self.assertIn('<chromedash-header', rendered_html)
        self.assertIn('<chromedash-drawer', rendered_html)
        self.assertIn('<chromedash-footer', rendered_html)
        self.assertIn(
            "document.body.classList.remove('loading');", rendered_html
        )
