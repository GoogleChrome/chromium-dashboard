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

from framework import basehandlers
from pages import guideforms
from internals import models
from internals import processes


class FeatureDetailHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'feature.html'

  def get_template_data(self, feature_id):
    f = models.Feature.get_by_id(feature_id)
    if f is None:
      self.abort(404, msg='Feature not found')

    if f.deleted:
      # TODO(jrobbins): Check permissions and offer option to undelete.
      self.abort(404, msg='Feature has been deleted')

    feature_process = processes.ALL_PROCESSES.get(
        f.feature_type, processes.BLINK_LAUNCH_PROCESS)
    field_defs = guideforms.DISPLAY_FIELDS_IN_STAGES
    template_data = {
        'process_json': json.dumps(processes.process_to_dict(feature_process)),
        'field_defs_json': json.dumps(field_defs),
        'feature': f.format_for_template(),
        'feature_id': f.key.integer_id(),
        'feature_json': json.dumps(f.format_for_template()),
        'updated_display': f.updated.strftime("%Y-%m-%d"),
        'new_crbug_url': f.new_crbug_url(),
    }
    return template_data
