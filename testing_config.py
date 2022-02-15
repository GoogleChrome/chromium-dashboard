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

from google.cloud import ndb

os.environ['DJANGO_SECRET'] = 'test secret'
os.environ['SERVER_SOFTWARE'] = 'test ' + os.environ.get('SERVER_SOFTWARE', '')
os.environ['CURRENT_VERSION_ID'] = 'test.123'
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
os.environ['APPLICATION_ID'] = 'testing'
# Envs for datastore-emulator, same as running `gcloud beta emulators datastore env-init`.
os.environ['DATASTORE_DATASET'] = 'cr-status-staging'
os.environ['DATASTORE_EMULATOR_HOST'] = 'localhost:15606'
os.environ['DATASTORE_EMULATOR_HOST_PATH'] = 'localhost:15606/datastore'
os.environ['DATASTORE_HOST'] = 'http//localhost:15606'
os.environ['DATASTORE_PROJECT_ID'] = 'cr-status-staging'


from framework import cloud_tasks_helpers

class FakeCloudTasksClient(object):
  """We have no GCT server for unit tests, so just log."""

  def queue_path(self, project, location, queue):
    """Return a fully-qualified queue string."""
    # This is value is not actually used, but it might be good for debugging.
    return "projects/{project}/locations/{location}/queues/{queue}".format(
        project=project, location=location, queue=queue)

  def create_task(self, parent=None, task=None, **kwargs):
    """Just log that the task would have been created URL."""
    self.uri = task.get('app_engine_http_request').get('relative_uri')
    self.body = task.get('app_engine_http_request').get('body')
    logging.info('Task uri: %r', self.uri)
    logging.info('Task body: %r', self.body)
    return 'fake task'


cloud_tasks_helpers._client = FakeCloudTasksClient()


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
  os.environ['USER_EMAIL'] = ''
  os.environ['USER_ID'] = ''
  os.environ['USER_IS_ADMIN'] = '0'
  os.environ['AUTH_DOMAIN'] = '1'

def sign_in(user_email, user_id):
  """Set env variables to represent a signed out user."""
  os.environ['USER_EMAIL'] = user_email
  os.environ['USER_ID'] = str(user_id)
  os.environ['USER_IS_ADMIN'] = '0'
  os.environ['AUTH_DOMAIN'] = '0'


class CustomTestCase(unittest.TestCase):

  def run(self, result=None):
    client = ndb.Client()
    with client.context():
      super(CustomTestCase, self).run(result=result)
