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




import json
import logging

from framework import basehandlers
from pages import guideforms
from internals import core_models
from internals import processes


class FeatureDetailHandler(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'feature.html'

  def get_template_data(self, feature_id):
    f = core_models.Feature.get_by_id(feature_id)
    if f is None:
      self.abort(404, msg='Feature not found')

    if f.deleted:
      # TODO(jrobbins): Check permissions and offer option to undelete.
      self.abort(404, msg='Feature has been deleted')

    context_link = '/features'
    if self.request.args.get('context') == 'myfeatures':
      context_link = '/myfeatures'

    template_data = {
        'feature': f.format_for_template(),
        'feature_id': feature_id,
        'context_link': context_link,
    }
    return template_data
