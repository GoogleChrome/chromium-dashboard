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

import base64
import hmac
import logging
import random
import string
import time

from google.appengine.ext import db


# For random key generation
RANDOM_KEY_LENGTH = 128
RANDOM_KEY_CHARACTERS = string.ascii_letters + string.digits


def make_random_key(length=RANDOM_KEY_LENGTH, chars=RANDOM_KEY_CHARACTERS):
  """Return a string with lots of random characters."""
  chars = [random.choice(chars) for _ in range(length)]
  return ''.join(chars)


class Secrets(db.Model):
  """A server-side-only value that we use to generate security tokens."""

  xsrf_secret = db.StringProperty()
  session_secret = db.StringProperty()

  @classmethod
  def _get_or_make_singleton(cls):
    needs_save = False
    singleton = None
    existing = Secrets.all().fetch(1)
    if existing:
      singleton = existing[0]

    if not singleton:
      logging.info('Creating new secrets')
      singleton = Secrets()
      needs_save = True

    if not singleton.xsrf_secret:
      singleton.xsrf_secret = make_random_key()
      logging.info('Added XSRF secret: %r' % singleton.xsrf_secret)
      needs_save = True

    if not singleton.session_secret:
      singleton.session_secret = make_random_key()
      logging.info('Added session secret: %r' % singleton.session_secret)
      needs_save = True

    if needs_save:
      logging.info('Saving new secrets')
      singleton.put()

    return singleton


def get_xsrf_secret():
  """Return the xsrf secret key."""
  singleton = Secrets._get_or_make_singleton()
  return singleton.xsrf_secret


def get_session_secret():
  """Return the session secret key."""
  singleton = Secrets._get_or_make_singleton()
  return singleton.session_secret
