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
from framework import permissions
from framework import users
from internals import approval_defs
from internals import models
from internals import review_models


FIELDS_REQUIRING_LGTMS = [
    approval_defs.ShipApproval, approval_defs.ExperimentApproval,
    approval_defs.ExtendExperimentApproval,
    ]


# Email prefixes that we don't care about: Re: or [blink-dev] or Fwd:
PREFIX_RE = re.compile(r're:|fwd:|\[[-._\w]+\]')

INTEND_PATTERN = r'(intent|intend(ing)?|request(ing)?) (to|for)'
SHIP_PATTERN = r'(ship|remove|\w+ and ship|\w+ and remove)'
PROTO_PATTERN = r'(prototype|prototyping|implement|deprecate)'
EXPERIMENT_PATTERN = r'(experiment|deprecation)'
EXTEND_PATTERN = (r'(continue|continuing|extend|extending) '
                  r'(experiment|origin|deprecation)')

SHIP_RE = re.compile('%s %s' % (INTEND_PATTERN, SHIP_PATTERN))
PROTO_RE = re.compile('%s %s' % (INTEND_PATTERN, PROTO_PATTERN))
EXPERIMENT_RE = re.compile('%s %s' % (INTEND_PATTERN, EXPERIMENT_PATTERN))
EXTEND_RE = re.compile('%s %s' % (INTEND_PATTERN, EXTEND_PATTERN))


def detect_field(subject):
  """Look for key words in the subject line that indicate intent type.

  These should detect recent actual intent threads as seen in the blink-dev
  archive: https://groups.google.com/a/chromium.org/g/blink-dev.
  """
  subject = subject.lower().strip()
  subject = PREFIX_RE.sub('', subject)  # Strip any number of prefixes

  subject = subject.replace('&', ' and ')
  subject = subject.replace('+', ' and ')
  subject = ' '.join(subject.split())  # collapse multiple spaces

  if SHIP_RE.match(subject):
    return approval_defs.ShipApproval

  if PROTO_RE.match(subject):
    return approval_defs.PrototypeApproval

  if EXPERIMENT_RE.match(subject):
    return approval_defs.ExperimentApproval

  if EXTEND_RE.match(subject):
    return approval_defs.ExtendExperimentApproval

  return None


CHROMESTATUS_LINK_GENERATED_RE = re.compile(
    r'entry on the Chrome Platform Status:?\s+'
    r'[> ]*https?://(www\.)?chromestatus\.com/'
    r'(feature|guide/edit)/(?P<id>\d+)', re.I)
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


THREAD_LINK_RE = re.compile(
    r'To view this discussion on the web visit\s+'
    r'(https://groups\.google\.com/a/chromium.org/d/msgid/blink-dev/'
    r'\S+)[.]')
STAGING_THREAD_LINK_RE = re.compile(
    r'To view this discussion on the web visit\s+'
    r'(https://groups\.google\.com/d/msgid/jrobbins-test/'
    r'\S+)[.]')


def detect_thread_url(body):
  """Look for the link to the thread in the blink-dev archive."""
  match = (THREAD_LINK_RE.search(body) or
           STAGING_THREAD_LINK_RE.search(body))
  if match:
    return match.group(1)
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


def is_lgtm_allowed(from_addr, feature, approval_field):
  """Return true if the user is allowed to approve this feature."""
  user = users.User(email=from_addr)
  approvers = approval_defs.get_approvers(approval_field.field_id)
  allowed = permissions.can_approve_feature(user, feature, approvers)
  return allowed


def detect_new_thread(feature_id, approval_field):
  """Return True if there are no previous approval values for this intent."""
  existing_approvals = review_models.Approval.get_approvals(
      feature_id=feature_id, field_id=approval_field.field_id)
  return not existing_approvals


def remove_markdown(body):
  """Remove the simple markdown used by Google Groups."""
  return body.replace('*', '')


class IntentEmailHandler(basehandlers.FlaskHandler):
  """This task handles an inbound email to detect intent threads."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self):
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

    approval_field = detect_field(subject)
    if not approval_field:
      logging.info('This does not appear to be an intent')
      return {'message': 'Not an intent'}

    feature_id = detect_feature_id(body)
    thread_url = detect_thread_url(body)
    feature, message = self.load_detected_feature(
        feature_id, thread_url, approval_field)
    if message:
      logging.info(message)
      return {'message': message}
    if not feature:
      logging.info('Could not retrieve feature')
      return {'message': 'Feature not found'}

    self.set_intent_thread_url(feature, approval_field, thread_url, subject)
    self.create_approvals(feature, approval_field, from_addr, body)
    return {'message': 'Done'}

  def load_detected_feature(self, feature_id, thread_url, approval_field):
    """Find the feature being referenced by this email message.

    Returns a pair with the feature and an error message, either of
    which can be None.
    """
    # If the message had a link to a chromestatus entry, use its ID.
    if feature_id:
      return models.Feature.get_by_id(feature_id), None

    # If there is also no thread_url, then give up.
    if not thread_url:
      return None, 'No feature ID or discussion link'

    # Find the feature by querying for the previously saved discussion link.
    matching_features = []
    if approval_field == approval_defs.PrototypeApproval:
      query = models.Feature.query(
          models.Feature.intent_to_implement_url == thread_url)
      matching_features = query.fetch()
    # TODO(jrobbins): Ready-for-trial threads
    elif approval_field == approval_defs.ExperimentApproval:
      query = models.Feature.query(
          models.Feature.intent_to_experiment_url == thread_url)
      matching_features = query.fetch()
    elif approval_field == approval_defs.ExtendExperimentApproval:
      query = models.Feature.query(
          models.Feature.intent_to_extend_experiment_url == thread_url)
      matching_features = query.fetch()
    elif approval_field == approval_defs.ShipApproval:
      query = models.Feature.query(
          models.Feature.intent_to_ship_url == thread_url)
      matching_features = query.fetch()
    else:
      return None, 'Unsupported approval field'

    if len(matching_features) == 0:
      return None, 'No feature entry references this discussion thread'
    if len(matching_features) > 1:
      ids = [f.key.integer_id() for f in matching_features]
      return None, 'Ambiguous feature entries %r' % ids

    return matching_features[0], None

  def set_intent_thread_url(
      self, feature, approval_field, thread_url, subject):
    """If the feature has no previous thread URL for this intent, set it."""
    if not thread_url:
      return

    if (approval_field == approval_defs.PrototypeApproval and
        not feature.intent_to_implement_url):
      feature.intent_to_implement_url = thread_url
      feature.intent_to_implement_subject_line = subject
      feature.put()

    # TODO(jrobbins): Ready-for-trial threads

    if (approval_field == approval_defs.ExperimentApproval and
        not feature.intent_to_experiment_url):
      feature.intent_to_experiment_url = thread_url
      feature.intent_to_experiment_subject_line = subject
      feature.put()

    if (approval_field == approval_defs.ExtendExperimentApproval and
        not feature.intent_to_extend_experiment_url):
      feature.intent_to_extend_experiment_url = thread_url
      feature.intent_to_extend_experiment_subject_line = subject
      feature.put()

    if (approval_field == approval_defs.ShipApproval and
        not feature.intent_to_ship_url):
      feature.intent_to_ship_url = thread_url
      feature.intent_to_ship_subject_line = subject
      feature.put()

  def create_approvals(self, feature, approval_field, from_addr, body):
    """Store either a REVIEW_REQUESTED or an APPROVED approval value."""
    feature_id = feature.key.integer_id()

    # Case 1: Detect LGTMs in body, verify that sender has permission,
    # set an approval value, and clear the original REVIEW_REQUESTED if
    # the approval rule (1 or 3 LTGMs) is satisfied.
    if (detect_lgtm(body) and
        is_lgtm_allowed(from_addr, feature, approval_field)):
      logging.info('found LGTM')
      review_models.Approval.set_approval(
          feature_id, approval_field.field_id,
          review_models.Approval.APPROVED, from_addr)
      self.record_lgtm(feature, approval_field, from_addr)

    # Case 2: Create a review request for any discussion that does not already
    # have any approval values stored.
    elif detect_new_thread(feature_id, approval_field):
      logging.info('found new thread')
      if approval_field in FIELDS_REQUIRING_LGTMS:
        logging.info('requesting a review')
        review_models.Approval.set_approval(
            feature_id, approval_field.field_id,
            review_models.Approval.REVIEW_REQUESTED, from_addr)

  def record_lgtm(self, feature, approval_field, from_addr):
    """Add from_addr to the old way or recording LGTMs."""
    # Note: Intent-to-prototype and Intent-to-extend are not checked
    # here because there are no old fields for them.

    if (approval_field == approval_defs.ExperimentApproval and
        from_addr not in feature.i2e_lgtms):
      feature.i2e_lgtms += [from_addr]
      feature.put()

    if (approval_field == approval_defs.ShipApproval and
        from_addr not in feature.i2s_lgtms):
      feature.i2s_lgtms += [from_addr]
      feature.put()
