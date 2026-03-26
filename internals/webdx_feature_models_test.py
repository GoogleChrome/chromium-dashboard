# Copyright 2025 Google Inc.  # noqa: D100
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

import testing_config
from internals.webdx_feature_models import WebdxFeatures


class WebdxFeaturesTest(testing_config.CustomTestCase):  # noqa: D101
    def setUp(self):  # noqa: D102
        self.webdx = WebdxFeatures(feature_ids=['abc'])
        self.webdx.put()

    def test_get_webdx_feature_id_list(self):  # noqa: D102
        result = WebdxFeatures.get_webdx_feature_id_list()

        self.assertIsNotNone(result)
        self.assertEqual(len(result.feature_ids), 1)
        self.assertEqual(result.feature_ids[0], 'abc')

    def test_store_webdx_feature_id_list__success(self):  # noqa: D102
        WebdxFeatures.store_webdx_feature_id_list(['foo'])

        result = WebdxFeatures.query().fetch()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].feature_ids[0], 'foo')

    def test_store_webdx_feature_id_list__success_from_empty(self):  # noqa: D102
        self.webdx.key.delete()

        WebdxFeatures.store_webdx_feature_id_list(['foo'])

        result = WebdxFeatures.query().fetch()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].feature_ids[0], 'foo')
