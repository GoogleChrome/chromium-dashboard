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

import base64
import datetime
import requests
import testing_config  # Must be imported before the module under test.
import unittest
import urllib.request, urllib.parse, urllib.error

from unittest import mock
import flask
import werkzeug

from internals import approval_defs
from internals import models


class FetchOwnersTest(unittest.TestCase):

  @mock.patch('requests.get')
  def test__normal(self, mock_get):
    """We can fetch and parse an OWNERS file.  And reuse cached value."""
    file_contents = (
        '# Blink API owners are responsible for ...\n'
        '#\n'
        '# See https://www.chromium.org/blink#new-features for details.\n'
        'owner1@example.com\n'
        'owner2@example.com\n'
        'owner3@example.com\n'
        '\n')
    encoded = base64.b64encode(file_contents.encode())
    mock_get.return_value = testing_config.Blank(
        status_code=200,
        content=encoded)

    actual = approval_defs.fetch_owners('https://example.com')
    again = approval_defs.fetch_owners('https://example.com')

    # Only called once because second call will be a ramcache hit.
    mock_get.assert_called_once_with('https://example.com')
    self.assertEqual(
        actual,
        ['owner1@example.com', 'owner2@example.com', 'owner3@example.com'])
    self.assertEqual(again, actual)

  @mock.patch('logging.error')
  @mock.patch('requests.get')
  def test__error(self, mock_get, mock_err):
    """If we can't read the OWNER file, raise an exception."""
    mock_get.return_value = testing_config.Blank(
        status_code=404)

    with self.assertRaises(ValueError):
      approval_defs.fetch_owners('https://example.com')

    mock_get.assert_called_once_with('https://example.com')



MOCK_APPROVALS_BY_ID = {
    1: approval_defs.ApprovalFieldDef(
        'Intent to test',
        'You need permission to test',
        1, approval_defs.ONE_LGTM, ['approver@example.com']),
    2: approval_defs.ApprovalFieldDef(
        'Intent to optimize',
        'You need permission to optimize',
        2, approval_defs.THREE_LGTM, 'https://example.com'),
}


class GetApproversTest(unittest.TestCase):

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  @mock.patch('internals.approval_defs.fetch_owners')
  def test__hard_coded(self, mock_fetch_owner):
    """Some approvals may have a hard-coded list of appovers."""
    actual = approval_defs.get_approvers(1)
    mock_fetch_owner.assert_not_called()
    self.assertEqual(actual, ['approver@example.com'])

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  @mock.patch('internals.approval_defs.fetch_owners')
  def test__url(self, mock_fetch_owner):
    """Some approvals may have a hard-coded list of appovers."""
    mock_fetch_owner.return_value = ['owner@example.com']
    actual = approval_defs.get_approvers(2)
    mock_fetch_owner.assert_called_once_with('https://example.com')
    self.assertEqual(actual, ['owner@example.com'])


class IsValidFieldIdTest(unittest.TestCase):

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  def test(self):
    """We know if a field_id is defined or not."""
    self.assertTrue(approval_defs.is_valid_field_id(1))
    self.assertTrue(approval_defs.is_valid_field_id(2))
    self.assertFalse(approval_defs.is_valid_field_id(3))


class IsApprovedTest(unittest.TestCase):

  def setUp(self):
    feature_1_id = 123456
    self.appr_nr = models.Approval(
        feature_id=feature_1_id, field_id=1,
        state=models.Approval.REVIEW_REQUESTED,
        set_on=datetime.datetime.now(),
        set_by='one@example.com')
    self.appr_na = models.Approval(
        feature_id=feature_1_id, field_id=1,
        state=models.Approval.NA,
        set_on=datetime.datetime.now(),
        set_by='one@example.com')
    self.appr_no = models.Approval(
        feature_id=feature_1_id, field_id=1,
        state=models.Approval.NOT_APPROVED,
        set_on=datetime.datetime.now(),
        set_by='two@example.com')
    self.appr_yes = models.Approval(
        feature_id=feature_1_id, field_id=1,
        state=models.Approval.APPROVED,
        set_on=datetime.datetime.now(),
        set_by='three@example.com')

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  def test_is_approved(self):
    """We know if an approval rule has been satisfied."""

    # Field requires 1 LGTM
    self.assertFalse(approval_defs.is_approved([], 1))
    self.assertFalse(approval_defs.is_approved([self.appr_nr], 1))
    self.assertFalse(approval_defs.is_approved([self.appr_no], 1))
    self.assertTrue(approval_defs.is_approved([self.appr_yes], 1))
    self.assertTrue(approval_defs.is_approved([self.appr_na], 1))
    self.assertFalse(approval_defs.is_approved([self.appr_nr, self.appr_no], 1))
    self.assertFalse(approval_defs.is_approved(
        [self.appr_nr, self.appr_no, self.appr_yes], 1))
    self.assertTrue(approval_defs.is_approved([self.appr_nr, self.appr_yes], 1))
    self.assertTrue(approval_defs.is_approved([self.appr_nr, self.appr_na], 1))

    # Field requires 3 LGTMs
    self.assertFalse(approval_defs.is_approved([], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_nr], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_no], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_yes], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_na], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_nr, self.appr_no], 2))
    self.assertFalse(approval_defs.is_approved(
        [self.appr_nr, self.appr_no, self.appr_yes], 2))
    self.assertFalse(approval_defs.is_approved([self.appr_nr, self.appr_yes], 2))

    self.assertTrue(approval_defs.is_approved(
        [self.appr_yes, self.appr_yes, self.appr_yes], 2))
    self.assertTrue(approval_defs.is_approved(
        [self.appr_yes, self.appr_yes, self.appr_na], 2))
    self.assertTrue(approval_defs.is_approved(
        [self.appr_na, self.appr_na, self.appr_na], 2))
    self.assertFalse(approval_defs.is_approved(
        [self.appr_yes, self.appr_yes, self.appr_yes, self.appr_no], 2))
    self.assertFalse(approval_defs.is_approved(
        [self.appr_na, self.appr_yes, self.appr_yes, self.appr_no], 2))

  @mock.patch('internals.approval_defs.APPROVAL_FIELDS_BY_ID',
              MOCK_APPROVALS_BY_ID)
  def test_is_resolved(self):
    """We know if an approval request has been resolved."""
    # Field requires 1 LGTM
    self.assertFalse(approval_defs.is_resolved([], 1))
    self.assertFalse(approval_defs.is_resolved([self.appr_nr], 1))
    self.assertTrue(approval_defs.is_resolved([self.appr_no], 1))
    self.assertTrue(approval_defs.is_resolved([self.appr_yes], 1))
    self.assertTrue(approval_defs.is_resolved([self.appr_nr, self.appr_no], 1))
    self.assertTrue(approval_defs.is_resolved(
        [self.appr_nr, self.appr_no, self.appr_yes], 1))
    self.assertTrue(approval_defs.is_resolved([self.appr_nr, self.appr_yes], 1))

    # Field requires 3 LGTMs
    self.assertFalse(approval_defs.is_resolved([], 2))
    self.assertFalse(approval_defs.is_resolved([self.appr_nr], 2))
    self.assertTrue(approval_defs.is_resolved([self.appr_no], 2))
    self.assertFalse(approval_defs.is_resolved([self.appr_yes], 2))
    self.assertTrue(approval_defs.is_resolved([self.appr_nr, self.appr_no], 2))
    self.assertTrue(approval_defs.is_resolved(
        [self.appr_nr, self.appr_no, self.appr_yes], 2))
    self.assertFalse(approval_defs.is_resolved([self.appr_nr, self.appr_yes], 2))

    self.assertTrue(approval_defs.is_resolved(
        [self.appr_yes, self.appr_yes, self.appr_yes], 2))
    self.assertTrue(approval_defs.is_resolved(
        [self.appr_yes, self.appr_yes, self.appr_yes, self.appr_no], 2))
