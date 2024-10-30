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

from chromestatus_openapi.models import AddAttachmentResponse

from framework import basehandlers
from framework import permissions
from internals import attachments


class AttachmentsAPI(basehandlers.EntitiesAPIHandler):
  """Features are the the main records that we track."""

  @permissions.require_create_feature
  def do_post(self, **kwargs) -> dict[str, str]:
    """Handle POST requests to create a single feature."""
    feature_id = kwargs.get('feature_id', None)
    logging.info('Got an attachments POST on %r', feature_id)

    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      self.abort(403, msg='User lacks permission to edit')

    logging.info('files are %r', self.request.files)
    if 'uploaded-file' not in self.request.files:
      self.abort(400, msg='Unexpected file upload')

    file = self.request.files['uploaded-file']
    if file.filename == '':
      self.abort(400, msg='No file was selected')
    content = file.read()

    attach = attachments.store_attachment(feature_id, content, file.mimetype)
    uri = attachments.get_attachment_uri(attach)
    return AddAttachmentResponse.from_dict({'attachment_uri': uri}).to_dict()


class AttachmentServing(basehandlers.FlaskHandler):
  """Serve an attachment."""

  def maybe_redirect(self):
    """If needed, redirect to a safe domain."""
    return None

  def get_template_data(self, **kwargs):
    """Serve the attachment data, or redirect to a cookieless domain."""
    feature_id = kwargs.get('feature_id')
    attachment_id = kwargs.get('attachment_id')
    redirect_response = self.maybe_redirect()
    if redirect_response:
      return redirect_response

    logging.info('host is: %r ', self.request.host)

    content = 'this is an image'
    headers = self.get_headers()
    headers['Content-Type'] = 'text/plain'

    return content, headers
