# -*- coding: utf-8 -*-
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

"""API endpoints for managing per-user done state on features."""

from chromestatus_openapi.models import SuccessMessage

from framework import basehandlers
from internals.user_models import DoneFeature


class DoneFeaturesAPI(basehandlers.APIHandler):
    """Users can mark a feature as done by clicking an icon. The done
    state is per-user and used to filter the "Features I can edit" list.
    """  # noqa: D205

    def do_get(self, **kwargs):
        """Return a list of all done feature IDs for the signed-in user."""
        user = self.get_current_user()
        if user:
            feature_ids = DoneFeature.get_user_done_ids(user.email())
        else:
            feature_ids = []
        return {'feature_ids': feature_ids}

    def do_post(self, **kwargs):
        """Set or clear done on the specified feature."""
        feature_id = self.get_int_param('featureId', required=True)
        done = self.get_bool_param('done', default=True)
        user = self.get_current_user(required=True)
        DoneFeature.set_done(user.email(), feature_id, done)
        return SuccessMessage(message='Done')
