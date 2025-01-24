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
from internals.webdx_feature_models import WebdxFeatures

MISSING_FEATURE_ID = 'N/A'
TBD_FEATURE_ID = 'TBD'


class WebdxFeatureAPI(basehandlers.APIHandler):
  """The list of ordered webdx feature ID populates the "Web Feature ID" select field
  in the guide form"""

  def do_get(self, **kwargs):
    """Returns an ordered dict with Webdx feature id as both keys and values."""
    webdx_features = WebdxFeatures.get_webdx_feature_id_list()
    if not webdx_features:
        logging.error('Webdx feature id list is empty.')
        return {}

    feature_ids_dict = OrderedDict()
    # The first key, value pair is the id when features are missing from the list.
    feature_ids_dict[MISSING_FEATURE_ID] = [MISSING_FEATURE_ID, MISSING_FEATURE_ID]
    feature_ids_dict[TBD_FEATURE_ID] = [TBD_FEATURE_ID, TBD_FEATURE_ID]

    feature_list = webdx_features.feature_ids
    feature_list.sort()
    for id in feature_list:
      feature_ids_dict[id] = [id, id]

    return feature_ids_dict
