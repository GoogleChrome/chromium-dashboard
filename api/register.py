# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc.
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

from __future__ import division
from __future__ import print_function

import settings
from api import accounts_api
from api import approvals_api
from api import cues_api
from api import features_api
from api import stars_api
from api import token_refresh_api
from framework import basehandlers

from api import login_api
from api import logout_api


# TODO(jrobbins): Advance this to v1 once we have it fleshed out
API_BASE = '/api/v0'

app = basehandlers.FlaskApplication([
    ('/features', features_api.FeaturesAPI),
    ('/features/<int:feature_id>', features_api.FeaturesAPI),
    ('/features/<int:feature_id>/approvals/<int:field_id>',
     approvals_api.ApprovalsAPI),
    # ('/features/<int:feature_id>/approvals/<int:field_id>/comments', TODO),

    ('/login', login_api.LoginAPI),
    ('/logout', logout_api.LogoutAPI),
    ('/currentuser/stars', stars_api.StarsAPI),
    ('/currentuser/cues', cues_api.CuesAPI),
    ('/currentuser/token', token_refresh_api.TokenRefreshAPI),
    # ('/currentuser/autosaves', TODO),
    # ('/currentuser/settings', TODO),

    # Admin operations for user accounts
    ('/accounts', accounts_api.AccountsAPI),
    ('/accounts/<int:account_id>', accounts_api.AccountsAPI),

    # ('/channels', TODO),  # omaha data
    # ('/schedule', TODO),  # chromiumdash data
    # ('/metrics/<str:kind>', TODO),  # uma-export data
    # ('/metrics/<str:kind>/<int:bucket_id>', TODO),

    ],
    pattern_base=API_BASE,
    debug=settings.DEBUG)
