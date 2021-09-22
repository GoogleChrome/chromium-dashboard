from __future__ import division
from __future__ import print_function

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

import logging
import os
import sys
import unittest

app_engine_path = os.environ.get('APP_ENGINE_PATH', '')
if not app_engine_path:
  app_engine_path = '/usr/lib/google-cloud-sdk/platform/google_appengine'
if os.path.exists(app_engine_path):
  sys.path.insert(0, app_engine_path)
else:
  print('Could not find appengine, please set APP_ENGINE_PATH',
        file=sys.stderr)
  sys.exit(1)

import dev_appserver
dev_appserver.fix_sys_path()

lib_path = os.path.join(os.path.dirname(__file__), 'lib')
from google.appengine.ext import vendor
vendor.add(lib_path) # add third party libs to "lib" folder.

os.environ['DJANGO_SECRET'] = 'test secret'
os.environ['SERVER_SOFTWARE'] = 'test ' + os.environ.get('SERVER_SOFTWARE', '')
os.environ['CURRENT_VERSION_ID'] = 'test.123'
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
os.environ['APPLICATION_ID'] = 'testing'


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
