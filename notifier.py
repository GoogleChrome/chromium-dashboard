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

def send_notification_to_feature_subscribers(feature=None, is_update=False):
  data = """{{
    "notification": {{
      "title": "{title}",
      "body": "{added_str}. Click here for more information.",
      "icon": "/static/img/crstatus_192.png",
      "click_action": "https://www.chromestatus.com/feature/{id}"
    }},
    "to": "/topics/{id}"
  }}""".format(title=feature.name, id=feature.key().id(),
               added_str=('Was updated' if is_update else 'Was added'))

  result = urlfetch.fetch(url='https://fcm.googleapis.com/fcm/send',
      payload=data, method=urlfetch.POST, headers=get_default_headers())

  if result.status_code != 200:
    logging.error('Error: sending notification to topic: %s' % result.content)
    return

  resp = json.loads(result.content)

def create_wf_content_list(component):
  list = ''
  wf_component_content = models.BlinkComponent.fetch_wf_content_for_components()
  content = wf_component_content.get(component)
  if not content:
    return []

  for url in content:
    list += '    - <a href="{url}">{url}</a>. Last updated: {updatedOn})\n'.format(
        url=url['url'], updatedOn=url['updatedOn'])
  if not wf_component_content:
    list = 'None'
  return list

def email_feature_owners(feature, is_update=False, changes=[]):
  for component_name in feature.blink_components:
    component = models.BlinkComponent.get_by_name(component_name)
    if not component:
      logging.warn('Blink component "%s" not found. Not sending email to owners' % component_name)
      return

    owner_names = [owner.name for owner in component.owners]
    if not owner_names:
      logging.info('Blink component "%s" has no owners. Skipping email.' % component_name)
      return

    if feature.shipped_milestone:
      milestone_str = feature.shipped_milestone
    elif feature.shipped_milestone is None and feature.shipped_android_milestone:
      milestone_str = feature.shipped_android_milestone + ' (android)'
    else:
      milestone_str = 'not yet assigned'

    created_on = datetime.datetime.strptime(str(feature.created), "%Y-%m-%d %H:%M:%S.%f").date()
    new_msg = """
Hi {owners},

{created_by} added a new feature to chromestatus. You are listed as a web platform owner for "{component_name}".
See https://www.chromestatus.com/feature/{id} for more details.
---

Feature: {name}

Created: {created}
Implementation status: {status}
Milestone: {milestone}

---
Next steps:
- Try the API, write a sample, provide early feedback to eng.
- Consider authoring a new article/update for /web.
- Write a <a href="https://github.com/GoogleChrome/lighthouse/tree/master/docs/recipes/custom-audit">new Lighthouse audit</a>. This can  help drive adoption of an API over time.
- Add a sample to https://github.com/GoogleChrome/samples (see <a href="https://github.com/GoogleChrome/samples#contributing-samples">contributing</a>).
  - Don't forget add your demo link to the <a href="https://www.chromestatus.com/admin/features/edit/{id}">chromestatus feature entry</a>.
""".format(name=feature.name, id=feature.key().id(), created=created_on,
           created_by=feature.created_by, component_name=component_name,
           owners=', '.join(owner_names), milestone=milestone_str,
           status=models.IMPLEMENTATION_STATUS[feature.impl_status_chrome])

  updated_on = datetime.datetime.strptime(str(feature.updated), "%Y-%m-%d %H:%M:%S.%f").date()
  formatted_changes = ''
  for prop in changes:
    formatted_changes += '- %s: %s -> %s\n' % (prop['prop_name'], prop['old_val'], prop['new_val'])
  if not formatted_changes:
    formatted_changes = 'None'

  update_msg = """
Hi {owners},

{updated_by} updated a feature on chromestatus. You are listed as a web platform owner for "{component_name}".
See https://www.chromestatus.com/feature/{id} for more details.
---

Feature: <a href="https://www.chromestatus.com/feature/{id}">{name}</a>

Updated: {updated}
Implementation status: {status}
Milestone: {milestone}

Changes:
{formatted_changes}

---
Next steps:
- Check existing <a href="https://github.com/GoogleChrome/lighthouse/tree/master/lighthouse-core/audits">Lighthouse audits</a> for correctness.
- Check existing /web content for correctness. Non-exhaustive list:
{wf_content}
""".format(name=feature.name, id=feature.key().id(), updated=updated_on,
           updated_by=feature.updated_by, component_name=component_name,
           owners=', '.join(owner_names), milestone=milestone_str,
           status=models.IMPLEMENTATION_STATUS[feature.impl_status_chrome],
           formatted_changes=formatted_changes,
           wf_content=create_wf_content_list(component_name))

  message = mail.EmailMessage(sender='Chromestatus <admin@cr-status.appspotmail.com>',
                              subject='chromestatus update',
                              to=[owner.email for owner in component.owners])

  if is_update:
    message.html = update_msg
    message.subject = 'chromestatus: updated feature'
  else:
    message.html = new_msg
    message.subject = 'chromestatus: new feature'

  message.check_initialized()

  if settings.SEND_EMAIL:
    message.send()


class EmailOwnersHandler(webapp2.RequestHandler):
  def post(self):
    json_body = json.loads(self.request.body)
    feature = json_body.get('feature') or None
    is_update = json_body.get('is_update') or False
    changes = json_body.get('changes') or []

    # Email feature owners if the feature exists and there were actually changes to it.
    feature = models.Feature.get_by_id(feature['id'])
    if feature and (is_update and len(changes) or not is_update):
      email_feature_owners(feature, is_update=is_update, changes=changes)


class PushNotificationNewSubscriptionHandler(webapp2.RequestHandler):
  def post(self):
    json_body = json.loads(self.request.body)
    subscription_id = json_body.get('subscriptionId') or None

    if subscription_id is None:
      return

    # Don't add duplicates
    query = PushSubscription.all(keys_only=True).filter('subscription_id =', subscription_id)
    found_token = query.get()
    if found_token is None:
      subscription = PushSubscription(subscription_id=subscription_id)
      subscription.put()


class PushNotificationSubscribeHandler(webapp2.RequestHandler):
  def post(self, feature_id=None):
    json_body = json.loads(self.request.body)
    subscription_id = json_body.get('subscriptionId') or None
    remove = json_body.get('remove') or False

    if subscription_id is None or feature_id is None:
      return

    data = {}
    if remove:
      url = 'https://iid.googleapis.com/iid/v1:batchRemove'
      data = """{{
        "to": "/topics/{feature_id}",
        "registration_tokens": ["{token}"]
      }}""".format(feature_id=feature_id, token=subscription_id)
    else:
      url = 'https://iid.googleapis.com/iid/v1/%s/rel/topics/%s' % (subscription_id, feature_id)

    result = urlfetch.fetch(url=url, payload=data, method=urlfetch.POST, headers=get_default_headers())

    if result.status_code != 200:
      logging.error('Error: subscribing %s to topic: %s' % (subscription_id, feature_id))
      return

    resp = json.loads(result.content)


class PushNotificationSendHandler(webapp2.RequestHandler):
  def post(self):
    json_body = json.loads(self.request.body)
    feature = json_body.get('feature') or None
    is_update = json_body.get('is_update') or False
    changes = json_body.get('changes') or []

    # Email feature owners if the feature exists and there were changes to it.
    feature = models.Feature.get_by_id(feature['id'])
    if feature and (is_update and len(changes) or not is_update):
      send_notification_to_feature_subscribers(feature=feature, is_update=is_update)


class PushNotificationSubscriptionInfoHandler(webapp2.RequestHandler):
  def post(self):
    json_body = json.loads(self.request.body)
    subscription_id = json_body.get('subscriptionId') or None

    if subscription_id is None:
      return

    url = 'https://iid.googleapis.com/iid/info/%s?details=true' % subscription_id
    result = urlfetch.fetch(url=url, method=urlfetch.GET, headers=get_default_headers())

    if result.status_code != 200:
      logging.error('Error: fetching info for subscription %s' % subscription_id)
      return

    self.response.write(result.content)


app = webapp2.WSGIApplication([
  ('/tasks/email-owners', EmailOwnersHandler),
  ('/tasks/send_notifications', PushNotificationSendHandler),
  ('/features/push/new', PushNotificationNewSubscriptionHandler),
  ('/features/push/info', PushNotificationSubscriptionInfoHandler),
  ('/features/push/subscribe/([0-9]*)', PushNotificationSubscribeHandler),
], debug=settings.DEBUG)