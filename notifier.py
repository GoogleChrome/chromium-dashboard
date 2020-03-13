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
import webapp2

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.api import taskqueue
from google.appengine.ext.webapp.mail_handlers import BounceNotificationHandler

from django.template.loader import render_to_string
from django.utils.html import conditional_escape as escape

import common
import settings
import models


def get_default_headers():
  headers = {
    'Authorization': 'key=%s' % settings.FIREBASE_SERVER_KEY,
    'Content-Type': 'application/json'
    }
  return headers


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

    formatted_changes += ('<li>%s: <br/><b>old:</b> %s <br/>'
                          '<b>new:</b> %s<br/></li>\n' %
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
    addr_reasons[user.email].append(reason)


def convert_reasons_to_task(addr, reasons, email_html, subject):
  """Add a task dict to task_list for each user who has not already got one."""
  assert reasons, 'We are emailing someone without any reason'
  footer_lines = ['<p>You are receiving this email because:</p>', '<ul>']
  for reason in sorted(set(reasons)):
    footer_lines.append('<li>%s</li>' % reason)
  footer_lines.append('</ul>')
  email_html_with_footer = email_html + '\n\n' + '\n'.join(footer_lines)
  one_email_task = {
      'to': addr,
      'subject': subject,
      'html': email_html_with_footer
  }
  return one_email_task


def make_email_tasks(feature, is_update=False, changes=[]):
  """Return a list of task dicts to notify users of feature changes."""
  feature_watchers = models.FeatureOwner.all().filter('watching_all_features = ', True).fetch(None)

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

  all_tasks = [convert_reasons_to_task(addr, reasons, email_html, subject)
               for addr, reasons in sorted(addr_reasons.items())]
  return all_tasks


class PushSubscription(models.DictModel):
  subscription_id = db.StringProperty(required=True)


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


class FeatureChangeHandler(webapp2.RequestHandler):
  """This task handles a feature creation or update by making email tasks."""

  def post(self):
    json_body = json.loads(self.request.body)
    feature = json_body.get('feature') or None
    is_update = json_body.get('is_update') or False
    changes = json_body.get('changes') or []

    # Email feature subscribers if the feature exists and there were
    # actually changes to it.
    feature = models.Feature.get_by_id(feature['id'])
    if feature and (is_update and len(changes) or not is_update):
      email_tasks = make_email_tasks(
          feature, is_update=is_update, changes=changes)
      for one_email_dict in email_tasks:
        payload = json.dumps(one_email_dict)
        task = taskqueue.Task(
            method='POST', url='/tasks/outbound-email', payload=payload,
            target='notifier')
        taskqueue.Queue().add(task)


class OutboundEmailHandler(webapp2.RequestHandler):
  """Task to send a notification email to one recipient."""

  def post(self):
    json_body = json.loads(self.request.body)
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


class NotificationNewSubscriptionHandler(webapp2.RequestHandler):

  def post(self):
    json_body = json.loads(self.request.body)
    subscription_id = json_body.get('subscriptionId') or None

    if subscription_id is None:
      return

    # Don't add duplicate tokens.
    query = PushSubscription.all(keys_only=True).filter('subscription_id =', subscription_id)
    found_token = query.get()
    if found_token is None:
      subscription = PushSubscription(subscription_id=subscription_id)
      subscription.put()


class SetStarHandler(webapp2.RequestHandler):
  """Handle JSON API requests to set/clear a star."""

  def post(self):
    """Stars or unstars a feature for the signed in user."""
    json_body = json.loads(self.request.body)
    feature_id = json_body.get('featureId')
    starred = json_body.get('starred', True)

    if type(feature_id) != int:
      logging.info('Invalid feature_id: %r', feature_id)
      self.abort(400)

    feature = models.Feature.get_feature(feature_id)
    if not feature:
      logging.info('feature not found: %r', feature_id)
      self.abort(404)

    user = users.get_current_user()
    if not user:
      logging.info('User must be signed in before starring')
      self.abort(400)

    FeatureStar.set_star(user.email(), feature_id, starred)
    data = {}
    self.response.headers['Content-Type'] = 'application/json;charset=utf-8'
    result = self.response.write(json.dumps(data, separators=(',',':')))


class GetUserStarsHandler(webapp2.RequestHandler):
  """Handle JSON API requests list all stars for current user."""

  def post(self):
    """Returns a list of starred feature_ids for the signed in user."""
    # Note: the post body is not used.

    user = users.get_current_user()
    if user:
      feature_ids = FeatureStar.get_user_stars(user.email())
    else:
      feature_ids = []  # Anon users cannot star features.

    data = {
        'featureIds': feature_ids,
        }
    self.response.headers['Content-Type'] = 'application/json;charset=utf-8'
    result = self.response.write(json.dumps(data, separators=(',',':')))



class NotificationSubscribeHandler(webapp2.RequestHandler):

  def post(self, feature_id=None):
    """Subscribes or unsubscribes a token to a topic."""
    json_body = json.loads(self.request.body)
    subscription_id = json_body.get('subscriptionId') or None
    remove = json_body.get('remove') or False

    if subscription_id is None or feature_id is None:
      return

    data = {}
    topic_id = feature_id if feature_id else 'new-feature'
    url = 'https://iid.googleapis.com/iid/v1/%s/rel/topics/%s' % (subscription_id, topic_id)

    if remove:
      url = 'https://iid.googleapis.com/iid/v1:batchRemove'
      data = """{{
        "to": "/topics/{topic_id}",
        "registration_tokens": ["{token}"]
      }}""".format(topic_id=topic_id, token=subscription_id)

    result = urlfetch.fetch(url=url, payload=data, method=urlfetch.POST,
                            headers=get_default_headers())

    if result.status_code != 200:
      logging.error('Error: subscribing %s to topic: %s' % (subscription_id, topic_id))
      return


class NotificationSendHandler(webapp2.RequestHandler):

  def _send_notification_to_feature_subscribers(self, feature, is_update=False):
    """Sends a notification to users when new features are added or updated.

    Args:
      feature: Feature that was added/modified.
      is_update: True if this was an update to the feature. False if it was newly added.
    """
    if not settings.SEND_PUSH_NOTIFICATIONS:
      return

    feature_id = feature.key().id()
    topic_id = feature_id if is_update else 'new-feature'

    data = """{{
      "notification": {{
        "title": "{title}",
        "body": "{added_str}. Click here for more information.",
        "icon": "/static/img/crstatus_192.png",
        "click_action": "https://www.chromestatus.com/feature/{id}"
      }},
      "to": "/topics/{topic_id}"
    }}""".format(title=feature.name, id=feature_id, topic_id=topic_id,
        added_str=('Was updated' if is_update else 'New feature added'))

    result = urlfetch.fetch(url='https://fcm.googleapis.com/fcm/send',
        payload=data, method=urlfetch.POST, headers=get_default_headers())

    if result.status_code != 200:
      logging.error('Error sending notification to topic %s. %s' % (topic_id, result.content))
      return

  def post(self):
    json_body = json.loads(self.request.body)
    feature = json_body.get('feature') or None
    is_update = json_body.get('is_update') or False
    changes = json_body.get('changes') or []

    # Email feature subscribers if the feature exists and there were changes to it.
    feature = models.Feature.get_by_id(feature['id'])
    if feature and (is_update and len(changes) or not is_update):
      self._send_notification_to_feature_subscribers(feature=feature, is_update=is_update)


class NotificationSubscriptionInfoHandler(webapp2.RequestHandler):
  def post(self):
    json_body = json.loads(self.request.body)
    subscription_id = json_body.get('subscriptionId') or None

    if subscription_id is None:
      return

    url = 'https://iid.googleapis.com/iid/info/%s?details=true' % subscription_id
    result = urlfetch.fetch(url=url, method=urlfetch.GET, headers=get_default_headers())

    if result.status_code != 200:
      logging.error('Error: fetching info for subscription %s' % subscription_id)
      self.response.set_status(400, message=result.content)
      self.response.write(result.content)
      return

    self.response.write(result.content)


class NotificationsListHandler(common.ContentHandler):
  def get(self):
    subscriptions = PushSubscription.all().fetch(None)

    template_data = {
      'FIREBASE_SERVER_KEY': settings.FIREBASE_SERVER_KEY,
      'subscriptions': json.dumps([s.subscription_id for s in subscriptions])
    }
    self.render(data=template_data, template_path=os.path.join('admin/notifications/list.html'))



class BouncedEmailHandler(BounceNotificationHandler):
  BAD_WRAP_RE = re.compile('=\r\n')
  BAD_EQ_RE = re.compile('=3D')

  """Handler to notice when email to given user is bouncing."""
  # For docs on AppEngine's bounce email handling, see:
  # https://cloud.google.com/appengine/docs/python/mail/bounce
  # Source code is in file:
  # google_appengine/google/appengine/ext/webapp/mail_handlers.py
  def post(self):
    try:
      super(BouncedEmail, self).post()
    except AttributeError:
      # Work-around for
      # https://code.google.com/p/googleappengine/issues/detail?id=13512
      raw_message = self.request.POST.get('raw-message')
      logging.info('raw_message %r', raw_message)
      raw_message = self.BAD_WRAP_RE.sub('', raw_message)
      raw_message = self.BAD_EQ_RE.sub('=', raw_message)
      logging.info('fixed raw_message %r', raw_message)
      mime_message = email.message_from_string(raw_message)
      logging.info('get_payload gives %r', mime_message.get_payload())
      self.request.POST['raw-message'] = mime_message
      super(BouncedEmail, self).post()  # Retry with mime_message

  def receive(self, bounce_message):
    email_addr = bounce_message.original.get('to')
    msg = 'Mail to %r bounced' % email_addr
    logging.info(msg)
    pref_list = models.UserPref.get_prefs_for_emails([email_addr])
    user_pref = pref_list[0]
    user_pref.bounced = True
    user_pref.put()

    # Escalate to someone who might do something about it, e.g.
    # find a new owner for a component.
    message = mail.EmailMessage(
        sender='Chromestatus <admin@%s.appspotmail.com>' % settings.APP_ID,
        to=settings.BOUNCE_ESCALATION_ADDR,
        subject=msg,
        html='See subject.  Check logs.')
    message.check_initialized()
    if settings.SEND_EMAIL:
      message.send()



app = webapp2.WSGIApplication([
  ('/admin/notifications/list', NotificationsListHandler),
  ('/tasks/email-subscribers', FeatureChangeHandler),
  ('/tasks/outbound-email', OutboundEmailHandler),
  ('/tasks/send_notifications', NotificationSendHandler),
  ('/features/push/new', NotificationNewSubscriptionHandler),
  ('/features/push/info', NotificationSubscriptionInfoHandler),
  ('/features/push/subscribe/([0-9]*)', NotificationSubscribeHandler),
  ('/features/star/set', SetStarHandler),
  ('/features/star/list', GetUserStarsHandler),
  ('/_ah/bounce', BouncedEmailHandler),
], debug=settings.DEBUG)

app.error_handlers[404] = common.handle_404

if settings.PROD and not settings.DEBUG:
  app.error_handlers[500] = common.handle_500
