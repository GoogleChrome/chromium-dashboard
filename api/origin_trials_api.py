# Copyright 2023 Google Inc.
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
from framework import origin_trials_client


class OriginTrialsAPI(basehandlers.APIHandler):

  def do_get(self, **kwargs):
    """Get a list of all origin trials."""
    trials_list, err = origin_trials_client.get_trials_list()
    if err is not None:
      status_code, error_message = err
      self.abort(status_code, error_message)

    return trials_list
