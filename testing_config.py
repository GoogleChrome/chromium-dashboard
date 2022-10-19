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
import unittest

from google.cloud import ndb  # type: ignore
from pathlib import Path

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


class Testdata(object):
  def __init__(self, test_file_path: str):
    """Helper class to load testdata
    Common pattern to place the testdata in the following format:

    Given a test file, atest_test.py, and it is located at
    /some/module/atest_test.py.

    The testdata should be located at /some/module/testdata/atest_test/
    """
    self.testdata = {}
    test_file_name = Path(test_file_path).stem
    self.testdata_dir = os.path.join(
        os.path.abspath(os.path.dirname(test_file_path)),
        'testdata',
        test_file_name)
    for filename in os.listdir(self.testdata_dir):
      test_data_file_path = os.path.join(self.testdata_dir, filename)
      with open(test_data_file_path, 'r', encoding='UTF-8') as f:
        self.testdata[filename] = f.read()

  def make_golden(self, raw_data, test_data_file_name):
    """Helper function to make golden file
    """
    test_data_file_path = os.path.join(self.testdata_dir, test_data_file_name)
    with open(test_data_file_path, 'w', encoding='UTF-8') as f:
      f.write(raw_data)

  def __getitem__(self, key):
      return self.testdata[key]
