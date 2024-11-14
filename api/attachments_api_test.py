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

import io
import flask
from datetime import datetime
from unittest import mock
from google.cloud import ndb  # type: ignore
import werkzeug.exceptions

import settings
from api import attachments_api
from internals.core_enums import *
from internals.core_models import FeatureEntry
from internals import attachments

test_app = flask.Flask(__name__)
test_app.secret_key ='test'


class AttachmentsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature = FeatureEntry(
        name='feat', summary='sum', category=1,
        owner_emails=['owner@chromium.org'],
        impl_status_chrome=ENABLED_BY_DEFAULT)
    self.feature.put()

    self.feature_id = self.feature.key.integer_id()
    self.request_path = f'/api/v0/features/{self.feature_id}/attachments'
    self.handler = attachments_api.AttachmentsAPI()
    self.content = b'hello attachments!'

  def tearDown(self):
    testing_config.sign_out()
    kinds: list[ndb.Model] = [FeatureEntry, attachments.Attachment]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_do_post__anon(self):
    """Anon users cannot add attachments."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(feature_id=self.feature_id)

  def test_do_post__unregistered(self):
    """Users who cannot create features cannot add attachments."""
    testing_config.sign_in('someone@example.com', 111)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(feature_id=self.feature_id)

  def test_do_post__noneditor(self):
    """Users who cannot edit this particular feature cannot add attachments."""
    testing_config.sign_in('someone@example.com', 111)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post(feature_id=self.feature_id)

  def test_do_post__no_files(self):
    """Reject requests that have no attachments."""
    testing_config.sign_in('owner@chromium.org', 111)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(feature_id=self.feature_id)

  def test_do_post__empty_file(self):
    """Reject requests where the user did not upload."""
    testing_config.sign_in('owner@chromium.org', 111)
    body = b''
    with test_app.test_request_context(self.request_path, data=body):
      with self.assertRaises(werkzeug.exceptions.BadRequest):
        self.handler.do_post(feature_id=self.feature_id)

  def test_do_post__valid_file(self):
    """With a valid user and valid request, we store the attachment."""
    testing_config.sign_in('owner@chromium.org', 111)
    mock_file = (io.BytesIO(self.content), 'hello_attach.txt')
    with test_app.test_request_context(
        self.request_path, data={'uploaded-file': mock_file}):
      actual = self.handler.do_post(feature_id=self.feature_id)

    attachment_id = int(actual['attachment_url'].split('/')[-1])
    attachment = attachments.Attachment.get_by_id(attachment_id)
    expected_url = attachments.get_attachment_url(attachment)
    self.assertEqual(actual['attachment_url'], expected_url)


class AttachmentServingTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature = FeatureEntry(
        name='feat', summary='sum', category=1,
        owner_emails=['owner@chromium.org'],
        impl_status_chrome=ENABLED_BY_DEFAULT)
    self.feature.put()
    self.feature_id = self.feature.key.integer_id()

    self.content = b'Are you being served?'
    self.attachment = attachments.Attachment(
        feature_id=self.feature_id,
        content=self.content,
        mime_type='text/plain')
    self.attachment.put()
    self.attachment_id = self.attachment.key.integer_id()

    self.request_path = (
        f'/feature/{self.feature_id}/attachment/{self.attachment_id}')
    self.handler = attachments_api.AttachmentServing()

  def tearDown(self):
    testing_config.sign_out()
    kinds: list[ndb.Model] = [FeatureEntry, attachments.Attachment]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_maybe_redirect__expected_url(self):
    """Requesting an attachment from the canonical URL returns None."""
    # self.request_path is the same as the canonical URL.
    base = settings.SITE_URL
    with test_app.test_request_context(self.request_path, base_url=base):
      actual = self.handler.maybe_redirect(self.attachment, False)
      self.assertIsNone(actual)

    with test_app.test_request_context(
        self.request_path + '/thumbnail', base_url=base):
      actual = self.handler.maybe_redirect(self.attachment, True)
      self.assertIsNone(actual)

  def test_maybe_redirect__alt_base(self):
    """Requesting an attachment from a different URL gives a redirect."""
    alt_base = 'https://chromestatus.com'
    with test_app.test_request_context(self.request_path, base_url=alt_base):
      actual = self.handler.maybe_redirect(self.attachment, False)
      self.assertEqual(actual.status_code, 302)
      self.assertEqual(
          actual.location, attachments.get_attachment_url(self.attachment))

  def test_get_template_data__not_found(self):
    """Requesting with a wrong ID gives a 404."""
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(
            feature_id=self.feature_id, attachment_id=self.attachment_id + 1)
      with self.assertRaises(werkzeug.exceptions.NotFound):
        self.handler.get_template_data(
            feature_id=self.feature_id + 1, attachment_id=self.attachment_id)

  def test_get_template_data__found(self):
    """We can fetch an attachment."""
    base = settings.SITE_URL
    with test_app.test_request_context(self.request_path, base_url=base):
      content, headers = self.handler.get_template_data(
          feature_id=self.feature_id, attachment_id=self.attachment_id)

    self.assertEqual(content, self.content)
    self.assertEqual(headers['Content-Type'], 'text/plain')


class RoundTripTest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature = FeatureEntry(
        name='feat', summary='sum', category=1,
        owner_emails=['owner@chromium.org'],
        impl_status_chrome=ENABLED_BY_DEFAULT)
    self.feature.put()
    self.feature_id = self.feature.key.integer_id()

    self.content = b'hello attachments!'
    self.api_request_path = f'/api/v0/features/{self.feature_id}/attachments'
    self.api_handler = attachments_api.AttachmentsAPI()
    self.serving_handler = attachments_api.AttachmentServing()

  def tearDown(self):
    testing_config.sign_out()
    kinds: list[ndb.Model] = [FeatureEntry, attachments.Attachment]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def testRoundTrip(self):
    """We can upload an attachment and then download it."""
    testing_config.sign_in('owner@chromium.org', 111)
    mock_file = (io.BytesIO(self.content), 'hello_attach.txt')
    with test_app.test_request_context(
        self.api_request_path, data={'uploaded-file': mock_file}):
      actual = self.api_handler.do_post(feature_id=self.feature_id)

    actual_url = actual['attachment_url']
    base = settings.SITE_URL
    feature_id = int(actual_url.split('/')[-3])
    attachment_id = int(actual_url.split('/')[-1])
    with test_app.test_request_context(actual_url, base_url=base):
      content, headers = self.serving_handler.get_template_data(
          feature_id=feature_id, attachment_id=attachment_id)

    self.assertEqual(content, self.content)
    self.assertEqual(headers['Content-Type'], 'text/plain')
