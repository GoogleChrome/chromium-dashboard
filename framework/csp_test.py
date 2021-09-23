# Copyright 2020 Google Inc.
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




import unittest
import testing_config  # Must be imported before the module under test.

import flask
import mock
import werkzeug.exceptions  # Flask HTTP stuff.

from framework import csp

test_app = flask.Flask(__name__)


class CspTest(unittest.TestCase):

  def setUp(self):
    csp.ENABLED = True
    csp.REPORT_ONLY = False
    csp.REPORT_URI = 'test'

    self.test_policy = {
        'upgrade-insecure-requests': '',
        'default-src': ["'self'"],
        'base-uri': ["'none'"],
        'object-src': ["'none'"],
        'img-src': ["'self'", 'https:', 'data:'],
    }

  def test_get_nonce(self):
    """Many different nonce values are all different."""
    nonces = []
    for _ in range(1000):
      nonces.append(csp.get_nonce())

    self.assertEqual(len(nonces), len(set(nonces)))

  @mock.patch('framework.csp.USE_NONCE_ONLY_POLICY', False)
  def test_get_default_policy__strict(self):
    """We can get the regular strict policy."""
    policy = csp.get_default_policy(nonce='12345')
    self.assertCountEqual(list(csp.DEFAULT_POLICY.keys()), list(policy.keys()))
    self.assertIn('strict-dynamic', policy['script-src'])
    self.assertIn("'nonce-12345'", policy['script-src'])

  @mock.patch('framework.csp.USE_NONCE_ONLY_POLICY', True)
  def test_get_default_policy__strict(self):
    """We can get the even stricter nonce-only policy."""
    policy = csp.get_default_policy(nonce='12345')
    self.assertCountEqual(list(csp.NONCE_ONLY_POLICY.keys()), list(policy.keys()))
    self.assertNotIn('strict-dynamic', policy['script-src'])
    self.assertIn("'nonce-12345'", policy['script-src'])

  @mock.patch('framework.csp.REPORT_ONLY', False)
  def test_get_csp_header_key__enforced(self):
    """We can get the header used when the policy."""
    self.assertEqual(
        csp.HEADER_KEY_ENFORCE,
        csp.get_csp_header_key())

  @mock.patch('framework.csp.REPORT_ONLY', True)
  def test_get_csp_header_key__enforced(self):
    """We can get the header used when only reporting violations."""
    self.assertEqual(
        csp.HEADER_KEY_REPORT_ONLY,
        csp.get_csp_header_key())

  def test_build_policy(self):
    """Each part of the CSP policy is in the header."""
    expected_directives = [
        'upgrade-insecure-requests', "default-src 'self'", "base-uri 'none'",
        "object-src 'none'", "img-src 'self' https: data:", 'report-uri test'
    ]
    result = csp.build_policy(self.test_policy)
    result_directives = [x.strip() for x in result.split(';')]
    self.assertCountEqual(expected_directives, result_directives)

  @mock.patch('framework.csp.REPORT_ONLY', True)
  def test_get_headers(self):
    """We can get a complete header dict."""
    actual = csp.get_headers('12345')
    self.assertIn('12345', actual[csp.HEADER_KEY_REPORT_ONLY])


class CspReporttest(unittest.TestCase):

  @mock.patch('logging.error')
  def test_report_handler(self, mock_error):
    """The report handler logs something for each request."""
    with test_app.test_request_context('/csp', data='12345', method='POST'):
      actual = csp.report_handler()

    self.assertEqual('', actual)
    mock_error.assert_called_once()
