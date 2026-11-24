# -*- coding: utf-8 -*-
# Copyright 2026 Google Inc.
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

"""Tests for the gates_api module."""

import flask
import werkzeug.exceptions

import testing_config  # Must be imported before the module under test.
from api import gates_api
from framework import rediscache
from internals import approval_defs, core_enums, user_models
from internals.review_models import GateDef

test_app = flask.Flask(__name__)


class GatesAdminAPITest(testing_config.CustomTestCase):
    """Tests for GatesAdminAPI."""

    def setUp(self):
        """Set up test admin user, normal user, and handler."""
        self.admin_user = user_models.AppUser(
            email='admin@example.com', is_admin=True
        )
        self.admin_user.put()
        self.normal_user = user_models.AppUser(
            email='user@example.com', is_admin=False
        )
        self.normal_user.put()
        for gate_def in GateDef.query():
            gate_def.key.delete()
        self.handler = gates_api.GatesAdminAPI()
        self._clear_cache()

    def tearDown(self):
        """Clean up datastore entities and cache."""
        testing_config.sign_out()
        for entity in user_models.AppUser.query():
            entity.key.delete()
        for gate_def in GateDef.query():
            gate_def.key.delete()
        self._clear_cache()

    def _clear_cache(self):
        for gate_type in approval_defs.APPROVAL_FIELDS_BY_ID:
            cache_key = '%s|%s' % (approval_defs.APPROVERS_CACHE_KEY, gate_type)
            rediscache.delete(cache_key)

    def test_get__anon_forbidden(self):
        """Anonymous users are rejected with 403."""
        testing_config.sign_out()
        with test_app.test_request_context('/api/v0/gates'):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_get()

    def test_get__non_admin_forbidden(self):
        """Non-admin users are rejected with 403."""
        testing_config.sign_in('user@example.com', 123)
        with test_app.test_request_context('/api/v0/gates'):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_get()

    def test_get__admin_returns_all_gates(self):
        """Site admins receive all gate definitions with approver details."""
        GateDef(
            gate_type=core_enums.GATE_PRIVACY_SHIP,
            approvers=['privacy1@example.com', 'privacy2@example.com'],
            rotation_url='https://rotation.example.com/privacy',
        ).put()
        testing_config.sign_in('admin@example.com', 1)

        with test_app.test_request_context('/api/v0/gates'):
            actual = self.handler.do_get()

        self.assertIn('gates', actual)
        gates_by_type = {g['gate_type']: g for g in actual['gates']}
        self.assertEqual(
            set(gates_by_type.keys()),
            set(approval_defs.APPROVAL_FIELDS_BY_ID.keys()),
        )

        privacy_gate = gates_by_type[core_enums.GATE_PRIVACY_SHIP]
        self.assertEqual(privacy_gate['name'], 'Privacy Ship Review')
        self.assertEqual(privacy_gate['team_name'], 'Privacy')
        self.assertEqual(privacy_gate['rule'], approval_defs.ONE_LGTM)
        self.assertTrue(privacy_gate['is_editable'])
        self.assertIsNone(privacy_gate['approvers_url'])
        self.assertEqual(
            privacy_gate['approvers'],
            ['privacy1@example.com', 'privacy2@example.com'],
        )
        self.assertEqual(
            privacy_gate['rotation_url'],
            'https://rotation.example.com/privacy',
        )
        self.assertEqual(
            privacy_gate['escalation_email'],
            'chrome-privacy-owp-rotation@google.com',
        )
        self.assertEqual(privacy_gate['slo_initial_response'], 6)
        self.assertEqual(
            privacy_gate['slo_resolve'],
            approval_defs.DEFAULT_SLO_RESOLVE_LIMIT,
        )

        api_ship_gate = gates_by_type[core_enums.GATE_API_SHIP]
        self.assertFalse(api_ship_gate['is_editable'])
        self.assertEqual(
            api_ship_gate['approvers_url'], approval_defs.API_OWNERS_URL
        )
        self.assertEqual(api_ship_gate['approvers'], ['example@chromium.org'])

    def test_get__with_id_method_not_allowed(self):
        """GET on /api/v0/gates/<id> is rejected with 405."""
        testing_config.sign_in('admin@example.com', 1)
        with test_app.test_request_context(
            f'/api/v0/gates/{core_enums.GATE_PRIVACY_SHIP}'
        ):
            with self.assertRaises(werkzeug.exceptions.MethodNotAllowed):
                self.handler.do_get(id=core_enums.GATE_PRIVACY_SHIP)

    def test_patch__anon_forbidden(self):
        """Anonymous users cannot PATCH gate definitions."""
        testing_config.sign_out()
        with test_app.test_request_context(
            f'/api/v0/gates/{core_enums.GATE_PRIVACY_SHIP}',
            json={'approvers': ['a@example.com']},
        ):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_patch(id=core_enums.GATE_PRIVACY_SHIP)

    def test_patch__non_admin_forbidden(self):
        """Non-admin users cannot PATCH gate definitions."""
        testing_config.sign_in('user@example.com', 123)
        with test_app.test_request_context(
            f'/api/v0/gates/{core_enums.GATE_PRIVACY_SHIP}',
            json={'approvers': ['a@example.com']},
        ):
            with self.assertRaises(werkzeug.exceptions.Forbidden):
                self.handler.do_patch(id=core_enums.GATE_PRIVACY_SHIP)

    def test_patch__unknown_gate_not_found(self):
        """Unknown gate type returns 404."""
        testing_config.sign_in('admin@example.com', 1)
        with test_app.test_request_context(
            '/api/v0/gates/99999',
            json={'approvers': ['a@example.com']},
        ):
            with self.assertRaises(werkzeug.exceptions.NotFound):
                self.handler.do_patch(id=99999)

    def test_patch__non_editable_gate_rejected(self):
        """API Owners gates cannot be edited via PATCH."""
        testing_config.sign_in('admin@example.com', 1)
        with test_app.test_request_context(
            f'/api/v0/gates/{core_enums.GATE_API_SHIP}',
            json={'approvers': ['a@example.com']},
        ):
            with self.assertRaises(werkzeug.exceptions.BadRequest):
                self.handler.do_patch(id=core_enums.GATE_API_SHIP)

    def test_patch__invalid_approvers_rejected(self):
        """Non-list or invalid email entries return 400."""
        testing_config.sign_in('admin@example.com', 1)

        with test_app.test_request_context(
            f'/api/v0/gates/{core_enums.GATE_ENTERPRISE_SHIP}',
            json={'approvers': 'not-a-list'},
        ):
            with self.assertRaises(werkzeug.exceptions.BadRequest):
                self.handler.do_patch(id=core_enums.GATE_ENTERPRISE_SHIP)

        with test_app.test_request_context(
            f'/api/v0/gates/{core_enums.GATE_ENTERPRISE_SHIP}',
            json={'approvers': ['valid@example.com', 'not-an-email']},
        ):
            with self.assertRaises(werkzeug.exceptions.BadRequest):
                self.handler.do_patch(id=core_enums.GATE_ENTERPRISE_SHIP)

    def test_patch__updates_ndb_and_invalidates_cache(self):
        """PATCH saves cleaned approvers to NDB and clears rediscache."""
        gate_type = core_enums.GATE_ENTERPRISE_SHIP
        GateDef(
            gate_type=gate_type,
            approvers=['old@example.com'],
        ).put()
        # Prime cache with old approvers.
        self.assertEqual(
            approval_defs.get_approvers(gate_type), ['old@example.com']
        )

        testing_config.sign_in('admin@example.com', 1)
        with test_app.test_request_context(
            f'/api/v0/gates/{gate_type}',
            json={
                'approvers': [
                    '  new1@example.com ',
                    '',
                    'new2@example.com',
                    'new1@example.com',
                ]
            },
        ):
            actual = self.handler.do_patch(id=gate_type)

        self.assertEqual(
            actual['approvers'], ['new1@example.com', 'new2@example.com']
        )
        self.assertTrue(actual['is_editable'])

        # Verify NDB was updated.
        updated_def = GateDef.get_gate_def(gate_type)
        self.assertEqual(
            updated_def.approvers, ['new1@example.com', 'new2@example.com']
        )
        # Verify cache was invalidated and get_approvers returns new list.
        self.assertEqual(
            approval_defs.get_approvers(gate_type),
            ['new1@example.com', 'new2@example.com'],
        )
