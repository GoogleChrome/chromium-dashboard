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




# from google.appengine.api import users
from framework import users

from internals import models
from framework import basehandlers
from framework import permissions
from internals import processes

INTENT_PARAM = 'intent'
LAUNCH_PARAM = 'launch'
VIEW_FEATURE_URL = '/feature'


class IntentEmailPreviewHandler(basehandlers.FlaskHandler):
  """Show a preview of an intent email, as appropriate to the feature stage."""

  TEMPLATE_PATH = 'admin/features/launch.html'

  @permissions.require_edit_feature
  def get_template_data(self, feature_id=None, stage_id=None):

    f = self.get_specified_feature(feature_id=feature_id)
    intent_stage = stage_id if stage_id is not None else f.intent_stage

    page_data = self.get_page_data(feature_id, f, intent_stage)
    return page_data

  def get_page_data(self, feature_id, f, intent_stage):
    """Return a dictionary of data used to render the page."""
    page_data = {
        'subject_prefix': self.compute_subject_prefix(f, intent_stage),
        'feature': f.format_for_template(),
        'sections_to_show': processes.INTENT_EMAIL_SECTIONS.get(
            intent_stage, []),
        'intent_stage': intent_stage,
        'default_url': '%s://%s%s/%s' % (
            self.request.scheme, self.request.host,
            VIEW_FEATURE_URL, feature_id),
    }

    if LAUNCH_PARAM in self.request.args:
      page_data[LAUNCH_PARAM] = True
    if INTENT_PARAM in self.request.args:
      page_data[INTENT_PARAM] = True

    return page_data

  def compute_subject_prefix(self, feature, intent_stage):
    """Return part of the subject line for an intent email."""

    if intent_stage == models.INTENT_INCUBATE:
      if feature.feature_type == models.FEATURE_TYPE_DEPRECATION_ID:
        return 'Intent to Deprecate and Remove'
    elif intent_stage == models.INTENT_IMPLEMENT:
      return 'Intent to Prototype'
    elif intent_stage == models.INTENT_EXPERIMENT:
      return 'Ready for Trial'
    elif intent_stage == models.INTENT_EXTEND_TRIAL:
      if feature.feature_type == models.FEATURE_TYPE_DEPRECATION_ID:
        return 'Request for Deprecation Trial'
      else:
        return 'Intent to Experiment'
    elif intent_stage == models.INTENT_SHIP:
      return 'Intent to Ship'
    elif intent_stage == models.INTENT_REMOVED:
      return 'Intent to Extend Deprecation Trial'

    return 'Intent stage "%s"' % models.INTENT_STAGES[intent_stage]
