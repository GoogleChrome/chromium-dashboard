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

import mock
import unittest
import testing_config  # Must be imported before the module under test.

import requests

from framework import cloud_tasks_helpers
# Note that testing_config sets cloud_tasks_helpers._client to a fake.


class LocalCloudTasksClientTest(unittest.TestCase):

  def setUp(self):
    self.client = cloud_tasks_helpers.LocalCloudTasksClient()

  def test_queue_path(self):
    """We get back a string like the kind that GCT uses."""
    actual = self.client.queue_path('P', 'L', 'Q')
    self.assertEqual(
        'projects/P/locations/L/queues/Q',
        actual)

  @mock.patch('requests.request')
  def test_create_task(self, mock_fetch):
    """The local stub makes a synchronous HTTP request to the task handler."""
    parent = 'parent'
    task = cloud_tasks_helpers._make_task('/handler', {'a': 1})
    mock_fetch.return_value = testing_config.Blank(
        status_code=200, content='content')

    actual = self.client.create_task(parent, task)

    self.assertIsNone(actual)
    mock_fetch.assert_called_once_with(
      'POST',
        'http://localhost:8080/handler',
        data='{"a": 1}',
        allow_redirects=False,
        headers={'X-AppEngine-QueueName': 'default'})


class CloudTasksHelpersTest(unittest.TestCase):

  def test_get_client__unit_tests(self):
    """During unit testing, we are using a fake object."""
    actual = cloud_tasks_helpers._get_client()
    self.assertEqual(
        testing_config.FakeCloudTasksClient,
        type(actual))

  @mock.patch('settings.DEV_MODE', True)
  def test_get_client__dev_mode(self):
    """When running locally, we make a LocalCloudTasksClient."""
    orig_client = cloud_tasks_helpers._client
    try:
      cloud_tasks_helpers._client = None
      actual = cloud_tasks_helpers._get_client()
      self.assertEqual(
          cloud_tasks_helpers.LocalCloudTasksClient,
          type(actual))
    finally:
      cloud_tasks_helpers._client = orig_client

  def test_make_task(self):
    """We can make a task info dict in the expected format."""
    handler_path = '/handler'
    task_params = {'a': 1}

    actual = cloud_tasks_helpers._make_task(handler_path, task_params)

    self.assertEqual(
        { 'app_engine_http_request': {
            'relative_uri': '/handler',
            'body': '{"a": 1}',
            }
         },
        actual)

  def test_enqueue_task(self):
    """We can call the GCT client to enqueue a task."""
    handler_path = '/handler'
    task_params = {'a': 1}

    actual = cloud_tasks_helpers.enqueue_task(handler_path, task_params)

    self.assertEqual('fake task', actual)
    self.assertEqual('/handler', cloud_tasks_helpers._client.uri)
    self.assertEqual('{"a": 1}', cloud_tasks_helpers._client.body)
