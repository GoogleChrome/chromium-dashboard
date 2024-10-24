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
from google.appengine.api import images
from google.cloud import ndb  # type: ignore
from typing import Tuple


RESIZABLE_MIME_TYPES = [
    'image/png', 'image/jpg', 'image/jpeg', 'image/gif', 'image/webp',
    ]
THUMB_WIDTH = 250
THUMB_HEIGHT = 200
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB


class Attachment(ndb.Model):
  """Attaches files, such as screenshots, to a feature entry."""
  feature_id = ndb.IntegerProperty(required=True)
  created_on = ndb.DateTimeProperty(auto_now_add=True)
  content = ndb.BlobProperty(required=True)
  mime_type = ndb.StringProperty(required=True)
  thumbnail = ndb.BlobProperty()
  is_deleted = ndb.BooleanProperty(default=False)


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
    'txt': 'text/plain',
}


def guess_content_type_from_filename(filename: str) -> str:
  """Guess a file's content type based on the filename extension."""
  ext = filename.split('.')[-1] if ('.' in filename) else ''
  ext = ext.lower()
  return _EXTENSION_TO_CTYPE_TABLE.get(ext, 'application/octet-stream')


def store_attachment(feature_id: int, content: bytes, mime_type: str) -> str:
  """"Store some data for an attachment.  Return its URI."""
  check_attachment_size(content)
  check_attachment_type(mime_type)
  logging.info('Storing attachment with %r bytes', len(content))

  attachment = Attachment(
      feature_id=feature_id,
      content=content,
      mime_type=mime_type)

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
      attachment.thumbnail = thumb_content

  attachment.put()
  return attachment


def check_attachment_size(content: bytes):
  """Reject attachments that are too large."""
  if len(content) > MAX_ATTACHMENT_SIZE:
    raise AttachmentTooLarge('Attachment size %r is too large' % len(content))


def check_attachment_type(mime_type: str):
  """Reject attachments that are of an unsupported type."""
  if mime_type not in _EXTENSION_TO_CTYPE_TABLE.values():
    raise UnsupportedMimeType(
        'Please upload an image with one of the following mime types:\n%s' %
            ', '.join(_EXTENSION_TO_CTYPE_TABLE.values()))


def get_attachment(feature_id: int, attachment_id: int) -> Attachment|None:
  """Return attachment, if feature_id  matches, and attachment is not deleted."""
  attachment = Attachment.get_by_id(attachment_id)
  if (attachment and
      attachment.feature_id == feature_id and
      not attachment.is_deleted):
    return attachment

  return None


def get_attachment_uri(attachment: Attachment) -> str:
  """Return the URI path that will serve tis attachment."""
  uri = '/feature/%r/attachment/%r' % (
      attachment.feature_id, attachment.key.integer_id())
  return uri


def mark_attachment_deleted(attachment: Attachment) -> None:
  """Mark an attachment as deleted so that it will no longer be served."""
  attachment.is_deleted = True
  attachment.put()
