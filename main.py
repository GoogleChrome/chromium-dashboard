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

from flask import Flask
import logging

from api import accounts_api
from api import approvals_api
from api import channels_api
from api import comments_api
from api import cues_api
from api import features_api
from api import login_api
from api import logout_api
from api import metricsdata
from api import stars_api
from api import token_refresh_api
from framework import basehandlers
from framework import csp
from internals import detect_intent
from internals import fetchmetrics
from internals import notifier
from pages import blink_handler
from pages import featuredetail
from pages import featurelist
from pages import guide
from pages import intentpreview
from pages import metrics
from pages import myfeatures
from pages import roadmap
from pages import samples
from pages import schedule
from pages import users
import settings

# Sets up Cloud Logging client library.
if not settings.UNIT_TEST_MODE and not settings.DEV_MODE:
  import google.cloud.logging
  client = google.cloud.logging.Client()
  client.get_default_handler()
  client.setup_logging()

# Sets up Cloud Debugger client library.
if not settings.UNIT_TEST_MODE and not settings.DEV_MODE:
  try:
    import googleclouddebugger
    googleclouddebugger.enable(breakpoint_enable_canary=False)
  except ImportError:
    pass


# Note: In the URLs below, parameters like <int:feature_id> are
# required for the URL to match the route, but we still accecpt
# those parameters as keywords in those handlers where the same
# handler might be used for multiple routes that have the field
# or not.


metrics_chart_routes = [
    ('/data/timeline/cssanimated', metricsdata.AnimatedTimelineHandler),
    ('/data/timeline/csspopularity', metricsdata.PopularityTimelineHandler),
    ('/data/timeline/featurepopularity',
     metricsdata.FeatureObserverTimelineHandler),
    ('/data/csspopularity', metricsdata.CSSPopularityHandler),
    ('/data/cssanimated', metricsdata.CSSAnimatedHandler),
    ('/data/featurepopularity', metricsdata.FeatureObserverPopularityHandler),
    ('/data/blink/<string:prop_type>', metricsdata.FeatureBucketsHandler),
]

# TODO(jrobbins): Advance this to v1 once we have it fleshed out
API_BASE = '/api/v0'
api_routes = [
    (API_BASE + '/features', features_api.FeaturesAPI),
    (API_BASE + '/features/<int:feature_id>', features_api.FeaturesAPI),
    (API_BASE + '/features/<int:feature_id>/approvals',
     approvals_api.ApprovalsAPI),
    (API_BASE + '/features/<int:feature_id>/approvals/<int:field_id>',
     approvals_api.ApprovalsAPI),
    (API_BASE + '/features/<int:feature_id>/configs',
     approvals_api.ApprovalConfigsAPI),
    (API_BASE + '/features/<int:feature_id>/approvals/comments',
     comments_api.CommentsAPI),
    (API_BASE + '/features/<int:feature_id>/approvals/<int:field_id>/comments',
     comments_api.CommentsAPI),

    (API_BASE + '/login', login_api.LoginAPI),
    (API_BASE + '/logout', logout_api.LogoutAPI),
    (API_BASE + '/currentuser/stars', stars_api.StarsAPI),
    (API_BASE + '/currentuser/cues', cues_api.CuesAPI),
    (API_BASE + '/currentuser/token', token_refresh_api.TokenRefreshAPI),
    # (API_BASE + '/currentuser/autosaves', TODO),
    # (API_BASE + '/currentuser/settings', TODO),

    # Admin operations for user accounts
    (API_BASE + '/accounts', accounts_api.AccountsAPI),
    (API_BASE + '/accounts/<int:account_id>', accounts_api.AccountsAPI),

    (API_BASE + '/channels', channels_api.ChannelsAPI),  # omaha data
    # (API_BASE + '/schedule', TODO),  # chromiumdash data
    # (API_BASE + '/metrics/<str:kind>', TODO),  # uma-export data
    # (API_BASE + '/metrics/<str:kind>/<int:bucket_id>', TODO),
]


page_routes = [
    ('/admin/subscribers', blink_handler.SubscribersHandler),
    ('/admin/blink', blink_handler.BlinkHandler),

    ('/feature/<int:feature_id>', featuredetail.FeatureDetailHandler),

    # Note: The only requests being made now hit /features.json and
    # /features_v2.json, but both of those cause version == 2.
    # There was logic to accept another version value, but it it was not used.
    (r'/features.json', featurelist.FeaturesJsonHandler),
    (r'/features_v2.json', featurelist.FeaturesJsonHandler),

    ('/', basehandlers.Redirector,
     {'location': '/features'}),

    ('/features', featurelist.FeatureListHandler),
    ('/features/<int:feature_id>', featurelist.FeatureListHandler),
    ('/features.xml', featurelist.FeatureListXMLHandler),

    ('/guide/new', guide.FeatureNew),
    ('/guide/edit/<int:feature_id>', guide.ProcessOverview),
    ('/guide/stage/<int:feature_id>/<int:stage_id>', guide.FeatureEditStage),
    ('/guide/editall/<int:feature_id>', guide.FeatureEditAllFields),

    ('/admin/features/launch/<int:feature_id>',
     intentpreview.IntentEmailPreviewHandler),
    ('/admin/features/launch/<int:feature_id>/<int:stage_id>',
     intentpreview.IntentEmailPreviewHandler),

    ('/metrics', basehandlers.Redirector,
     {'location': '/metrics/css/popularity'}),
    ('/metrics/css', basehandlers.Redirector,
     {'location': '/metrics/css/popularity'}),

    # TODO(jrobbins): These seem like they belong in metrics.py.
    ('/metrics/css/popularity', basehandlers.ConstHandler,
     {'template_path': 'metrics/css/popularity.html'}),
    ('/metrics/css/animated', basehandlers.ConstHandler,
     {'template_path': 'metrics/css/animated.html'}),
    ('/metrics/css/timeline/popularity', metrics.CssPopularityHandler),
    ('/metrics/css/timeline/popularity/<int:bucket_id>',
     metrics.CssPopularityHandler),
    ('/metrics/css/timeline/animated', metrics.CssAnimatedHandler),
    ('/metrics/css/timeline/animated/<int:bucket_id>',
     metrics.CssAnimatedHandler),
    ('/metrics/feature/popularity', basehandlers.ConstHandler,
     {'template_path': 'metrics/feature/popularity.html'}),
    ('/metrics/feature/timeline/popularity', metrics.FeaturePopularityHandler),
    ('/metrics/feature/timeline/popularity/<int:bucket_id>',
     metrics.FeaturePopularityHandler),
    ('/omaha_data', metrics.OmahaDataHandler),

    ('/myfeatures', myfeatures.MyFeaturesHandler),

    ('/roadmap', roadmap.RoadmapHandler),

    ('/samples', samples.SamplesHandler),
    ('/samples.json', samples.SamplesJSONHandler),
    ('/samples.xml', samples.SamplesXMLHandler),

    ('/features/schedule', schedule.ScheduleHandler),

    ('/settings', users.SettingsHandler),
    ('/admin/users/new', users.UserListHandler),
]


internals_routes = [
  ('/cron/metrics', fetchmetrics.YesterdayHandler),
  ('/cron/histograms', fetchmetrics.HistogramsHandler),
  ('/cron/update_blink_components', fetchmetrics.BlinkComponentHandler),

  ('/tasks/email-subscribers', notifier.FeatureChangeHandler),

  ('/tasks/detect-intent', detect_intent.IntentEmailHandler),
]


# All requests to the app-py3 GAE service are handled by this Flask app.
app = basehandlers.FlaskApplication(
    __name__,
    (metrics_chart_routes + api_routes + page_routes +
     internals_routes))

# TODO(jrobbins): Make the CSP handler be a class like our others.
app.add_url_rule(
    '/csp', view_func=csp.report_handler,
     methods=['POST'])


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080)
