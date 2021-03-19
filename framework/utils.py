# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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

from __future__ import division
from __future__ import print_function

import datetime
import flask
import logging
import time
import traceback

from google.appengine.api import users

import settings

from django.utils import feedgenerator


def format_feature_url(feature_id):
  """Return the feature detail page URL for the specified feature."""
  return '/feature/%d' % feature_id


def retry(tries, delay=1, backoff=2):
  """A retry decorator with exponential backoff.

  Functions are retried when Exceptions occur.

  Args:
    tries: int Number of times to retry, set to 0 to disable retry.
    delay: float Initial sleep time in seconds.
    backoff: float Must be greater than 1, further failures would sleep
             delay*=backoff seconds.
  """
  if backoff <= 1:
    raise ValueError("backoff must be greater than 1")
  if tries < 0:
    raise ValueError("tries must be 0 or greater")
  if delay <= 0:
    raise ValueError("delay must be greater than 0")

  def decorator(func):
    def wrapper(*args, **kwargs):
      _tries, _delay = tries, delay
      _tries += 1  # Ensure we call func at least once.
      while _tries > 0:
        try:
          ret = func(*args, **kwargs)
          return ret
        except Exception:
          _tries -= 1
          if _tries == 0:
            logging.error('Exceeded maximum number of retries for %s.',
                          func.__name__)
            raise
          trace_str = traceback.format_exc()
          logging.warning('Retrying %s due to Exception: %s',
                          func.__name__, trace_str)
          time.sleep(_delay)
          _delay *= backoff  # Wait longer the next time we fail.
    return wrapper
  return decorator


def strip_trailing_slash(handler):
  """Strips the trailing slash on the URL."""
  def remove_slash(self, *args, **kwargs):
    path = args[0]
    if path[-1] == '/':
      return self.redirect(self.request.path.rstrip('/'))

    return handler(self, *args, **kwargs) # Call the handler method
  return remove_slash


def render_atom_feed(request, title, data):
  features_url = '%s://%s%s' % (request.scheme,
                                request.host,
                                request.path.replace('.xml', ''))
  feature_url_prefix = '%s://%s%s' % (request.scheme,
                                      request.host,
                                      '/feature')

  feed = feedgenerator.Atom1Feed(
      title=unicode('%s - %s' % (settings.APP_TITLE, title)),
      link=features_url,
      description=u'New features exposed to web developers',
      language=u'en'
  )
  for f in data:
    pubdate = datetime.datetime.strptime(str(f['updated'][:19]),
                                         '%Y-%m-%d  %H:%M:%S')
    feed.add_item(
        title=unicode(f['name']),
        link='%s/%s' % (feature_url_prefix, f.get('id')),
        description=f.get('summary', ''),
        pubdate=pubdate,
        author_name=unicode(settings.APP_TITLE),
        categories=[f['category']]
    )
  headers = {
      'Strict-Transport-Security':
          'max-age=63072000; includeSubDomains; preload',
      'Content-Type': 'application/atom+xml;charset=utf-8'}
  text = feed.writeString('utf-8')
  return text, headers
