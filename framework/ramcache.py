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

"""
This module manages a distributed RAM cache as a global python dictionary in
each AppEngine instance.  AppEngine can spin up new instances or kill old ones
at any time.  Each instance's RAM cache is independent and might not have the
same entries as found in the RAM caches of other instances.

Each instance will do the work needed to compute a given RAM cache entry
itself.  The values computed in a given instance will speed up future requests
made to that instance only.

When the user edits something in the app, the updated entity is stored in
datastore.  Also, the singleton SharedInvalidate entity is updated with the
timestamp of the change.  Every request handler must start processing a request
by first calling SharedInvalidate.check_for_distributed_invalidation() which
checks for any needed invalidations and clears RAM cache entries in
that instance if needed.

For now, there is only a single RAM cache per instance and when anything is
invalidated, that entire RAM cache is completely cleared.  In the future,
invalidations could be compartmentalized by RAM cache type, or even specific
entity IDs.  Monorail uses that approach, but existing ChromeStatus code does
not need it.

Calling code must not mutate any value that is passed into set() or returned
from get().  If calling code needs to mutate such objects, it should call
copy.copy() or copy.deepcopy() to avoid unintentional cumulative mutations.

Unlike memcache, this RAM cache has no concept of expiration time.  So,
whenever a cached value would become invalid, it must be invalidated.
"""

import logging
import time as time_module
from google.appengine.ext import db


global_cache = {}
expires = {}

# Whenever the cache would have more than this many items, some
# random item is dropped, or the entire cache is cleared.
# If our instances are killed by appengine for exceeding memory limits,
# we can configure larger instances and/or reduce this value.
MAX_CACHE_SIZE = 10000

total_num_hits = 0
total_num_misses = 0


def set(key, value, time=None):
  """Emulate the memcache.set() method using a RAM cache."""
  if len(global_cache) + 1 > MAX_CACHE_SIZE:
    popped_item = global_cache.popitem()
    if popped_item[0] in expires:
      del expires[popped_item[0]]
  global_cache[key] = value
  if time:
    expires[key] = int(time_module.time()) + time


def _check_expired(keys):
  now = int(time_module.time())
  for key in keys:
    if key in expires and expires[key] < now:
      del expires[key]
      del global_cache[key]


def _count_hit_or_miss(keys):
  global total_num_hits, total_num_misses
  for key in keys:
    if key in global_cache:
      total_num_hits += 1
      verb = 'hit'
    else:
      total_num_misses += 1
      verb = 'miss'

    # TODO(jrobbins): Replace this with proper monitoring variables
    logging.info('cache %s for %r.  Hit ratio: %5.2f%%.', verb, key,
                 total_num_hits / (total_num_hits + total_num_misses) * 100)


def get(key):
  """Emulate the memcache.get() method using a RAM cache."""
  _check_expired([key])
  _count_hit_or_miss([key])
  return global_cache.get(key)


def get_multi(keys):
  """Emulate the memcache.get_multi() method using a RAM cache."""
  _check_expired(keys)
  _count_hit_or_miss(keys)
  return {
      key: global_cache[key]
      for key in keys
      if key in global_cache
  }


def set_multi(entries, time=None):
  """Emulate the memcache.set_multi() method using a RAM cache."""
  if len(global_cache) + len(entries) > MAX_CACHE_SIZE:
    global_cache.clear()
    expires.clear()
  global_cache.update(entries)
  if time:
    expire_time = int(time_module.time()) + time
    for key in entries:
      expires[key] = expire_time


def delete(key):
  """Emulate the memcache.delete() method using a RAM cache."""
  if key in global_cache:
    del global_cache[key]
    flush_all()  # Note: this is wasteful but infrequent in our app.


def flush_all():
  """Emulate the memcache.flush_all() method using a RAM cache.

     This does not clear the RAM cache in this instance.  That happens
     at the start of the next request when the request handler calls
     SharedInvalidate.check_for_distributed_invalidation().
  """
  SharedInvalidate.invalidate()


class SharedInvalidateParent(db.Model):
  pass


class SharedInvalidate(db.Model):

  PARENT_ENTITY_ID = 1234
  PARENT_KEY = db.Key.from_path('SharedInvalidateParent', PARENT_ENTITY_ID)
  SINGLETON_ENTITY_ID = 5678
  SINGLETON_KEY = db.Key.from_path(
      'SharedInvalidateParent', PARENT_ENTITY_ID,
      'SharedInvalidate', SINGLETON_ENTITY_ID)
  last_processed_timestamp = None

  updated = db.DateTimeProperty(auto_now=True)

  @classmethod
  def invalidate(cls):
    """Tell this and other appengine instances to invalidate their caches."""
    singleton = cls.get(cls.SINGLETON_KEY)
    if not singleton:
      singleton = SharedInvalidate(key=cls.SINGLETON_KEY)
    singleton.put()  # automatically sets singleton.updated to now.
    # The cache in each instance (including this one) will be
    # cleared on the next call to check_for_distributed_invalidation()
    # which should happen at the start of request processing.

  @classmethod
  def check_for_distributed_invalidation(cls):
    """Check if any appengine instance has invlidated the cache."""
    singleton = cls.get(cls.SINGLETON_KEY, read_policy=db.STRONG_CONSISTENCY)
    if not singleton:
      return  # No news is good news
    if (cls.last_processed_timestamp is None or
        singleton.updated > cls.last_processed_timestamp):
      global_cache.clear()
      expires.clear()
      cls.last_processed_timestamp = singleton.updated


def check_for_distributed_invalidation():
  """Just a shorthand way to call the class method."""
  SharedInvalidate.check_for_distributed_invalidation()
