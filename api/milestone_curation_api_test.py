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

"""Tests for milestone_curation_api module."""

import json

import flask
import werkzeug.exceptions
from google.cloud import ndb

import testing_config
from api import milestone_curation_api
from internals import core_enums
from internals.core_models import MilestoneCuration
from internals.user_models import AppUser

test_app = flask.Flask(__name__)


class MilestoneCurationAPITest(testing_config.CustomTestCase):
    """Unit tests for MilestoneCurationAPI handler."""

    def setUp(self):
        """Set up test environment and users."""
        super().setUp()
        self.handler = milestone_curation_api.MilestoneCurationAPI()
        self.app_user = AppUser(email='admin@example.com', is_site_editor=True)
        self.app_user.put()
        testing_config.sign_in('admin@example.com', 12345)

        self.curation_130 = MilestoneCuration(
            id='130',
            milestone=130,
            status=core_enums.MilestoneCurationStatus.IN_REVIEW.value,
            curator_emails=['curator@example.com'],
        )
        self.curation_130.put()

    def tearDown(self):
        """Clean up test NDB entities."""
        ndb.delete_multi([self.app_user.key, self.curation_130.key])
        testing_config.sign_out()
        super().tearDown()

    def test_get__default_not_started(self):
        """It returns default PENDING state when curation entity does not exist."""
        with test_app.test_request_context('/api/v0/milestone-curation/131'):
            actual = self.handler.do_get(milestone=131)
            self.assertEqual(131, actual['milestone'])
            self.assertEqual('PENDING', actual['status'])
            self.assertEqual([], actual['curator_emails'])

    def test_get__existing_curation(self):
        """It returns stored curation entity details."""
        with test_app.test_request_context('/api/v0/milestone-curation/130'):
            actual = self.handler.do_get(milestone=130)
            self.assertEqual(130, actual['milestone'])
            self.assertEqual('IN_REVIEW', actual['status'])
            self.assertEqual(['curator@example.com'], actual['curator_emails'])

    def test_get__invalid_milestone_400(self):
        """It aborts HTTP 400 for non-positive milestone values."""
        with test_app.test_request_context('/api/v0/milestone-curation/0'):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_get(milestone=0)
            self.assertEqual(400, cm.exception.code)

    def test_patch__unauthorized_403(self):
        """It aborts HTTP 403 when user is not signed in."""
        testing_config.sign_out()
        payload = {'status': 'COMPLETED'}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/milestone-curation/130',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(milestone=130)
            self.assertEqual(403, cm.exception.code)

    def test_patch__non_editor_user_403(self):
        """It aborts HTTP 403 when user is signed in but lacks site editor or admin role."""
        testing_config.sign_in('regular_user@example.com', 54321)
        payload = {'status': 'COMPLETED'}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/milestone-curation/130',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(milestone=130)
            self.assertEqual(403, cm.exception.code)

    def test_patch__invalid_status_400(self):
        """It aborts HTTP 400 when status parameter is invalid."""
        payload = {'status': 'INVALID_STATUS'}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/milestone-curation/130',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(milestone=130)
            self.assertEqual(400, cm.exception.code)

    def test_patch__invalid_curator_emails_400(self):
        """It aborts HTTP 400 when curator_emails parameter is not a list of strings."""
        payload = {'curator_emails': 'not_a_list'}
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/milestone-curation/130',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            with self.assertRaises(werkzeug.exceptions.HTTPException) as cm:
                self.handler.do_patch(milestone=130)
            self.assertEqual(400, cm.exception.code)

    def test_patch__success_new_entity(self):
        """It successfully creates a new MilestoneCuration entity on first PATCH."""
        payload = {
            'status': 'IN_REVIEW',
            'curator_emails': ['new_curator@example.com'],
        }
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/milestone-curation/132',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            actual = self.handler.do_patch(milestone=132)
            self.assertEqual(132, actual['milestone'])
            self.assertEqual('IN_REVIEW', actual['status'])
            self.assertEqual(
                ['new_curator@example.com'], actual['curator_emails']
            )

        # Clean up created entity
        new_entity = MilestoneCuration.get_by_id('132')
        self.assertIsNotNone(new_entity)
        ndb.delete_multi([new_entity.key])

    def test_patch__success_update(self):
        """It successfully updates milestone curation status and curator emails."""
        payload = {
            'status': 'COMPLETED',
            'curator_emails': ['editor1@example.com', 'editor2@example.com'],
        }
        json_data = json.dumps(payload)

        with test_app.test_request_context(
            '/api/v0/milestone-curation/130',
            method='PATCH',
            data=json_data,
            content_type='application/json',
        ):
            actual = self.handler.do_patch(milestone=130)
            self.assertEqual(130, actual['milestone'])
            self.assertEqual('COMPLETED', actual['status'])
            self.assertEqual(
                ['editor1@example.com', 'editor2@example.com'],
                actual['curator_emails'],
            )

        # Verify Datastore entity state
        updated_entity = MilestoneCuration.get_by_id('130')
        self.assertIsNotNone(updated_entity)
        self.assertEqual('COMPLETED', updated_entity.status)
        self.assertEqual(
            ['editor1@example.com', 'editor2@example.com'],
            updated_entity.curator_emails,
        )
