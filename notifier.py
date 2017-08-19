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

import logging
import datetime
import json
import os
import webapp2

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue

import common
import settings
import models


class PushSubscription(models.DictModel):
  subscription_id = db.StringProperty(required=True)


def get_default_headers():
  headers = {
    'Authorization': 'key=%s' % settings.FIREBASE_SERVER_KEY,
    'Content-Type': 'application/json'
    }
  return headers

def create_wf_content_list(component):
  list = ''
  wf_component_content = models.BlinkComponent.fetch_wf_content_for_components()
  content = wf_component_content.get(component)
  if not content:
    return '<li>None</li>'

  for url in content:
    list += '<li><a href="{url}">{url}</a>. Last updated: {updatedOn})</li>'.format(
        url=url['url'], updatedOn=url['updatedOn'])
  if not wf_component_content:
    list = '<li>None</li>'
  return list

def email_feature_subscribers(feature, is_update=False, changes=[]):
  for component_name in feature.blink_components:
    component = models.BlinkComponent.get_by_name(component_name)
    if not component:
      logging.warn('Blink component "%s" not found. Not sending email to subscribers' % component_name)
      return

    # subscribers = component.subscribers
    # TODO: restrict emails to me for now to see if they're not too noisy.
    subscribers = models.FeatureOwner.all().filter('email = ', 'e.bidelman@google.com').fetch(1)

    if not subscribers:
      logging.info('Blink component "%s" has no subscribers. Skipping email.' % component_name)
      return

    if feature.shipped_milestone:
      milestone_str = feature.shipped_milestone
    elif feature.shipped_milestone is None and feature.shipped_android_milestone:
      milestone_str = feature.shipped_android_milestone + ' (android)'
    else:
      milestone_str = 'not yet assigned'

    created_on = datetime.datetime.strptime(str(feature.created), "%Y-%m-%d %H:%M:%S.%f").date()
    new_msg = """
<html><body>
<p>Hi {subscribers},</p>

<p>You are listed as a web platform owner for "{component_name}". {created_by} added a new feature to this component:</p>
<hr>

<p><b><a href="https://www.chromestatus.com/feature/{id}">{name}</a></b> (added {created})</p>
<p><b>Milestone</b>: {milestone}</p>
<p><b>Implementation status</b>: {status}</p>

<hr>
<p>Next steps:</p>
<ul>
  <li>Try the API, write a sample, provide early feedback to eng.</li>
  <li>Consider authoring a new article/update for /web.</li>
  <li>Write a <a href="https://github.com/GoogleChrome/lighthouse/tree/master/docs/recipes/custom-audit">new Lighthouse audit</a>. This can  help drive adoption of an API over time.</li>
  <li>Add a sample to https://github.com/GoogleChrome/samples (see <a href="https://github.com/GoogleChrome/samples#contributing-samples">contributing</a>).</li>
  <li>Don't forget add your demo link to the <a href="https://www.chromestatus.com/admin/features/edit/{id}">chromestatus feature entry</a>.</li>
</ul>
</body></html>
""".format(name=feature.name, id=feature.key().id(), created=created_on,
           created_by=feature.created_by, component_name=component_name,
           subscribers=', '.join([s.name for s in subscribers]), milestone=milestone_str,
           status=models.IMPLEMENTATION_STATUS[feature.impl_status_chrome])

  updated_on = datetime.datetime.strptime(str(feature.updated), "%Y-%m-%d %H:%M:%S.%f").date()
  formatted_changes = ''
  for prop in changes:
    formatted_changes += '<li>%s: %s -> %s</li>' % (prop['prop_name'], prop['old_val'], prop['new_val'])
  if not formatted_changes:
    formatted_changes = '<li>None</li>'

  update_msg = """<html><body>
<p>Hi {subscribers},</p>

<p>You are listed as a web platform owner for "{component_name}". {updated_by} updated this feature:</p>
<hr>

<p><b><a href="https://www.chromestatus.com/feature/{id}">{name}</a></b> (updated {updated})</p>
<p><b>Milestone</b>: {milestone}</p>
<p><b>Implementation status</b>: {status}</p>

<p>Changes:</p>
<ul>
{formatted_changes}
</ul>

<hr>
<p>Next steps:</p>
<ul>
<li>Check existing <a href="https://github.com/GoogleChrome/lighthouse/tree/master/lighthouse-core/audits">Lighthouse audits</a> for correctness.</li>
<li>Check existing /web content for correctness. Non-exhaustive list:
  <ul>{wf_content}</ul>
</li>
</ul>
</body></html>
""".format(name=feature.name, id=feature.key().id(), updated=updated_on,
           updated_by=feature.updated_by, component_name=component_name,
           subscribers=', '.join([s.name for s in subscribers]), milestone=milestone_str,
           status=models.IMPLEMENTATION_STATUS[feature.impl_status_chrome],
           formatted_changes=formatted_changes,
           wf_content=create_wf_content_list(component_name))

  message = mail.EmailMessage(sender='Chromestatus <admin@cr-status.appspotmail.com>',
                              subject='update',
                              to=[s.email for s in subscribers])

  if is_update:
    message.html = update_msg
    message.subject = 'updated feature: %s' % feature.name
  else:
    message.html = new_msg
    message.subject = 'new feature: %s' % feature.name

  message.check_initialized()

  if settings.SEND_EMAIL:
    message.send()


class EmailHandler(webapp2.RequestHandler):

  def post(self):
    json_body = json.loads(self.request.body)
    feature = json_body.get('feature') or None
    is_update = json_body.get('is_update') or False
    changes = json_body.get('changes') or []

    # Email feature subscribers if the feature exists and there were actually changes to it.
    feature = models.Feature.get_by_id(feature['id'])
    if feature and (is_update and len(changes) or not is_update):
      email_feature_subscribers(feature, is_update=is_update, changes=changes)


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


app = webapp2.WSGIApplication([
  ('/admin/notifications/list', NotificationsListHandler),
  ('/tasks/email-subscribers', EmailHandler),
  ('/tasks/send_notifications', NotificationSendHandler),
  ('/features/push/new', NotificationNewSubscriptionHandler),
  ('/features/push/info', NotificationSubscriptionInfoHandler),
  ('/features/push/subscribe/([0-9]*)', NotificationSubscribeHandler),
], debug=settings.DEBUG)