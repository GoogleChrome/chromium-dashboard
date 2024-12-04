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
  """Store attachments such as screenshots."""

  @permissions.require_create_feature
  def do_post(self, **kwargs) -> dict[str, str]:
    """Handle POST requests to create a single attachment."""
    feature_id = kwargs.get('feature_id', None)

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
    url = attachments.get_attachment_url(attach)
    return AddAttachmentResponse.from_dict({'attachment_url': url}).to_dict()


class AttachmentServing(basehandlers.FlaskHandler):
  """Serve an attachment."""

  def maybe_redirect(self, attachment: attachments.Attachment, is_thumb: bool):
    """If needed, redirect to a safe domain."""
    logging.info('url is: %r ', self.request.url)
    attach_url = attachments.get_attachment_url(attachment)
    thumb_url = attach_url + '/thumbnail'
    logging.info('attach_url is: %r ', attach_url)

    if self.request.url in (attach_url, thumb_url):
      return None

    if is_thumb:
      return self.redirect(thumb_url)
    else:
      return self.redirect(attach_url)

  def get_template_data(self, **kwargs):
    """Serve the attachment data, or redirect to a cookieless domain."""
    feature_id = kwargs.get('feature_id')
    is_thumb = 'thumbnail' in kwargs
    attachment_id = kwargs.get('attachment_id')
    attachment = attachments.get_attachment(feature_id, attachment_id)
    if not attachment:
      self.abort(404, msg='Attachment not found')

    redirect_response = self.maybe_redirect(attachment, is_thumb)
    if redirect_response:
      return redirect_response

    headers = self.get_headers()
    if is_thumb:
      thumbnail = attachments.get_thumbnail(attachment_id)
      if thumbnail:
        headers['Content-Type'] = 'image/png'
        return thumbnail.thumb_content, headers

    headers['Content-Type'] = attachment.mime_type
    return attachment.content, headers
