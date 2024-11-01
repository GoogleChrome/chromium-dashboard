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

import io
import logging
from PIL import Image
from google.cloud import ndb  # type: ignore
from typing import Tuple

import settings


RESIZABLE_MIME_TYPES = [
    'image/png', 'image/jpg', 'image/jpeg', 'image/gif', 'image/webp',
    ]
THUMB_WIDTH = 450
THUMB_HEIGHT = 300



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


SUPPORTED_MIME_TYPES = RESIZABLE_MIME_TYPES + ['text/plain']


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
      im = Image.open(io.BytesIO(content))
      im.thumbnail((THUMB_WIDTH, THUMB_HEIGHT))
      thumb_buffer = io.BytesIO()
      im.save(thumb_buffer, 'PNG')
      thumb_content = thumb_buffer.getvalue()
    except Exception as e:
      # Do not raise exception for incorrectly formed images.
      logging.exception(e)
    if thumb_content:
      attachment.thumbnail = thumb_content
      logging.info('Thumbnail is %r bytes', len(thumb_content))

  attachment.put()
  return attachment


def check_attachment_size(content: bytes):
  """Reject attachments that are too large."""
  if len(content) > settings.MAX_ATTACHMENT_SIZE:
    raise AttachmentTooLarge('Attachment size %r is too large' % len(content))


def check_attachment_type(mime_type: str):
  """Reject attachments that are of an unsupported type."""
  if mime_type not in SUPPORTED_MIME_TYPES:
    raise UnsupportedMimeType(
        'Please upload an image with one of the following mime types:\n%s' %
            ', '.join(SUPPORTED_MIME_TYPES))


def get_attachment(feature_id: int, attachment_id: int) -> Attachment|None:
  """Return attachment, if feature_id  matches, and attachment is not deleted."""
  attachment = Attachment.get_by_id(attachment_id)
  if (attachment and
      attachment.feature_id == feature_id and
      not attachment.is_deleted):
    return attachment

  return None


def get_attachment_url(attachment: Attachment) -> str:
  """Return the URL path that will serve this attachment."""
  if settings.DEV_MODE or settings.UNIT_TEST_MODE:
    origin = settings.SITE_URL
  else:
    digits = attachment.key.integer_id() % 1000
    origin = 'https://img%d-dot-%s.appspot.com/' % (digits, settings.APP_ID)

  uri = 'feature/%r/attachment/%r' % (
      attachment.feature_id, attachment.key.integer_id())
  url = origin + uri
  return url


def mark_attachment_deleted(attachment: Attachment) -> None:
  """Mark an attachment as deleted so that it will no longer be served."""
  attachment.is_deleted = True
  attachment.put()
