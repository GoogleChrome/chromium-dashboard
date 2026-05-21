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

"""Tests for the metrics data handlers."""

import flask

import testing_config
from api import metrics_api

test_app = flask.Flask(__name__)


class OmahaDataHandlerTest(testing_config.CustomTestCase):
    """Tests for OmahaDataHandler."""

    def setUp(self):
        """Set up the test handler."""
        self.handler = metrics_api.OmahaDataHandler()

    def test_do_get(self):
        """User can get Omaha data metrics."""
        with test_app.test_request_context('/api/v0/omaha_data'):
            response = self.handler.do_get()

        self.assertEqual(1, len(response))
        self.assertIn('versions', response[0])
        versions = response[0]['versions']
        self.assertEqual(3, len(versions))

        channels = {v['channel']: v['version'] for v in versions}
        self.assertEqual('147.0.7727.56', channels['stable'])
        self.assertEqual('148.0.7778.5', channels['beta'])
        self.assertEqual('149.0.7779.3', channels['dev'])
