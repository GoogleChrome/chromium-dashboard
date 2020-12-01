from __future__ import division
from __future__ import print_function

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
import re
import time
import traceback
import webapp2

# App Engine imports.
from google.appengine.api import users
from google.appengine.ext import db

import settings
import models

from django.template.loader import render_to_string
from django.utils import feedgenerator
import django

# Initialize django so that it'll function when run as a standalone script.
# https://django.readthedocs.io/en/latest/releases/1.7.html#standalone-scripts
django.setup()


def format_feature_url(feature_id):
  """Return the feature detail page URL for the specified feature."""
  return '/feature/%d' % feature_id


def retry(tries, delay=1, backoff=2):
  """A retry decorator with exponential backoff.

  Functions are retried when Exceptions occur.

  Args:
    tries: int Number of times to retry, set to 0 to disable retry.
    delay: float Initial sleep time in seconds.
    backoff: float Must be greater than 1, further failures would sleep
             delay*=backoff seconds.
  """
  if backoff <= 1:
    raise ValueError("backoff must be greater than 1")
  if tries < 0:
    raise ValueError("tries must be 0 or greater")
  if delay <= 0:
    raise ValueError("delay must be greater than 0")

  def decorator(func):
    def wrapper(*args, **kwargs):
      _tries, _delay = tries, delay
      _tries += 1  # Ensure we call func at least once.
      while _tries > 0:
        try:
          ret = func(*args, **kwargs)
          return ret
        except Exception:
          _tries -= 1
          if _tries == 0:
            logging.error('Exceeded maximum number of retries for %s.',
                          func.__name__)
            raise
          trace_str = traceback.format_exc()
          logging.warning('Retrying %s due to Exception: %s',
                          func.__name__, trace_str)
          time.sleep(_delay)
          _delay *= backoff  # Wait longer the next time we fail.
    return wrapper
  return decorator


def require_edit_permission(handler):
  """Handler decorator to require the user have edit permission."""
  def check_login(self, *args, **kwargs):
    user = users.get_current_user()
    if not user:
      return self.redirect(users.create_login_url(self.request.uri))
    elif not self.user_can_edit(user):
      handle_401(self.request, self.response, Exception)
      return

    return handler(self, *args, **kwargs) # Call the handler method
  return check_login

def strip_trailing_slash(handler):
  """Strips the trailing slash on the URL."""
  def remove_slash(self, *args, **kwargs):
    path = args[0]
    if path[-1] == '/':
      return self.redirect(self.request.path.rstrip('/'))

    return handler(self, *args, **kwargs) # Call the handler method
  return remove_slash


class BaseHandler(webapp2.RequestHandler):

  def __init__(self, request, response):
    self.initialize(request, response)

    # Add CORS and Chrome Frame to all responses.
    self.response.headers.add_header('Access-Control-Allow-Origin', '*')
    self.response.headers.add_header('X-UA-Compatible', 'IE=Edge,chrome=1')

    # Settings can't be global in python 2.7 env.
    logging.getLogger().setLevel(logging.DEBUG)

  def user_can_edit(self, user):
    if not user:
      return False

    can_edit = False

    if users.is_current_user_admin():
      can_edit = True
    elif user.email().endswith(('@chromium.org', '@google.com')):
      can_edit = True
    else:
      # TODO(ericbidelman): memcache user lookup.
      query = models.AppUser.all(keys_only=True).filter('email =', user.email())
      found_user = query.get()

      if found_user is not None:
        can_edit = True

    return can_edit


class JSONHandler(BaseHandler):

  def __truncate_day_percentage(self, data):
    # Need 8 decimals b/c num will by multiplied by 100 to get a percentage and
    # we want 6 decimals.
    data.day_percentage = float("%.*f" % (8, data.day_percentage))
    return data

  def _is_googler(self, user):
    return user and user.email().endswith('@google.com')

  def _clean_data(self, data):
    user = users.get_current_user()
    # Don't show raw percentages if user is not a googler.
    if not self._is_googler(user):
      data = map(self.__truncate_day_percentage, data)
    return data

  def get(self, data, formatted=False, public=True):
    cache_type = 'public'
    if not public:
      cache_type = 'private'

    # Cache script generated json responses.
    self.response.headers['Cache-Control'] = '%s, max-age=%s' % (
        cache_type, settings.DEFAULT_CACHE_TIME)
    self.response.headers['Content-Type'] = 'application/json;charset=utf-8'

    if not formatted:
      data = [entity.to_dict() for entity in data]

      # Remove keys that the frontend doesn't render.
      for item in data:
        item.pop('rolling_percentage', None)
        item.pop('updated', None)
        item.pop('created', None)

    return self.response.write(json.dumps(data, separators=(',',':')))


class ContentHandler(BaseHandler):

  def split_input(self, field_name, delim='\\r?\\n'):
    """Split the input lines, strip whitespace, and skip blank lines."""
    input_text = self.request.get(field_name) or ''
    return filter(bool, [
        x.strip() for x in re.split(delim, input_text)])

  def split_emails(self, param_name):
    """Split one input field and construct db.Email objects."""
    addr_strs = self.split_input(param_name, delim=',')
    emails = [db.Email(addr) for addr in addr_strs]
    return emails

  def parse_link(self, param_name):
    link = self.request.get(param_name) or None
    if link:
      if not link.startswith('http'):
        link = db.Link('http://' + link)
      else:
        link = db.Link(link)
    return link

  def parse_int(self, param_name):
    param = self.request.get(param_name) or None
    if param:
      param = int(param)
    return param

  def _add_common_template_values(self, d):
    """Mixin common values for templates into d."""

    template_data = {
      'prod': settings.PROD,
      'APP_TITLE': settings.APP_TITLE,
      'current_path': self.request.path,
      'VULCANIZE': settings.VULCANIZE,
      'TEMPLATE_CACHE_TIME': settings.TEMPLATE_CACHE_TIME
      }

    user = users.get_current_user()
    if user:
      user_pref = models.UserPref.get_signed_in_user_pref()
      template_data['login'] = (
          'Sign out', users.create_logout_url(dest_url=self.request.path))
      template_data['user'] = {
        'can_edit': self.user_can_edit(user),
        'is_admin': users.is_current_user_admin(),
        'email': user.email(),
        'dismissed_cues': json.dumps(user_pref.dismissed_cues),
      }
    else:
      template_data['user'] = None
      template_data['login'] = (
          'Sign in', users.create_login_url(dest_url=self.request.path))

    d.update(template_data)

  def render(self, data={}, template_path=None, status=None, message=None,
             relpath=None):
    if status is not None and status != 200:
      self.response.set_status(status, message)

    # Add common template data to every request.
    self._add_common_template_values(data)

    try:
      self.response.out.write(render_to_string(template_path, data))
    except Exception as e:
      logging.exception(e)
      handle_404(self.request, self.response, e)

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
    '<style>'
      'body { padding: 2em; }'
      'h1, h2 { font-weight: 300; font-family: "Roboto", sans-serif; }\n'
    '</style>\n'
    '<title>401 Unauthorized</title>\n'
    '<h1>Error: Unauthorized</h1>\n'
    '<h2>User does not have permission to view this page.</h2>')
  response.write(ERROR_401)
  response.set_status(401)

def handle_404(request, response, exception):
  ERROR_404 = (
    '<style>'
      'body { padding: 2em; }'
      'h1, h2 { font-weight: 300; font-family: "Roboto", sans-serif; }\n'
    '</style>\n'
    '<title>404 Not Found</title>\n'
    '<h1>Error: Not Found</h1>\n'
    '<h2>The requested URL was not found on this server.'
    '</h2>')
  response.write(ERROR_404)
  response.set_status(404)

def handle_500(request, response, exception):
  logging.exception(exception)
  ERROR_500 = (
    '<style>'
      'body { padding: 2em; }'
      'h1, h2 { font-weight: 300; font-family: "Roboto", sans-serif; }\n'
    '</style>\n'
    '<title>500 Internal Server Error</title>\n'
    '<h1>Error: 500 Internal Server Error</h1>')
  response.write(ERROR_500)
  response.set_status(500)
