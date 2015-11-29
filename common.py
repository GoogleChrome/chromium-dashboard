# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc.
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


import datetime
import json
import logging
import webapp2

# App Engine imports.
from google.appengine.api import users

from django.template.loader import render_to_string
from django.utils import feedgenerator

import models
import settings


class BaseHandler(webapp2.RequestHandler):

  def __init__(self, request, response):
    self.initialize(request, response)

    # Add CORS and Chrome Frame to all responses.
    self.response.headers.add_header('Access-Control-Allow-Origin', '*')
    self.response.headers.add_header('X-UA-Compatible', 'IE=Edge,chrome=1')

    # Settings can't be global in python 2.7 env.
    logging.getLogger().setLevel(logging.DEBUG)


class JSONHandler(BaseHandler):

  def __truncate_day_percentage(self, data):
    # Need 6 decimals b/c num will by mutiplied by 100 to get a percentage.
    data.day_percentage = float("%.*f" % (6, data.day_percentage))
    return data

  def _is_googler(self, user):
    return user and user.email().endswith('@google.com')

  def _clean_data(self, data):

    user = users.get_current_user()
    # Show raw day percentage numbers if user is a googler.
    if not self._is_googler(user):
      data = map(self.__truncate_day_percentage, data)

    return data

  def get(self, data, formatted=False):
    self.response.headers['Content-Type'] = 'application/json;charset=utf-8'
    if formatted:
      return self.response.write(json.dumps(data, separators=(',',':')))
    else:
      data = [entity.to_dict() for entity in data]
      return self.response.write(json.dumps(data, separators=(',',':')))


class ContentHandler(BaseHandler):

  def _is_user_whitelisted(self, user):
    if not user:
      return False

    is_whitelisted = False

    if users.is_current_user_admin():
      is_whitelisted = True
    elif user.email().endswith('@chromium.org'):
      is_whitelisted = True
    else:
      # TODO(ericbidelman): memcache user lookup.
      query = models.AppUser.all(keys_only=True).filter('email =', user.email())
      found_user = query.get()

      if found_user is not None:
        is_whitelisted = True

    return is_whitelisted

  def _add_common_template_values(self, d):
    """Mixin common values for templates into d."""

    template_data = {
      'prod': settings.PROD,
      'APP_TITLE': settings.APP_TITLE,
      'current_path': self.request.path,
      'VULCANIZE': settings.VULCANIZE
      }

    user = users.get_current_user()
    if user:
      template_data['login'] = (
          'Logout', users.create_logout_url(dest_url=self.request.path))
      template_data['user'] = {
        'is_whitelisted': self._is_user_whitelisted(user),
        'is_admin': users.is_current_user_admin(),
        'email': user.email(),
      }
    else:
      template_data['user'] = None
      template_data['login'] = (
          'Login', users.create_login_url(dest_url=self.request.path))

    d.update(template_data)

  def render(self, data={}, template_path=None, status=None, message=None,
             relpath=None):
    if status is not None and status != 200:
      self.response.set_status(status, message)

    # Add common template data to every request.
    self._add_common_template_values(data)

    try:
      self.response.out.write(render_to_string(template_path, data))
    except Exception:
      handle_404(self.request, self.response, Exception)

  def render_atom_feed(self, title, data):
    features_url = '%s://%s%s' % (self.request.scheme,
                                  self.request.host,
                                  self.request.path.replace('.xml', ''))
    feature_url_prefix = '%s://%s%s' % (self.request.scheme,
                                        self.request.host,
                                        '/feature')

    feed = feedgenerator.Atom1Feed(
        title=unicode('%s - %s' % (settings.APP_TITLE, title)),
        link=features_url,
        description=u'New features exposed to web developers',
        language=u'en'
    )
    for f in data:
      pubdate = datetime.datetime.strptime(str(f['updated'][:19]),
                                           '%Y-%m-%d  %H:%M:%S')
      feed.add_item(
          title=unicode(f['name']),
          link='%s/%s' % (feature_url_prefix, f.get('id')),
          description=f.get('summary', ''),
          pubdate=pubdate,
          author_name=unicode(settings.APP_TITLE),
          categories=[f['category']]
      )
    self.response.headers.add_header('Content-Type',
      'application/atom+xml;charset=utf-8')
    self.response.out.write(feed.writeString('utf-8'))


def handle_401(request, response, exception):
  ERROR_401 = (
    '<title>401 Unauthorized</title>\n'
    '<h1>Error: Unauthorized</h1>\n'
    '<h2>User does not have permission to view this page.</h2>')
  response.write(ERROR_401)
  response.set_status(401)

def handle_404(request, response, exception):
  ERROR_404 = (
    '<title>404 Not Found</title>\n'
    '<h1>Error: Not Found</h1>\n'
    '<h2>The requested URL <code>%s</code> was not found on this server.'
    '</h2>' % request.url)
  response.write(ERROR_404)
  response.set_status(404)

def handle_500(request, response, exception):
  logging.exception(exception)
  ERROR_500 = (
    '<title>500 Internal Server Error</title>\n'
    '<h1>Error: 500 Internal Server Error</h1>')
  response.write(ERROR_500)
  response.set_status(500)
