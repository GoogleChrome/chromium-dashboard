# Copyright 2024 Google Inc.
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
import requests
import urllib
import urllib.parse
import uuid
from typing import Tuple

from google.appengine.api import app_identity
from google.appengine.api import images
from google.cloud import storage
from google.cloud import ndb  # type: ignore

from framework import utils
import settings


RESIZABLE_MIME_TYPES = [
    'image/png', 'image/jpg', 'image/jpeg', 'image/gif', 'image/webp',
    ]
THUMB_WIDTH = 250
THUMB_HEIGHT = 200
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB


class FakeGCS(ndb.Model):
  """A simple way to store attachments locally for developers."""
  bucket_and_blob = ndb.StringProperty(required=True)
  content = ndb.BlobProperty(required=True)
  mime_type = ndb.StringProperty(required=True)


class UnsupportedMimeType(Exception):
  pass

class AttachmentTooLarge(Exception):
  pass


_EXTENSION_TO_CTYPE_TABLE = {
    # These are image types that we trust the browser to display.
    'gif': 'image/gif',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'webp': 'image/webp',
}


def guess_content_type_from_filename(filename: str) -> str:
  """Guess a file's content type based on the filename extension."""
  ext = filename.split('.')[-1] if ('.' in filename) else ''
  ext = ext.lower()
  return _EXTENSION_TO_CTYPE_TABLE.get(ext, 'application/octet-stream')


def store_object_in_gcs(
    bucket_name: str, content: bytes, mime_type: str, blob_name: str) -> None:
  storage_client = storage.Client()
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(blob_name)
  blob.upload_from_string(content, content_type=mime_type)


def store_object_in_fake_gcs(
    bucket_name: str, content: bytes, mime_type: str, blob_name: str) -> None:
  """Store the content in RAM because we have no GCS emulator."""
  logging.info(
      'Storing locally %r bytes in bucket %r blob %r',
      len(content), bucket_name, blob_name)
  blob = FakeGCS(
      bucket_and_blob=f'{bucket_name}/{blob_name}',
      content=content,
      mime_type=mime_type)
  blob.put()


def store_object(field_name: str, content: bytes, mime_type: str) -> str:
  """"Store some data in GCS or NDB.  Return a URI for it."""
  check_attachment_size(content)
  check_attachment_type(mime_type)
  default_bucket_name = app_identity.get_default_gcs_bucket_name()
  bucket_name = f'{default_bucket_name}-{field_name}'
  blob_name = str(uuid.uuid4())
  if settings.DEV_MODE:
    store_object_in_fake_gcs(bucket_name, content, mime_type, blob_name)
  else:
    store_object_in_gcs(bucket_name, content, mime_type, blob_name)

  if mime_type in RESIZABLE_MIME_TYPES:
    # Create and save a thumbnail too.
    thumb_content = None
    try:
      thumb_content = images.resize(content, THUMB_WIDTH, THUMB_HEIGHT)
    except images.LargeImageError:
      # Don't log the whole exception because we don't need to see
      # this on the Cloud Error Reporting page.
      logging.info('Got LargeImageError on image with %d bytes', len(content))
    except Exception as e:
      # Do not raise exception for incorrectly formed images.
      # See https://bugs.chromium.org/p/monorail/issues/detail?id=597 for more
      # detail.
      logging.exception(e)
    if thumb_content:
      thumb_blob_name = f'{blob_name}-thumbnail'
      if settings.DEV_MODE:
        store_object_in_fake_gcs(
            bucket_name, thumb_content, 'image/png', thumb_blob_name)
      else:
        store_object_in_gcs(
            bucket_name, thumb_content, 'image/png', thumb_blob_name)

  return f'/attachments/{field_name}/{blob_name}'


def check_attachment_size(content: bytes):
  """Reject attachments that are too large."""
  if len(content) > MAX_ATTACHMENT_SIZE:
    raise AttachmentTooLarge('Attachment size %r is too large' % len(content))


def check_attachment_type(mime_type: str):
  """Reject attachments that are of an unsupported type."""
  if mime_type not in RESIZABLE_MIME_TYPES:
    raise UnsupportedMimeType(
        'Please upload an image with one of the following mime types:\n%s' %
            ', '.join(RESIZABLE_MIME_TYPES))


@utils.retry(3, delay=0.25, backoff=1.25)
def _fetch_signed_url(url):
  """Request that devstorage API signs a GCS content URL."""
  resp = requests.get(url, allow_redirects=False)
  redir_url = resp.headers["Location"]
  return str(redir_url)


def get_object_url_in_gcs(field_name: str, blob_name: str) -> str:
  """Return a URL to view a GCS object.
  Args:
    field_name: string GCS bucket name.
    blob_name: string object ID of the file to serve.
  Returns:
    A signed URL, or '/mising-gcs-url' if signing failed.
  """
  try:
    default_bucket_name = app_identity.get_default_gcs_bucket_name()
    bucket_name = f'{default_bucket_name}-{field_name}'
    quoted_blob = urllib.parse.quote_plus(blob_name)
    scopes = ['https://www.googleapis.com/auth/devstorage.read_only']
    token = app_identity.get_access_token(scopes)[0]
    rest_api_url = (
        f'https://www.googleapis.com/storage/v1'
        '/b/{bucket_name}'
        '/o/{quoted_blob}'
        '?access_token={token}&alt=media')
    attachment_url = _fetch_signed_url(rest_api_url)
    return attachment_url
  except Exception as e:
    logging.exception(e)
    return '/missing-gcs-url'  # This will 404.


def get_content_from_fake_gcs(
    bucket_name: str, blob_name: str) -> Tuple[bytes|None, str|None]:
  """Return content from our fake GCS when running locally."""
  bucket_and_blob = f'{bucket_name}/{blob_name}'
  q = FakeGCS.query(FakeGCS.bucket_and_blob == bucket_and_blob)
  blob = q.get()
  if blob:
    return blob.content, blob.mime_type
  else:
    return None, None
