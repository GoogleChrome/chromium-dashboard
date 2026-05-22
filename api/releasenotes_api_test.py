# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the releasenotes_api module."""

import testing_config  # isort: split

import flask
import werkzeug.exceptions  # Flask HTTP stuff.

from api import releasenotes_api

test_app = flask.Flask(__name__)


class ReleaseNotesL10nAPITest(testing_config.CustomTestCase):
    """Tests for ReleaseNotesL10nAPI."""

    def setUp(self):
        """Set up the test case."""
        self.handler = releasenotes_api.ReleaseNotesL10nAPI()
        self.request_path = '/api/v0/releasenotes/l10n'

    def test_do_get__missing_start(self):
        """It aborts with 400 if startMilestone is missing."""
        path = self.request_path + '?endMilestone=120'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)
            self.assertEqual(
                '400 Bad Request: Missing startMilestone', str(cm.exception)
            )

    def test_do_get__missing_end(self):
        """It aborts with 400 if endMilestone is missing."""
        path = self.request_path + '?startMilestone=110'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)
            self.assertEqual(
                '400 Bad Request: Missing endMilestone', str(cm.exception)
            )

    def test_do_get__invalid_start(self):
        """It aborts with 400 if startMilestone is not an integer."""
        path = self.request_path + '?startMilestone=abc&endMilestone=120'
        with test_app.test_request_context(path):
            with self.assertRaises(werkzeug.exceptions.BadRequest) as cm:
                self.handler.do_get()
            self.assertEqual(400, cm.exception.code)

    def test_do_get__success(self):
        """It returns an empty ReleaseNotesL10nResponse on success."""
        path = self.request_path + '?startMilestone=110&endMilestone=120'
        with test_app.test_request_context(path):
            actual = self.handler.do_get()
        self.assertEqual({'features': [], 'descriptions': {}}, actual)
