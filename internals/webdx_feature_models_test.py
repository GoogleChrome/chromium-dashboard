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

"""Tests for the Webdx feature IDs NDB models."""

from webstatus_openapi import BaselineInfo
from webstatus_openapi import Feature as WSFeature

import testing_config
from internals.webdx_feature_models import WebdxFeatureInfo, WebdxFeatures


class WebdxFeaturesTest(testing_config.CustomTestCase):
    """Tests for the WebdxFeatures model."""

    def setUp(self):
        """Sets up test data for the WebdxFeatures model."""
        self.webdx = WebdxFeatures(
            feature_ids=['abc'],
            feature_infos=[
                WebdxFeatureInfo(feature_id='abc', status='limited')
            ],
        )
        self.webdx.put()

    def test_get_singleton(self):
        """Tests that get_singleton retrieves the singleton entity."""
        result = WebdxFeatures.get_singleton()

        self.assertIsNotNone(result)
        self.assertEqual(len(result.feature_ids), 1)
        self.assertEqual(result.feature_ids[0], 'abc')
        self.assertEqual(len(result.feature_infos), 1)
        self.assertEqual(result.feature_infos[0].feature_id, 'abc')
        self.assertEqual(result.feature_infos[0].status, 'limited')

    def test_get_singleton__empty(self):
        """Tests that get_singleton returns None when no singleton exists."""
        self.webdx.key.delete()

        result = WebdxFeatures.get_singleton()

        self.assertIsNone(result)

    def test_store_webdx_feature_infos__success(self):
        """Tests storing a new list of Webdx feature infos successfully."""
        ws_feature = WSFeature(
            feature_id='foo',
            name='Foo',
            baseline=BaselineInfo(status='widely'),
        )
        WebdxFeatures.store_webdx_feature_infos([ws_feature])

        result = WebdxFeatures.query().fetch()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].feature_ids, ['foo'])
        self.assertEqual(len(result[0].feature_infos), 1)
        self.assertEqual(result[0].feature_infos[0].feature_id, 'foo')
        self.assertEqual(result[0].feature_infos[0].status, 'widely')

    def test_store_webdx_feature_infos__success_from_empty(self):
        """Tests storing a new list when no feature infos exist."""
        self.webdx.key.delete()

        ws_feature = WSFeature(
            feature_id='foo',
            name='Foo',
            baseline=BaselineInfo(status='newly'),
        )
        WebdxFeatures.store_webdx_feature_infos([ws_feature])

        result = WebdxFeatures.query().fetch()
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].feature_ids, ['foo'])
        self.assertEqual(len(result[0].feature_infos), 1)
        self.assertEqual(result[0].feature_infos[0].feature_id, 'foo')
        self.assertEqual(result[0].feature_infos[0].status, 'newly')
