# -*- coding: utf-8 -*-
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

import base64
import collections
import logging
import requests

from framework import permissions
from framework import ramcache
from internals import models
import settings

CACHE_EXPIRATION = 60 * 60  # One hour


ONE_LGTM = 'One LGTM'
THREE_LGTM = 'Three LGTMs'
API_OWNERS_URL = (
    'https://chromium.googlesource.com/chromium/src/+/'
    'main/third_party/blink/API_OWNERS?format=TEXT')

ApprovalFieldDef = collections.namedtuple(
    'ApprovalField',
    'name, description, field_id, rule, approvers')

PrototypeApproval = ApprovalFieldDef(
    'Intent to prototype',
    'One API Owner must approve your intent',
    1, ONE_LGTM, API_OWNERS_URL)

ExperimentApproval = ApprovalFieldDef(
    'Intent to experiment',
    'One API Owner must approve your intent',
    2, ONE_LGTM, API_OWNERS_URL)

ExtendExperimentApproval = ApprovalFieldDef(
    'Intent to extend experiment',
    'One API Owner must approve your intent',
    3, ONE_LGTM, API_OWNERS_URL)

ShipApproval = ApprovalFieldDef(
    'Intent to ship',
    'Three API Owners must approve your intent',
    4, THREE_LGTM, API_OWNERS_URL)

APPROVAL_FIELDS_BY_ID = {
    afd.field_id: afd
    for afd in [PrototypeApproval, ExperimentApproval, ShipApproval]
    }


def fetch_owners(url):
  """Load a list of email addresses from an OWNERS file."""
  cached_owners = ramcache.get(url)
  if cached_owners:
    return cached_owners

  owners = []
  response = requests.get(url)
  if response.status_code != 200:
    logging.error('Could not fetch %r', url)
    logging.error('Got response %s', repr(response)[:settings.MAX_LOG_LINE])
    raise ValueError('Could not get OWNERS file')

  decoded = base64.b64decode(response.content).decode()
  for line in decoded.split('\n'):
    logging.info('got line: '  + line[:settings.MAX_LOG_LINE])
    if '#' in line:
      line = line[:line.index('#')]
    line = line.strip()
    if '@' in line and '.' in line:
      owners.append(line)

  ramcache.set(url, owners, time=CACHE_EXPIRATION)
  return owners


def get_approvers(field_id):
  """Return a list of email addresses of users allowed to approve."""
  afd = APPROVAL_FIELDS_BY_ID[field_id]

  # afd.approvers can be either a hard-coded list of approver emails
  # or it can be a URL of an OWNERS file.  Right now we only use the
  # URL approach, but both are supported.
  if isinstance(afd.approvers, str):
    owners = fetch_owners(afd.approvers)
    return owners

  return afd.approvers


def fields_approvable_by(user):
  """Return a set of field IDs that the user is allowed to approve."""
  if permissions.can_admin_site(user):
    return set(APPROVAL_FIELDS_BY_ID.keys())

  email = user.email()
  approvable_ids = {
      field_id for field_id in APPROVAL_FIELDS_BY_ID
      if email in get_approvers(field_id)}
  return approvable_ids


def is_valid_field_id(field_id):
  """Return true if field_id is a known field."""
  return field_id in APPROVAL_FIELDS_BY_ID


def is_approved(approval_values, field_id):
  """Return true if we have all needed APPROVED values and no NOT_APPROVED."""
  count = 0
  for av in approval_values:
    if av.state in (models.Approval.APPROVED, models.Approval.NA):
      count += 1
    elif av.state == models.Approval.NOT_APPROVED:
      return False
  afd = APPROVAL_FIELDS_BY_ID[field_id]

  if afd.rule == ONE_LGTM:
    return count >= 1
  elif afd.rule == THREE_LGTM:
    return count >= 3
  else:
    logging.error('Unexpected approval rule')
    return False


def is_resolved(approval_values, field_id):
  """Return true if the review is done (approved or not approved)."""
  if is_approved(approval_values, field_id):
    return True

  # Any NOT_APPROVED value means that the review is no longer pending.
  for av in approval_values:
    if av.state == models.Approval.NOT_APPROVED:
      return True

  return False
