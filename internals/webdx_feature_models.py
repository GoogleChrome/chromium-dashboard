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

from google.cloud import ndb  # type: ignore


class WebdxFeatures(ndb.Model):
  """A singleton model to store Webdx feature IDs"""
  feature_ids = ndb.StringProperty(repeated=True)

  @classmethod
  def get_webdx_feature_id_list(cls):
    fetch_results = cls.query().fetch(1)
    if not fetch_results:
      return None

    return fetch_results[0]

  @classmethod
  def store_webdx_feature_id_list(cls, new_list: list[str]):
    webdx_features = WebdxFeatures.get_webdx_feature_id_list()
    if not webdx_features:
      webdx_features = WebdxFeatures(feature_ids=new_list)
    else:
      webdx_features.feature_ids = new_list
    webdx_features.put()
