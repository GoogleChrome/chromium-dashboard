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
from dataclasses import dataclass
import datetime
import json
import logging
from typing import Optional
import requests

from framework import permissions
from framework import rediscache
from internals import core_enums
from internals import slo
from internals.review_models import Gate, GateDef, OwnersFile, Vote
import settings

APPROVERS_CACHE_KEY = 'approvers'
CACHE_EXPIRATION = 60 * 60  # One hour
IN_NDB = 'stored in ndb'


ONE_LGTM = 'One LGTM'
THREE_LGTM = 'Three LGTMs'
API_OWNERS_URL = (
    'https://chromium.googlesource.com/chromium/src/+/'
    'main/third_party/blink/API_OWNERS?format=TEXT')
PRIVACY_APPROVERS = IN_NDB
SECURITY_APPROVERS = IN_NDB
ENTERPRISE_APPROVERS = [
    'mhoste@google.com',
    'angelaweber@google.com',
    'davidayad@google.com',
    'bheenan@google.com',
]
DEBUGGABILITY_APPROVERS = IN_NDB
TESTING_APPROVERS = [
    'sadapala@google.com',
    'santhoshkumarm@google.com',
    'vivianz@google.com',
]

DEFAULT_SLO_LIMIT = 5  # Five weekdays in the Pacific timezone.

@dataclass(eq=True, frozen=True)
class ApprovalFieldDef:
  name: str
  description: str
  field_id: int
  rule: str
  approvers: str | list[str]
  team_name: str
  escalation_email: str | None = None
  slo_initial_response: int = DEFAULT_SLO_LIMIT


# Note: This can be requested manually through the UI, but it is not
# triggered by a blink-dev thread because i2p intents are only FYIs to
# bilnk-dev and don't actually need approval by the API Owners.
PrototypeApproval = ApprovalFieldDef(
    'Intent to Prototype',
    'Not normally used.  If a review is requested, API Owners can approve.',
    core_enums.GATE_API_PROTOTYPE, ONE_LGTM,
    approvers=API_OWNERS_URL, team_name='API Owners')

ExperimentApproval = ApprovalFieldDef(
    'Intent to Experiment',
    'One API Owner must approve your intent',
    core_enums.GATE_API_ORIGIN_TRIAL, ONE_LGTM,
    approvers=API_OWNERS_URL, team_name='API Owners')

ExtendExperimentApproval = ApprovalFieldDef(
    'Intent to Extend Experiment',
    'One API Owner must approve your intent',
    core_enums.GATE_API_EXTEND_ORIGIN_TRIAL, ONE_LGTM,
    approvers=API_OWNERS_URL, team_name='API Owners')

ShipApproval = ApprovalFieldDef(
    'Intent to Ship',
    'Three API Owners must approve your intent',
    core_enums.GATE_API_SHIP, THREE_LGTM,
    approvers=API_OWNERS_URL, team_name='API Owners')

PlanApproval = ApprovalFieldDef(
    'Intent to Deprecate and Remove',
    'Three API Owners must approve your intent',
    core_enums.GATE_API_PLAN, THREE_LGTM,
    approvers=API_OWNERS_URL, team_name='API Owners')

PrivacyOriginTrialApproval = ApprovalFieldDef(
    'Privacy OT Review',
    'Privacy OT Review',
    core_enums.GATE_PRIVACY_ORIGIN_TRIAL, ONE_LGTM,
    approvers=PRIVACY_APPROVERS, team_name='Privacy',
    escalation_email='chrome-privacy-owp-rotation@google.com',
    slo_initial_response=6)

PrivacyShipApproval = ApprovalFieldDef(
    'Privacy Ship Review',
    'Privacy Ship Review',
    core_enums.GATE_PRIVACY_SHIP, ONE_LGTM,
    approvers=PRIVACY_APPROVERS, team_name='Privacy',
    escalation_email='chrome-privacy-owp-rotation@google.com',
    slo_initial_response=6)

# Note: There is no PrivacyPlanApproval

SecurityOriginTrialApproval = ApprovalFieldDef(
    'Security OT Review',
    'Security OT Review',
    core_enums.GATE_SECURITY_ORIGIN_TRIAL, ONE_LGTM,
    approvers=SECURITY_APPROVERS, team_name='Security',
    slo_initial_response=6)

SecurityShipApproval = ApprovalFieldDef(
    'Security Ship Review',
    'Security Ship Review',
    core_enums.GATE_SECURITY_SHIP, ONE_LGTM,
    approvers=SECURITY_APPROVERS, team_name='Security',
    slo_initial_response=6)

# Note: There is no SecurityPlanApproval

EnterpriseShipApproval = ApprovalFieldDef(
    'Enterprise Ship Review',
    'Enterprise Ship Review',
    core_enums.GATE_ENTERPRISE_SHIP, ONE_LGTM,
    approvers=ENTERPRISE_APPROVERS, team_name='Enterprise')

EnterprisePlanApproval = ApprovalFieldDef(
    'Enterprise Deprecation Plan Review',
    'Enterprise Deprecation Plan Review',
    core_enums.GATE_ENTERPRISE_PLAN, ONE_LGTM,
    approvers=ENTERPRISE_APPROVERS, team_name='Enterprise')

DebuggabilityOriginTrialApproval = ApprovalFieldDef(
    'Debuggability OT Review',
    'Debuggability OT Review',
    core_enums.GATE_DEBUGGABILITY_ORIGIN_TRIAL, ONE_LGTM,
    approvers=DEBUGGABILITY_APPROVERS, team_name='Debuggability',
    escalation_email='devtools-dev@chromium.org')

DebuggabilityShipApproval = ApprovalFieldDef(
    'Debuggability Ship Review',
    'Debuggability Ship Review',
    core_enums.GATE_DEBUGGABILITY_SHIP, ONE_LGTM,
    approvers=DEBUGGABILITY_APPROVERS, team_name='Debuggability',
    escalation_email='devtools-dev@chromium.org')

DebuggabilityPlanApproval = ApprovalFieldDef(
    'Debuggability Deprecation Plan Review',
    'Debuggability Deprecation Plan Review',
    core_enums.GATE_DEBUGGABILITY_PLAN, ONE_LGTM,
    approvers=DEBUGGABILITY_APPROVERS, team_name='Debuggability',
    escalation_email='devtools-dev@chromium.org')

TestingShipApproval = ApprovalFieldDef(
    'Testing Ship Review',
    'Testing Ship Review',
    core_enums.GATE_TESTING_SHIP, ONE_LGTM,
    approvers=TESTING_APPROVERS, team_name='Testing')

TestingPlanApproval = ApprovalFieldDef(
    'Testing Deprecation Plan Review',
    'Testing Deprecation Plan Review',
    core_enums.GATE_TESTING_PLAN, ONE_LGTM,
    approvers=TESTING_APPROVERS, team_name='Testing')

APPROVAL_FIELDS_BY_ID = {
    afd.field_id: afd
    for afd in [
        PrototypeApproval, ExperimentApproval, ExtendExperimentApproval,
        ShipApproval, PlanApproval,
        PrivacyOriginTrialApproval, PrivacyShipApproval,
        SecurityOriginTrialApproval, SecurityShipApproval,
        EnterpriseShipApproval, EnterprisePlanApproval,
        DebuggabilityOriginTrialApproval, DebuggabilityShipApproval,
        DebuggabilityPlanApproval,
        TestingShipApproval, TestingPlanApproval,
        ]
    }


def fetch_owners(url) -> list[str]:
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


def decode_raw_owner_content(raw_content) -> list[str]:
  owners = []
  decoded = base64.b64decode(raw_content).decode()
  for line in decoded.split('\n'):
    if '#' in line:
      line = line[:line.index('#')]
    line = line.strip()
    if '@' in line and '.' in line:
      owners.append(line)

  return owners


def auto_assign_reviewer(gate):
  """If a previous review was assigned, use the same reviewer.
     If this gate has a reviewer rotation, use the current on-call user."""
  afd = APPROVAL_FIELDS_BY_ID[gate.gate_type]

  all_gates: list[Gate] = Gate.query(Gate.feature_id == gate.feature_id).fetch()
  for other_gate in all_gates:
    other_afd = APPROVAL_FIELDS_BY_ID[other_gate.gate_type]
    if (other_gate.key.integer_id() != gate.key.integer_id() and
        other_afd.team_name == afd.team_name and
        other_afd.rule == afd.rule and
        other_gate.assignee_emails):
      gate.assignee_emails = other_gate.assignee_emails
      gate.put()
      return

  if afd.approvers != IN_NDB:
    return

  gate_def = GateDef.get_gate_def(gate.gate_type)
  if not gate_def.rotation_url:
    return

  response = requests.get(gate_def.rotation_url)
  if response.status_code != 200:
    logging.error('Could not fetch %r', gate_def.rotation_url)
    logging.error('Got response %s', repr(response)[:settings.MAX_LOG_LINE])
    return

  try:
    logging.info(
        'response.content is:\n%s', response.content[:settings.MAX_LOG_LINE])
    response_json = json.loads(response.content)
  except ValueError:
    logging.info('failed to parse content')

  if 'emails' in response_json:
    gate.assignee_emails = response_json['emails']
    gate.put()


def get_approvers(field_id) -> list[str]:
  """Return a list of email addresses of users allowed to approve."""
  if field_id not in APPROVAL_FIELDS_BY_ID:
    return []

  cache_key = '%s|%s' % (APPROVERS_CACHE_KEY, field_id)
  cached_approvers = rediscache.get(cache_key)
  if cached_approvers:
    return cached_approvers

  afd = APPROVAL_FIELDS_BY_ID[field_id]

  if afd.approvers == IN_NDB:
    gate_def = GateDef.get_gate_def(field_id)
    owners = gate_def.approvers
  elif isinstance(afd.approvers, str):
    # afd.approvers can be either a hard-coded list of approver emails
    # or it can be a URL of an OWNERS file.  Right now we only use the
    # URL approach, but both are supported.
    owners = fetch_owners(afd.approvers)
  else:
    owners = afd.approvers

  rediscache.set(cache_key, owners, time=CACHE_EXPIRATION)
  return owners


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
  """Return true if we have all needed APPROVED values and no DENIED."""
  count = 0
  for av in approval_values:
    if av.state in (Vote.APPROVED, Vote.NA):
      count += 1
    elif av.state == Vote.DENIED:
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

  # Any DENIED value means that the review is no longer pending.
  for av in approval_values:
    if av.state == Vote.DENIED:
      return True

  return False


def set_vote(feature_id: int,  gate_type: int | None, new_state: int,
    set_by_email: str, gate_id: int | None=None) -> int | None:
  """Add or update an approval value and return new approval state if
  changed.
  """
  gate: Optional[Gate] = None
  if gate_id is None and gate_type is not None:
    gate = get_gate_by_type(feature_id, gate_type)
    # If a vote is being set, a corresponding gate should already exist.
    if not gate:
      logging.warning('Gate entity not found for the given feature. '
          'Cannot set vote.')
      return None
    gate_id = gate.key.integer_id()
    gate_type = gate.gate_type
  else:
    gate = Gate.get_by_id(gate_id)

  if not Vote.is_valid_state(new_state):
    raise ValueError('Invalid approval state')

  now = datetime.datetime.now()
  existing_list: list[Vote] = Vote.get_votes(feature_id=feature_id,
      gate_id=gate_id, set_by=set_by_email)
  if existing_list:
    existing = existing_list[0]
    existing.set_on = now
    existing.state = new_state
    existing.put()
  else:
    new_vote = Vote(feature_id=feature_id, gate_id=gate_id,
        gate_type=gate_type, state=new_state, set_on=now, set_by=set_by_email)
    new_vote.put()

  if gate:
    votes = Vote.get_votes(gate_id=gate.key.integer_id())
    state_was_updated = update_gate_approval_state(gate, votes)
    slo_was_updated = slo.record_vote(gate, votes)
    if state_was_updated or slo_was_updated:
      gate.put()
      return gate.state
  return None

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


def _calc_gate_state(votes: list[Vote], rule: str) -> int:
  """Returns the state that a gate should have based on its votes."""
  # If enough reviewed APPROVED or said it is NA, then that is used.
  num_lgtms = sum((1 if v.state in (Vote.APPROVED, Vote.NA) else 0)
                  for v in votes)
  if ((rule == ONE_LGTM and num_lgtms >= 1) or
      (rule == THREE_LGTM and num_lgtms >= 3)):
    if any(v.state == Vote.NA for v in votes):
      return Vote.NA  # Any NA vote counts, but makes the result NA.
    else:
      return Vote.APPROVED

  # Return the most recent of any REVIEW_REQUESTED, NEEDS_WORK,
  # REVIEW_STARTED, INTERNAL_REVIEW, or DENIED.  This could allow a
  # feature owner to re-request a review after addressing feedback and
  # have the gate show up as REVIEW_STARTED again.  However, we will
  # not offer "re-review" in the UI yet.
  for vote in sorted(votes, reverse=True, key=lambda v: v.set_on):
    if vote.state in (
        Vote.NEEDS_WORK, Vote.REVIEW_STARTED, Vote.REVIEW_REQUESTED,
        Vote.DENIED, Vote.INTERNAL_REVIEW, Vote.NA_REQUESTED):
      return vote.state

  # An API Owner can kick off review of an I2S thread that was not detected
  # by voting Approve for their "LGTM1".
  if rule == THREE_LGTM and num_lgtms >= 1:
    return Vote.REVIEW_REQUESTED

  # The feature owner has not requested review yet, or the request was
  # withdrawn.
  return Gate.PREPARING


def update_gate_approval_state(gate: Gate, votes: list[Vote]) -> bool:
  """Change the Gate state in RAM based on its votes. Return True if changed."""
  afd = APPROVAL_FIELDS_BY_ID.get(gate.gate_type)
  # Assume any gate of a type that is not currently supported is ONE_LGTM.
  rule = afd.rule if afd else ONE_LGTM
  new_state = _calc_gate_state(votes, rule)
  if new_state == gate.state:
    return False
  gate.state = new_state
  if votes:
    gate.requested_on = min(v.set_on for v in votes)

  # Starting a review resets responded_on.
  if new_state in (Vote.REVIEW_REQUESTED, Vote.NA_REQUESTED):
    gate.responded_on = None

  return True
