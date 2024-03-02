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

import logging

from flask import session

from framework import basehandlers


class LogoutAPI(basehandlers.APIHandler):
  """Clear the session when the user signs out."""

  def do_get(self, **kwargs):
    """Reject unneeded GET requests without triggering Error Reporting."""
    self.abort(405, valid_methods=['POST'])

  def do_post(self, **kwargs):
    session.clear()
    return {'message': 'Done'}
