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

import logging
import random
import settings
import string
import time

from google.cloud import ndb  # type: ignore


# For random key generation
RANDOM_KEY_LENGTH = 128
RANDOM_KEY_CHARACTERS = string.ascii_letters + string.digits

ot_api_key: str|None = None

def make_random_key(length=RANDOM_KEY_LENGTH, chars=RANDOM_KEY_CHARACTERS):
  """Return a string with lots of random characters."""
  chars = [random.choice(chars) for _ in range(length)]
  return ''.join(chars)


class Secrets(ndb.Model):
  """A server-side-only value that we use to generate security tokens."""

  xsrf_secret = ndb.StringProperty()
  session_secret = ndb.StringProperty()

  @classmethod
  @ndb.transactional(retries=4)
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
  failure_timestamp = ndb.IntegerProperty(default=0)

  @classmethod
  def select_token_for_api(cls, api_name: str) -> 'ApiCredential':
    """Return one of our credientials for the requested API or make a blank."""
    query = ApiCredential.query(ApiCredential.api_name == api_name)
    all_for_api = query.fetch(None)
    if not all_for_api:
      blank_entry = ApiCredential(api_name=api_name)
      blank_entry.put()
      logging.info('Created an ApiCredential for %r', api_name)
      logging.info('Please use the Cloud Console to fill in a token')
      return blank_entry

    # If ndb has multiple tokens for the same API, choose one
    # that has not failed recently for any reason (including quota).
    logging.info('Found %r tokens for %r', len(all_for_api), api_name)
    sorted_for_api = sorted(all_for_api, key=lambda ac: ac.failure_timestamp)
    return sorted_for_api[0]

  @classmethod
  def get_github_credendial(cls) -> 'ApiCredential':
    """Return an ApiCredential for GitHub."""
    return cls.select_token_for_api(GITHUB_API_NAME)

  def record_failure(self, now=None) -> None:
    """Mark this ApiCredential as failing now."""
    logging.info('Recording failure at %r', now or int(time.time()))
    self.failure_timestamp = now or int(time.time())
    self.put()


def get_ot_api_key() -> str|None:
  """Obtain an API key to be used for requests to the origin trials API."""
  # Reuse the API key's value if we've already obtained it.
  if settings.OT_API_KEY is not None:
    return settings.OT_API_KEY

  if settings.DEV_MODE or settings.UNIT_TEST_MODE:
    # In dev or unit test mode, pull the API key from a local file.
    try:
      with open(f'{settings.ROOT_DIR}/ot_api_key.txt', 'r') as f:
        settings.OT_API_KEY = f.read().strip()
        return settings.OT_API_KEY
    except:
      logging.info('No key found locally for the Origin Trials API.')
      return None
  else:
    # If in staging or prod, pull the API key from the project secrets.
    from google.cloud.secretmanager import SecretManagerServiceClient
    client = SecretManagerServiceClient()
    name = (f'{client.secret_path(settings.APP_ID, "OT_API_KEY")}'
            '/versions/latest')
    response = client.access_secret_version(request={'name': name})
    if response:
      settings.OT_API_KEY = response.payload.data.decode("UTF-8")
      return settings.OT_API_KEY
  return None


def get_ot_support_emails() -> str|None:
  """Obtain a comma-separated list of the OT support members."""
  if settings.DEV_MODE or settings.UNIT_TEST_MODE:
    # In dev or unit test mode, return a dummy value.
    return settings.DEV_MODE_OT_SUPPORT_EMAILS

  # If in staging or prod, pull the value from the project secrets.
  from google.cloud.secretmanager import SecretManagerServiceClient
  client = SecretManagerServiceClient()
  name = (f'{client.secret_path(settings.APP_ID, "OT_SUPPORT_EMAILS")}'
          '/versions/latest')
  response = client.access_secret_version(request={'name': name})
  if response:
    return response.payload.data.decode("UTF-8")
  return None


def get_ot_data_access_admin_group() -> str|None:
  """Obtain the name of the data access admn group for OT."""
  # Reuse the value if we've already obtained it.
  if settings.OT_DATA_ACCESS_ADMIN_GROUP_NAME is not None:
    return settings.OT_DATA_ACCESS_ADMIN_GROUP_NAME

  # If in staging or prod, pull the value from the project secrets.
  from google.cloud.secretmanager import SecretManagerServiceClient
  client = SecretManagerServiceClient()
  secret_path = client.secret_path(settings.APP_ID,
                                    "OT_DATA_ACCESS_ADMIN_GROUP_NAME")
  name = f'{secret_path}/versions/latest'
  response = client.access_secret_version(request={'name': name})
  if response:
    settings.OT_DATA_ACCESS_ADMIN_GROUP_NAME = (
        response.payload.data.decode("UTF-8"))
    return settings.OT_DATA_ACCESS_ADMIN_GROUP_NAME
  return None
