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

from framework import gcs_helpers


class GCSHelpersTests(testing_config.CustomTestCase):

  def tearDown(self):
    for blob in gcs_helpers.FakeGCS.query().fetch(None):
      blob.key.delete()

  def test_guess_content_type_from_filename(self):
    """We can guess mime type based on filename extension."""
    guess = gcs_helpers.guess_content_type_from_filename
    self.assertEqual(guess('screenshot.gif'), 'image/gif')
    self.assertEqual(guess('screenshot.jpg'), 'image/jpeg')
    self.assertEqual(guess('screenshot.jpeg'), 'image/jpeg')
    self.assertEqual(guess('screenshot.png'), 'image/png')
    self.assertEqual(guess('screenshot.webp'), 'image/webp')

    self.assertEqual(guess('screen.shot.webp'), 'image/webp')
    self.assertEqual(guess('.webp'), 'image/webp')
    self.assertEqual(guess('screen shot.webp'), 'image/webp')

    self.assertEqual(guess('screenshot.pdf'), 'application/octet-stream')
    self.assertEqual(guess('screenshot gif'), 'application/octet-stream')
    self.assertEqual(guess('screenshotgif'), 'application/octet-stream')
    self.assertEqual(guess('gif'), 'application/octet-stream')
    self.assertEqual(guess(''), 'application/octet-stream')

  def test_store_object_in_fake_gcs(self):
    """We can store content locally for developers."""
    gcs_helpers.store_object_in_fake_gcs(
        'default-screenshots', b'test content', 'text/plain', 'blob_name')
    q = gcs_helpers.FakeGCS.query(
        gcs_helpers.FakeGCS.bucket_and_blob == 'default-screenshots/blob_name')
    blob = q.get()
    self.assertEqual(blob.content, b'test content')
    self.assertEqual(blob.mime_type, 'text/plain')

  def test_check_attachment_size(self):
    """We can check the size of the attachment content."""
    gcs_helpers.check_attachment_size(b'small content')

    large_content = b'very large content ' * 1024 * 1024
    with self.assertRaises(gcs_helpers.AttachmentTooLarge):
      gcs_helpers.check_attachment_size(large_content)

  def test_check_attachment_type(self):
    """We can check the type of the attachment."""
    gcs_helpers.check_attachment_type('image/gif')
    gcs_helpers.check_attachment_type('image/jpeg')
    gcs_helpers.check_attachment_type('image/png')
    gcs_helpers.check_attachment_type('image/webp')

    with self.assertRaises(gcs_helpers.UnsupportedMimeType):
      gcs_helpers.check_attachment_type('application/octet-stream')

    with self.assertRaises(gcs_helpers.UnsupportedMimeType):
      gcs_helpers.check_attachment_type('video/mpeg')

  def test_get_content_from_fake_gcs(self):
    """We can retrive blobs when running locally."""
    gcs_helpers.store_object_in_fake_gcs(
        'default-screenshots', b'test content', 'text/plain', 'blob_name')
    content, mime_type = gcs_helpers.get_content_from_fake_gcs(
        'default-screenshots', 'blob_name')
    self.assertEqual(content, b'test content')
    self.assertEqual(mime_type, 'text/plain')

    content, mime_type = gcs_helpers.get_content_from_fake_gcs(
        'default-screenshots', 'no_such_blob')
    self.assertEqual(content, None)
    self.assertEqual(mime_type, None)
