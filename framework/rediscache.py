

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

import os
import json
import logging
import settings

from google.cloud import ndb
import redis
import fakeredis

redis_client = None

if settings.UNIT_TEST_MODE:
  redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
elif settings.STAGING or settings.PROD:
  # Create a Redis client.
  redis_host = os.environ.get('REDISHOST', 'localhost')
  redis_port = int(os.environ.get('REDISPORT', 6379))
  redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

gae_version = None
if settings.UNIT_TEST_MODE:
  # gae_version prefix for testing.
  gae_version = 'testing'
elif settings.STAGING or settings.PROD:
  gae_version = os.environ.get('GAE_VERSION', 'Undeployed')


def set(key, value, time=86400):
  """
  Redis SET sets the str key, value pair, https://redis.io/commands/set/; if
  ``key`` already holds a value, it is overwritten.

  ``time`` sets the expire time for this key, in seconds.
  """
  if redis_client is None:
    return

  if not isinstance(value, str):
    logging.info(
        'value %s is not an instance of str, abort set caching', value)
    return

  cache_key = add_gae_prefix(key)
  if time:
    redis_client.set(cache_key, value, ex=time)
  else:
    redis_client.set(cache_key, value)


def get(key):
  """
  Redis GET gets the value of key. Return nil if ``key`` does not
  exist; return an error if the value returned is not a str.
  """
  if redis_client is None:
    return None

  cache_key = add_gae_prefix(key)
  return redis_client.get(cache_key)


def get_multi(keys):
  """Return the values of all given keys."""
  if redis_client is None:
    return None

  cache_keys = [add_gae_prefix(k) for k in keys]
  vals = redis_client.mget(cache_keys)
  return dict(zip(keys, vals))


def set_multi(entries, time=86400):
  """
  Set the given keys to their respective values.

  ``time`` sets the expire time for this key, in seconds.
  """
  if redis_client is None:
    return

  data_entries = {}
  for key in entries:
    if not isinstance(entries[key], str):
      logging.info(
          'value %s is not an instance of str, skipping this cache', entries[key])
      continue

    if time:
      data_entries[key] = entries[key]
    else:
      # gae prefix is needed for mset.
      cache_key = add_gae_prefix(key)
      data_entries[cache_key] = entries[key]

  if not time:
    # https://redis.io/commands/mset/.
    redis_client.mset(data_entries)
    return

  for key in data_entries:
    set(key, data_entries[key], time)


def delete(key):
  """Redis DEL removes the value to the key, https://redis.io/commands/del/."""
  if redis_client is None:
    return

  cache_key = add_gae_prefix(key)
  redis_client.delete(cache_key)


def flushall():
  """Delete all the keys in Redis, https://redis.io/commands/flushall/."""
  if redis_client is None:
    return

  redis_client.flushall()


def add_gae_prefix(key):
  if gae_version is None:
    return key

  return gae_version + '-' + key

def serialize_non_str(data):
  if data is None:
    return None
  return json.dumps(data)

def deserialize_non_str(raw_data):
  if raw_data is None:
    return None
  return json.loads(raw_data)
