# Copyright 2025 Google Inc.
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
from collections import OrderedDict

from framework import basehandlers
from internals.metrics_models import WebDXFeatureObserver


class WebdxFeatureAPI(basehandlers.APIHandler):
  """The list of ordered webdx feature ID populates the "Web Feature ID" select field
  in the guide form"""

  def do_get(self, **kwargs):
    """Returns an ordered dict with the following structure,
    {Webdx feature name: [Webdx feature name, usecounter enum], ...}"""
    webdx_features_mapping = sorted(
      WebDXFeatureObserver.get_all().items(), key=lambda item: item
    )
    if len(webdx_features_mapping) == 0:
      logging.error('Webdx feature mapping is empty.')
      return {}

    web_features_dict = OrderedDict()
    # The first key, value pair is the id when features are missing from the list.
    web_features_dict[WebDXFeatureObserver.MISSING_FEATURE_ID] = [
      WebDXFeatureObserver.MISSING_FEATURE_ID,
      WebDXFeatureObserver.MISSING_FEATURE_ID,
    ]
    web_features_dict[WebDXFeatureObserver.TBD_FEATURE_ID] = [
      WebDXFeatureObserver.TBD_FEATURE_ID,
      WebDXFeatureObserver.TBD_FEATURE_ID,
    ]

    for entry in webdx_features_mapping:
      web_features_dict[entry[1]] = [entry[1], str(entry[0])]

    return web_features_dict
