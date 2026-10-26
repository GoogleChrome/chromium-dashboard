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

"""Defines NDB models for storing and retrieving Webdx feature IDs."""

from google.cloud import ndb  # type: ignore
from webstatus_openapi import Feature as WSFeature


class WebdxFeatureInfo(ndb.Model):
    """A sub-model to store info on one web-feature."""

    feature_id = ndb.StringProperty(required=True)
    status = ndb.StringProperty(required=True)


class WebdxFeatures(ndb.Model):
    """A singleton model to store Webdx feature infos"""  # noqa: D415

    # TODO(jrobbins): Remove feature_ids after prod users all use feature_infos.
    feature_ids = ndb.StringProperty(repeated=True)
    feature_infos = ndb.StructuredProperty(WebdxFeatureInfo, repeated=True)

    @classmethod
    def get_singleton(cls):
        """Retrieves the singleton entity that has all Webdx feature info."""
        fetch_results = cls.query().fetch(1)
        if not fetch_results:
            return None

        return fetch_results[0]

    @classmethod
    def store_webdx_feature_infos(cls, new_list: list[WSFeature]):
        """Stores a new list of Webdx feature IDs, updating or creating as needed."""
        id_list = [wsf.feature_id for wsf in new_list]
        infos_list = [
            WebdxFeatureInfo(
                feature_id=wsf.feature_id,
                status=wsf.baseline.status if wsf.baseline else 'none',
            )
            for wsf in new_list
        ]
        singleton = WebdxFeatures.get_singleton()
        if not singleton:
            singleton = WebdxFeatures(
                feature_ids=id_list, feature_infos=infos_list
            )
        else:
            singleton.feature_ids = id_list
            singleton.feature_infos = infos_list
        singleton.put()
