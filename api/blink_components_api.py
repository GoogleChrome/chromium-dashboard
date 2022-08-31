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
from internals import user_models


class BlinkComponentsAPI(basehandlers.APIHandler):
  """The list of blink components populates the "Blink component" select field
  in the guide form"""

  def do_get(self):
    """Returns a dict with blink components as both keys and values."""
    return {x: [x, x] for x in user_models.BlinkComponent.fetch_all_components()}
