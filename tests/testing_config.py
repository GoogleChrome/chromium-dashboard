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

from __future__ import print_function
import os
import sys
import unittest

app_engine_path = os.environ.get('APP_ENGINE_PATH', '')
if not app_engine_path:
  app_engine_path = '/usr/lib/google-cloud-sdk/platform/google_appengine'
if not os.path.exists(app_engine_path):
  app_engine_path = '/home/travis/google-cloud-sdk/platform/google_appengine'
if os.path.exists(app_engine_path):
  sys.path.insert(0, app_engine_path)
else:
  print('Could not find appengine, please set APP_ENGINE_PATH',
        file=sys.stderr)
  sys.exit(1)

import dev_appserver
dev_appserver.fix_sys_path()

lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
sys.path.insert(0, lib_path)

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import testbed

os.environ['DJANGO_SECRET'] = 'test secret'
os.environ['SERVER_SOFTWARE'] = 'test ' + os.environ.get('SERVER_SOFTWARE', '')
os.environ['CURRENT_VERSION_ID'] = 'test.123'


ourTestbed = testbed.Testbed()

def setUpOurTestbed():
  # needed because endpoints expects a . in this value
  ourTestbed.setup_env(current_version_id='testbed.version')
  ourTestbed.activate()
  # Can't use init_all_stubs() because PIL isn't in wheel.
  ourTestbed.init_app_identity_stub()
  ourTestbed.init_blobstore_stub()
  ourTestbed.init_capability_stub()
  ourTestbed.init_channel_stub()
  ourTestbed.init_datastore_v3_stub()
  ourTestbed.init_files_stub()
  ourTestbed.init_logservice_stub()
  ourTestbed.init_mail_stub()
  ourTestbed.init_memcache_stub()
  ourTestbed.init_modules_stub()
  ourTestbed.init_search_stub()
  ourTestbed.init_taskqueue_stub()
  ourTestbed.init_urlfetch_stub()
  ourTestbed.init_user_stub()
  ourTestbed.init_xmpp_stub()

# Normally this would be done in the setUp() methods of individual test files,
# but we need it to be done before importing any application code because
# models.py makes GAE API calls to in code that runs during loading.
setUpOurTestbed()


class Blank(object):
  """Simple class that assigns all named args to attributes.
  Tip: supply a lambda to define a method.
  """
  def __init__(self, **kwargs):
    vars(self).update(kwargs)
  def __repr__(self):
    return '%s(%s)' % (self.__class__.__name__, str(vars(self)))
  def __eq__(self, other):
    if other is None:
      return False
    return vars(self) == vars(other)


def sign_out():
  """Set env variables to represent a signed out user."""
  ourTestbed.setup_env(
      user_email='', user_id='', overwrite=True)


def sign_in(user_email, user_id):
  """Set env variables to represent a signed out user."""
  ourTestbed.setup_env(
      user_email=user_email,
      user_id=str(user_id),
      overwrite=True)
