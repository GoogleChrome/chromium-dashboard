# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc.
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

__author__ = 'ericbidelman@chromium.org (Eric Bidelman)'


import json
import logging

from api import accounts_api
from framework import basehandlers
from framework import permissions
from internals import user_models


class UserListHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'admin/users/new.html'

  @permissions.require_admin_site
  def get_template_data(self):
    users = user_models.AppUser.query().fetch(None)
    user_list = [accounts_api.user_to_json_dict(user) for user in users]

    logging.info('user_list is %r', user_list)
    template_data = {
      'users': json.dumps(user_list)
    }
    return template_data
