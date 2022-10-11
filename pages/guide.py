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
from framework import rediscache

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
    cc_emails = self.split_emails('cc_recipients')

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
        summary=self.form.get('summary'),
        owner=owners,
        editors=editors,
        cc_recipients=cc_emails,
        creator=signed_in_user.email(),
        accurate_as_of=datetime.now(),
        unlisted=self.form.get('unlisted') == 'on',
        blink_components=blink_components,
        tag_review_status=processes.initial_tag_review_status(feature_type),
        created_by=signed_in_user,
        updated_by=signed_in_user)
    key = feature.put()

    # Write for new FeatureEntry entity.
    feature_entry = core_models.FeatureEntry(
        id=feature.key.integer_id(),
        category=int(self.form.get('category')),
        name=self.form.get('name'),
        feature_type=feature_type,
        summary=self.form.get('summary'),
        owner_emails=owners,
        editor_emails=editors,
        cc_emails=cc_emails,
        creator_email=signed_in_user.email(),
        updater_email=signed_in_user.email(),
        accurate_as_of=datetime.now(),
        unlisted=self.form.get('unlisted') == 'on',
        blink_components=blink_components,
        tag_review_status=processes.initial_tag_review_status(feature_type))
    feature_entry.put()

    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(core_models.feature_cache_prefix())

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
    selects = ['category', 'intent_stage', 'standard_maturity',
        'security_review_status', 'privacy_review_status', 'tag_review_status',
        'safari_views', 'ff_views', 'web_dev_views', 'blink_components',
        'impl_status_chrome']
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
      feature_entry = core_models.FeatureEntry.get_by_id(feature_id)
      if feature is None:
        self.abort(404, msg='Feature not found')
      else:
        feature.stash_values()

    logging.info('POST is %r', self.form)

    update_items = []
    stage_update_items = []

    if self.touched('spec_link'):
      feature.spec_link = self.parse_link('spec_link')
      update_items.append(('spec_link', self.parse_link('spec_link')))

    if self.touched('standard_maturity'):
      feature.standard_maturity = self.parse_int('standard_maturity')
      update_items.append(('standard_maturity',
          self.parse_int('standard_maturity')))

    if self.touched('api_spec'):
      feature.api_spec = self.form.get('api_spec') == 'on'
      update_items.append(('api_spec', self.form.get('api_spec') == 'on'))

    if self.touched('spec_mentors'):
      feature.spec_mentors = self.split_emails('spec_mentors')
      update_items.append(('spec_mentor_emails',
          self.split_emails('spec_mentors')))

    if self.touched('security_review_status'):
      feature.security_review_status = self.parse_int('security_review_status')
      update_items.append(('security_review_status',
          self.parse_int('security_review_status')))

    if self.touched('privacy_review_status'):
      feature.privacy_review_status = self.parse_int('privacy_review_status')
      update_items.append(('privacy_review_status',
          self.parse_int('privacy_review_status')))

    if self.touched('initial_public_proposal_url'):
      feature.initial_public_proposal_url = self.parse_link(
          'initial_public_proposal_url')
      update_items.append(('initial_public_proposal_url',
          self.parse_link('initial_public_proposal_url')))

    if self.touched('explainer_links'):
      feature.explainer_links = self.parse_links('explainer_links')
      update_items.append(('explainer_links',
          self.parse_links('explainer_links')))

    if self.touched('bug_url'):
      feature.bug_url = self.parse_link('bug_url')
      update_items.append(('bug_url', self.parse_link('bug_url')))
    if self.touched('launch_bug_url'):
      feature.launch_bug_url = self.parse_link('launch_bug_url')
      update_items.append(('launch_bug_url', self.parse_link('launch_bug_url')))

    if self.touched('intent_to_implement_url'):
      feature.intent_to_implement_url = self.parse_link(
          'intent_to_implement_url')
      stage_update_items.append(('intent_to_implement_url', self.parse_link(
          'intent_to_implement_url')))

    if self.touched('intent_to_ship_url'):
      feature.intent_to_ship_url = self.parse_link(
          'intent_to_ship_url')
      stage_update_items.append(('intent_to_ship_url',
          self.parse_link('intent_to_ship_url')))

    if self.touched('ready_for_trial_url'):
      feature.ready_for_trial_url = self.parse_link(
          'ready_for_trial_url')

    if self.touched('intent_to_experiment_url'):
      feature.intent_to_experiment_url = self.parse_link(
          'intent_to_experiment_url')
      stage_update_items.append(('intent_to_experiment_url',
          self.parse_link('intent_to_experiment_url')))

    if self.touched('intent_to_extend_experiment_url'):
      feature.intent_to_extend_experiment_url = self.parse_link(
          'intent_to_extend_experiment_url')
      stage_update_items.append(('intent_to_extend_experiment_url',
          self.parse_link('intent_to_extend_experiment_url')))

    if self.touched('origin_trial_feedback_url'):
      feature.origin_trial_feedback_url = self.parse_link(
          'origin_trial_feedback_url')
      stage_update_items.append(('origin_trial_feedback_url',
          self.parse_link('origin_trial_feedback_url')))

    if self.touched('anticipated_spec_changes'):
      feature.anticipated_spec_changes = self.form.get(
          'anticipated_spec_changes')
      update_items.append(('anticipated_spec_changes',
          self.form.get('anticipated_spec_changes')))

    if self.touched('finch_url'):
      feature.finch_url = self.parse_link('finch_url')
      stage_update_items.append(('finch_url', self.parse_link('finch_url')))

    if self.touched('i2e_lgtms'):
      feature.i2e_lgtms = self.split_emails('i2e_lgtms')

    if self.touched('i2s_lgtms'):
      feature.i2s_lgtms = self.split_emails('i2s_lgtms')

    # Cast incoming milestones to ints.
    # TODO(jrobbins): Consider supporting milestones that are not ints.
    if self.touched('shipped_milestone'):
      feature.shipped_milestone = self.parse_int('shipped_milestone')
      stage_update_items.append(('shipped_milestone',
          self.parse_int('shipped_milestone')))

    if self.touched('shipped_android_milestone'):
      feature.shipped_android_milestone = self.parse_int(
          'shipped_android_milestone')
      stage_update_items.append(('shipped_android_milestone',
          self.parse_int('shipped_android_milestone')))

    if self.touched('shipped_ios_milestone'):
      feature.shipped_ios_milestone = self.parse_int('shipped_ios_milestone')
      stage_update_items.append(('shipped_ios_milestone',
          self.parse_int('shipped_ios_milestone')))

    if self.touched('shipped_webview_milestone'):
      feature.shipped_webview_milestone = self.parse_int(
          'shipped_webview_milestone')
      stage_update_items.append(('shipped_webview_milestone',
          self.parse_int('shipped_webview_milestone')))

    if self.touched('ot_milestone_desktop_start'):
      feature.ot_milestone_desktop_start = self.parse_int(
          'ot_milestone_desktop_start')
      stage_update_items.append(('ot_milestone_desktop_start',
          self.parse_int('ot_milestone_desktop_start')))
    if self.touched('ot_milestone_desktop_end'):
      feature.ot_milestone_desktop_end = self.parse_int(
          'ot_milestone_desktop_end')
      stage_update_items.append(('ot_milestone_desktop_end',
          self.parse_int('ot_milestone_desktop_end')))

    if self.touched('ot_milestone_android_start'):
      feature.ot_milestone_android_start = self.parse_int(
          'ot_milestone_android_start')
      stage_update_items.append(('ot_milestone_android_start',
          self.parse_int('ot_milestone_android_start')))
    if self.touched('ot_milestone_android_end'):
      feature.ot_milestone_android_end = self.parse_int(
          'ot_milestone_android_end')
      stage_update_items.append(('ot_milestone_android_end',
          self.parse_int('ot_milestone_android_end')))

    if self.touched('ot_milestone_webview_start'):
      feature.ot_milestone_webview_start = self.parse_int(
          'ot_milestone_webview_start')
      stage_update_items.append(('ot_milestone_webview_start',
          self.parse_int('ot_milestone_webview_start')))
    if self.touched('ot_milestone_webview_end'):
      feature.ot_milestone_webview_end = self.parse_int(
          'ot_milestone_webview_end')
      stage_update_items.append(('ot_milestone_webview_end',
          self.parse_int('ot_milestone_webview_end')))

    if self.touched('requires_embedder_support'):
      feature.requires_embedder_support = (
          self.form.get('requires_embedder_support') == 'on')
      update_items.append(('requires_embedder_support',
          self.form.get('requires_embedder_support') == 'on'))

    if self.touched('devtrial_instructions'):
      feature.devtrial_instructions = self.parse_link('devtrial_instructions')
      update_items.append(('devtrial_instructions',
          self.parse_link('devtrial_instructions')))

    if self.touched('dt_milestone_desktop_start'):
      feature.dt_milestone_desktop_start = self.parse_int(
          'dt_milestone_desktop_start')
      stage_update_items.append(('dt_milestone_desktop_start',
          self.parse_int('dt_milestone_desktop_start')))

    if self.touched('dt_milestone_android_start'):
      feature.dt_milestone_android_start = self.parse_int(
          'dt_milestone_android_start')
      stage_update_items.append(('dt_milestone_android_start',
          self.parse_int('dt_milestone_android_start')))

    if self.touched('dt_milestone_ios_start'):
      feature.dt_milestone_ios_start = self.parse_int(
          'dt_milestone_ios_start')
      stage_update_items.append(('dt_milestone_ios_start',
          self.parse_int('dt_milestone_ios_start')))

    if self.touched('dt_milestone_webview_start'):
      feature.dt_milestone_webview_start = self.parse_int(
          'dt_milestone_webview_start')
      stage_update_items.append(('dt_milestone_webview_start',
          self.parse_int('dt_milestone_webview_start')))

    if self.touched('flag_name'):
      feature.flag_name = self.form.get('flag_name')
      update_items.append(('flag_name', self.form.get('flag_name')))

    if self.touched('owner'):
      feature.owner = self.split_emails('owner')
      update_items.append(('owner_emails', self.split_emails('owner')))

    if self.touched('editors'):
      feature.editors = self.split_emails('editors')
      update_items.append(('editor_emails', self.split_emails('editors')))

    if self.touched('cc_recipients'):
      feature.cc_recipients = self.split_emails('cc_recipients')
      update_items.append(('cc_emails', self.split_emails('cc_recipients')))

    if self.touched('doc_links'):
      feature.doc_links = self.parse_links('doc_links')
      update_items.append(('doc_links', self.parse_links('doc_links')))

    if self.touched('measurement'):
      feature.measurement = self.form.get('measurement')
      update_items.append(('measurement', self.form.get('measurement')))

    if self.touched('sample_links'):
      feature.sample_links = self.parse_links('sample_links')
      update_items.append(('sample_links', self.parse_links('sample_links')))

    if self.touched('search_tags'):
      feature.search_tags = self.split_input('search_tags', delim=',')
      update_items.append(('search_tags',
          self.split_input('search_tags', delim=',')))

    if self.touched('blink_components'):
      feature.blink_components = (
          self.split_input('blink_components', delim=',') or
          [settings.DEFAULT_COMPONENT])
      update_items.append(('blink_components', (
          self.split_input('blink_components', delim=',') or
          [settings.DEFAULT_COMPONENT])))

    if self.touched('devrel'):
      feature.devrel = self.split_emails('devrel')
      update_items.append(('devrel_emails', self.split_emails('devrel')))

    # intent_stage can be be set either by <select> or a checkbox
    if self.touched('intent_stage'):
      feature.intent_stage = int(self.form.get('intent_stage'))
      update_items.append(('intent_stage', int(self.form.get('intent_stage'))))
    elif self.form.get('set_stage') == 'on':
      feature.intent_stage = stage_id
      update_items.append(('intent_stage', stage_id))

    if self.touched('category'):
      feature.category = int(self.form.get('category'))
      update_items.append(('category', int(self.form.get('category'))))
    if self.touched('name'):
      feature.name = self.form.get('name')
      update_items.append(('name', self.form.get('name')))
    if self.touched('summary'):
      feature.summary = self.form.get('summary')
      update_items.append(('summary', self.form.get('summary')))
    if self.touched('motivation'):
      feature.motivation = self.form.get('motivation')
      update_items.append(('motivation', self.form.get('motivation')))

    # impl_status_chrome can be be set either by <select> or a checkbox
    if self.touched('impl_status_chrome'):
      feature.impl_status_chrome = int(self.form.get('impl_status_chrome'))
      update_items.append(('impl_status_chrome',
          int(self.form.get('impl_status_chrome'))))
    elif self.form.get('set_impl_status') == 'on':
      feature.impl_status_chrome = self.parse_int('impl_status_offered')
      update_items.append(('impl_status_chrome',
          self.parse_int('impl_status_offered')))

    if self.touched('interop_compat_risks'):
      feature.interop_compat_risks = self.form.get('interop_compat_risks')
      update_items.append(('interop_compat_risks',
          self.form.get('interop_compat_risks')))
    if self.touched('ergonomics_risks'):
      feature.ergonomics_risks = self.form.get('ergonomics_risks')
      update_items.append(('ergonomics_risks',
          self.form.get('ergonomics_risks')))
    if self.touched('activation_risks'):
      feature.activation_risks = self.form.get('activation_risks')
      update_items.append(('activation_risks',
          self.form.get('activation_risks')))
    if self.touched('security_risks'):
      feature.security_risks = self.form.get('security_risks')
      update_items.append(('security_risks', self.form.get('security_risks')))
    if self.touched('debuggability'):
      feature.debuggability = self.form.get('debuggability')
      update_items.append(('debuggability', self.form.get('debuggability')))
    if self.touched('all_platforms'):
      feature.all_platforms = self.form.get('all_platforms') == 'on'
      update_items.append(('all_platforms',
          self.form.get('all_platforms') == 'on'))
    if self.touched('all_platforms_descr'):
      feature.all_platforms_descr = self.form.get('all_platforms_descr')
      update_items.append(('all_platforms_descr',
          self.form.get('all_platforms_descr')))
    if self.touched('wpt'):
      feature.wpt = self.form.get('wpt') == 'on'
      update_items.append(('wpt', self.form.get('wpt') == 'on'))
    if self.touched('wpt_descr'):
      feature.wpt_descr = self.form.get('wpt_descr')
      update_items.append(('wpt_descr', self.form.get('wpt_descr')))
    if self.touched('ff_views'):
      feature.ff_views = int(self.form.get('ff_views'))
      update_items.append(('ff_views', int(self.form.get('ff_views'))))
    if self.touched('ff_views_link'):
      feature.ff_views_link = self.parse_link('ff_views_link')
      update_items.append(('ff_views_link', self.parse_link('ff_views_link')))
    if self.touched('ff_views_notes'):
      feature.ff_views_notes = self.form.get('ff_views_notes')
      update_items.append(('ff_views_notes', self.form.get('ff_views_notes')))

    # TODO(jrobbins): Delete after the next deployment
    if self.touched('ie_views'):
      feature.ie_views = int(self.form.get('ie_views'))
    if self.touched('ie_views_link'):
      feature.ie_views_link = self.parse_link('ie_views_link')
    if self.touched('ie_views_notes'):
      feature.ie_views_notes = self.form.get('ie_views_notes')

    if self.touched('safari_views'):
      feature.safari_views = int(self.form.get('safari_views'))
      update_items.append(('safari_views', int(self.form.get('safari_views'))))
    if self.touched('safari_views_link'):
      feature.safari_views_link = self.parse_link('safari_views_link')
      update_items.append(('safari_views_link',
          self.parse_link('safari_views_link')))
    if self.touched('safari_views_notes'):
      feature.safari_views_notes = self.form.get('safari_views_notes')
      update_items.append(('safari_views_notes',
          self.form.get('safari_views_notes')))
    if self.touched('web_dev_views'):
      feature.web_dev_views = int(self.form.get('web_dev_views'))
      update_items.append(('web_dev_views',
          int(self.form.get('web_dev_views'))))
    if self.touched('web_dev_views_link'):
      feature.web_dev_views_link = self.parse_link('web_dev_views_link')
      update_items.append(('web_dev_views_link',
          self.parse_link('web_dev_views_link')))
    if self.touched('web_dev_views_notes'):
      feature.web_dev_views_notes = self.form.get('web_dev_views_notes')
      update_items.append(('web_dev_views_notes',
          self.form.get('web_dev_views_notes')))
    if self.touched('other_views_notes'):
      feature.other_views_notes = self.form.get('other_views_notes')
      update_items.append(('other_views_notes',
          self.form.get('other_views_notes')))
    if self.touched('prefixed'):
      feature.prefixed = self.form.get('prefixed') == 'on'
      update_items.append(('prefixed', self.form.get('prefixed') == 'on'))
    if self.touched('non_oss_deps'):
      feature.non_oss_deps = self.form.get('non_oss_deps')
      update_items.append(('non_oss_deps', self.form.get('non_oss_deps')))

    if self.touched('tag_review'):
      feature.tag_review = self.form.get('tag_review')
      update_items.append(('tag_review', self.form.get('tag_review')))
    if self.touched('tag_review_status'):
      feature.tag_review_status = self.parse_int('tag_review_status')
      update_items.append(('tag_review_status',
          self.parse_int('tag_review_status')))
    if self.touched('webview_risks'):
      feature.webview_risks = self.form.get('webview_risks')
      update_items.append(('webview_risks', self.form.get('webview_risks')))

    if self.touched('standardization'):
      feature.standardization = int(self.form.get('standardization'))
    if self.form.get('accurate_as_of'):
      feature.accurate_as_of = datetime.now()
      update_items.append(('accurate_as_of', datetime.now()))
    if self.touched('unlisted'):
      feature.unlisted = self.form.get('unlisted') == 'on'
      update_items.append(('unlisted', self.form.get('unlisted') == 'on'))
    if self.touched('comments'):
      feature.comments = self.form.get('comments')
      update_items.append(('feature_notes', self.form.get('comments')))
    if self.touched('experiment_goals'):
      feature.experiment_goals = self.form.get('experiment_goals')
      stage_update_items.append(('experiment_goals',
          self.form.get('experiment_goals')))
    if self.touched('experiment_timeline'):
      feature.experiment_timeline = self.form.get('experiment_timeline')
    if self.touched('experiment_risks'):
      feature.experiment_risks = self.form.get('experiment_risks')
      stage_update_items.append(('experiment_risks',
          self.form.get('experiment_risks')))
    if self.touched('experiment_extension_reason'):
      feature.experiment_extension_reason = self.form.get(
          'experiment_extension_reason')
      stage_update_items.append(('experiment_extension_reason',
          self.form.get('experiment_extension_reason')))
    if self.touched('ongoing_constraints'):
      feature.ongoing_constraints = self.form.get('ongoing_constraints')
      update_items.append(('ongoing_constraints',
          self.form.get('ongoing_constraints')))

    feature.updated_by = ndb.User(
        email=self.get_current_user().email(),
        _auth_domain='gmail.com')
    update_items.append(('updater_email', self.get_current_user().email()))
    update_items.append(('updated', datetime.now()))
    key = feature.put()

    # Write for new FeatureEntry entity.
    if feature_entry:
      for field, value in update_items:
        setattr(feature_entry, field, value)
      feature_entry.put()
    
    # Write changes made to the corresponding stage type.
    if stage_update_items:
      self.update_stage_fields(feature_id, feature.feature_type,
          stage_update_items)

    # Remove all feature-related cache.
    rediscache.delete_keys_with_prefix(core_models.feature_cache_prefix())

    redirect_url = '/guide/edit/' + str(key.integer_id())
    return self.redirect(redirect_url)

  def update_stage_fields(self, feature_id, feature_type, update_items) -> None:
    # Get all existing stages associated with the feature.
    stages = core_models.Stage.get_feature_stages(feature_id)

    for field, value in update_items:
      # Determine the stage type that the field should change on.
      stage_type = core_enums.STAGE_TYPES_BY_FIELD_MAPPING[field][feature_type]
      # If this feature type does not have this field, skip it
      # (e.g. developer-facing code changes cannot have origin trial fields).
      if stage_type is None:
        continue
      stage = stages.get(stage_type, None)
      # If a stage of this type does not exist for this feature, create it.
      if stage is None:
        stage = core_models.Stage(feature_id=feature_id, stage_type=stage_type)
        stage.put()
        stages[stage_type] = stage
      
      # Change the field based on the field type.
      # If this field changing is a milestone, change it in the
      # MilestoneSet entity.
      if field in core_models.MilestoneSet.MILESTONE_FIELD_MAPPING:
        milestone_field = (
            core_models.MilestoneSet.MILESTONE_FIELD_MAPPING[field])
        milestoneset_entity = getattr(stage, 'milestones')
        # If the MilestoneSet entity has not been initiated, create it.
        if milestoneset_entity is None:
          milestoneset_entity = core_models.MilestoneSet()
        setattr(milestoneset_entity, milestone_field, value)
        stage.milestones = milestoneset_entity
      # If the field starts with "intent_", it should modify the
      # more general "intent_thread_url" field.
      elif field.startswith('intent_'):
        setattr(stage, 'intent_thread_url', value)
      # Otherwise, replace field value with attribute of the same field name.
      else:
        setattr(stage, field, value)
    
    # Write to all the stages.
    for stage in stages.values():
      stage.put()
