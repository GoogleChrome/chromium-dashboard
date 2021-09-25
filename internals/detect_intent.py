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

from __future__ import division
from __future__ import print_function

import logging

import settings
from framework import basehandlers


class IntentEmailHandler(basehandlers.FlaskHandler):
  """This task handles an inbound email to detect intent threads."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self):
    self.require_task_header()

    from_addr = self.get_param('from_addr')
    subject = self.get_param('subject')
    in_reply_to = self.get_param('in_reply_to', required=False)
    body = self.get_param('body')

    logging.info('In IntentEmailHandler')
    logging.info('From addr:   %r', from_addr)
    logging.info('Subject:     %r', subject)
    logging.info('In reply to: %r', in_reply_to)
    logging.info('Body:        %r', body)

    # TODO(jrobbins): Write code to parse out:
    # 1. The type of intent.
    # 2. The feature ID number
    # 3. Any clear "LGTM"s
    # And retrieve model objects for the feature and the sending user.
    # Set the thread URL on the feature.
    # Set an LGTM if appropriate.

    return {'message': 'Done'}
