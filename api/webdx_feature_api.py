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
from internals.metrics_models import WebDXFeatureObserver


class WebFeatureIDsAPI(basehandlers.APIHandler):
  """The web feature IDs that populates a datalist menu for web_feature."""

  def do_get(self, **kwargs):
    """Returns a sorted list of WebDX feature IDs."""
    singleton: WebdxFeatures | None = WebdxFeatures.get_webdx_feature_id_list()
    web_feature_ids = sorted(singleton.feature_ids if singleton else [])
    return web_feature_ids


# TODO(jrobbins): Move the ot_webfeature_use_counter form field a shipping
# stage and change have it use datalist populated by this API.
class WebdxFeatureAPI(basehandlers.APIHandler):
  """The webdx feature UseCounter enums that populates a datalist menu."""

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
