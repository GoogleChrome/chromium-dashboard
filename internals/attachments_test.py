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

import testing_config  # Must be imported before the module under test.

from unittest import mock

from internals import attachments


class AttachmentsTests(testing_config.CustomTestCase):

  def setUp(self):
    self.feature_id = 12345678

  def tearDown(self):
    for attach in attachments.Attachment.query().fetch(None):
      attach.key.delete()

  def test_store_attachment(self):
    """We can store attachment content."""
    actual = attachments.store_attachment(
        self.feature_id, b'test content', 'text/plain')
    attach_id = actual.key.integer_id()
    retrieved = attachments.Attachment.get_by_id(attach_id)
    self.assertEqual(retrieved.feature_id, self.feature_id)
    self.assertEqual(retrieved.content, b'test content')
    self.assertEqual(retrieved.mime_type, 'text/plain')

  def test_check_attachment_size(self):
    """We can check the size of the attachment content."""
    attachments.check_attachment_size(b'small content')

    large_content = b'very large content ' * 1024 * 1024
    with self.assertRaises(attachments.AttachmentTooLarge):
      attachments.check_attachment_size(large_content)

  def test_check_attachment_type(self):
    """We can check the type of the attachment."""
    attachments.check_attachment_type('image/gif')
    attachments.check_attachment_type('image/jpeg')
    attachments.check_attachment_type('image/png')
    attachments.check_attachment_type('image/webp')

    with self.assertRaises(attachments.UnsupportedMimeType):
      attachments.check_attachment_type('application/octet-stream')

    with self.assertRaises(attachments.UnsupportedMimeType):
      attachments.check_attachment_type('video/mpeg')

  def test_get_attachment__found(self):
    """We can retrive an attachment, with checking for the proper feature."""
    stored = attachments.store_attachment(
        self.feature_id, b'test content', 'text/plain')
    attach_id = stored.key.integer_id()

    actual = attachments.get_attachment(self.feature_id, attach_id)

    self.assertEqual(actual.feature_id, self.feature_id)
    self.assertEqual(actual.content, b'test content')
    self.assertEqual(actual.mime_type, 'text/plain')

  def test_get_attachment__not_found(self):
    """We return None when there is no such attachment."""
    # Nothing is stored
    actual = attachments.get_attachment(self.feature_id, 99999)
    self.assertEqual(actual, None)

  def test_get_attachment__reject_probing(self):
    """We return None when an attempt is made to find all attachments."""
    stored = attachments.store_attachment(
        self.feature_id, b'test content', 'text/plain')
    attach_id = stored.key.integer_id()

    # The attachment is not part of any other feature.
    actual = attachments.get_attachment(self.feature_id + 1, attach_id)

    self.assertEqual(actual, None)

  def test_get_attachment__deleted(self):
    """We return None when attempting to get a deleted attachment."""
    stored = attachments.store_attachment(
        self.feature_id, b'test content', 'text/plain')
    attachments.mark_attachment_deleted(stored)

    # The attachment was marked deleted.
    actual = attachments.get_attachment(
        self.feature_id + 1, stored.key.integer_id())

    self.assertEqual(actual, None)
