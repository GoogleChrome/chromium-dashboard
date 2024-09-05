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

import re
import logging
import random
import time
from typing import Optional

import settings
from framework import basehandlers
from framework import permissions
from framework import users
from internals import approval_defs
from internals import core_enums
from internals import notifier_helpers
from internals import slo
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Vote, Gate


GATE_TYPES_REQUIRING_LGTMS = [
    approval_defs.PlanApproval.gate_type,
    approval_defs.ShipApproval.gate_type,
    approval_defs.ExperimentApproval.gate_type,
    approval_defs.ExtendExperimentApproval.gate_type,
    ]


# Email prefixes that we don't care about: Re: or [blink-dev] or Fwd:
PREFIX_RE = re.compile(r're:|fwd:|\[[-._\w]+\]')

INTEND_PATTERN = r'(intent|intend(ing)?|request(ing)?) (to|for)'
PLAN_PATTERN = r'(deprecate and remove)'
SHIP_PATTERN = r'(ship|remove|\w+ and ship)'
PROTO_PATTERN = r'(prototype|prototyping|implement|deprecate)'
EXPERIMENT_PATTERN = r'(experiment|deprecation)'
EXTEND_PATTERN = (r'(continue|continuing|extend|extending) '
                  r'(experiment|origin|deprecation)')

PLAN_RE = re.compile('%s %s' % (INTEND_PATTERN, PLAN_PATTERN))
SHIP_RE = re.compile('%s %s' % (INTEND_PATTERN, SHIP_PATTERN))
PROTO_RE = re.compile('%s %s' % (INTEND_PATTERN, PROTO_PATTERN))
EXPERIMENT_RE = re.compile('%s %s' % (INTEND_PATTERN, EXPERIMENT_PATTERN))
EXTEND_RE = re.compile('%s %s' % (INTEND_PATTERN, EXTEND_PATTERN))


def detect_gate_info(subject: str) -> approval_defs.GateInfo | None:
  """Look for key words in the subject line that indicate intent type.

  These should detect recent actual intent threads as seen in the blink-dev
  archive: https://groups.google.com/a/chromium.org/g/blink-dev.
  """
  subject = subject.lower().strip()
  subject = PREFIX_RE.sub('', subject)  # Strip any number of prefixes

  subject = subject.replace('&', ' and ')
  subject = subject.replace('+', ' and ')
  subject = ' '.join(subject.split())  # collapse multiple spaces

  if PLAN_RE.match(subject):
    return approval_defs.PlanApproval

  if SHIP_RE.match(subject):
    return approval_defs.ShipApproval

  if PROTO_RE.match(subject):
    return approval_defs.PrototypeApproval

  if EXPERIMENT_RE.match(subject):
    return approval_defs.ExperimentApproval

  if EXTEND_RE.match(subject):
    return approval_defs.ExtendExperimentApproval

  return None

CHROMESTATUS_LINK_GENERATED_PATTERN = (
    r'Chrome( Platform)? ?Status(.com)?[ \w]*:?\s+'
    r'[> ]*https?://(www\.)?chromestatus\.com/'
    r'(feature|guide/edit)/(?P<id>\d+)')

CHROMESTATUS_LINK_GENERATED_RE = re.compile(
    CHROMESTATUS_LINK_GENERATED_PATTERN, re.I)
CHROMESTATUS_LINK_GENERATED_GATE_RE = re.compile(
    CHROMESTATUS_LINK_GENERATED_PATTERN + r'\?gate=(?P<gate_id>\d+)', re.I)
CHROMESTATUS_LINK_ALTERNATE_RE = re.compile(
    r'entry on the feature dashboard.*\s+'
    r'[> ]*https?://(www\.)?chromestatus\.com/'
    r'(feature|guide/edit)/(?P<id>\d+)', re.I)
NOT_LGTM_RE = re.compile(
    r'\b(not|almost|need|want|missing) (a |an )?LGTM\b',
    re.I)
LGTM_RE = re.compile(r'\b(LGTM|LGTM1|LGTM2|LGTM3)\b', re.I)


def detect_feature_id(body):
  """Look for the link to a chromestatus entry."""
  match = (CHROMESTATUS_LINK_GENERATED_RE.search(body) or
           CHROMESTATUS_LINK_ALTERNATE_RE.search(body))
  if match:
    return int(match.group('id'))
  return None


def detect_gate_id(body) -> int | None:
  """Detect the gate ID within the chromestatus URL."""
  match = CHROMESTATUS_LINK_GENERATED_GATE_RE.search(body)
  if match:
    return int(match.group('gate_id'))
  return None


THREAD_LINK_RE = re.compile(
    r'To view this discussion on the web visit\s+'
    r'(> )?(https://groups\.google\.com/a/chromium.org/d/msgid/blink-dev/'
    r'[-_0-9a-zA-Z%.]+[-_0-9a-zA-Z])', re.MULTILINE)
STAGING_THREAD_LINK_RE = re.compile(
    r'To view this discussion on the web visit\s+'
    r'(> )?(https://groups\.google\.com/d/msgid/jrobbins-test/'
    r'[-_0-9a-zA-Z%.]+[-_0-9a-zA-Z])', re.MULTILINE)


def detect_thread_url(body):
  """Look for the link to the thread in the blink-dev archive."""
  match = (THREAD_LINK_RE.search(body) or
           STAGING_THREAD_LINK_RE.search(body))
  if match:
    return match.group(2)
  return None


def detect_lgtm(body):
  """Return true if LGTM is on first non-blank line."""
  lines = body.split('\n')

  first_nonblank_line = ''
  for line in lines:
    if line.strip():
      first_nonblank_line = line.strip()
      break

  if (first_nonblank_line.startswith('>') or
      NOT_LGTM_RE.search(first_nonblank_line)):
    return False

  match = LGTM_RE.search(first_nonblank_line)
  return match


def is_lgtm_allowed(from_addr, feature, gate_info):
  """Return true if the user is allowed to approve this feature."""
  user = users.User(email=from_addr)
  approvers = approval_defs.get_approvers(gate_info.gate_type)
  gate = None  # TODO(jrobbins): Detect assignee who is not an approver.
  allowed = permissions.can_review_gate(user, feature, gate, approvers)
  return allowed


def detect_new_thread(gate_id: int) -> bool:
  """Return True if there are no previous approval values for this gate."""
  existing_votes = Vote.get_votes(gate_id=gate_id)
  return not existing_votes


def remove_markdown(body):
  """Remove the simple markdown used by Google Groups."""
  return body.replace('*', '')


class IntentEmailHandler(basehandlers.FlaskHandler):
  """This task handles an inbound email to detect intent threads."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self, **kwargs):
    self.require_task_header()

    from_addr = self.get_param('from_addr')
    subject = self.get_param('subject')
    in_reply_to = self.get_param('in_reply_to', required=False)
    body = self.get_param('body')
    body = remove_markdown(body)

    logging.info('In IntentEmailHandler:\n'
                 'From addr:   %r\n'
                 'Subject:     %r\n'
                 'In reply to: %r\n'
                 'Body:        %r\n',
                 from_addr, subject, in_reply_to, body[:settings.MAX_LOG_LINE])

    gate_info = detect_gate_info(subject)
    if not gate_info:
      logging.info('This does not appear to be an intent')
      return {'message': 'Not an intent'}

    feature_id = detect_feature_id(body)
    gate_id = detect_gate_id(body)
    thread_url = detect_thread_url(body)
    feature, message = self.load_detected_feature(
        feature_id, thread_url)
    if message:
      logging.info(message)
      return {'message': message}
    if not feature:
      logging.info('Could not retrieve feature')
      return {'message': 'Feature not found'}

    gate, stage = self.get_gate_and_stage(
        feature, gate_info, gate_id, thread_url)
    if stage is None:
      message = (f'Stage not found for intent type {gate_info.gate_type} '
                 f'of feature {feature_id}')
      logging.info(message)
      return {'message': message}
    if gate is None:
      message = (f'Gate not found for intent type {gate_info.gate_type} '
                 f'of feature {feature_id}')
      logging.info(message)
      return {'message': message}
    if gate.gate_type != gate_info.gate_type:
      message = (f'Gate {gate.key.integer_id()} has gate type {gate.gate_type} '
                 'and does not match gate info gate type '
                 f'{gate_info.gate_type}')
      logging.info(message)
      return {'message': message}

    self.set_intent_thread_url(stage, thread_url, subject)
    gate_id = gate.key.integer_id()  # In case it was found by gate_type.
    is_new_thread = detect_new_thread(gate_id)
    self.create_approvals(
        feature, stage, gate, gate_info, from_addr, body, is_new_thread)
    self.record_slo(feature, gate_info, from_addr, is_new_thread)
    return {'message': 'Done'}

  def load_detected_feature(self, feature_id: Optional[int],
      thread_url: Optional[str]) -> tuple[Optional[FeatureEntry], Optional[str]]:
    """Find the feature being referenced by this email message.

    Returns a pair with the feature and an error message, either of
    which can be None.
    """
    # If the message had a link to a chromestatus entry, use its ID.
    if feature_id:
      return FeatureEntry.get_by_id(feature_id), None

    # If there is also no thread_url, then give up.
    if not thread_url:
      return None, 'No feature ID or discussion link'

    # Find the feature by querying for the previously saved discussion link.
    matching_stages = Stage.query(Stage.intent_thread_url == thread_url).fetch()
    fe_ids = list(set([s.feature_id for s in matching_stages]))

    if len(fe_ids) == 0:
      return None, 'No feature entry references this discussion thread'
    if len(fe_ids) > 1:
      return None, 'Ambiguous feature entries %r' % fe_ids

    return FeatureEntry.get_by_id(fe_ids[0]), None

  def get_gate_and_stage(
      self,
      feature: FeatureEntry,
      gate_info: approval_defs.GateInfo,
      gate_id: int | None,
      thread_url: str) -> tuple[Gate | None, Stage | None]:
    # If a gate ID is detected, query for the gate.
    if gate_id:
      logging.info(f'Using detected gate ID {gate_id}')
      gate = Gate.get_by_id(gate_id)
      # Return nulls if the gate ID is invalid.
      if gate is None:
        logging.info('Gate not found')
        return None, None
      stage = Stage.get_by_id(gate.stage_id)
    # Otherwise, try to find the matching gate based on other feature info.
    else:
      logging.info('Attempting to find stage/gate without detected gate ID')
      stage = self.find_matching_stage(feature, gate_info, thread_url)
      if stage is None:
        return None, None
      gate = Gate.query(Gate.stage_id == stage.key.integer_id(),
                        Gate.gate_type == gate_info.gate_type).get()
    return gate, stage

  def find_matching_stage(self, feature: FeatureEntry,
      gate_info: approval_defs.GateInfo,
      thread_url: str | None) -> Stage | None:
    """Find the stage in which the thread is associated with."""
    if not thread_url:
      logging.info('Given false thread_url %r', thread_url)
      return None

    stage_type = core_enums.STAGE_TYPES_BY_GATE_TYPE_MAPPING[
        gate_info.gate_type][feature.feature_type]
    if stage_type is None:
      logging.info('stage_type not found for %r %r',
                   gate_info.gate_type, feature.feature_type)
      return None

    # Get all stages of the detected stage type that belong to the feature.
    stages_of_type_in_feature: list[Stage] = Stage.query(
        Stage.feature_id == feature.key.integer_id(),
        Stage.stage_type == stage_type).fetch()
    if len(stages_of_type_in_feature) == 0:
      logging.info('No matching stage found for feature: '
                   f'{feature.key.integer_id()}, stage_type: {stage_type}')
      return None

    # If only 1 stage is found, it's assumed to be the correct stage.
    if len(stages_of_type_in_feature) == 1:
      return stages_of_type_in_feature[0]

    matching_stage = next((s for s in stages_of_type_in_feature
                            if s.intent_thread_url == thread_url), None)
    if matching_stage:
      logging.info('intent_thread_url was already set to %r',
                   matching_stage.intent_thread_url)
      return matching_stage

    # TODO(DanielRyanSmith): This logic could still fail in some circumstances.
    # Move to a guaranteed gate ID detection method, or post intent threads
    # on behalf of the user with a unique identifier.
    # If only 1 stage exists without a set intent URL, we can assume that
    # this thread is associated with that stage.
    stages_with_no_intent_thread_url = list(filter(
        lambda s: s.intent_thread_url is None or s.intent_thread_url == '',
        stages_of_type_in_feature))
    if len(stages_with_no_intent_thread_url) != 1:
      logging.info(f'Ambiguous stages: {stages_of_type_in_feature}')
      return None
    return stages_with_no_intent_thread_url[0]

  def set_intent_thread_url(
      self, stage: Stage, thread_url: str | None, subject: str | None) -> None:
    if stage.intent_thread_url and stage.intent_subject_line:
      logging.info('Not setting intent_thread_url or intent_subject_line')
      return

    stage.intent_thread_url = thread_url
    stage.intent_subject_line = subject
    stage.put()
    logging.info(f'Set intent_thread_url to {thread_url} '
                 f'and intent_subject_line to {subject}')

  def create_approvals(self, feature: FeatureEntry, stage: Stage, gate: Gate,
      gate_info: approval_defs.GateInfo,
      from_addr: str, body: str, is_new_thread: bool) -> None:
    """Store either a REVIEW_REQUESTED or an APPROVED approval value."""
    feature_id = feature.key.integer_id()

    # Case 1: Detect LGTMs in body, verify that sender has permission,
    # set an approval value, and update the gate state if
    # the approval rule (1 or 3 LTGMs) is satisfied.
    if (detect_lgtm(body) and
        is_lgtm_allowed(from_addr, feature, gate_info)):
      logging.info('found LGTM')
      # Avoid a race condition when blink-dev is in both To: and Cc: lines.
      time.sleep(random.uniform(0, 5))
      gate = Gate.get_by_id(gate.key.integer_id())  # Reload after sleep
      old_gate_state = gate.state
      new_gate_state = approval_defs.set_vote(
          feature_id, gate_info.gate_type, Vote.APPROVED, from_addr,
          gate.key.integer_id())
      recently_approved = (old_gate_state not in (Vote.APPROVED, Vote.NA) and
                           new_gate_state in (Vote.APPROVED, Vote.NA))
      if (gate.gate_type == core_enums.GATE_API_EXTEND_ORIGIN_TRIAL and
          recently_approved):
        notifier_helpers.send_trial_extension_approved_notification(
            feature, stage, gate.key.integer_id())

    # Case 2: Create a review request and set gate state for any
    # discussion that does not already have any approval values
    # stored.
    elif is_new_thread:
      logging.info('found new thread')
      if gate_info.gate_type in GATE_TYPES_REQUIRING_LGTMS:
        logging.info('requesting a review')
        approval_defs.set_vote(feature_id, gate_info.gate_type,
            Vote.REVIEW_REQUESTED, from_addr, gate.key.integer_id())

  def record_slo(self, feature, gate_info, from_addr, is_new_thread) -> None:
    """Update SLO timestamps."""
    if is_new_thread:
      return  # The initial request can never count as a response.
    feature_id = feature.key.integer_id()
    matching_gates = Gate.query(
        Gate.feature_id == feature_id,
        Gate.gate_type == gate_info.gate_type).fetch(None)
    if len(matching_gates) == 0:
      logging.info('Did not find a gate')
      return
    if len(matching_gates) > 1:
      logging.info(f'Ambiguous gates: {feature_id}')
      return
    gate = matching_gates[0]
    user = users.User(email=from_addr)
    approvers = approval_defs.get_approvers(gate.gate_type)
    if slo.record_comment(feature, gate, user, approvers):
      gate.put()
