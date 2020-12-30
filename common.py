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
import os
import re
import time
import traceback
import webapp2

import flask
import flask.views

# App Engine imports.
from google.appengine.api import users
from google.appengine.ext import db

import ramcache
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


# TODO(jrobbins): phase out this class and have all calls use FlaskHandler.
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
      # TODO(ericbidelman): ramcache user lookup.
      query = models.AppUser.all(keys_only=True).filter('email =', user.email())
      found_user = query.get()

      if found_user is not None:
        can_edit = True

    return can_edit


# TODO(jrobbins): phase out this class and have all calls use FlaskHandler.
class JSONHandler(BaseHandler):

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


# TODO(jrobbins): phase out this class and have all calls use FlaskHandler.
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



def render_atom_feed(request, title, data):
  features_url = '%s://%s%s' % (request.scheme,
                                request.host,
                                request.path.replace('.xml', ''))
  feature_url_prefix = '%s://%s%s' % (request.scheme,
                                      request.host,
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
  headers = {
      'Content-Type': 'application/atom+xml;charset=utf-8'}
  text = feed.writeString('utf-8')
  return text, headers


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


class FlaskHandler(flask.views.MethodView):

  TEMPLATE_PATH = None  # Subclasses should define this.
  HTTP_CACHE_TYPE = None  # Subclasses can use 'public' or 'private'
  JSONIFY = False  # Set to True for JSON feeds.

  def get_cache_headers(self):
    """Add cache control headers if HTTP_CACHE_TYPE is set."""
    if self.HTTP_CACHE_TYPE:
      directive = '%s, max-age=%s' % (
          self.HTTP_CACHE_TYPE, settings.DEFAULT_CACHE_TIME)
      return {'Cache-Control': directive}

    return {}

  def get_headers(self):
    """Add CORS and Chrome Frame to all responses."""
    headers = {
        'Access-Control-Allow-Origin': '*',
        'X-UA-Compatible': 'IE=Edge,chrome=1',
        }
    headers.update(self.get_cache_headers())
    return headers

  def get_template_data(self):
    """Subclasses should implement this method to handle a GET request."""
    raise NotImplementedError()

  def get_template_path(self, template_data):
    """Subclasses can override their class constant via template_data."""
    if 'template_path' in template_data:
      return template_data['template_path']
    if self.TEMPLATE_PATH:
      return self.TEMPLATE_PATH
    raise ValueError(
        'No TEMPLATE_PATH was defined in %r or returned in template_data.' %
        self.__class__.__name__)

  def process_post_data(self):
    """Subclasses should implement this method to handle a POST request."""
    raise NotImplementedError()

  def get_common_data(self, path=None):
    """Return template data used on all pages, e.g., sign-in info."""
    current_path = path or flask.request.path
    common_data = {
      'prod': settings.PROD,
      'APP_TITLE': settings.APP_TITLE,
      'current_path': current_path,
      'VULCANIZE': settings.VULCANIZE,
      'TEMPLATE_CACHE_TIME': settings.TEMPLATE_CACHE_TIME
      }

    user = users.get_current_user()
    if user:
      user_pref = models.UserPref.get_signed_in_user_pref()
      common_data['login'] = (
          'Sign out', users.create_logout_url(dest_url=current_path))
      common_data['user'] = {
        'can_edit': self.user_can_edit(user),
        'is_admin': users.is_current_user_admin(),
        'email': user.email(),
        'dismissed_cues': json.dumps(user_pref.dismissed_cues),
      }
    else:
      common_data['user'] = None
      common_data['login'] = (
          'Sign in', users.create_login_url(dest_url=current_path))
    return common_data

  def render(self, template_data, template_path):
    return render_to_string(template_path, template_data)

  def get(self, *args, **kwargs):
    """GET handlers can render templates, return JSON, or do redirects."""
    ramcache.check_for_distributed_invalidation()
    handler_data = self.get_template_data(*args, **kwargs)

    if self.JSONIFY and type(handler_data) in (dict, list):
      headers = self.get_headers()
      return flask.jsonify(handler_data), headers

    elif type(handler_data) == dict:
      status = handler_data.get('status', 200)
      handler_data.update(self.get_common_data())
      template_path = self.get_template_path(handler_data)
      template_text = self.render(handler_data, os.path.join(template_path))
      headers = self.get_headers()
      return template_text, status, headers

    else:
      # handler_data is a string or redirect response object.
      return handler_data

  def post(self, *args, **kwargs):
    """POST handlers return a string, JSON, or a redirect."""
    ramcache.check_for_distributed_invalidation()
    handler_data = self.process_post_data(*args, **kwargs)
    headers = self.get_headers()

    if self.JSONIFY and type(handler_data) in (dict, list):
      return flask.jsonify(handler_data), headers
    else:
      # handler_data is a string or redirect response object.
      return handler_data, headers

  def abort(self, status):
    """Support webapp2-style, e.g., self.abort(400)."""
    flask.abort(status)

  def redirect(self, url):
    """Support webapp2-style, e.g., return self.redirect(url)."""
    return flask.redirect(url)

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

  @property
  def request(self):
    return flask.request

  @property
  def form(self):
    """Property for POST values dict."""
    return flask.request.form

  def split_input(self, field_name, delim='\\r?\\n'):
    """Split the input lines, strip whitespace, and skip blank lines."""
    input_text = flask.request.form.get(field_name) or ''
    return filter(bool, [
        x.strip() for x in re.split(delim, input_text)])

  def split_emails(self, param_name):
    """Split one input field and construct db.Email objects."""
    addr_strs = self.split_input(param_name, delim=',')
    emails = [db.Email(addr) for addr in addr_strs]
    return emails

  def parse_link(self, param_name):
    link = flask.request.form.get(param_name) or None
    if link:
      if not link.startswith('http'):
        link = db.Link('http://' + link)
      else:
        link = db.Link(link)
    return link

  def parse_int(self, param_name):
    param = flask.request.form.get(param_name) or None
    if param:
      param = int(param)
    return param


class Redirector(FlaskHandler):
  """Reusable handler that always redirects.
     Specify the location in the third part of a routing rule using:
     {'location': '/path/to/page'}."""

  def get_template_data(self, location='/'):
    return flask.redirect(location)


class ConstHandler(FlaskHandler):
  """Reusable handler for templates that require no page-specific logic.
     Specify the location in the third part of a routing rule using:
     {'template_path': 'path/to/template.html'}."""

  def get_template_data(self, **defaults):
    """Render a template, or return a JSON constant."""
    if 'template_path' in defaults:
      template_path = defaults['template_path']
      if '.html' not in template_path:
        logging.error('template_path %r does not end with .html', template_path)
        self.abort(500)
      return defaults

    return flask.jsonify(defaults)


def FlaskApplication(routes, debug=False):
  """Make a Flask app and add routes and handlers that work like webapp2."""

  app = flask.Flask(__name__)
  for i, rule in enumerate(routes):
    pattern = rule[0]
    handler_class = rule[1]
    defaults = rule[2] if len(rule) > 2 else None
    classname = handler_class.__name__
    app.add_url_rule(
        pattern,
        endpoint=classname + str(i),  # We don't use it, but it must be unique.
        view_func=handler_class.as_view(classname),
        defaults=defaults)

  # Note: debug parameter is not used because the following accomplishes
  # what we need it to do.
  app.config["TRAP_BAD_REQUEST_ERRORS"] = True  # Needed to log execptions
  # Flask apps also have a debug setting that can be used to auto-reload
  # template source code, but we use django for that.

  return app
