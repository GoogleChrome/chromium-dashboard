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

import base64
import hmac
import logging
import random
import string
import time

from google.cloud import ndb  # type: ignore


# For random key generation
RANDOM_KEY_LENGTH = 128
RANDOM_KEY_CHARACTERS = string.ascii_letters + string.digits


def make_random_key(length=RANDOM_KEY_LENGTH, chars=RANDOM_KEY_CHARACTERS):
  """Return a string with lots of random characters."""
  chars = [random.choice(chars) for _ in range(length)]
  return ''.join(chars)


class Secrets(ndb.Model):
  """A server-side-only value that we use to generate security tokens."""

  xsrf_secret = ndb.StringProperty()
  session_secret = ndb.StringProperty()

  @classmethod
  def _get_or_make_singleton(cls):
    needs_save = False
    singleton = None
    existing = Secrets.query().fetch(1)
    if existing:
      singleton = existing[0]

    if not singleton:
      logging.info('Creating new secrets')
      singleton = Secrets()
      needs_save = True

    if not singleton.xsrf_secret:
      random_xsrf = make_random_key()
      singleton.xsrf_secret = random_xsrf
      logging.info('Added XSRF info: %r', random_xsrf[:8])
      needs_save = True

    if not singleton.session_secret:
      random_sess = make_random_key()
      singleton.session_secret = random_sess
      logging.info('Added session info: %r', random_sess[:8])
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


GITHUB_API_NAME = 'github'


class ApiCredential(ndb.Model):
  """A server-side-only list of values that we use to access APIs."""
  api_name = ndb.StringProperty(required=True)
  token = ndb.StringProperty()

  @classmethod
  def randomly_select_token_for_api(cls, api_name: str) -> str | None:
    """Return one of our tokens for the requested API or None."""
    query = ApiCredential.query(ApiCredential.api_name == api_name)
    all_for_api = query.fetch(None)
    if not all_for_api:
      blank_entry = ApiCredential(api_name=api_name)
      blank_entry.put()
      logging.info('Created an ApiCredential for %r', api_name)
      logging.info('Please use the Cloud Console to fill in a token')
      return None

    # If ndb has multiple tokens for the same API, choose randomly
    # among them so that different server instances will use different
    # tokens and spend the quota of each token roughly evenly.
    logging.info('Found %r tokens for %r', len(all_for_api), api_name)
    return random.choice(all_for_api).token

  @classmethod
  def get_github_token(cls) -> str | None:
    """Return one of our GitHub tokens or None."""
    return cls.randomly_select_token_for_api(GITHUB_API_NAME)
