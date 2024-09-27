

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
import pickle
import logging
import settings

import redis
import fakeredis

from redis.retry import Retry
from redis.backoff import ExponentialBackoff

redis_client = None

if settings.UNIT_TEST_MODE:
  redis_client = fakeredis.FakeStrictRedis()
elif settings.STAGING or settings.PROD:
  # Create a Redis client.
  redis_host = os.environ.get('REDISHOST', 'localhost')
  redis_port = int(os.environ.get('REDISPORT', 6379))
  redis_client = redis.Redis(host=redis_host, port=redis_port, health_check_interval=30,
                             socket_keepalive=True, retry_on_timeout=True, retry=Retry(ExponentialBackoff(cap=5, base=1), 5))

gae_version = None
if settings.UNIT_TEST_MODE:
  # gae_version prefix for testing.
  gae_version = 'testing'
elif settings.STAGING or settings.PROD:
  gae_version = os.environ.get('GAE_VERSION', 'Undeployed')


def set(key, value, time=86400):
  """
  Redis SET sets the str/binary key, value pair, https://redis.io/commands/set/; if
  ``key`` already holds a value, it is overwritten.

  ``time`` sets the expire time for this key, in seconds.
  """
  if redis_client is None:
    return

  cache_key = add_gae_prefix(key)
  if time:
    redis_client.set(cache_key, pickle.dumps(value), ex=time)
  else:
    redis_client.set(cache_key, pickle.dumps(value))


def get(key):
  """
  Redis GET gets the value of key. Return None if ``key`` does not
  exist; return an error if the value returned is not a str/binary.
  """
  if redis_client is None:
    return None

  cache_key = add_gae_prefix(key)
  raw_value = redis_client.get(cache_key)
  if raw_value is None:
    return None
  return pickle.loads(raw_value)


def get_multi(keys):
  """Return the values of all given keys."""
  if redis_client is None:
    return None

  cache_keys = [add_gae_prefix(k) for k in keys]
  raw_vals = redis_client.mget(cache_keys)
  vals = [pickle.loads(v) if v is not None else None for v in raw_vals]
  return dict(zip(keys, vals))


def set_multi(entries, time=86400):
  """
  Set the given keys to their respective values.

  ``time`` sets the expire time for this key, in seconds.
  """
  if redis_client is None:
    return

  if time:
    for key in entries:
      set(key, entries[key], time)
    return

  data_entries = {}
  for key in entries:
    # gae prefix is needed for mset.
    cache_key = add_gae_prefix(key)
    data_entries[cache_key] = pickle.dumps(entries[key])

  # https://redis.io/commands/mset/.
  redis_client.mset(data_entries)


def delete(key):
  """Redis DEL removes the value to the key, https://redis.io/commands/del/."""
  if redis_client is None:
    return

  cache_key = add_gae_prefix(key)
  redis_client.delete(cache_key)


def delete_keys_with_prefix(prefix: str):
  """Delete all keys matching a prefix."""
  pattern = prefix + '|*'
  if redis_client is None:
    return

  prefix = add_gae_prefix(pattern)
  # https://redis.io/commands/scan/
  pos, keys = redis_client.scan(cursor=0, match=prefix)
  target = keys
  while pos != 0:
    pos, keys = redis_client.scan(cursor=pos, match=prefix)
    target.extend(keys)

  for key in target:
    redis_client.delete(key)


def flushall():
  """Delete all the keys in Redis, https://redis.io/commands/flushall/."""
  if redis_client is None:
    return

  redis_client.flushall()


def add_gae_prefix(key):
  if gae_version is None:
    return key

  return gae_version + '-' + key
