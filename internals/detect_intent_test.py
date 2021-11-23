# Copyright 2021 Google Inc.
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

import testing_config  # Must be imported first

import flask
import mock
import werkzeug

from internals import models
from internals import approval_defs
from internals import detect_intent

test_app = flask.Flask(__name__)


class FunctionTest(testing_config.CustomTestCase):

  def test_detect_field(self):
    """We can detect intent thread type by subject line."""
    test_data = {
      approval_defs.PrototypeApproval: [
          'Intent to Prototype: Something cool',
          'Re: Re:Intent to Prototype: Something cool',
          'intent to prototype: something cool',
          'Intent to Prototype request for Something cool',
        ],
      approval_defs.ExperimentApproval: [
          'Intent to Experiment: Something cool',
          'intent to experiment: something cool',
          'Intent to experiment on Something cool',
      ],
      approval_defs.ExtendExperimentApproval: [
          'Intent to Continue Experiment: Something cool',
          'Intent to Extend Experiment: Something cool',
          'Intent to Continue Experiment: Something cool',
      ],
      approval_defs.ShipApproval: [
          'Intent to Ship: Something cool',
          'intent to ship: something cool',
          'Intent to ship request for Something cool',
        ],
      None: [
          'Status of something cool',
          '[meta] Are Intent to Prototype threads too long?',
          'PSA: We are making changes',
          'Why is feature so cool?',
          'Save the date for BlinkOn',
        ],
     }

    for expected, subjects in test_data.items():
      for subject in subjects:
        with self.subTest(subject=subject):
          actual = detect_intent.detect_field(subject)
          self.assertEqual(expected, actual)

  def test_detect_feature_id__generated(self):
    """We can parse the feature ID from a link in the generated body."""
    body = (
        'blah blah blah\n'
        'Link to entry on the Chrome Platform Status\n'
        'https://www.chromestatus.com/feature/5144822362931200\n'
        'blah blah blah')
    self.assertEqual(
        5144822362931200,
        detect_intent.detect_feature_id(body))

  def test_detect_feature_id__alternative(self):
    """We can parse the feature ID from another common link."""
    body = (
        'blah blah blah\n'
        'Entry on the feature dashboard\n'
        'https://www.chromestatus.com/feature/5144822362931200\n'
        'blah blah blah')
    self.assertEqual(
        5144822362931200,
        detect_intent.detect_feature_id(body))

  def test_detect_thread_url(self):
    """We can parse the thread archive link from the body footer."""
    footer = (
        'You received this message because you are subscribed to the Google '
        'Groups "blink-dev" group.\n'
        'To unsubscribe from this group and stop receiving emails from it,'
        'send an email to blink-dev+unsubscribe@chromium.org.\n'
        'To view this discussion on the web visit https://groups.google.com'
        '/a/chromium.org/d/msgid/blink-dev/CAMO6jDPGfXfE5z6hJcWO112zX3We'
        '-oNTb%2BZjiJk%2B6RNb9%2Bv05w%40mail.gmail.com.')
    self.assertEqual(
        ('https://groups.google.com'
         '/a/chromium.org/d/msgid/blink-dev/CAMO6jDPGfXfE5z6hJcWO112zX3We'
         '-oNTb%2BZjiJk%2B6RNb9%2Bv05w%40mail.gmail.com'),
        detect_intent.detect_thread_url(footer))

    def test_detect_lgtm__good(self):
      """We can find an LGTM in the email body text."""
      self.assertTrue(detect_intent.detect_lgtm('LGTM'))
      self.assertTrue(detect_intent.detect_lgtm('Lgtm'))
      self.assertTrue(detect_intent.detect_lgtm('lgtm'))
      self.assertTrue(detect_intent.detect_lgtm('LGTM1'))
      self.assertTrue(detect_intent.detect_lgtm('LGTM2'))
      self.assertTrue(detect_intent.detect_lgtm('LGTM3'))

      self.assertTrue(detect_intent.detect_lgtm('LGTM with nits'))
      self.assertTrue(detect_intent.detect_lgtm('This LGTM!'))
      self.assertTrue(detect_intent.detect_lgtm('Sounds good! LGTM2'))
      self.assertTrue(detect_intent.detect_lgtm('LGTM to extend M94-M97'))

      self.assertTrue(detect_intent.detect_lgtm('''

        LGTM

        Thanks for all your work.
      '''))

    def test_detect_lgtm__bad(self):
      """We don't mistakenly count a message as an LGTM ."""
      self.assertFalse(detect_intent.detect_lgtm("> LGTM from other approver"))

      self.assertFalse(detect_intent.detect_lgtm('LG'))
      self.assertFalse(detect_intent.detect_lgtm('Looks good to me'))

      self.assertFalse(detect_intent.detect_lgtm('Almost LGTM'))
      self.assertFalse(detect_intent.detect_lgtm('This is not an LGTM'))
      self.assertFalse(detect_intent.detect_lgtm('Not LGTM yet'))
      self.assertFalse(detect_intent.detect_lgtm('You still need LGTM'))
      self.assertFalse(detect_intent.detect_lgtm("You're missing LGTM"))
      self.assertFalse(detect_intent.detect_lgtm("You're missing a LGTM"))
      self.assertFalse(detect_intent.detect_lgtm("You're missing an LGTM"))

      self.assertFalse(detect_intent.detect_lgtm('''
        Any discussion whatsoever that might even include the word
        LGTM on any line other than the first line.
        '''))

    @mock.patch('internals.approval_defs.get_approvers')
    def test_is_lgtm_allowed__approver(self, mock_get_approvers):
      """A user who is in the list of approvers can LGTM."""
      mock_get_approvers.return_value = ['owner@example.com']
      self.assertTrue(detect_intent.is_lgtm_allowed(
          'owner@example.com', f, approval_defs.ShipApproval))

    @mock.patch('framework.permissions.can_admin_site')
    @mock.patch('internals.approval_defs.get_approvers')
    def test_is_lgtm_allowed__admin(
        self, mock_get_approvers, mock_can_admin_site):
      """A site admin can LGTM."""
      mock_get_approvers.return_value = ['owner@example.com']
      mock_can_admin_site.return_value = True
      self.assertTrue(detect_intent.is_lgtm_allowed(
          'admin@example.com', f, approval_defs.ShipApproval))

    @mock.patch('internals.approval_defs.get_approvers')
    def test_is_lgtm_allowed__other(self, mock_get_approvers):
      """An average user cannot LGTM."""
      mock_get_approvers.return_value = ['owner@example.com']
      self.assertFalse(detect_intent.is_lgtm_allowed(
          'other@example.com', f, approval_defs.ShipApproval))

    @mock.patch('internals.models.Approval.get_approvals')
    def test_detect_new_thread(self, mock_get_approvals):
      """A thread is new if there are no previsou approval values."""
      mock_get_approvals.return_value = []
      self.assertTrue(detect_intent.detect_new_thread('id', 'field'))

      mock_get_approvals.return_value = ['fake approval value']
      self.assertTrue(detect_intent.detect_new_thread('id', 'field'))


class IntentEmailHandlerTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_1 = models.Feature(
        name='feature one', summary='detailed sum', category=1, visibility=1,
        standardization=1, web_dev_views=1, impl_status_chrome=1,
        intent_stage=models.INTENT_IMPLEMENT)
    self.feature_1.put()
    self.feature_id = self.feature_1.key.integer_id()

    self.request_path = '/tasks/detect-intent'

    self.thread_url = (
        'https://groups.google.com/a/chromium.org/d/msgid/blink-dev/fake')
    self.entry_link = (
        '\n*Link to entry on the Chrome Platform Status*\n'
        'https://www.chromestatus.com/feature/%d\n' % self.feature_id)
    self.footer = (
        '\n--\n'
        'instructions...\n'
        '---\n'
        'To view this discussion on the web visit ' +
        self.thread_url + '.')
    self.review_json_data = {
        'from_addr': 'user@example.com',
        'subject': 'Intent to Ship: Featurename',
        'body': 'Please review. ' + self.entry_link + self.footer,
        }
    self.lgtm_json_data = {
        'from_addr': 'user@example.com',
        'subject': 'Intent to Ship: Featurename',
        'body': 'LGTM. ' + self.footer,
        }
    self.handler = detect_intent.IntentEmailHandler()

  def tearDown(self):
    self.feature_1.key.delete()
    for appr in models.Approval.query().fetch(None):
      appr.key.delete()

  def test_process_post_data__new_thread(self):
    """When we detect a new thread, we record it as the intent thread."""
    with test_app.test_request_context(
        self.request_path, json=self.review_json_data):
      actual = self.handler.process_post_data()

    self.assertEqual(actual, {'message': 'Done'})

    created_approvals = list(models.Approval.query().fetch(None))
    self.assertEqual(1, len(created_approvals))
    appr = created_approvals[0]
    self.assertEqual(self.feature_id, appr.feature_id)
    self.assertEqual(approval_defs.ShipApproval.field_id, appr.field_id)
    self.assertEqual(models.Approval.REVIEW_REQUESTED, appr.state)
    self.assertEqual('user@example.com', appr.set_by)
    self.assertEqual(self.feature_1.intent_to_ship_url, self.thread_url)

  @mock.patch('internals.detect_intent.is_lgtm_allowed')
  def test_process_post_data__lgtm(self, mock_is_lgtm_allowed):
    """If we get an LGTM, we store the approval value and update the feature."""
    mock_is_lgtm_allowed.return_value = True
    self.feature_1.intent_to_ship_url = self.thread_url
    self.feature_1.put()

    with test_app.test_request_context(
        self.request_path, json=self.lgtm_json_data):
      actual = self.handler.process_post_data()

    self.assertEqual(actual, {'message': 'Done'})

    created_approvals = list(models.Approval.query().fetch(None))
    self.assertEqual(1, len(created_approvals))
    appr = created_approvals[0]
    self.assertEqual(self.feature_id, appr.feature_id)
    self.assertEqual(approval_defs.ShipApproval.field_id, appr.field_id)
    self.assertEqual(models.Approval.APPROVED, appr.state)
    self.assertEqual('user@example.com', appr.set_by)
    self.assertEqual(self.feature_1.intent_to_ship_url, self.thread_url)
    self.assertEqual(self.feature_1.i2s_lgtms, ['user@example.com'])
