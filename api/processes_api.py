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
from internals import models
from internals import processes


class ProcessesAPI(basehandlers.APIHandler):
  """Processes contain details about the feature status"""

  def do_get(self, feature_id):
    """Return the process of the feature."""
    f = models.Feature.get_by_id(feature_id)
    feature_process = processes.ALL_PROCESSES.get(
      f.feature_type, processes.BLINK_LAUNCH_PROCESS)

    return processes.process_to_dict(feature_process)
