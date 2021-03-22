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

from __future__ import division
from __future__ import print_function

import json
import logging
import os
import re

import flask
import flask.views

from google.appengine.api import users
from google.appengine.ext import db

from framework import ramcache
import settings
import models

from django.template.loader import render_to_string
import django

# Initialize django so that it'll function when run as a standalone script.
# https://django.readthedocs.io/en/latest/releases/1.7.html#standalone-scripts
django.setup()


class BaseHandler(flask.views.MethodView):

  @property
  def request(self):
    return flask.request

  def abort(self, status):
    """Support webapp2-style, e.g., self.abort(400)."""
    flask.abort(status)

  def redirect(self, url):
    """Support webapp2-style, e.g., return self.redirect(url)."""
    return flask.redirect(url)


class APIHandler(BaseHandler):

  def get_current_user(self):
    # TODO(jrobbins): oauth support
    return users.get_current_user()

  def get_headers(self):
    """Add CORS and Chrome Frame to all responses."""
    headers = {
        'Strict-Transport-Security':
            'max-age=63072000; includeSubDomains; preload',
        'Access-Control-Allow-Origin': '*',
        'X-UA-Compatible': 'IE=Edge,chrome=1',
        }
    return headers

  def get(self, *args, **kwargs):
    """Handle an incoming HTTP GET request."""
    headers = self.get_headers()
    ramcache.check_for_distributed_invalidation()
    handler_data = self.do_get(*args, **kwargs)
    return flask.jsonify(handler_data), headers

  def post(self, *args, **kwargs):
    """Handle an incoming HTTP POST request."""
    headers = self.get_headers()
    ramcache.check_for_distributed_invalidation()
    handler_data = self.do_post(*args, **kwargs)
    return flask.jsonify(handler_data), headers

  def patch(self, *args, **kwargs):
    """Handle an incoming HTTP PATCH request."""
    headers = self.get_headers()
    ramcache.check_for_distributed_invalidation()
    handler_data = self.do_patch(*args, **kwargs)
    return flask.jsonify(handler_data), headers

  def delete(self, *args, **kwargs):
    """Handle an incoming HTTP DELETE request."""
    headers = self.get_headers()
    ramcache.check_for_distributed_invalidation()
    handler_data = self.do_delete(*args, **kwargs)
    return flask.jsonify(handler_data), headers

  def do_get(self):
    """Subclasses should implement this method to handle a GET request."""
    raise NotImplementedError()

  def do_post(self):
    """Subclasses should implement this method to handle a POST request."""
    raise NotImplementedError()

  def do_patch(self):
    """Subclasses should implement this method to handle a PATCH request."""
    raise NotImplementedError()

  def do_delete(self):
    """Subclasses should implement this method to handle a DELETE request."""
    raise NotImplementedError()


class FlaskHandler(BaseHandler):

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
        'Strict-Transport-Security':
            'max-age=63072000; includeSubDomains; preload',
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

  def user_can_edit(self, user):
    if not user:
      return False

    can_edit = False

    if users.is_current_user_admin():
      can_edit = True
    elif user.email().endswith(('@chromium.org', '@google.com')):
      can_edit = True
    else:
      # TODO(ericbidelman): cache user lookup.
      query = models.AppUser.all(keys_only=True).filter('email =', user.email())
      found_user = query.get()

      if found_user is not None:
        can_edit = True

    return can_edit

  @property
  def form(self):
    """Property for POST values dict."""
    return flask.request.form

  def require_task_header(self):
    """Abort if this is not a Google Cloud Tasks request."""
    if settings.UNIT_TEST_MODE:
      return
    if 'X-AppEngine-QueueName' not in self.request.headers:
      logging.info('Lacking X-AppEngine-QueueName header')
      self.abort(403)

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
    return flask.redirect(location), self.get_headers()


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


def FlaskApplication(routes, pattern_base='', debug=False):
  """Make a Flask app and add routes and handlers that work like webapp2."""

  app = flask.Flask(__name__)
  for i, rule in enumerate(routes):
    pattern = rule[0]
    handler_class = rule[1]
    defaults = rule[2] if len(rule) > 2 else None
    classname = handler_class.__name__
    app.add_url_rule(
        pattern_base + pattern,
        endpoint=classname + str(i),  # We don't use it, but it must be unique.
        view_func=handler_class.as_view(classname),
        defaults=defaults)

  # Note: debug parameter is not used because the following accomplishes
  # what we need it to do.
  app.config["TRAP_BAD_REQUEST_ERRORS"] = True  # Needed to log execptions
  # Flask apps also have a debug setting that can be used to auto-reload
  # template source code, but we use django for that.

  return app
