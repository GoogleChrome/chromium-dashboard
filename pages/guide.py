# -*- coding: utf-8 -*-
# Copyright 2020 Google Inc.
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

from datetime import datetime
import logging
from google.cloud import ndb

# Appengine imports.
from framework import ramcache

from framework import basehandlers
from framework import permissions
from internals import core_enums
from internals import core_models
from internals import processes
import settings


class FeatureCreateHandler(basehandlers.FlaskHandler):

  @permissions.require_create_feature
  def process_post_data(self):
    owners = self.split_emails('owner')
    editors = self.split_emails('editors')

    blink_components = (
        self.split_input('blink_components', delim=',') or
        [settings.DEFAULT_COMPONENT])

    # TODO(jrobbins): Validate input, even though it is done on client.

    feature_type = int(self.form.get('feature_type', 0))
    signed_in_user = ndb.User(
        email=self.get_current_user().email(),
        _auth_domain='gmail.com')
    feature = core_models.Feature(
        category=int(self.form.get('category')),
        name=self.form.get('name'),
        feature_type=feature_type,
        intent_stage=core_enums.INTENT_NONE,
        summary=self.form.get('summary'),
        owner=owners,
        editors=editors,
        creator=signed_in_user.email(),
        accurate_as_of=datetime.now(),
        impl_status_chrome=core_enums.NO_ACTIVE_DEV,
        standardization=core_enums.EDITORS_DRAFT,
        unlisted=self.form.get('unlisted') == 'on',
        web_dev_views=core_enums.DEV_NO_SIGNALS,
        blink_components=blink_components,
        tag_review_status=processes.initial_tag_review_status(feature_type),
        created_by=signed_in_user,
        updated_by=signed_in_user)
    key = feature.put()

    # TODO(jrobbins): enumerate and remove only the relevant keys.
    ramcache.flush_all()

    redirect_url = '/guide/edit/' + str(key.integer_id())
    return self.redirect(redirect_url)


class FeatureEditHandler(basehandlers.FlaskHandler):

  def touched(self, param_name):
    """Return True if the user edited the specified field."""
    # TODO(jrobbins): for now we just consider everything on the current form
    # to have been touched.  Later we will add javascript to populate a
    # hidden form field named "touched" that lists the names of all fields
    # actually touched by the user.

    # For now, checkboxes are always considered "touched", if they are
    # present on the form.
    checkboxes = ['accurate_as_of', 'unlisted', 'api_spec',
      'all_platforms', 'wpt', 'requires_embedder_support', 'prefixed']
    if param_name in checkboxes:
      form_fields_str = self.form.get('form_fields')
      if form_fields_str:
        form_fields = [field_name.strip()
                       for field_name in form_fields_str.split(',')]
        return param_name in form_fields
      else:
        return True

    # For now, selects are considered "touched", if they are
    # present on the form and are not empty strings.
    selects = ['category', 'feature_type', 'intent_stage',
      'standard_maturity', 'security_review_status',
      'privacy_review_status', 'tag_review_status',
      'safari_views', 'ff_views', 'web_dev_views',
      'blink_components', 'impl_status_chrome']
    if param_name in selects:
      return self.form.get(param_name)

    # See TODO at top of this method.
    return param_name in self.form

  def process_post_data(self, feature_id, stage_id=0):
    # Validate the user has edit permissions and redirect if needed.
    redirect_resp = permissions.validate_feature_edit_permission(
        self, feature_id)
    if redirect_resp:
      return redirect_resp

    if feature_id:
      # Load feature directly from NDB so as to never get a stale cached copy.
      feature = core_models.Feature.get_by_id(feature_id)
      if feature is None:
        self.abort(404, msg='Feature not found')
      else:
        feature.stash_values()

    logging.info('POST is %r', self.form)

    if self.touched('spec_link'):
      feature.spec_link = self.parse_link('spec_link')

    if self.touched('standard_maturity'):
      feature.standard_maturity = self.parse_int('standard_maturity')

    if self.touched('api_spec'):
      feature.api_spec = self.form.get('api_spec') == 'on'

    if self.touched('spec_mentors'):
      feature.spec_mentors = self.split_emails('spec_mentors')

    if self.touched('security_review_status'):
      feature.security_review_status = self.parse_int('security_review_status')

    if self.touched('privacy_review_status'):
      feature.privacy_review_status = self.parse_int('privacy_review_status')

    if self.touched('initial_public_proposal_url'):
      feature.initial_public_proposal_url = self.parse_link(
          'initial_public_proposal_url')

    if self.touched('explainer_links'):
      feature.explainer_links = self.parse_links('explainer_links')

    if self.touched('bug_url'):
      feature.bug_url = self.parse_link('bug_url')
    if self.touched('launch_bug_url'):
      feature.launch_bug_url = self.parse_link('launch_bug_url')

    if self.touched('intent_to_implement_url'):
      feature.intent_to_implement_url = self.parse_link(
          'intent_to_implement_url')

    if self.touched('intent_to_ship_url'):
      feature.intent_to_ship_url = self.parse_link(
          'intent_to_ship_url')

    if self.touched('ready_for_trial_url'):
      feature.ready_for_trial_url = self.parse_link(
          'ready_for_trial_url')

    if self.touched('intent_to_experiment_url'):
      feature.intent_to_experiment_url = self.parse_link(
          'intent_to_experiment_url')

    if self.touched('intent_to_extend_experiment_url'):
      feature.intent_to_extend_experiment_url = self.parse_link(
          'intent_to_extend_experiment_url')

    if self.touched('origin_trial_feedback_url'):
      feature.origin_trial_feedback_url = self.parse_link(
          'origin_trial_feedback_url')

    if self.touched('anticipated_spec_changes'):
      feature.anticipated_spec_changes = self.form.get(
          'anticipated_spec_changes')

    if self.touched('finch_url'):
      feature.finch_url = self.parse_link('finch_url')

    if self.touched('i2e_lgtms'):
      feature.i2e_lgtms = self.split_emails('i2e_lgtms')

    if self.touched('i2s_lgtms'):
      feature.i2s_lgtms = self.split_emails('i2s_lgtms')

    # Cast incoming milestones to ints.
    # TODO(jrobbins): Consider supporting milestones that are not ints.
    if self.touched('shipped_milestone'):
      feature.shipped_milestone = self.parse_int('shipped_milestone')

    if self.touched('shipped_android_milestone'):
      feature.shipped_android_milestone = self.parse_int(
          'shipped_android_milestone')

    if self.touched('shipped_ios_milestone'):
      feature.shipped_ios_milestone = self.parse_int('shipped_ios_milestone')

    if self.touched('shipped_webview_milestone'):
      feature.shipped_webview_milestone = self.parse_int(
          'shipped_webview_milestone')

    if self.touched('shipped_opera_milestone'):
      feature.shipped_opera_milestone = (
          self.parse_int('shipped_opera_milestone'))

    if self.touched('shipped_opera_android'):
      feature.shipped_opera_android_milestone = self.parse_int(
          'shipped_opera_android_milestone')

    if self.touched('ot_milestone_desktop_start'):
      feature.ot_milestone_desktop_start = self.parse_int(
          'ot_milestone_desktop_start')
    if self.touched('ot_milestone_desktop_end'):
      feature.ot_milestone_desktop_end = self.parse_int(
          'ot_milestone_desktop_end')

    if self.touched('ot_milestone_android_start'):
      feature.ot_milestone_android_start = self.parse_int(
          'ot_milestone_android_start')
    if self.touched('ot_milestone_android_end'):
      feature.ot_milestone_android_end = self.parse_int(
          'ot_milestone_android_end')

    if self.touched('ot_milestone_webview_start'):
      feature.ot_milestone_webview_start = self.parse_int(
          'ot_milestone_webview_start')
    if self.touched('ot_milestone_webview_end'):
      feature.ot_milestone_webview_end = self.parse_int(
          'ot_milestone_webview_end')

    if self.touched('requires_embedder_support'):
      feature.requires_embedder_support = (
          self.form.get('requires_embedder_support') == 'on')

    if self.touched('devtrial_instructions'):
      feature.devtrial_instructions = self.parse_link('devtrial_instructions')

    if self.touched('dt_milestone_desktop_start'):
      feature.dt_milestone_desktop_start = self.parse_int(
          'dt_milestone_desktop_start')

    if self.touched('dt_milestone_android_start'):
      feature.dt_milestone_android_start = self.parse_int(
          'dt_milestone_android_start')

    if self.touched('dt_milestone_ios_start'):
      feature.dt_milestone_ios_start = self.parse_int(
          'dt_milestone_ios_start')

    if self.touched('dt_milestone_webview_start'):
      feature.dt_milestone_webview_start = self.parse_int(
          'dt_milestone_webview_start')

    if self.touched('flag_name'):
      feature.flag_name = self.form.get('flag_name')

    if self.touched('owner'):
      feature.owner = self.split_emails('owner')

    if self.touched('editors'):
      feature.editors = self.split_emails('editors')

    if self.touched('doc_links'):
      feature.doc_links = self.parse_links('doc_links')

    if self.touched('measurement'):
      feature.measurement = self.form.get('measurement')

    if self.touched('sample_links'):
      feature.sample_links = self.parse_links('sample_links')

    if self.touched('search_tags'):
      feature.search_tags = self.split_input('search_tags', delim=',')

    if self.touched('blink_components'):
      feature.blink_components = (
          self.split_input('blink_components', delim=',') or
          [settings.DEFAULT_COMPONENT])

    if self.touched('devrel'):
      feature.devrel = self.split_emails('devrel')

    if self.touched('feature_type'):
      feature.feature_type = int(self.form.get('feature_type'))

    # intent_stage can be be set either by <select> or a checkbox
    if self.touched('intent_stage'):
      feature.intent_stage = int(self.form.get('intent_stage'))
    elif self.form.get('set_stage') == 'on':
      feature.intent_stage = stage_id

    if self.touched('category'):
      feature.category = int(self.form.get('category'))
    if self.touched('name'):
      feature.name = self.form.get('name')
    if self.touched('summary'):
      feature.summary = self.form.get('summary')
    if self.touched('motivation'):
      feature.motivation = self.form.get('motivation')

    # impl_status_chrome can be be set either by <select> or a checkbox
    if self.touched('impl_status_chrome'):
      feature.impl_status_chrome = int(self.form.get('impl_status_chrome'))
    elif self.form.get('set_impl_status') == 'on':
      feature.impl_status_chrome = self.parse_int('impl_status_offered')

    if self.touched('interop_compat_risks'):
      feature.interop_compat_risks = self.form.get('interop_compat_risks')
    if self.touched('ergonomics_risks'):
      feature.ergonomics_risks = self.form.get('ergonomics_risks')
    if self.touched('activation_risks'):
      feature.activation_risks = self.form.get('activation_risks')
    if self.touched('security_risks'):
      feature.security_risks = self.form.get('security_risks')
    if self.touched('debuggability'):
      feature.debuggability = self.form.get('debuggability')
    if self.touched('all_platforms'):
      feature.all_platforms = self.form.get('all_platforms') == 'on'
    if self.touched('all_platforms_descr'):
      feature.all_platforms_descr = self.form.get('all_platforms_descr')
    if self.touched('wpt'):
      feature.wpt = self.form.get('wpt') == 'on'
    if self.touched('wpt_descr'):
      feature.wpt_descr = self.form.get('wpt_descr')
    if self.touched('ff_views'):
      feature.ff_views = int(self.form.get('ff_views'))
    if self.touched('ff_views_link'):
      feature.ff_views_link = self.parse_link('ff_views_link')
    if self.touched('ff_views_notes'):
      feature.ff_views_notes = self.form.get('ff_views_notes')

    # TODO(jrobbins): Delete after the next deployment
    if self.touched('ie_views'):
      feature.ie_views = int(self.form.get('ie_views'))
    if self.touched('ie_views_link'):
      feature.ie_views_link = self.parse_link('ie_views_link')
    if self.touched('ie_views_notes'):
      feature.ie_views_notes = self.form.get('ie_views_notes')

    if self.touched('safari_views'):
      feature.safari_views = int(self.form.get('safari_views'))
    if self.touched('safari_views_link'):
      feature.safari_views_link = self.parse_link('safari_views_link')
    if self.touched('safari_views_notes'):
      feature.safari_views_notes = self.form.get('safari_views_notes')
    if self.touched('web_dev_views'):
      feature.web_dev_views = int(self.form.get('web_dev_views'))
    if self.touched('web_dev_views'):
      feature.web_dev_views_link = self.parse_link('web_dev_views_link')
    if self.touched('web_dev_views_notes'):
      feature.web_dev_views_notes = self.form.get('web_dev_views_notes')
    if self.touched('other_views_notes'):
      feature.other_views_notes = self.form.get('other_views_notes')
    if self.touched('prefixed'):
      feature.prefixed = self.form.get('prefixed') == 'on'
    if self.touched('non_oss_deps'):
      feature.non_oss_deps = self.form.get('non_oss_deps')

    if self.touched('tag_review'):
      feature.tag_review = self.form.get('tag_review')
    if self.touched('tag_review_status'):
      feature.tag_review_status = self.parse_int('tag_review_status')
    if self.touched('webview_risks'):
      feature.webview_risks = self.form.get('webview_risks')

    if self.touched('standardization'):
      feature.standardization = int(self.form.get('standardization'))
    if self.form.get('accurate_as_of'):
      feature.accurate_as_of = datetime.now()
    if self.touched('unlisted'):
      feature.unlisted = self.form.get('unlisted') == 'on'
    if self.touched('comments'):
      feature.comments = self.form.get('comments')
    if self.touched('experiment_goals'):
      feature.experiment_goals = self.form.get('experiment_goals')
    if self.touched('experiment_timeline'):
      feature.experiment_timeline = self.form.get('experiment_timeline')
    if self.touched('experiment_risks'):
      feature.experiment_risks = self.form.get('experiment_risks')
    if self.touched('experiment_extension_reason'):
      feature.experiment_extension_reason = self.form.get(
          'experiment_extension_reason')
    if self.touched('ongoing_constraints'):
      feature.ongoing_constraints = self.form.get('ongoing_constraints')

    feature.updated_by = ndb.User(
        email=self.get_current_user().email(),
        _auth_domain='gmail.com')
    key = feature.put()

    # TODO(jrobbins): enumerate and remove only the relevant keys.
    ramcache.flush_all()

    redirect_url = '/guide/edit/' + str(key.integer_id())
    return self.redirect(redirect_url)
