# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
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


from framework import basehandlers
from internals import core_models
from internals import processes


class ProcessesAPI(basehandlers.APIHandler):
  """Processes contain details about the feature status"""

  def do_get(self, **kwargs):
    """Return the process of the feature."""
    # Load feature directly from NDB so as to never get a stale cached copy.
    feature_id = kwargs['feature_id']
    f = core_models.Feature.get_by_id(feature_id)
    if f is None:
      self.abort(404, msg=f'Feature {feature_id} not found')

    feature_process = processes.ALL_PROCESSES.get(
      f.feature_type, processes.BLINK_LAUNCH_PROCESS)

    return processes.process_to_dict(feature_process)


class ProgressAPI(basehandlers.APIHandler):
  """Progress is either a boolean value when the checkmark should be shown,
  or a string that starts with "http:" or "https:" that contain details about
  the progress of a feature so far"""

  def do_get(self, **kwargs):
    """Return the progress of the feature."""
    feature_id = kwargs['feature_id']
    f = core_models.Feature.get_by_id(feature_id)
    if f is None:
      self.abort(404, msg=f'Feature {feature_id} not found')

    progress_so_far = {}
    for progress_item, detector in list(processes.PROGRESS_DETECTORS.items()):
      detected = detector(f)
      if detected:
        progress_so_far[progress_item] = str(detected)
    return progress_so_far
