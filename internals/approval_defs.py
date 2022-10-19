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
import datetime
import logging
from typing import Optional
import requests

from framework import permissions
from internals import core_enums
from internals.review_models import Approval, Gate, OwnersFile, Vote
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

# Note: This can be requested manually through the UI, but it is not
# triggered by a blink-dev thread because i2p intents are only FYIs to
# bilnk-dev and don't actually need approval by the API Owners.
PrototypeApproval = ApprovalFieldDef(
    'Intent to Prototype',
    'Not normally used.  If a review is requested, API Owners can approve.',
    core_enums.GATE_PROTOTYPE, ONE_LGTM, API_OWNERS_URL)

ExperimentApproval = ApprovalFieldDef(
    'Intent to Experiment',
    'One API Owner must approve your intent',
    core_enums.GATE_ORIGIN_TRIAL, ONE_LGTM, API_OWNERS_URL)

ExtendExperimentApproval = ApprovalFieldDef(
    'Intent to Extend Experiment',
    'One API Owner must approve your intent',
    core_enums.GATE_EXTEND_ORIGIN_TRIAL, ONE_LGTM, API_OWNERS_URL)

ShipApproval = ApprovalFieldDef(
    'Intent to Ship',
    'Three API Owners must approve your intent',
    core_enums.GATE_SHIP, THREE_LGTM, API_OWNERS_URL)

APPROVAL_FIELDS_BY_ID = {
    afd.field_id: afd
    for afd in [
        PrototypeApproval, ExperimentApproval, ExtendExperimentApproval,
        ShipApproval]
    }


def fetch_owners(url):
  """Load a list of email addresses from an OWNERS file."""
  raw_content = OwnersFile.get_raw_owner_file(url)
  if raw_content:
    return decode_raw_owner_content(raw_content)

  response = requests.get(url)
  if response.status_code != 200:
    logging.error('Could not fetch %r', url)
    logging.error('Got response %s', repr(response)[:settings.MAX_LOG_LINE])
    raise ValueError('Could not get OWNERS file')

  OwnersFile(url=url, raw_content=response.content).add_owner_file()
  return decode_raw_owner_content(response.content)


def decode_raw_owner_content(raw_content):
  owners = []
  decoded = base64.b64decode(raw_content).decode()
  for line in decoded.split('\n'):
    logging.info('got line: '  + line[:settings.MAX_LOG_LINE])
    if '#' in line:
      line = line[:line.index('#')]
    line = line.strip()
    if '@' in line and '.' in line:
      owners.append(line)

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
    if av.state in (Approval.APPROVED, Approval.NA):
      count += 1
    elif av.state == Approval.NOT_APPROVED:
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
    if av.state == Approval.NOT_APPROVED:
      return True

  return False

def set_vote(
    feature_id: int,  gate_type: int, new_state: int, set_by_email: str,
    gate_id: Optional[int]=None) -> None:
  """Add or update an approval value."""
  gate: Optional[Gate] = None
  if not gate_id:
    gate = get_gate_by_type(feature_id, gate_type)
    # If a vote is being set, a corresponding gate should already exist.
    if not gate:
      logging.warning('Gate entity not found for the given feature. '
          'Cannot set vote.')
      return
    gate_id = gate.key.integer_id()
  else:
    gate = Gate.get_by_id(gate_id)

  if not Vote.is_valid_state(new_state):
    raise ValueError('Invalid approval state')

  now = datetime.datetime.now()
  existing_list: list[Vote] = Vote.get_votes(
      feature_id=feature_id, gate_id=gate_id, set_by=set_by_email)
  if existing_list:
    existing = existing_list[0]
    existing.set_on = now
    existing.state = new_state
    existing.put()
  else:
    new_vote = Vote(feature_id=feature_id, gate_id=gate_id, state=new_state,
        set_on=now, set_by=set_by_email)
    new_vote.put()

  update_gate_approval_state(gate)

def get_gate_by_type(feature_id: int, gate_type: int):
  """Return a single gate based on the feature and gate type."""
  # TODO(danielrsmith): As of today, there is only 1 gate per
  # gate type and feature. Passing the gate ID will be required when adding
  # UI functionality for multiple versions of the same stage/gate.
  gates: list[Gate] = Gate.query(
    Gate.feature_id == feature_id, Gate.gate_type == gate_type).fetch()
  if len(gates) == 0:
    return None
  return gates[0]

def _calc_gate_status(gate: Gate) -> int:
  """Evaluates the current state that this gate should have."""
  votes = Vote.get_votes(gate_id=gate.key.integer_id())
  approvals = 0
  for vote in votes:
    if vote.state in (Vote.APPROVED, Vote.NA):
      approvals += 1
    elif vote.state == Vote.NOT_APPROVED:
      return Vote.NOT_APPROVED
  afd = APPROVAL_FIELDS_BY_ID[gate.gate_type]

  if ((afd.rule == ONE_LGTM and approvals >= 1) or
      (afd.rule == THREE_LGTM and approvals >= 3)):
    return Vote.APPROVED
  return gate.state

def update_gate_approval_state(gate: Gate) -> int:
  """Change the Gate state if it has changed."""
  was_not_resolved = not gate.is_resolved()
  gate.state = _calc_gate_status(gate)
  gate.put()
  if was_not_resolved and gate.is_resolved():
    gate.clear_request()
  return gate.state
