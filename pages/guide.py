from __future__ import division
from __future__ import print_function

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

import datetime
import flask
import json
import logging
import os
import re
import sys
from django import forms

# Appengine imports.
from framework import ramcache
from google.appengine.api import users
from google.appengine.ext import db

from framework import basehandlers
from framework import utils
from pages import guideforms
import models
import processes
import settings


# Forms to be used for each stage of each process.
# { feature_type_id: { stage_id: stage_specific_form} }
STAGE_FORMS = {
    models.FEATURE_TYPE_INCUBATE_ID: {
        models.INTENT_INCUBATE: guideforms.NewFeature_Incubate,
        models.INTENT_IMPLEMENT: guideforms.NewFeature_Prototype,
        models.INTENT_EXPERIMENT: guideforms.Any_DevTrial,
        models.INTENT_IMPLEMENT_SHIP: guideforms.NewFeature_EvalReadinessToShip,
        models.INTENT_EXTEND_TRIAL: guideforms.NewFeature_OriginTrial,
        models.INTENT_SHIP: guideforms.Most_PrepareToShip,
        models.INTENT_SHIPPED: guideforms.Any_Ship,
        },

    models.FEATURE_TYPE_EXISTING_ID: {
        models.INTENT_INCUBATE: guideforms.Any_Identify,
        models.INTENT_IMPLEMENT: guideforms.Any_Implement,
        models.INTENT_EXPERIMENT: guideforms.Any_DevTrial,
        models.INTENT_EXTEND_TRIAL: guideforms.Existing_OriginTrial,
        models.INTENT_SHIP: guideforms.Most_PrepareToShip,
        models.INTENT_SHIPPED: guideforms.Any_Ship,
        },

    models.FEATURE_TYPE_CODE_CHANGE_ID: {
        models.INTENT_INCUBATE: guideforms.Any_Identify,
        models.INTENT_IMPLEMENT: guideforms.Any_Implement,
        models.INTENT_EXPERIMENT: guideforms.Any_DevTrial,
        models.INTENT_SHIP: guideforms.PSA_PrepareToShip,
        models.INTENT_SHIPPED: guideforms.Any_Ship,
        },

    models.FEATURE_TYPE_DEPRECATION_ID: {
        models.INTENT_INCUBATE: guideforms.Any_Identify,
        models.INTENT_IMPLEMENT: guideforms.Any_Implement,
        models.INTENT_EXPERIMENT: guideforms.Any_DevTrial,
        models.INTENT_EXTEND_TRIAL: guideforms.Deprecation_DeprecationTrial,
        models.INTENT_SHIP: guideforms.Deprecation_PrepareToShip,
        models.INTENT_REMOVED: guideforms.Deprecation_Removed,
        },
}


IMPL_STATUS_FORMS = {
    models.INTENT_EXPERIMENT:
        (models.BEHIND_A_FLAG, guideforms.ImplStatus_DevTrial),
    models.INTENT_EXTEND_TRIAL:
        (models.ORIGIN_TRIAL, guideforms.ImplStatus_OriginTrial),
    models.INTENT_IMPLEMENT_SHIP:
        (None, guideforms.ImplStatus_EvalReadinessToShip),
    models.INTENT_SHIP:
        (models.ENABLED_BY_DEFAULT, guideforms.ImplStatus_AllMilestones),
    models.INTENT_SHIPPED:
        (models.ENABLED_BY_DEFAULT, guideforms.ImplStatus_AllMilestones),
    models.INTENT_REMOVED:
        (models.REMOVED, guideforms.ImplStatus_AllMilestones),
    }

# Forms to be used on the "Edit all" page that shows a flat list of fields.
# [('Section name': form_class)].
FLAT_FORMS = [
    ('Feature metadata', guideforms.Flat_Metadata),
    ('Indentify the need', guideforms.Flat_Identify),
    ('Prototype a solution', guideforms.Flat_Implement),
    ('Dev trial', guideforms.Flat_DevTrial),
    ('Origin trial', guideforms.Flat_OriginTrial),
    ('Prepare to ship', guideforms.Flat_PrepareToShip),
    ('Ship', guideforms.Flat_Ship),
]


class FeatureNew(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'guide/new.html'

  def get_template_data(self):
    user = users.get_current_user()
    if user is None:
      return self.redirect(users.create_login_url(self.request.path))

    if not self.user_can_edit(user):
      self.abort(403)

    new_feature_form = guideforms.NewFeatureForm(
        initial={'owner': user.email()})
    template_data = {
        'overview_form': new_feature_form,
        }
    return template_data

  def process_post_data(self):
    user = users.get_current_user()
    if user is None or (user and not self.user_can_edit(user)):
      self.abort(403)

    owners = self.split_emails('owner')

    blink_components = (
        self.split_input('blink_components', delim=',') or
        [models.BlinkComponent.DEFAULT_COMPONENT])

    # TODO(jrobbins): Validate input, even though it is done on client.

    feature_type = int(self.form.get('feature_type', 0))
    feature = models.Feature(
        category=int(self.form.get('category')),
        name=self.form.get('name'),
        feature_type=feature_type,
        intent_stage=models.INTENT_NONE,
        summary=self.form.get('summary'),
        owner=owners,
        impl_status_chrome=models.NO_ACTIVE_DEV,
        standardization=models.EDITORS_DRAFT,
        unlisted=self.form.get('unlisted') == 'on',
        web_dev_views=models.DEV_NO_SIGNALS,
        blink_components=blink_components,
        tag_review_status=processes.initial_tag_review_status(feature_type))
    key = feature.put()

    # TODO(jrobbins): enumerate and remove only the relevant keys.
    ramcache.flush_all()

    redirect_url = '/guide/edit/' + str(key.id())
    return self.redirect(redirect_url)


class ProcessOverview(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'guide/edit.html'

  def detect_progress(self, f):
    progress_so_far = {}
    for progress_item, detector in processes.PROGRESS_DETECTORS.items():
      detected = detector(f)
      if detected:
        progress_so_far[progress_item] = str(detected)
    return progress_so_far

  def get_template_data(self, feature_id):
    user = users.get_current_user()
    if user is None:
      # Redirect to public URL for unauthenticated users.
      return self.redirect(utils.format_feature_url(feature_id))

    if not self.user_can_edit(user):
      self.abort(403)

    f = models.Feature.get_by_id(long(feature_id))
    if f is None:
      self.abort(404)

    feature_process = processes.ALL_PROCESSES.get(
        f.feature_type, processes.BLINK_LAUNCH_PROCESS)
    template_data = {
        'overview_form': guideforms.MetadataForm(f.format_for_edit()),
        'process_json': json.dumps(processes.process_to_dict(feature_process)),
        }

    progress_so_far = self.detect_progress(f)

    # Provide new or populated form to template.
    template_data.update({
        'feature': f.format_for_template(),
        'feature_id': f.key().id,
        'feature_json': json.dumps(f.format_for_template()),
        'progress_so_far': json.dumps(progress_so_far),
    })
    return template_data


class FeatureEditStage(basehandlers.FlaskHandler):

  TEMPLATE_PATH = 'guide/stage.html'

  def touched(self, param_name):
    """Return True if the user edited the specified field."""
    # TODO(jrobbins): for now we just consider everything on the current form
    # to have been touched.  Later we will add javascript to populate a
    # hidden form field named "touched" that lists the names of all fields
    # actually touched by the user.

    # For now, checkboxes are always considered "touched", if they are
    # present on the form.
    # TODO(jrobbins): Simplify this after next deployment.
    checkboxes = ('unlisted', 'all_platforms', 'wpt', 'prefixed', 'api_spec')
    if param_name in checkboxes:
      form_fields_str = self.form.get('form_fields')
      if form_fields_str:
        form_fields = [field_name.strip()
                       for field_name in form_fields_str.split(',')]
        return param_name in form_fields
      else:
        return True
    return param_name in self.form

  def get_blink_component_from_bug(self, blink_components, bug_url):
    # TODO(jrobbins): Use monorail API instead of scrapping.
    return []

  def get_feature_and_process(self, feature_id):
    """Look up the feature that the user wants to edit, and its process."""
    f = models.Feature.get_by_id(feature_id)
    if f is None:
      self.abort(404)

    feature_process = processes.ALL_PROCESSES.get(
        f.feature_type, processes.BLINK_LAUNCH_PROCESS)

    return f, feature_process

  def get_template_data(self, feature_id, stage_id):
    user = users.get_current_user()
    if user is None:
      # Redirect to public URL for unauthenticated users.
      return self.redirect(utils.format_feature_url(feature_id))

    if not self.user_can_edit(user):
      self.abort(403)

    f, feature_process = self.get_feature_and_process(feature_id)

    stage_name = ''
    for stage in feature_process.stages:
      if stage.outgoing_stage == stage_id:
        stage_name = stage.name

    template_data = {
        'stage_name': stage_name,
        'stage_id': stage_id,
        }

    # TODO(jrobbins): show useful error if stage not found.
    detail_form_class = STAGE_FORMS[f.feature_type][stage_id]

    impl_status_offered, impl_status_form_class = IMPL_STATUS_FORMS.get(
        stage_id, (None, None))

    feature_edit_dict = f.format_for_edit()
    detail_form = None
    if detail_form_class:
      detail_form = detail_form_class(feature_edit_dict)
    impl_status_form = None
    if impl_status_form_class:
      impl_status_form = impl_status_form_class(feature_edit_dict)

    # Provide new or populated form to template.
    template_data.update({
        'feature': f,
        'feature_id': f.key().id,
        'feature_form': detail_form,
        'already_on_this_stage': stage_id == f.intent_stage,
        'already_on_this_impl_status':
            impl_status_offered == f.impl_status_chrome,
        'impl_status_form': impl_status_form,
        'impl_status_name': models.IMPLEMENTATION_STATUS.get(
            impl_status_offered, None),
        'impl_status_offered': impl_status_offered,
    })
    return template_data

  def process_post_data(self, feature_id, stage_id=0):
    user = users.get_current_user()
    if user is None or (user and not self.user_can_edit(user)):
      self.abort(403)

    if feature_id:
      feature = models.Feature.get_by_id(feature_id)
      if feature is None:
        self.abort(404)

    logging.info('POST is %r', self.form)

    if self.touched('spec_link'):
      feature.spec_link = self.parse_link('spec_link')

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
      feature.explainer_links = self.split_input('explainer_links')

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

    if self.touched('origin_trial_feedback_url'):
      feature.origin_trial_feedback_url = self.parse_link(
          'origin_trial_feedback_url')

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
      feature.shipped_opera_milestone = self.parse_int('shipped_opera_milestone')

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

    if self.touched('flag_name'):
      feature.flag_name = self.form.get('flag_name')

    if self.touched('owner'):
      feature.owner = self.split_emails('owner')

    if self.touched('doc_links'):
      feature.doc_links = self.split_input('doc_links')

    if self.touched('measurement'):
      feature.measurement = self.form.get('measurement')

    if self.touched('sample_links'):
      feature.sample_links = self.split_input('sample_links')

    if self.touched('search_tags'):
      feature.search_tags = self.split_input('search_tags', delim=',')

    if self.touched('blink_components'):
      feature.blink_components = (
          self.split_input('blink_components', delim=',') or
          [models.BlinkComponent.DEFAULT_COMPONENT])

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
    if self.touched('prefixed'):
      feature.prefixed = self.form.get('prefixed') == 'on'

    if self.touched('tag_review'):
      feature.tag_review = self.form.get('tag_review')
    if self.touched('tag_review_status'):
      feature.tag_review_status = self.parse_int('tag_review_status')

    if self.touched('standardization'):
      feature.standardization = int(self.form.get('standardization'))
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

    if self.form.get('intent_to_implement') == 'on':
      feature.intent_template_use_count += 1

    key = feature.put()

    # TODO(jrobbins): enumerate and remove only the relevant keys.
    ramcache.flush_all()

    redirect_url = '/guide/edit/' + str(key.id())
    return self.redirect(redirect_url)


class FeatureEditAllFields(FeatureEditStage):
  """Flat form page that lists all fields in seprate sections."""

  TEMPLATE_PATH = 'guide/editall.html'

  def get_template_data(self, feature_id):
    user = users.get_current_user()
    if user is None:
      # Redirect to public URL for unauthenticated users.
      return self.redirect(utils.format_feature_url(feature_id))

    if not self.user_can_edit(user):
      self.abort(403)

    f, feature_process = self.get_feature_and_process(feature_id)

    feature_edit_dict = f.format_for_edit()
    # TODO(jrobbins): make flat forms process specific?
    flat_form_section_list = FLAT_FORMS
    flat_forms = [
        (section_name, form_class(feature_edit_dict))
        for section_name, form_class in flat_form_section_list]
    template_data = {
        'feature': f,
        'feature_id': f.key().id,
        'flat_forms': flat_forms,
    }
    return template_data


app = basehandlers.FlaskApplication([
  ('/guide/new', FeatureNew),
  ('/guide/edit/<int:feature_id>', ProcessOverview),
  # TODO(jrobbins): ('/guide/delete/<int:feature_id>', FeatureDelete),
  ('/guide/stage/<int:feature_id>/<int:stage_id>', FeatureEditStage),
  ('/guide/editall/<int:feature_id>', FeatureEditAllFields),
], debug=settings.DEBUG)
