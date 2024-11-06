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

import flask
from datetime import datetime
from unittest import mock
from google.cloud import ndb  # type: ignore
import werkzeug.exceptions

from api import attachments_api
from internals.core_enums import *
from internals.core_models import FeatureEntry
from internals.attachments import Attachment

test_app = flask.Flask(__name__)

class AttachmentsAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.feature = FeatureEntry(
        name='feat', summary='sum', category=1,
        impl_status_chrome=ENABLED_BY_DEFAULT)
    self.feature.put()

    self.feature_id = self.feature.key.integer_id()
    self.request_path = f'/api/v0/features/{self.feature_id}/attachments'
    self.handler = attachments_api.AttachmentsAPI()

  def tearDown(self):
    testing_config.sign_out()
    kinds: list[ndb.Model] = [FeatureEntry, Attachment]
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()

  def test_do_post__anon(self):
    """Anon users cannot add attachments."""
    testing_config.sign_out()
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

  def test_do_post__unregistered(self):
    """Users who cannot create features cannot add attachments."""
    testing_config.sign_in('someone@example.com', 111)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()

  def test_do_post__noneditor(self):
    """Users who cannot edit this particular feature cannot add attachments."""
    testing_config.sign_in('someone@example.com', 111)
    with test_app.test_request_context(self.request_path):
      with self.assertRaises(werkzeug.exceptions.Forbidden):
        self.handler.do_post()
