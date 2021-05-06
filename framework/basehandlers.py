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
import werkzeug.exceptions

from google.appengine.api import users as gae_users
from google.appengine.ext import db

import settings
from framework import permissions
from framework import ramcache
from framework import secrets
from framework import xsrf
from internals import models

from django.template.loader import render_to_string
import django

from google.oauth2 import id_token
from google.auth.transport import requests
from flask import session
import sys
from framework import users
from settings import UNIT_TEST_MODE

# Initialize django so that it'll function when run as a standalone script.
# https://django.readthedocs.io/en/latest/releases/1.7.html#standalone-scripts
django.setup()


# Our API responses are prefixed with this ro prevent attacks that
# exploit <script src="...">.  See go/xssi.
XSSI_PREFIX = ')]}\'\n';

class BaseHandler(flask.views.MethodView):

  @property
  def request(self):
    return flask.request

  def abort(self, status, msg=None, **kwargs):
    """Support webapp2-style, e.g., self.abort(400)."""
    if msg:
      if status == 500:
        logging.error('ISE: %s' % msg)
      else:
        logging.info('Abort %r: %s' % (status, msg))
      flask.abort(status, description=msg, **kwargs)
    else:
      flask.abort(status, **kwargs)

  def redirect(self, url):
    """Support webapp2-style, e.g., return self.redirect(url)."""
    return flask.redirect(url)

  def get_current_user(self, required=False):
    # TODO(jrobbins): oauth support
    current_user = None 
    if not UNIT_TEST_MODE and self.request.method == 'POST':
      current_user = users.get_current_user() or gae_users.get_current_user()
    else:
      current_user = users.get_current_user()      

    if required and not current_user:
      self.abort(403, msg='User must be signed in')
    return current_user

  def get_param(
      self, name, default=None, required=True, validator=None, allowed=None):
    """Get the specified JSON parameter."""
    json_body = self.request.get_json(force=True)
    val = json_body.get(name, default)
    if required and not val:
      self.abort(400, msg='Missing parameter %r' % name)
    if val and validator and not validator(val):
      self.abort(400, msg='Invalid value for parameter %r' % name)
    if val and allowed and val not in allowed:
      self.abort(400, msg='Unexpected value for parameter %r' % name)
    return val

  def get_int_param(
      self, name, default=None, required=True, validator=None, allowed=None):
    """Get the specified integer JSON parameter."""
    val = self.get_param(
        name, default=default, required=required, validator=validator,
        allowed=allowed)
    if type(val) != int:
      self.abort(400, msg='Parameter %r was not an int' % name)
    return val

  def get_bool_param(self, name, default=False, required=False):
    """Get the specified boolean JSON parameter."""
    val = self.get_param(name, default=default, required=required)
    if type(val) != bool:
      self.abort(400, msg='Parameter %r was not a bool' % name)
    return val

  def get_specified_feature(self, feature_id=None, required=True):
    """Get the feature specified in the featureId parameter."""
    feature_id = (feature_id or
                  self.get_int_param('featureId', required=required))
    if not required and not feature_id:
      return None
    feature = models.Feature.get_by_id(feature_id)
    if required and not feature:
      self.abort(404, msg='Feature not found')
    user = self.get_current_user()
    if not permissions.can_view_feature(user, feature):
      self.abort(403, msg='Cannot view that feature')
    return feature


class APIHandler(BaseHandler):

  def get_headers(self):
    """Add CORS and Chrome Frame to all responses."""
    headers = {
        'Strict-Transport-Security':
            'max-age=63072000; includeSubDomains; preload',
        'Access-Control-Allow-Origin': '*',
        'X-UA-Compatible': 'IE=Edge,chrome=1',
        }
    return headers

  def defensive_jsonify(self, handler_data):
    """Return a Flask Response object with a JSON string prefixed with junk."""
    body = json.dumps(handler_data)
    return flask.current_app.response_class(
        XSSI_PREFIX + body,
        mimetype=flask.current_app.config['JSONIFY_MIMETYPE'])

  def get(self, *args, **kwargs):
    """Handle an incoming HTTP GET request."""
    headers = self.get_headers()
    ramcache.check_for_distributed_invalidation()
    handler_data = self.do_get(*args, **kwargs)
    return self.defensive_jsonify(handler_data), headers

  def post(self, *args, **kwargs):
    """Handle an incoming HTTP POST request."""
    is_login_request = str(self.request.url_rule) == '/api/v0/login'

    if not is_login_request:
      self.require_signed_in_and_xsrf_token()
    headers = self.get_headers()
    ramcache.check_for_distributed_invalidation()
    handler_data = self.do_post(*args, **kwargs)
    return self.defensive_jsonify(handler_data), headers

  def patch(self, *args, **kwargs):
    """Handle an incoming HTTP PATCH request."""
    self.require_signed_in_and_xsrf_token()
    headers = self.get_headers()
    ramcache.check_for_distributed_invalidation()
    handler_data = self.do_patch(*args, **kwargs)
    return self.defensive_jsonify(handler_data), headers

  def delete(self, *args, **kwargs):
    """Handle an incoming HTTP DELETE request."""
    self.require_signed_in_and_xsrf_token()
    headers = self.get_headers()
    ramcache.check_for_distributed_invalidation()
    handler_data = self.do_delete(*args, **kwargs)
    return self.defensive_jsonify(handler_data), headers

  def _get_valid_methods(self):
    """For 405 responses, list methods the concrete handler implements."""
    valid_methods = ['GET']
    if self.do_post.__code__ is not APIHandler.do_post.__code__:
      valid_methods.append('POST')
    if self.do_patch.__code__ is not APIHandler.do_patch.__code__:
      valid_methods.append('PATCH')
    if self.do_delete.__code__ is not APIHandler.do_delete.__code__:
      valid_methods.append('DELETE')
    return valid_methods

  def do_get(self, **kwargs):
    """Subclasses should implement this method to handle a GET request."""
    # Every API handler must handle GET.
    raise NotImplementedError()

  def do_post(self, **kwargs):
    """Subclasses should implement this method to handle a POST request."""
    self.abort(405, valid_methods=self._get_valid_methods())

  def do_patch(self, **kwargs):
    """Subclasses should implement this method to handle a PATCH request."""
    self.abort(405, valid_methods=self._get_valid_methods())

  def do_delete(self, **kwargs):
    """Subclasses should implement this method to handle a DELETE request."""
    self.abort(405, valid_methods=self._get_valid_methods())

  def validate_token(self, token, email):
    """If the token is not valid, raise an exception."""
    # This is a separate method so that the refresh handler can override it.
    xsrf.validate_token(token, email)

  def require_signed_in_and_xsrf_token(self):
    """Every API POST, PUT, or DELETE must be signed in with an XSRF token."""
    user = self.get_current_user(required=True)
    if not user:
      self.abort(403, msg='Sign in required')
    token = self.request.headers.get('X-Xsrf-Token')
    if not token:
      try:
        token = self.get_param('token', required=False)
      except werkzeug.exceptions.BadRequest:
        pass  # Raised when the request has no body.
    if not token:
      # TODO(jrobbins): start enforcing in next release
      logging.info("would do self.abort(400, msg='Missing XSRF token')")
    try:
      self.validate_token(token, user.email())
    except xsrf.TokenIncorrect:
      # TODO(jrobbins): start enforcing in next release
      logging.info("would do self.abort(400, msg='Invalid XSRF token')")


class FlaskHandler(BaseHandler):

  TEMPLATE_PATH = None  # Subclasses should define this.
  HTTP_CACHE_TYPE = None  # Subclasses can use 'public' or 'private'
  JSONIFY = False  # Set to True for JSON feeds.
  IS_INTERNAL_HANDLER = False  # Subclasses can skip XSRF check.

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
    self.abort(405, msg='Unexpected HTTP method', valid_methods=['GET'])

  def get_common_data(self, path=None):
    """Return template data used on all pages, e.g., sign-in info."""
    current_path = path or flask.request.full_path
    common_data = {
      'prod': settings.PROD,
      'APP_TITLE': settings.APP_TITLE,
      'current_path': current_path,
      'TEMPLATE_CACHE_TIME': settings.TEMPLATE_CACHE_TIME,
      }

    user = self.get_current_user()
    if user:
      user_pref = models.UserPref.get_signed_in_user_pref()
      common_data['login'] = (
          'Sign out', "SignOut")
      common_data['user'] = {
        'can_create_feature': permissions.can_create_feature(user),
        'can_edit': permissions.can_edit_any_feature(user),
        'is_admin': permissions.can_admin_site(user),
        'email': user.email(),
        'dismissed_cues': json.dumps(user_pref.dismissed_cues),
      }
      common_data['xsrf_token'] = xsrf.generate_token(user.email())
      common_data['xsrf_token_expires'] = xsrf.token_expires_sec()
    else:
      common_data['user'] = None
      common_data['login'] = (
           'Sign in', "Sign In")
      common_data['xsrf_token'] = xsrf.generate_token(None)
      common_data['xsrf_token_expires'] = 0
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
    self.require_xsrf_token()
    handler_data = self.process_post_data(*args, **kwargs)
    headers = self.get_headers()

    if self.JSONIFY and type(handler_data) in (dict, list):
      return flask.jsonify(handler_data), headers
    else:
      # handler_data is a string or redirect response object.
      return handler_data, headers

  @property
  def form(self):
    """Property for POST values dict."""
    return flask.request.form

  def require_xsrf_token(self):
    """Every UI form submission must have a XSRF token."""
    if settings.UNIT_TEST_MODE or self.IS_INTERNAL_HANDLER:
      return
    token = self.form.get('token')
    if not token:
      # TODO(jrobbins): start enforcing in next release
      logging.info("would do self.abort(400, msg='Missing XSRF token')")
    user = self.get_current_user(required=True)
    try:
      xsrf.validate_token(token, user.email())
    except xsrf.TokenIncorrect:
      # TODO(jrobbins): start enforcing in next release
      logging.info("would do self.abort(400, msg='Invalid XSRF token')")

  def require_task_header(self):
    """Abort if this is not a Google Cloud Tasks request."""
    if settings.UNIT_TEST_MODE:
      return
    if 'X-AppEngine-QueueName' not in self.request.headers:
      self.abort(403, msg='Lacking X-AppEngine-QueueName header')

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
        self.abort(
            500, msg='template_path %r does not end with .html' % template_path)
      return defaults

    return flask.jsonify(defaults)


def FlaskApplication(routes, pattern_base='', debug=False):
  """Make a Flask app and add routes and handlers that work like webapp2."""

  app = flask.Flask(__name__)
  app.secret_key = secrets.get_session_secret()  # For flask.session

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
