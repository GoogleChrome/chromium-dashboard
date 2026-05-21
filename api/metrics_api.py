# Copyright 2026 Google Inc.
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


"""Provides handlers for metrics data, such as Omaha release data."""

from framework import basehandlers
from internals import fetchchannels


class OmahaDataHandler(basehandlers.EntitiesAPIHandler):
    """Handler for retrieving Omaha data metrics."""

    def do_get(self, **kwargs):
        """Returns Omaha data metrics as JSON."""
        omaha_data = fetchchannels.get_omaha_data()
        return omaha_data
