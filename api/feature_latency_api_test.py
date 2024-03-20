# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testing_config  # isort: split

from datetime import datetime

from api import feature_latency_api
from internals.core_models import FeatureEntry


class FeatureLatencyAPITest(testing_config.CustomTestCase):

  def setUp(self):
    self.handler = feature_latency_api.FeatureLatencyAPI()

  def test_get_date_range__unspecified(self):
    """If query string params were not set, it returns None, None."""
    actual = self.handler.get_date_range({})
    self.assertEqual((None, None), actual)

  def test_get_date_range__specified(self):
    """It parses dates from query-string params."""
    actual = self.handler.get_date_range({
        'startDate': '2023-01-15',
        'endDate': '2023-12-24'})
    self.assertEqual(
        (datetime(2023, 1, 15),
         datetime(2023, 12, 24)),
        actual)
