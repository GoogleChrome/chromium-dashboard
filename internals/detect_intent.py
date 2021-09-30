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

import settings
from framework import basehandlers
from internals import approval_defs
from internals import models


def detect_field(subject):
  """Look for key words in the subject line that indicate intent type.

  These should detect recent actual intent threads as seen in the blink-dev
  archive: https://groups.google.com/a/chromium.org/g/blink-dev.
  """
  subject = subject.lower().strip()
  if subject.startswith('[blink-dev]'):
    subject = subject[len('[blink-dev]'):].strip()
  while subject.startswith('re:'):
    subject = subject[len('re:'):].strip()

  if (subject.startswith('intent to ship') or
      subject.startswith('intent to prototype and ship') or
      subject.startswith('intent to implement and ship') or
      subject.startswith('intent to deprecate and remove') or
      subject.startswith('intent to remove')):
    return approval_defs.ShipApproval

  if (subject.startswith('intent to prototype') or
      subject.startswith('intent to implement') or
      subject.startswith('intent to deprecate')):
    return approval_defs.PrototypeApproval

  if (subject.startswith('intent to experiment') or
      subject.startswith('request for deprecation trial')):
    return approval_defs.ExperimentApproval

  if (subject.startswith('intent to continue experiment') or
      subject.startswith('intent to extend experiment') or
      subject.startswith('intent to continue origin') or
      subject.startswith('intent to extend origin')):
    return approval_defs.ExtendExperimentApproval

  return None


CHROMESTATUS_LINK_RE = re.compile(
    r'Link to entry on the Chrome Platform Status:?\s+'
    r'https://www.chromestatus.com/feature/(\d+)', re.I)


def detect_feature_id(body):
  """Look for the link to a chromestatus entry."""
  match = CHROMESTATUS_LINK_RE.search(body)
  if match:
    return int(match.group(1))
  return None


THREAD_LINK_RE = re.compile(
    r'To view this discussion on the web visit\s+'
    r'(https://groups.google.com/a/chromium.org/d/msgid/blink-dev/'
    r'\S+)[.]')


def detect_thread_url(body):
  """Look for the link to the thread in the blink-dev archive."""
  match = THREAD_LINK_RE.search(body)
  if match:
    return match.group(1)
  return None


class IntentEmailHandler(basehandlers.FlaskHandler):
  """This task handles an inbound email to detect intent threads."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self):
    self.require_task_header()

    from_addr = self.get_param('from_addr')
    subject = self.get_param('subject')
    in_reply_to = self.get_param('in_reply_to', required=False)
    body = self.get_param('body')

    logging.info('In IntentEmailHandler:\n'
                 'From addr:   %r\n'
                 'Subject:     %r\n'
                 'In reply to: %r\n'
                 'Body:        %r\n',
                 from_addr, subject, in_reply_to, body)

    approval_field = detect_field(subject)
    if not approval_field:
      logging.info('This does not appear to be an intent')
      return {'message': 'Not an intent'}

    feature_id = detect_feature_id(body)
    if not feature_id:
      logging.info('Could not find feature ID')
      return {'message': 'No feature ID'}
    feature = models.Feature.get_by_id(feature_id)
    if not feature:
      logging.info('Could not retrieve feature')
      return {'message': 'Feature not found'}

    thread_url = detect_thread_url(body)

    self.set_intent_thread_url(feature, approval_field, thread_url)
    self.create_approvals(feature_id, approval_field, from_addr, body)
    return {'message': 'Done'}

  def set_intent_thread_url(self, feature, approval_field, thread_url):
    """If the feature has no previous thread URL for this intent, set it."""
    if not thread_url:
      return

    if (approval_field == approval_defs.PrototypeApproval and
        not feature.intent_to_implement_url):
      feature.intent_to_implement_url = thread_url
      feature.put()

    # TODO(jrobbins): Ready-for-trial threads

    if (approval_field == approval_defs.ExperimentApproval and
        not feature.intent_to_experiment_url):
      feature.intent_to_experiment_url = thread_url
      feature.put()

    if (approval_field == approval_defs.ShipApproval and
        not feature.intent_to_ship_url):
      feature.intent_to_ship_url = thread_url
      feature.put()

  def create_approvals(self, feature_id, approval_field, from_addr, body):
    """Store either a NEEDS_REVIEW or an APPROVED approval value."""
    # Case 1: This is a new intent thread
    existing_approvals = models.Approval.get_approvals(
        feature_id=feature_id, field_id=approval_field.field_id)
    if not existing_approvals:
      models.Approval.set_approval(
          feature_id, approval_field.field_id,
          models.Approval.NEEDS_REVIEW, from_addr)

    # Case 2: This is an existing intent thread
    # TODO(jrobbins): Detect LGTMs in body, verify that sender has permission,
    # set an approval value, and clear the original NEEDS_REVIEW if
    # the approval rule (1 or 3 LTGMs) is satisfied.
