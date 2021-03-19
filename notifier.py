from __future__ import division
from __future__ import print_function

# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc.
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

__author__ = 'ericbidelman@chromium.org (Eric Bidelman)'

import collections
import logging
import datetime
import json
import os
import re

from framework import ramcache
from google.appengine.ext import db
from google.appengine.api import mail
import requests
from google.appengine.api import users
from google.appengine.ext.webapp.mail_handlers import BounceNotification

from django.template.loader import render_to_string
from django.utils.html import conditional_escape as escape

from framework import basehandlers
from framework import cloud_tasks_helpers
import settings
import models


def format_email_body(is_update, feature, changes):
  """Return an HTML string for a notification email body."""
  if feature.shipped_milestone:
    milestone_str = feature.shipped_milestone
  elif feature.shipped_milestone is None and feature.shipped_android_milestone:
    milestone_str = '%s (android)' % feature.shipped_android_milestone
  else:
    milestone_str = 'not yet assigned'

  moz_link_urls = [link for link in feature.doc_links
                   if 'developer.mozilla.org' in link]

  formatted_changes = ''
  for prop in changes:
    prop_name = prop['prop_name']
    new_val = prop['new_val']
    old_val = prop['old_val']

    formatted_changes += ('<li><b>%s:</b> <br/><b>old:</b> %s <br/>'
                          '<b>new:</b> %s<br/></li><br/>' %
                          (prop_name, escape(old_val), escape(new_val)))
  if not formatted_changes:
    formatted_changes = '<li>None</li>'

  body_data = {
      'feature': feature,
      'id': feature.key().id(),
      'milestone': milestone_str,
      'status': models.IMPLEMENTATION_STATUS[feature.impl_status_chrome],
      'formatted_changes': formatted_changes,
      'moz_link_urls': moz_link_urls,
  }
  template_path = ('update-feature-email.html' if is_update
                   else 'new-feature-email.html')
  body = render_to_string(template_path, body_data)
  return body


def accumulate_reasons(addr_reasons, user_list, reason):
  """Add a reason string for each user."""
  for user in user_list:
    if type(user) == str:
      addr_reasons[user].append(reason)
    else:
      addr_reasons[user.email].append(reason)


def convert_reasons_to_task(addr, reasons, email_html, subject):
  """Add a task dict to task_list for each user who has not already got one."""
  assert reasons, 'We are emailing someone without any reason'
  footer_lines = ['<p>You are receiving this email because:</p>', '<ul>']
  for reason in sorted(set(reasons)):
    footer_lines.append('<li>%s</li>' % reason)
  footer_lines.append('</ul>')
  footer_lines.append('<p><a href="%ssettings">Unsubscribe</a></p>' %
                      settings.SITE_URL)
  email_html_with_footer = email_html + '\n\n' + '\n'.join(footer_lines)
  one_email_task = {
      'to': addr,
      'subject': subject,
      'html': email_html_with_footer
  }
  return one_email_task


WEBVIEW_RULE_REASON = (
    'This feature has an android milestone, but not a webview milestone')
WEBVIEW_RULE_ADDRS = ['webview-leads-external@google.com']


def apply_subscription_rules(feature, changes):
  """Return {"reason": [addrs]} for users who set up rules."""
  # Note: for now this is hard-coded, but it will eventually be
  # configurable through some kind of user preference.
  changed_field_names = {c['prop_name'] for c in changes}
  results = {}

  # Check if feature has some other milestone set, but not webview.
  if (feature.shipped_android_milestone and
      not feature.shipped_webview_milestone):
    milestone_fields = ['shipped_android_milestone']
    if not changed_field_names.isdisjoint(milestone_fields):
      results[WEBVIEW_RULE_REASON] = WEBVIEW_RULE_ADDRS

  return results


def make_email_tasks(feature, is_update=False, changes=[]):
  """Return a list of task dicts to notify users of feature changes."""
  feature_watchers = models.FeatureOwner.all().filter(
      'watching_all_features = ', True).fetch(None)

  email_html = format_email_body(is_update, feature, changes)
  if is_update:
    subject = 'updated feature: %s' % feature.name
  else:
    subject = 'new feature: %s' % feature.name

  addr_reasons = collections.defaultdict(list)  # [{email_addr: [reason,...]}]

  accumulate_reasons(
      addr_reasons, feature_watchers,
      'You are watching all feature changes')

  # There will always be at least one component.
  for component_name in feature.blink_components:
    component = models.BlinkComponent.get_by_name(component_name)
    if not component:
      logging.warn('Blink component "%s" not found.'
                   'Not sending email to subscribers' % component_name)
      continue

    accumulate_reasons(
        addr_reasons, component.owners,
        'You are an owner of this feature\'s component')
    accumulate_reasons(
        addr_reasons, component.subscribers,
        'You subscribe to this feature\'s component')

  starrers = FeatureStar.get_feature_starrers(feature.key().id())
  accumulate_reasons(addr_reasons, starrers, 'You starred this feature')

  rule_results = apply_subscription_rules(feature, changes)
  for reason, sub_addrs in rule_results.items():
    accumulate_reasons(addr_reasons, sub_addrs, reason)

  all_tasks = [convert_reasons_to_task(addr, reasons, email_html, subject)
               for addr, reasons in sorted(addr_reasons.items())]
  return all_tasks


class FeatureStar(models.DictModel):
  """A FeatureStar represent one user's interest in one feature."""
  email = db.EmailProperty(required=True)
  feature_id = db.IntegerProperty(required=True)
  # This is so that we do not sync a bell to a star that the user has removed.
  starred = db.BooleanProperty(default=True)

  @classmethod
  def get_star(self, email, feature_id):
    """If that user starred that feature, return the model or None."""
    q = FeatureStar.all()
    q.filter('email =', email)
    q.filter('feature_id =', feature_id)
    return q.get()

  @classmethod
  def set_star(self, email, feature_id, starred=True):
    """Set/clear a star for the specified user and feature."""
    feature_star = self.get_star(email, feature_id)
    if not feature_star and starred:
      feature_star = FeatureStar(email=email, feature_id=feature_id)
      feature_star.put()
    elif feature_star and feature_star.starred != starred:
      feature_star.starred = starred
      feature_star.put()
    else:
      return  # No need to update anything in datastore

    feature = models.Feature.get_by_id(feature_id)
    feature.star_count += 1 if starred else -1
    if feature.star_count < 0:
      logging.error('count would be < 0: %r', (email, feature_id, starred))
      return
    feature.put(notify=False)

  @classmethod
  def get_user_stars(self, email):
    """Return a list of feature_ids of all features that the user starred."""
    q = FeatureStar.all()
    q.filter('email =', email)
    q.filter('starred =', True)
    feature_stars = q.fetch(None)
    logging.info('found %d stars for %r', len(feature_stars), email)
    feature_ids = [fs.feature_id for fs in feature_stars]
    logging.info('returning %r', feature_ids)
    return feature_ids

  @classmethod
  def get_feature_starrers(self, feature_id):
    """Return list of UserPref objects for starrers that want notifications."""
    q = FeatureStar.all()
    q.filter('feature_id =', feature_id)
    q.filter('starred =', True)
    feature_stars = q.fetch(None)
    logging.info('found %d stars for %r', len(feature_stars), feature_id)
    emails = [fs.email for fs in feature_stars]
    logging.info('looking up %r', emails)
    user_prefs = models.UserPref.get_prefs_for_emails(emails)
    user_prefs = [up for up in user_prefs
                  if up.notify_as_starrer and not up.bounced]
    return user_prefs


class FeatureChangeHandler(basehandlers.FlaskHandler):
  """This task handles a feature creation or update by making email tasks."""

  def process_post_data(self):
    self.require_task_header()

    json_body = self.request.get_json(force=True)
    feature = json_body.get('feature') or None
    is_update = json_body.get('is_update') or False
    changes = json_body.get('changes') or []

    logging.info('Starting to notify subscribers for feature %r', feature)

    # Email feature subscribers if the feature exists and there were
    # actually changes to it.
    feature = models.Feature.get_by_id(feature['id'])
    if feature and (is_update and len(changes) or not is_update):
      email_tasks = make_email_tasks(
          feature, is_update=is_update, changes=changes)
      logging.info('Processing %d email tasks', len(email_tasks))
      for one_email_dict in email_tasks:
        cloud_tasks_helpers.enqueue_task(
            '/tasks/outbound-email', one_email_dict)

    return {'message': 'Done'}


class OutboundEmailHandler(basehandlers.FlaskHandler):
  """Task to send a notification email to one recipient."""

  def process_post_data(self):
    self.require_task_header()

    json_body = self.request.get_json(force=True)
    to = json_body['to']
    subject = json_body['subject']
    email_html = json_body['html']

    if settings.SEND_ALL_EMAIL_TO:
      to_user, to_domain = to.split('@')
      to = settings.SEND_ALL_EMAIL_TO % {'user': to_user, 'domain': to_domain}

    message = mail.EmailMessage(
        sender='Chromestatus <admin@%s.appspotmail.com>' % settings.APP_ID,
        to=to, subject=subject, html=email_html)
    message.check_initialized()

    logging.info('Will send the following email:\n')
    logging.info('To: %s', message.to)
    logging.info('Subject: %s', message.subject)
    logging.info('Body:\n%s', message.html)
    if settings.SEND_EMAIL:
      message.send()
      logging.info('Email sent')
    else:
      logging.info('Email not sent because of settings.SEND_EMAIL')

    return {'message': 'Done'}


class BouncedEmailHandler(basehandlers.FlaskHandler):
  BAD_WRAP_RE = re.compile('=\r\n')
  BAD_EQ_RE = re.compile('=3D')

  """Handler to notice when email to given user is bouncing."""
  # For docs on AppEngine's bounce email handling, see:
  # https://cloud.google.com/appengine/docs/python/mail/bounce
  # Source code is in file:
  # google_appengine/google/appengine/ext/webapp/mail_handlers.py
  def process_post_data(self):
    self.receive(BounceNotification(self.form))
    return {'message': 'Done'}

  def receive(self, bounce_message):
    email_addr = bounce_message.original.get('to')
    subject = 'Mail to %r bounced' % email_addr
    logging.info(subject)
    pref_list = models.UserPref.get_prefs_for_emails([email_addr])
    user_pref = pref_list[0]
    user_pref.bounced = True
    user_pref.put()

    # Escalate to someone who might do something about it, e.g.
    # find a new owner for a component.
    body = ('The following message bounced.\n'
            '=================\n'
            'From: {from}\n'
            'To: {to}\n'
            'Subject: {subject}\n\n'
            '{text}\n'.format(**bounce_message.original))
    logging.info(body)
    message = mail.EmailMessage(
        sender='Chromestatus <admin@%s.appspotmail.com>' % settings.APP_ID,
        to=settings.BOUNCE_ESCALATION_ADDR, subject=subject, body=body)
    message.check_initialized()
    if settings.SEND_EMAIL:
      message.send()


app = basehandlers.FlaskApplication([
  ('/tasks/email-subscribers', FeatureChangeHandler),
  ('/tasks/outbound-email', OutboundEmailHandler),
  ('/_ah/bounce', BouncedEmailHandler),
], debug=settings.DEBUG)
