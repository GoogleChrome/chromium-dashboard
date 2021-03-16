from __future__ import division
from __future__ import print_function

# -*- coding: utf-8 -*-
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

# This code is based on a file from Monorail:
# https://chromium.googlesource.com/infra/infra/+/master/appengine/monorail/framework/cloud_tasks_helpers.py

import logging
import json

import requests

import settings

if not settings.UNIT_TEST_MODE:
  import grpc  # See requirements.dev.txt.
  from google.api_core import retry
  from google.cloud import tasks



_client = None

# Default exponential backoff retry config for enqueueing, not to be confused
# with retry config for dispatching, which exists per queue.
_DEFAULT_RETRY = None
if not settings.UNIT_TEST_MODE:
  _DEFAULT_RETRY = retry.Retry(
      initial=.1, maximum=1.6, multiplier=2, deadline=10)


class LocalCloudTasksClient(object):
  """We have no GCT server running locally, so hit the target synchronously."""

  def queue_path(self, project, location, queue):
    """Return a fully-qualified queue string."""
    # This is value is not actually used, but it might be good for debugging.
    return "projects/{project}/locations/{location}/queues/{queue}".format(
        project=project, location=location, queue=queue)

  def create_task(self, unused_parent, task, **kwargs):
    """Immediately hit the target URL."""
    uri = task.get('app_engine_http_request').get('relative_uri')
    target_url = 'http://localhost:8080' + uri
    body = task.get('app_engine_http_request').get('body')
    logging.info('Making request to %r', target_url)
    handler_response = requests.request('POST', 
        target_url, data=body, allow_redirects=False,
        # This header can only be set on internal requests, not by users.
        headers={'X-AppEngine-QueueName': 'default'})
    logging.info('Task handler status: %d', handler_response.status_code)
    logging.info('Task handler text: %r', handler_response.content)


def _get_client():
  """Returns a cloud tasks client."""
  global _client
  if not _client:
    if settings.DEV_MODE:
      _client = LocalCloudTasksClient()
    else:
      _client = tasks.CloudTasksClient()
  return _client


def _make_task(handler_path, task_params):
  body_json = json.dumps(task_params)
  return {
      'app_engine_http_request': {
          'relative_uri': handler_path,
          'body': body_json,
      }
  }


def enqueue_task(handler_path, task_params, queue='default', **kwargs):
  """Enqueue a JSON task item for Google Cloud Tasks.

  Args:
    handler_path: Rooted path of the task handler.
    task_params: Task parameters dict.
    queue: A string indicating name of the queue to add task to.
    kwargs: Additional arguments to pass to cloud task client's create_task

  Returns:
    Successfully created Task object.
  """
  task = _make_task(handler_path, task_params)
  client = _get_client()
  parent = client.queue_path(
      settings.APP_ID, settings.CLOUD_TASKS_REGION, queue)

  target = task.get('app_engine_http_request').get('relative_uri')
  logging.info('Enqueueing %s task to %s', target, parent)

  kwargs.setdefault('retry', _DEFAULT_RETRY)
  return client.create_task(parent, task, **kwargs)
