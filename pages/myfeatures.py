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

import json
import logging

import settings
from framework import basehandlers
from framework import permissions
from internals import models
from framework import ramcache


class MyFeaturesHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'myfeatures.html'

  def get_template_data(self):
    user_pref = models.UserPref.get_signed_in_user_pref()
    if not user_pref:
      return self.redirect(settings.LOGIN_PAGE_URL)

    template_data = {}
    return template_data
