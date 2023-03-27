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

import testing_config  # Must be imported before the module under test.

import json
from unittest import mock
import flask
import flask.views
import werkzeug.exceptions  # Flask HTTP stuff.

# from google.appengine.api import users
from framework import users

from main import Route
from framework import basehandlers
from framework import users
from framework import xsrf
from internals import user_models
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

  def process_post_data(self, **kwargs):
    redirect_to = kwargs.get('redirect_to', None)
    if redirect_to:
      return flask.redirect(redirect_to)

    return {'objects': [1, 2, 3]}


test_app = basehandlers.FlaskApplication(
    __name__,
    [Route('/test', TestableFlaskHandler),
     Route('/data/test', TestableFlaskHandler),
     Route('/old_path', basehandlers.Redirector,
      {'location': '/new_path'}),
     Route('/just_a_template', basehandlers.ConstHandler,
      {'template_path': 'test_template.html',
       'name': 'Guest'}),
     Route('/just_an_xml_template', basehandlers.ConstHandler,
      {'template_path': 'farewell-rss.xml'}),
     Route('/must_be_signed_in', basehandlers.ConstHandler,
      {'template_path': 'test_template.html',
       'require_signin': True}),
     Route('/messed_up_template', basehandlers.ConstHandler,
      {'template_path': 'not_a_template'}),
     Route('/ui/density.json', basehandlers.ConstHandler,
      {'UI density': ['default', 'comfortable', 'compact']}),
     ],
    debug=True)


class BaseHandlerTests(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = basehandlers.BaseHandler()

  @mock.patch('flask.request', 'fake request')
  def test_request(self):
    """We can get the flask request."""
    actual = self.handler.request
    self.assertEqual('fake request', actual)

  @mock.patch('flask.abort')
  def test_abort__no_msg(self, mock_abort):
    """We can abort request handling."""
    self.handler.abort(400)
    mock_abort.assert_called_once_with(400)

  @mock.patch('logging.info')
  @mock.patch('flask.abort')
  def test_abort__with_msg(self, mock_abort, mock_info):
    """We can abort request handling."""
    self.handler.abort(400, msg='You messed up')
    mock_abort.assert_called_once_with(400, description='You messed up')
    mock_info.assert_called_once()

  @mock.patch('logging.error')
  @mock.patch('flask.abort')
  def test_abort__with_500_msg(self, mock_abort, mock_error):
    """We can abort request handling."""
    self.handler.abort(500, msg='We messed up')
    mock_abort.assert_called_once_with(500, description='We messed up')
    mock_error.assert_called_once()

  @mock.patch('flask.redirect')
  def test_redirect(self, mock_redirect):
    """We can return a redirect."""
    mock_redirect.return_value = 'fake response'
    actual = self.handler.redirect('test url')
    self.assertEqual('fake response', actual)
    mock_redirect.assert_called_once_with('test url')

  def test_get_current_user__anon(self):
    """If the user is signed out, we get back None."""
    testing_config.sign_out()
    actual = self.handler.get_current_user()
    self.assertIsNone(actual)

  @mock.patch('framework.basehandlers.BaseHandler.abort')
  def test_get_current_user__required_but_anon(self, mock_abort):
    """If the user is signed out, we give a 403."""
    mock_abort.side_effect = werkzeug.exceptions.Forbidden
    testing_config.sign_out()
    with self.assertRaises(werkzeug.exceptions.Forbidden):
      self.handler.get_current_user(required=True)

  def test_get_current_user__signed_in(self):
    """We can get the signed in user."""
    testing_config.sign_in('test@example.com', 111)
    actual = self.handler.get_current_user()
    self.assertEqual('test@example.com', actual.email())

  def test_get_param__simple(self):
    """We can simply get a JSON parameter, with defaults."""
    with test_app.test_request_context('/test', json={'x': 1}):
      self.assertEqual(1, self.handler.get_param('x'))
      self.assertEqual(None, self.handler.get_param('missing', required=False))
      self.assertEqual('usual', self.handler.get_param(
          'missing', default='usual'))

  @mock.patch('framework.basehandlers.BaseHandler.abort')
  def test_get_param__missing_required(self, mock_abort):
    """If a required param is missing, we abort."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context('/test', json={'x': 1}):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.get_param('missing')
    mock_abort.assert_called_once_with(400, msg="Missing parameter 'missing'")

  @mock.patch('framework.basehandlers.BaseHandler.abort')
  def test_get_param__validator(self, mock_abort):
    """If a param fails validation, we abort."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context('/test', json={'x': 1}):
      actual = self.handler.get_param(
          'x', validator=lambda num: num % 2 == 1)
      self.assertEqual(1, actual)

      actual = self.handler.get_param(
          'missing', default=3, validator=lambda num: num % 2 == 1)
      self.assertEqual(3, actual)

      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.get_param(
            'x', validator=lambda num: num % 2 == 0)
      mock_abort.assert_called_once_with(
          400, msg="Invalid value for parameter 'x'")

  @mock.patch('framework.basehandlers.BaseHandler.abort')
  def test_get_param__allowed(self, mock_abort):
    """If a param has an unexpected value, we abort."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context('/test', json={'x': 1}):
      actual = self.handler.get_param('x', allowed=[1, 2, 3])
      self.assertEqual(1, actual)

      actual = self.handler.get_param(
          'missing', default=3, allowed=[1, 2, 3])
      self.assertEqual(3, actual)

      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.get_param('x', allowed=[10, 20, 30])
      mock_abort.assert_called_once_with(
          400, msg="Unexpected value for parameter 'x'")

  @mock.patch('framework.basehandlers.BaseHandler.abort')
  def test_get_int_param(self, mock_abort):
    """We can get an int, or abort."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context(
        '/test', json={'x': 1, 'y': 0, 'foo': 'bar'}):
      actual = self.handler.get_int_param('x')
      self.assertEqual(1, actual)

      actual = self.handler.get_int_param('y')
      self.assertEqual(0, actual)

      actual = self.handler.get_int_param('missing', default=3)
      self.assertEqual(3, actual)

      actual = self.handler.get_int_param('missing', required=False)
      self.assertIsNone(actual)

      actual = self.handler.get_int_param(
          'missing', required=False, validator=lambda x: x % 2 == 1)
      self.assertIsNone(actual)

      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.get_int_param('foo')
      mock_abort.assert_called_once_with(
          400, msg="Parameter 'foo' was not an int")

  @mock.patch('framework.basehandlers.BaseHandler.abort')
  def test_get_bool_param(self, mock_abort):
    """We can get a bool, or abort."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context(
        '/test', json={'x': True, 'foo': 'bar'}):
      actual = self.handler.get_bool_param('x')
      self.assertEqual(True, actual)

      actual = self.handler.get_bool_param('missing')
      self.assertEqual(False, actual)

      actual = self.handler.get_bool_param('missing', default=True)
      self.assertEqual(True, actual)

      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.get_bool_param('foo')
      mock_abort.assert_called_once_with(
          400, msg="Parameter 'foo' was not a bool")

  @mock.patch('framework.basehandlers.BaseHandler.abort')
  def test_get_specified_feature__missing(self, mock_abort):
    """Reject requests that need a feature ID but don't provide one."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context('/test', json={}):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.get_specified_feature()
      mock_abort.assert_called_once_with(
          400, msg="Missing parameter 'featureId'")

  @mock.patch('framework.basehandlers.BaseHandler.abort')
  def test_get_specified_feature__bad(self, mock_abort):
    """Reject requests that need a feature ID but provide junk."""
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context('/test', json={'featureId': 'junk'}):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.get_specified_feature()
      mock_abort.assert_called_once_with(
          400, msg="Parameter 'featureId' was not an int")

  def test_get_bool_arg__explicitly_true(self):
    """A bool query string arg that is "true" or "1" is true."""
    with test_app.test_request_context('/test?maybe=true'):
      self.assertTrue(self.handler.get_bool_arg('maybe'))

    with test_app.test_request_context('/test?maybe=1'):
      self.assertTrue(self.handler.get_bool_arg('maybe'))

  def test_get_bool_arg__implicitly_true(self):
    """A query string param is present but empty is considered true."""
    with test_app.test_request_context('/test?maybe'):
      self.assertTrue(self.handler.get_bool_arg('maybe'))

  def test_get_bool_arg__explicitly_false(self):
    """A bool query string arg that is anything funny is false."""
    with test_app.test_request_context('/test?maybe=abc'):
      self.assertFalse(self.handler.get_bool_arg('maybe'))

  def test_get_bool_arg__implicitly_false(self):
    """A missing query string param is considered false."""
    with test_app.test_request_context('/test'):
      self.assertFalse(self.handler.get_bool_arg('maybe'))

  @mock.patch('framework.basehandlers.BaseHandler.abort')
  def test_get_int_arg__bad(self, mock_abort):
    mock_abort.side_effect = werkzeug.exceptions.BadRequest

    with test_app.test_request_context('/test?num=abc'):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.get_int_arg('num')
      mock_abort.assert_called_once_with(
          400, msg="Request parameter 'num' was not an int")

  def test_get_int_arg(self):
    with test_app.test_request_context('/test?num=1'):
      actual = self.handler.get_int_arg('num')
      self.assertEqual(1, actual)

      actual = self.handler.get_int_arg('random')
      self.assertEqual(None, actual)


class RedirectorTests(testing_config.CustomTestCase):

  def test_redirector(self):
    """If the user hits a redirector, they get a redirect response."""
    with test_app.test_request_context('/old_path'):
      actual_redirect, actual_headers = test_app.dispatch_request()

    self.assertEqual(302, actual_redirect.status_code)
    self.assertEqual('/new_path', actual_redirect.headers['location'])


class ConstHandlerTests(testing_config.CustomTestCase):

  def test_template_found(self):
    """We can run a template that requires no handler logic."""
    with test_app.test_request_context('/just_a_template'):
      actual_tuple = test_app.dispatch_request()

    actual_text, actual_status, actual_headers = actual_tuple
    self.assertIn('Hi Guest,', actual_text)
    self.assertEqual(200, actual_status)
    self.assertNotIn('Access-Control-Allow-Origin', actual_headers)

  def test_xml_template_found(self):
    """We can run an XML template that requires no handler logic."""
    with test_app.test_request_context('/just_an_xml_template'):
      actual_tuple = test_app.dispatch_request()

    actual_text, actual_status, actual_headers = actual_tuple
    self.assertIn('RSS feed', actual_text)
    self.assertEqual(200, actual_status)
    self.assertNotIn('Access-Control-Allow-Origin', actual_headers)

  @mock.patch('logging.error')
  def test_bad_template_path(self, mock_err):
    """We can run a template that requires no handler logic."""
    with test_app.test_request_context('/messed_up_template'):
      with self.assertRaises(werkzeug.exceptions.InternalServerError):
        test_app.dispatch_request()
    self.assertEqual(1, len(mock_err.mock_calls))

  def test_json(self):
    """We can return constant JSON."""
    with test_app.test_request_context('/ui/density.json'):
      actual_response = test_app.dispatch_request()

    self.assertEqual(
        {'UI density': ['default', 'comfortable', 'compact']},
        actual_response.json)

  def test_require_signin__normal(self):
    """A const page renders when the user is signed in.."""
    testing_config.sign_in('user@example.com', 111)
    with test_app.test_request_context('/must_be_signed_in'):
      actual_tuple = test_app.dispatch_request()

    actual_text, actual_status, actual_headers = actual_tuple
    self.assertIn('This is used by unit tests', actual_text)
    self.assertEqual(200, actual_status)

  def test_require_signin__anon(self):
    """If sign-in is required and user is anon, we redirect."""
    testing_config.sign_out()
    with test_app.test_request_context('/must_be_signed_in'):
      actual_redirect, actual_headers = test_app.dispatch_request()

    self.assertEqual(302, actual_redirect.status_code)
    self.assertEqual(
        settings.LOGIN_PAGE_URL, actual_redirect.headers['location'])


class APIHandlerTests(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = basehandlers.APIHandler()

    self.appuser = user_models.AppUser(email='user@example.com')
    self.appuser.put()

  def tearDown(self):
    self.appuser.key.delete()

  def test_get_headers(self):
    """We always use some standard headers."""
    with test_app.test_request_context('/path'):
      actual = self.handler.get_headers()
    self.assertEqual(
        {'Strict-Transport-Security':
             'max-age=63072000; includeSubDomains; preload',
         'X-UA-Compatible': 'IE=Edge,chrome=1',
         'X-Frame-Options': 'DENY',
         },
        actual)

  def test_defensive_jsonify(self):
    """We prefix our JSON responses with defensive characters."""
    handler_data = {'one': 1, 'two': 2}
    with test_app.test_request_context('/path'):
      actual = self.handler.defensive_jsonify(handler_data)

    actual_sent_text = actual.response[0].decode()
    self.assertTrue(actual_sent_text.startswith(basehandlers.XSSI_PREFIX))
    self.assertIn(json.dumps(handler_data), actual_sent_text)

  def test_do_get(self):
    """If a subclass does not implement do_get(), raise NotImplementedError."""
    with self.assertRaises(NotImplementedError):
      self.handler.do_get()

    with self.assertRaises(NotImplementedError):
      self.handler.do_get(feature_id=1234)

  @mock.patch('flask.abort')
  def check_bad_HTTP_method(self, handler_method, mock_abort):
    mock_abort.side_effect = werkzeug.exceptions.MethodNotAllowed

    with self.assertRaises(mock_abort.side_effect):
      handler_method()
    mock_abort.assert_called_once_with(405, valid_methods=['GET'])

    # Extra URL parameters do not crash the app.
    with self.assertRaises(mock_abort.side_effect):
      handler_method(feature_id=1234)

  def test_do_post(self):
    """If a subclass does not implement do_post(), return a 405."""
    self.check_bad_HTTP_method(self.handler.do_post)

  def test_do_patch(self):
    """If a subclass does not implement do_patch(), return a 405."""
    self.check_bad_HTTP_method(self.handler.do_patch)

  def test_do_delete(self):
    """If a subclass does not implement do_delete(), return a 405."""
    self.check_bad_HTTP_method(self.handler.do_delete)

  @mock.patch('framework.basehandlers.APIHandler.validate_token')
  def test_require_signed_in_and_xsrf_token__OK_body(self, mock_validate_token):
    """User is signed in and has a token in the request body."""
    testing_config.sign_in('user@example.com', 111)
    params = {'token': 'valid body token'}
    with test_app.test_request_context('/path', json=params):
      self.handler.require_signed_in_and_xsrf_token()
    mock_validate_token.assert_called_once_with(
        'valid body token', 'user@example.com')

  @mock.patch('framework.basehandlers.APIHandler.validate_token')
  def test_require_signed_in_and_xsrf_token__OK_header(
      self, mock_validate_token):
    """User is signed in and has a token in the request header."""
    testing_config.sign_in('user@example.com', 111)
    headers = {'X-Xsrf-Token': 'valid header token'}
    params = {}
    with test_app.test_request_context('/path', headers=headers, json=params):
      self.handler.require_signed_in_and_xsrf_token()
    mock_validate_token.assert_called_once_with(
        'valid header token', 'user@example.com')

  @mock.patch('framework.basehandlers.APIHandler.validate_token')
  def test_require_signed_in_and_xsrf_token__missing(self, mock_validate_token):
    """User is signed in but missing a token."""
    testing_config.sign_in('user@example.com', 111)
    params = {}  # No token
    with test_app.test_request_context('/path', json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.require_signed_in_and_xsrf_token()
    mock_validate_token.assert_not_called()

  @mock.patch('framework.basehandlers.APIHandler.validate_token')
  def test_require_signed_in_and_xsrf_token__bad(self, mock_validate_token):
    """User is signed in but missing a token."""
    testing_config.sign_in('user@example.com', 111)
    mock_validate_token.side_effect = xsrf.TokenIncorrect()
    params = {'token': 'bad token'}
    with test_app.test_request_context('/path', json=params):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.require_signed_in_and_xsrf_token()
    mock_validate_token.assert_called()

  @mock.patch('framework.basehandlers.APIHandler.validate_token')
  def test_require_signed_in_and_xsrf_token__anon(self, mock_validate_token):
    """User is signed out, so reject."""
    testing_config.sign_out()
    with test_app.test_request_context('/path', json={}):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.require_signed_in_and_xsrf_token()
    mock_validate_token.assert_not_called()

  def test_update_last_visit_field__valid_user(self):
    """Update the last_visit field of a valid user."""
    updated_user = self.handler._update_last_visit_field("user@example.com")
    self.assertNotEqual(self.appuser.last_visit, None)
    self.assertTrue(updated_user)

  def test_update_last_field__no_user(self):
    """Don't update last_visit field if the user is unknown."""
    updated_invalid_user = self.handler._update_last_visit_field("invaliduser@example.com")
    self.assertFalse(updated_invalid_user)


class FlaskHandlerTests(testing_config.CustomTestCase):

  def setUp(self):
    self.user_1 = user_models.AppUser(email='registered@example.com')
    self.user_1.put()
    self.handler = TestableFlaskHandler()

  def tearDown(self):
    self.user_1.key.delete()

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
    with test_app.test_request_context('/path'):
      actual = self.handler.get_headers()
    self.assertEqual(
        {'Strict-Transport-Security':
             'max-age=63072000; includeSubDomains; preload',
         'X-UA-Compatible': 'IE=Edge,chrome=1',
         'X-Frame-Options': 'DENY',
         },
        actual)

  def test_get_template_data__missing(self):
    """Every subclass should overide get_template_data()."""
    self.handler = basehandlers.FlaskHandler()
    with self.assertRaises(NotImplementedError):
      self.handler.get_template_data()

  def test_get_template_path__missing(self):
    """Subclasses that don't define TEMPLATE_PATH trigger error."""
    self.handler = basehandlers.FlaskHandler()
    with self.assertRaises(ValueError):
      self.handler.get_template_path({})

  def test_get_template_path__specified_in_class(self):
    """Subclasses can define TEMPLATE_PATH."""
    actual = self.handler.get_template_path({})
    self.assertEqual('test_template.html', actual)

  def test_get_template_path__specalized_by_template_data(self):
    """If get_template_data() returned a template path, we use it."""
    actual = self.handler.get_template_path(
        {'template_path': 'special.html'})
    self.assertEqual('special.html', actual)

  def test_process_post_data__missing(self):
    """Subclasses that don't override process_post_data() give a 405."""
    self.handler = basehandlers.FlaskHandler()
    with self.assertRaises(werkzeug.exceptions.MethodNotAllowed):
      self.handler.process_post_data()

  def test_get_common_data__signed_out(self):
    """When user is signed out, offer sign in link."""
    testing_config.sign_out()

    actual = self.handler.get_common_data(path='/test/path')

    self.assertIn('prod', actual)
    self.assertIsNone(actual['user'])
    self.assertEqual(actual['app_version'], 'Undeployed')

  def test_get_common_data__signed_in(self):
    """When user is signed in, offer sign out link."""
    testing_config.sign_in('test@example.com', 111)

    actual = self.handler.get_common_data(path='/test/path')

    self.assertIn('prod', actual)
    self.assertIsNotNone(actual['user'])

  def test_render(self):
    """We can render a simple template to a string."""
    with test_app.app_context():
      actual = self.handler.render({'name': 'literal'}, 'test_template.html')
    self.assertIn('Hi literal', actual)

  def test_get__remove_www(self):
    """Requests to www.DOMAIN are redirected to the bare domain."""
    with test_app.test_request_context(
        '/test?foo=bar', base_url='https://www.chromestatus.com'):
      actual_response = self.handler.get()

    self.assertIn('/test?foo=bar', actual_response.headers['location'])
    self.assertNotIn('www', actual_response.headers['location'])

  def test_get__html_page(self):
    """We can process a request and return HTML and headers."""
    with test_app.test_request_context('/test'):
      actual_html, actual_status, actual_headers = self.handler.get()

    self.assertIn('Hi testing', actual_html)
    self.assertEqual(200, actual_status)
    self.assertNotIn('Access-Control-Allow-Origin', actual_headers)

  def test_get__json_dict(self):
    """We can process a GET request and JSON and headers."""
    self.handler.JSONIFY = True
    with test_app.test_request_context('/test'):
      actual_response, actual_headers = self.handler.get()

    self.assertIn('name', actual_response.get_json())
    self.assertEqual(200, actual_response.status_code)
    self.assertNotIn('Access-Control-Allow-Origin', actual_headers)

  def test_get__json_list(self):
    """We can process a GET request and JSON and headers."""
    self.handler.JSONIFY = True
    with test_app.test_request_context('/test'):
      actual_response, actual_headers = self.handler.get(
          item_list=[10, 20, 30])

    self.assertEqual([10, 20, 30], actual_response.get_json())
    self.assertEqual(200, actual_response.status_code)
    self.assertNotIn('Access-Control-Allow-Origin', actual_headers)

  def test_get__special_status(self):
    """get_template_data() can return a special HTTP status."""
    with test_app.test_request_context('/test'):
      actual_html, actual_status, actual_headers = self.handler.get(
          special_status=222)

    self.assertIn('Hi testing', actual_html)
    self.assertEqual(222, actual_status)
    self.assertNotIn('Access-Control-Allow-Origin', actual_headers)

  def test_get__redirect(self):
    """get_template_data() can return a redirect response object."""
    with test_app.test_request_context('/test'):
      actual_response = self.handler.get(
          redirect_to='some/other/path')

    self.assertIn('Response', type(actual_response).__name__)
    self.assertIn('some/other/path', actual_response.headers['location'])

  def test_post__json(self):
    """if process_post_data() returns a dict, it is passed to flask."""
    testing_config.sign_in('user@example.com', 111)
    with test_app.test_request_context('/test'):
      actual_dict, actual_headers = self.handler.post()

    self.assertEqual(
        {'objects': [1, 2, 3]},
        actual_dict)
    self.assertNotIn('Access-Control-Allow-Origin', actual_headers)

  def test_post__redirect(self):
    """if process_post_data() returns a redirect response, it is used."""
    testing_config.sign_in('user@example.com', 111)
    with test_app.test_request_context('/test'):
      actual_response, actual_headers = self.handler.post(
          redirect_to='some/other/path')

    self.assertIn('Response', type(actual_response).__name__)
    self.assertIn('some/other/path', actual_response.headers['location'])
    self.assertNotIn('Access-Control-Allow-Origin', actual_headers)

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
  def test_require_task_header__same_app(self):
    """If the incoming request is from our own app, we allow it."""
    headers = {'X-Appengine-Inbound-Appid': 'dev'}
    with test_app.test_request_context('/test', headers=headers):
      self.handler.require_task_header()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  def test_require_task_header__missing(self):
    """If the incoming request is not from GCT, abort."""
    with test_app.test_request_context('/test'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.require_task_header()

  def test_require_cron_header__while_testing(self):
    """During unit testing of cron handlers, we allow it."""
    with test_app.test_request_context('/test'):
      self.handler.require_cron_header()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  def test_require_cron_header__normal(self):
    """If the incoming request is from GCT, we allow it."""
    headers = {'X-AppEngine-Cron': 'true'}
    with test_app.test_request_context('/test', headers=headers):
      self.handler.require_cron_header()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  @mock.patch('framework.basehandlers.BaseHandler.get_current_user')
  @mock.patch('framework.permissions.can_admin_site')
  def test_require_cron_header__admin(
      self, mock_can_admin_site, mock_get_current_user):
    """If the incoming request is from an admin, we allow it."""
    mock_can_admin_site.return_value = True
    # Also mock get_current_user because it will not use the usual
    # unit test configuration if we have UNIT_TEST_MODE == False.
    mock_get_current_user.return_value = users.User('admin@example.com', 111)
    with test_app.test_request_context('/test'):
      self.handler.require_cron_header()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  @mock.patch('framework.basehandlers.BaseHandler.get_current_user')
  def test_require_cron_header__missing_nonadmin(self, mock_get_current_user):
    """If the incoming request is not from GAE, abort."""
    # Also mock get_current_user because it will not use the usual
    # unit test configuration if we have UNIT_TEST_MODE == False.
    mock_get_current_user.return_value = users.User('user1@example.com', 111)
    with test_app.test_request_context('/test'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.require_cron_header()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  def test_require_cron_header__missing_anon(self):
    """If the incoming request is not from GAE, abort."""
    testing_config.sign_out()
    with test_app.test_request_context('/test'):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.require_cron_header()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  @mock.patch('framework.users.get_current_user')
  def test_require_xsrf_token__normal(self, mock_get_user):
    """We accept a POST with a valid token."""
    testing_config.sign_in('user1@example.com', 111)
    mock_get_user.return_value = users.User(email='user1@example.com')
    form_data = {'token': xsrf.generate_token('user1@example.com')}
    with test_app.test_request_context('/test', data=form_data):
      self.handler.require_xsrf_token()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  def test_require_xsrf_token__missing(self):
    """We reject a POST with a missing token."""
    testing_config.sign_in('user1@example.com', 111)
    form_data = {}
    with test_app.test_request_context('/test', data=form_data):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.require_xsrf_token()

  @mock.patch('settings.UNIT_TEST_MODE', False)
  @mock.patch('framework.basehandlers.BaseHandler.get_current_user')
  def test_require_xsrf_token__wrong(self, mock_get_current_user):
    """We reject a POST with a incorrect token."""
    testing_config.sign_in('user1@example.com', 111)
    # Also mock get_current_user because it will not use the usual
    # unit test configuration if we have UNIT_TEST_MODE == False.
    mock_get_current_user.return_value = users.User('user1@example.com', 111)
    # Form has a token intended for a different user.
    form_data = {'token': xsrf.generate_token('user2@example.com')}
    with test_app.test_request_context('/test', data=form_data):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.require_xsrf_token()

  def test_split_input(self):
    """We can parse items from multi-item text fields."""
    with test_app.test_request_context(
        'path', data={
            'empty': '',
            'blanks': '   ',
            'colors': 'yellow\nblue',
            'names': 'alice, bob',
        }):
      self.assertEqual([], self.handler.split_input('missing'))
      self.assertEqual([], self.handler.split_input('empty'))
      self.assertEqual([], self.handler.split_input('blanks'))
      self.assertEqual(
          ['yellow', 'blue'],
          self.handler.split_input('colors'))
      self.assertEqual(
          ['alice', 'bob'],
          self.handler.split_input('names', delim=','))

  def test_split_emails(self):
    """We can parse emails from input fields with commas."""
    with test_app.test_request_context(
        'path', data={
            'empty': '',
            'blanks': '   ',
            'single': 'user@example.com',
            'nospace': 'user1@example.com,user2@example.com',
            'withspace': ' user1@example.com, user2@example.com ',
            'extracommas': ',user1@example.com, ,,user2@example.com, ',
        }):
      self.assertEqual([], self.handler.split_emails('missing'))
      self.assertEqual([], self.handler.split_emails('empty'))
      self.assertEqual([], self.handler.split_emails('blanks'))
      self.assertEqual(
          ['user@example.com'],
          self.handler.split_emails('single'))
      self.assertEqual(
          ['user1@example.com', 'user2@example.com'],
          self.handler.split_emails('nospace'))
      self.assertEqual(
          ['user1@example.com', 'user2@example.com'],
          self.handler.split_emails('withspace'))
      self.assertEqual(
          ['user1@example.com', 'user2@example.com'],
          self.handler.split_emails('extracommas'))

  def test_extract_link__normal(self):
    """We can detect a link (discarding other text)."""
    self.assertEqual(
        'http://example.com',
        self.handler._extract_link('http://example.com'))
    self.assertEqual(
        'http://example.com',
        self.handler._extract_link('http://example.com/'))
    self.assertEqual(
        'http://example.com/path#anchor',
        self.handler._extract_link('http://example.com/path#anchor'))
    self.assertEqual(
        'http://example.com/1/2/c?x=y&z=2+2',
        self.handler._extract_link('http://example.com/1/2/c?x=y&z=2+2'))
    self.assertEqual(
        'https://example.com',
        self.handler._extract_link('https://example.com'))
    self.assertEqual(
        'http://example.com',
        self.handler._extract_link('http://example.com is a website'))
    self.assertEqual(
        'http://example.com',
        self.handler._extract_link('Please see http://example.com.'))
    self.assertEqual(
        'http://example.com?x=y',
        self.handler._extract_link('<a href="http://example.com?x=y"'))
    self.assertEqual(
        'http://example.com:8080?x=y',
        self.handler._extract_link('<a href="http://example.com:8080?x=y"'))

  def test_extract_link__add_http(self):
    """We add http:// when no scheme is found."""
    self.assertEqual(
        'http://example.com',
        self.handler._extract_link('example.com'))
    self.assertEqual(
        'http://example.com/1/2/c?x=y&z=2+2',
        self.handler._extract_link('example.com/1/2/c?x=y&z=2+2'))
    self.assertEqual(
        'http://192.168.0.1/1/2/c?x=y&z=2+2',
        self.handler._extract_link('192.168.0.1/1/2/c?x=y&z=2+2'))
    self.assertEqual(
        'http://example.com',
        self.handler._extract_link('<a href="example.com"'))
    self.assertEqual(
        'http://example.com',
        self.handler._extract_link('mailto:user@example.com'))

  def test_extract_link__bad(self):
    """We do not accept these as links."""
    self.assertIsNone(self.handler._extract_link(
        None))
    self.assertIsNone(self.handler._extract_link(
        ''))
    self.assertIsNone(self.handler._extract_link(
        '  '))
    self.assertIsNone(self.handler._extract_link(
        'example..com'))
    self.assertIsNone(self.handler._extract_link(
        'TBD'))
    self.assertIsNone(self.handler._extract_link(
        'Coming soon'))
    self.assertIsNone(self.handler._extract_link(
        'http://localhost/'))
    self.assertIsNone(self.handler._extract_link(
        'http://localhost:8080/'))

    self.assertIsNone(self.handler._extract_link(
        'ftp://example.com/ftp'))
    self.assertIsNone(self.handler._extract_link(
        'javascript:alert(1)'))
    self.assertIsNone(self.handler._extract_link(
        'javascript:window.alert(1)'))
    self.assertIsNone(self.handler._extract_link(
        'about:flags'))


    # We might add support for these sometime, but not now.
    self.assertIsNone(self.handler._extract_link(
        'b/1234'))
    self.assertIsNone(self.handler._extract_link(
        'go/1234'))

  def test_parse_link(self):
    """We can parse a link from POST data."""
    with test_app.test_request_context(
        'path', data={
            'empty': '',
            'blanks': '   ',
            'noturl': 'Coming soon',
            'plain': 'http://example.com',
            'noscheme': 'example.com',
            'withspace': ' example.com ',
            'extrajunk': ' please see example.com, ',
        }):
      self.assertIsNone(self.handler.parse_link('missing'))
      self.assertIsNone(self.handler.parse_link('empty'))
      self.assertIsNone(self.handler.parse_link('blanks'))
      self.assertIsNone(self.handler.parse_link('noturl'))
      self.assertEqual(
          'http://example.com',
          self.handler.parse_link('plain'))
      self.assertEqual(
          'http://example.com',
          self.handler.parse_link('noscheme'))
      self.assertEqual(
          'http://example.com',
          self.handler.parse_link('withspace'))
      self.assertEqual(
          'http://example.com',
          self.handler.parse_link('extrajunk'))

  def test_parse_links(self):
    """We can parse links that are on separate lines."""
    with test_app.test_request_context(
        'path', data={
            'empty': '',
            'blanks': '   ',
            'noturl': ' Coming soon  ',
            'single': 'https://example.com',
            'multiple': 'example1.com\nexample2.com',
            'withspace': ' example1.com\n example2.com ',
            'extrajunk': ',example1.com,\n TODO: example2.com, ',
        }):
      self.assertEqual([], self.handler.parse_links('missing'))
      self.assertEqual([], self.handler.parse_links('empty'))
      self.assertEqual([], self.handler.parse_links('blanks'))
      self.assertEqual([], self.handler.parse_links('noturl'))
      self.assertEqual(
          ['https://example.com'],
          self.handler.parse_links('single'))
      self.assertEqual(
          ['http://example1.com', 'http://example2.com'],
          self.handler.parse_links('multiple'))
      self.assertEqual(
          ['http://example1.com', 'http://example2.com'],
          self.handler.parse_links('withspace'))
      self.assertEqual(
          ['http://example1.com', 'http://example2.com'],
          self.handler.parse_links('extrajunk'))


class TestCORS(testing_config.CustomTestCase):

  def test_with_allow_origin(self):
    """If the request hits a /data path, they get '*'."""
    with test_app.test_request_context('/data/test'):
      actual_response = test_app.full_dispatch_request()

    self.assertEqual(
        '*',
        actual_response.headers['Access-Control-Allow-Origin'])

  def test_without_allow_origin(self):
    """If the request hits any non-/data path, they get no header."""
    with test_app.test_request_context('/test'):
      actual_response = test_app.full_dispatch_request()

    self.assertNotIn('Access-Control-Allow-Origin', actual_response.headers)
