# Copyright 2020 Google Inc.
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

import unittest
import testing_config  # Must be imported before the module under test.

import mock
import flask
import flask.views
import werkzeug.exceptions  # Flask HTTP stuff.

from google.appengine.api import users

from framework import basehandlers
import models
import settings


class TestableFlaskHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'test_template.html'

  def get_template_data(
      self, special_status=None, redirect_to=None, item_list=None):
    if redirect_to:
      return flask.redirect(redirect_to)
    if item_list:
      return item_list

    template_data = {'name': 'testing'}
    if special_status:
      template_data['status'] = special_status
    return template_data

  def process_post_data(self, redirect_to=None):
    if redirect_to:
      return flask.redirect(redirect_to)

    return {'objects': [1, 2, 3]}


test_app = basehandlers.FlaskApplication(
    [('/test', TestableFlaskHandler),
     ('/old_path', basehandlers.Redirector,
      {'location': '/new_path'}),
     ('/just_a_template', basehandlers.ConstHandler,
      {'template_path': 'test_template.html',
       'name': 'Guest'}),
     ('/messed_up_template', basehandlers.ConstHandler,
      {'template_path': 'not_a_template'}),
     ('/ui/density.json', basehandlers.ConstHandler,
      {'UI density': ['default', 'comfortable', 'compact']}),
     ],
    debug=True)


class RedirectorTests(unittest.TestCase):

  def test_redirector(self):
    """If the user hits a redirector, they get a redirect response."""
    with test_app.test_request_context('/old_path'):
      actual_redirect, actual_headers = test_app.dispatch_request()

    self.assertEqual(302, actual_redirect.status_code)
    self.assertEqual('/new_path', actual_redirect.headers['location'])


class ConstHandlerTests(unittest.TestCase):

  def test_template_found(self):
    """We can run a template that requires no handler logic."""
    with test_app.test_request_context('/just_a_template'):
      actual_tuple = test_app.dispatch_request()

    actual_text, actual_status, actual_headers = actual_tuple
    self.assertIn('Hi Guest,', actual_text)
    self.assertEqual(200, actual_status)
    self.assertIn('Access-Control-Allow-Origin', actual_headers)

  def test_bad_template_path(self):
    """We can run a template that requires no handler logic."""
    with test_app.test_request_context('/messed_up_template'):
      with self.assertRaises(werkzeug.exceptions.InternalServerError):
        test_app.dispatch_request()

  def test_json(self):
    """We can return constant JSON."""
    with test_app.test_request_context('/ui/density.json'):
      actual_response = test_app.dispatch_request()

    self.assertEqual(
        {'UI density': ['default', 'comfortable', 'compact']},
        actual_response.json)


class FlaskHandlerTests(unittest.TestCase):

  def setUp(self):
    self.user_1 = models.AppUser(email='registered@example.com')
    self.user_1.put()
    self.handler = TestableFlaskHandler()

  def tearDown(self):
    self.user_1.delete()

  def test_get_cache_headers__disabled(self):
    """Most handlers return content that should not be cached."""
    cache_headers = self.handler.get_cache_headers()
    self.assertEqual({}, cache_headers)

  def test_get_cache_headers__private(self):
    """Some handlers have content that can be cached for one user."""
    self.handler.HTTP_CACHE_TYPE = 'private'
    cache_headers = self.handler.get_cache_headers()
    self.assertEqual(
        {'Cache-Control': 'private, max-age=%s' % settings.DEFAULT_CACHE_TIME},
        cache_headers)

  def test_get_cache_headers__public(self):
    """Some handlers have content that can be cached for anyone."""
    self.handler.HTTP_CACHE_TYPE = 'public'
    cache_headers = self.handler.get_cache_headers()
    self.assertEqual(
        {'Cache-Control': 'public, max-age=%s' % settings.DEFAULT_CACHE_TIME},
        cache_headers)

  def test_get_headers(self):
    """We always use some standard headers."""
    actual = self.handler.get_headers()
    self.assertEqual(
        {'Strict-Transport-Security':
             'max-age=63072000; includeSubDomains; preload',
         'Access-Control-Allow-Origin': '*',
         'X-UA-Compatible': 'IE=Edge,chrome=1',
         },
        actual)

  def test_get_template_data__missing(self):
    """Every subsclass should overide get_template_data()."""
    self.handler = basehandlers.FlaskHandler()
    with self.assertRaises(NotImplementedError):
      self.handler.get_template_data()

  def test_get_template_path__missing(self):
    """Subsclasses that don't define TEMPLATE_PATH trigger error."""
    self.handler = basehandlers.FlaskHandler()
    with self.assertRaises(ValueError):
      self.handler.get_template_path({})

  def test_get_template_path__specified_in_class(self):
    """Subsclasses can define TEMPLATE_PATH."""
    actual = self.handler.get_template_path({})
    self.assertEqual('test_template.html', actual)

  def test_get_template_path__specalized_by_template_data(self):
    """If get_template_data() returned a template path, we use it."""
    actual = self.handler.get_template_path(
        {'template_path': 'special.html'})
    self.assertEqual('special.html', actual)

  def test_process_post_data__missing(self):
    """Every subsclass should overide process_post_data()."""
    self.handler = basehandlers.FlaskHandler()
    with self.assertRaises(NotImplementedError):
      self.handler.process_post_data()

  def test_get_common_data__signed_out(self):
    """When user is signed out, offer sign in link."""
    testing_config.sign_out()

    actual = self.handler.get_common_data(path='/test/path')

    self.assertIn('prod', actual)
    self.assertIsNone(actual['user'])
    self.assertEqual('Sign in', actual['login'][0])
    self.assertIn('/Login', actual['login'][1])
    self.assertIn('/test/path', actual['login'][1])

  def test_get_common_data__signed_in(self):
    """When user is signed in, offer sign out link."""
    testing_config.sign_in('test@example.com', 111)

    actual = self.handler.get_common_data(path='/test/path')

    self.assertIn('prod', actual)
    self.assertIsNotNone(actual['user'])
    self.assertEqual('Sign out', actual['login'][0])
    self.assertIn('/Logout', actual['login'][1])
    self.assertIn('/test/path', actual['login'][1])

  def test_render(self):
    """We can render a simple template to a string."""
    actual = self.handler.render({'name': 'literal'}, 'test_template.html')
    self.assertIn('Hi literal', actual)

  def test_get__html_page(self):
    """We can process a request and return HTML and headers."""
    with test_app.test_request_context('/test'):
      actual_html, actual_status, actual_headers = self.handler.get()

    self.assertIn('Hi testing', actual_html)
    self.assertEqual(200, actual_status)
    self.assertIn('Access-Control-Allow-Origin', actual_headers)

  def test_get__json_dict(self):
    """We can process a GET request and JSON and headers."""
    self.handler.JSONIFY = True
    with test_app.test_request_context('/test'):
      actual_response, actual_headers = self.handler.get()

    self.assertIn('name', actual_response.get_json())
    self.assertEqual(200, actual_response.status_code)
    self.assertIn('Access-Control-Allow-Origin', actual_headers)

  def test_get__json_list(self):
    """We can process a GET request and JSON and headers."""
    self.handler.JSONIFY = True
    with test_app.test_request_context('/test'):
      actual_response, actual_headers = self.handler.get(
          item_list=[10, 20, 30])

    self.assertEqual([10, 20, 30], actual_response.get_json())
    self.assertEqual(200, actual_response.status_code)
    self.assertIn('Access-Control-Allow-Origin', actual_headers)

  def test_get__special_status(self):
    """get_template_data() can return a special HTTP status."""
    with test_app.test_request_context('/test'):
      actual_html, actual_status, actual_headers = self.handler.get(
          special_status=222)

    self.assertIn('Hi testing', actual_html)
    self.assertEqual(222, actual_status)
    self.assertIn('Access-Control-Allow-Origin', actual_headers)

  def test_get__redirect(self):
    """get_template_data() can return a redirect response object."""
    with test_app.test_request_context('/test'):
      actual_response = self.handler.get(
          redirect_to='some/other/path')

    self.assertIn('Response', type(actual_response).__name__)
    self.assertIn('some/other/path', actual_response.headers['location'])

  def test_post__json(self):
    """if process_post_data() returns a dict, it is passed to flask."""
    with test_app.test_request_context('/test'):
      actual_dict, actual_headers = self.handler.post()

    self.assertEqual(
        {'objects': [1, 2, 3]},
        actual_dict)
    self.assertIn('Access-Control-Allow-Origin', actual_headers)

  def test_post__redirect(self):
    """if process_post_data() returns a redirect response, it is used."""
    with test_app.test_request_context('/test'):
      actual_response, actual_headers = self.handler.post(
          redirect_to='some/other/path')

    self.assertIn('Response', type(actual_response).__name__)
    self.assertIn('some/other/path', actual_response.headers['location'])
    self.assertIn('Access-Control-Allow-Origin', actual_headers)

  def test_user_can_edit__anon(self):
    """Anon visitors cannot edit features."""
    actual = self.handler.user_can_edit(None)
    self.assertFalse(actual)

  def test_user_can_edit__normal(self):
    """Non-registered signed in users cannot edit features."""
    u = users.User(email='user@example.com')
    actual = self.handler.user_can_edit(u)
    self.assertFalse(actual)

  def test_user_can_edit__registered(self):
    """Users who have been registed by admins may edit features."""
    u = users.User(email='registered@example.com')
    actual = self.handler.user_can_edit(u)
    self.assertTrue(actual)

  def test_user_can_edit__preferred_domains(self):
    """Users signed in with certain email addresses may edit."""
    u = users.User(email='user@chromium.org')
    actual = self.handler.user_can_edit(u)
    self.assertTrue(actual)

    u = users.User(email='user@google.com')
    actual = self.handler.user_can_edit(u)
    self.assertTrue(actual)

    u = users.User(email='user@this-is-not-google.com')
    actual = self.handler.user_can_edit(u)
    self.assertFalse(actual)

    u = users.User(email='user@this-is-not.google.com')
    actual = self.handler.user_can_edit(u)
    self.assertFalse(actual)

  def test_require_task_header__while_testing(self):
    """During unit testing of task handlers, we allow it."""
    with test_app.test_request_context('/test'):
      self.handler.require_task_header()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  def test_require_task_header__normal(self):
    """If the incoming request is from GCT, we allow it."""
    headers = {'X-AppEngine-QueueName': 'default'}
    with test_app.test_request_context('/test', headers=headers):
      self.handler.require_task_header()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  def test_require_task_header__missing(self):
    """If the incoming request is not from GCT, abort."""
    with test_app.test_request_context('/test'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.require_task_header()
