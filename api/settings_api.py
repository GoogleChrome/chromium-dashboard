# -*- coding: utf-8 -*-
# Copyright 2022 Google Inc.
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
"""API endpoints for managing user preferences and settings."""

import werkzeug.exceptions
from chromestatus_openapi.models import (
    GetSettingsResponse,
    PostSettingsRequest,
    SuccessMessage,
)

from framework import basehandlers
from internals import user_models


class SettingsAPI(basehandlers.APIHandler):
    """Users can store their settings preferences such as whether to get
    notification from the features they starred.
    """  # noqa: D205

    def do_post(self, **kwargs):
        """Set the user settings."""  # noqa: D415
        user_pref = user_models.UserPref.get_signed_in_user_pref()
        if not user_pref:
            self.abort(403, msg='User must be signed in')
        raw_data = self.request.json

        has_notify = 'notify' in raw_data
        has_done_ids = 'editable_done_feature_ids' in raw_data
        if not has_notify and not has_done_ids:
            raise werkzeug.exceptions.BadRequest(
                "Expected 'notify' or 'editable_done_feature_ids'"
            )

        if has_notify:
            new_notify = raw_data.get('notify')
            if not isinstance(new_notify, bool):
                raise werkzeug.exceptions.BadRequest(
                    f"Expected boolean for 'notify', got {type(new_notify).__name__}"
                )
            settings_request = PostSettingsRequest.from_dict({'notify': new_notify})
            user_pref.notify_as_starrer = settings_request.notify

        if has_done_ids:
            done_ids = raw_data.get('editable_done_feature_ids')
            if not isinstance(done_ids, list) or not all(
                isinstance(x, int) and x > 0 for x in done_ids
            ):
                raise werkzeug.exceptions.BadRequest(
                    "Expected 'editable_done_feature_ids' to be a list of positive integers"
                )
            user_pref.editable_done_feature_ids = done_ids

        user_pref.put()
        # Callers don't use the JSON response for this API call.
        return SuccessMessage(message='Done').to_dict()

    def do_get(self, **kwargs):
        """Return the user settings."""  # noqa: D415
        user_pref = user_models.UserPref.get_signed_in_user_pref()
        if not user_pref:
            self.abort(404, msg='User preference not found')

        response = GetSettingsResponse.from_dict(
            {'notify_as_starrer': user_pref.notify_as_starrer}
        )
        response_dict = response.to_dict()
        response_dict['editable_done_feature_ids'] = (
            user_pref.editable_done_feature_ids or []
        )

        return response_dict
