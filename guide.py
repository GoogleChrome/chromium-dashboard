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
import json
import logging
import os
import re
import sys
import webapp2
from django import forms

# Appengine imports.
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api import taskqueue

# File imports.
import common
import guideforms
import models
import processes
import settings


# Forms to be used for each stage of each process.
STAGE_FORMS = {
    (models.PROCESS_BLINK_LAUNCH_ID, models.INTENT_NONE):
    guideforms.Incubate,
    (models.PROCESS_BLINK_LAUNCH_ID, models.INTENT_IMPLEMENT):
    guideforms.Prototype,
    (models.PROCESS_BLINK_LAUNCH_ID, models.INTENT_EXPERIMENT):
    guideforms.DevTrial,
    (models.PROCESS_BLINK_LAUNCH_ID, models.INTENT_EXTEND_TRIAL):
    guideforms.OriginTrial,

    (models.PROCESS_FAST_TRACK_ID, models.INTENT_NONE):
    guideforms.Incubate,
    (models.PROCESS_FAST_TRACK_ID, models.INTENT_IMPLEMENT_SHIP):
    guideforms.Prototype,
    (models.PROCESS_FAST_TRACK_ID, models.INTENT_SHIP):
    guideforms.DevTrial,
    (models.PROCESS_FAST_TRACK_ID, models.INTENT_EXTEND_TRIAL):
    guideforms.OriginTrial,

    (models.PROCESS_PSA_ONLY_ID, models.INTENT_NONE):
    guideforms.Incubate,
}


def format_feature_url(feature_id):
  """Return the feature detail page URL for the specified feature."""
  return '/feature/%d' % feature_id


class FeatureNew(common.ContentHandler):

  def get(self, path):
    user = users.get_current_user()
    if user is None:
      return self.redirect(users.create_login_url(self.request.uri))

    if not self._is_user_whitelisted(user):
      common.handle_401(self.request, self.response, Exception)
      return

    template_data = {
        'overview_form': guideforms.NewFeatureForm(),
        }

    self._add_common_template_values(template_data)

    self.render(data=template_data, template_path=os.path.join(path + '.html'))

  def post(self, path):
    user = users.get_current_user()
    if user is None or (user and not self._is_user_whitelisted(user)):
      common.handle_401(self.request, self.response, Exception)
      return

    owner_addrs = self.request.get('owner') or ''
    owner_addrs = filter(bool, [
        x.strip() for x in re.split(',', owner_addrs)])
    owners = [db.Email(addr) for addr in owner_addrs]

    # TODO(jrobbins): Validate input, even though it is done on client.

    feature = models.Feature(
        category=int(self.request.get('category')),
        name=self.request.get('name'),
        process=int(self.request.get('process', 0)),
        intent_stage=models.INTENT_NONE,
        summary=self.request.get('summary'),
        owner=owners,
        impl_status_chrome=models.NO_ACTIVE_DEV,
        visibility=models.WARRANTS_ARTICLE,
        standardization=models.EDITORS_DRAFT,
        unlisted=self.request.get('unlisted') == 'on',
        web_dev_views=models.DEV_NO_SIGNALS)
    key = feature.put()

    # TODO(jrobbins): enumerate and remove only the relevant keys.
    memcache.flush_all()

    redirect_url = '/guide/edit/' + str(key.id())
    return self.redirect(redirect_url)


class ProcessOverview(common.ContentHandler):

  def get(self, path, feature_id):
    user = users.get_current_user()
    if user is None:
      # Redirect to public URL for unauthenticated users.
      return self.redirect(format_feature_url(feature_id))

    if not self._is_user_whitelisted(user):
      common.handle_401(self.request, self.response, Exception)
      return

    f = models.Feature.get_by_id(long(feature_id))
    if f is None:
      self.abort(404)

    feature_process = processes.ALL_PROCESSES.get(
        f.process, processes.BLINK_LAUNCH_PROCESS)
    template_data = {
        'overview_form': guideforms.MetadataForm(f.format_for_edit()),
        'process_json': json.dumps(processes.process_to_dict(feature_process)),
        'progress_so_far': [],
        }

    progress_so_far = []  # An unordered list of progress item strings.
    # TODO(jrobbins): Replace this constant with a call to apply a bunch
    # of tiny functions to detect each bit of progress.
    progress_so_far = ['Explainer', 'API design']

    # Provide new or populated form to template.
    template_data.update({
        'feature': f.format_for_template(),
        'feature_id': f.key().id,
        'feature_json': json.dumps(f.format_for_template()),
        'progress_so_far': json.dumps(progress_so_far),
    })

    self._add_common_template_values(template_data)
    self.render(data=template_data, template_path=os.path.join(path + '.html'))


class FeatureEditStage(common.ContentHandler):

  LAUNCH_URL = '/admin/features/launch'

  INTENT_PARAM = 'intent'
  LAUNCH_PARAM = 'launch'

  def touched(self, param_name):
    """Return True if the user edited the specified field."""
    # TODO(jrobbins): for now we just consider everything on the current form
    # to have been touched.  Later we will add javascript to populate a
    # hidden form field named "touched" that lists the names of all fields
    # actually touched by the user.
    # For now, checkboxes are always considered "touched", otherwise there
    # would be no way to uncheck.
    if param_name in ('unlisted', 'all_platforms', 'wpt', 'prefixed'):
      return True
    return param_name in self.request.POST

  def split_input(self, field_name, delim='\\r?\\n'):
    """Split the input lines, strip whitespace, and skip blank lines."""
    input_text = self.request.get(field_name) or ''
    return filter(bool, [
        x.strip() for x in re.split(delim, input_text)])

  def __FullQualifyLink(self, param_name):
    link = self.request.get(param_name) or None
    if link:
      if not link.startswith('http'):
        link = db.Link('http://' + link)
      else:
        link = db.Link(link)
    return link

  def __ToInt(self, param_name):
    param = self.request.get(param_name) or None
    if param:
      param = int(param)
    return param

  def get_blink_component_from_bug(self, blink_components, bug_url):
    # TODO(jrobbins): Use monorail API instead of scrapping.
    return []

  def get(self, path, feature_id, stage_id):
    stage_id = int(stage_id)
    user = users.get_current_user()
    if user is None:
      # Redirect to public URL for unauthenticated users.
      return self.redirect(format_feature_url(feature_id))

    if not self._is_user_whitelisted(user):
      common.handle_401(self.request, self.response, Exception)
      return

    f = models.Feature.get_by_id(long(feature_id))
    if f is None:
      self.abort(404)

    feature_process = processes.ALL_PROCESSES.get(
        f.process, processes.BLINK_LAUNCH_PROCESS)
    stage_name = ''
    for stage in feature_process.stages:
      if stage.outgoing_stage == stage_id:
        stage_name = stage.name

    template_data = {
        'stage_name': stage_name,
        }

    # TODO(jrobbins): show useful error if stage not found.
    detail_form_class = STAGE_FORMS.get(
        (f.process, stage_id), models.FeatureForm)

    # Provide new or populated form to template.
    template_data.update({
        'feature': f,
        'feature_id': f.key().id,
        'feature_form': detail_form_class(f.format_for_edit()),
    })

    if self.LAUNCH_PARAM in self.request.params:
      template_data[self.LAUNCH_PARAM] = True
    if self.INTENT_PARAM in self.request.params:
      template_data[self.INTENT_PARAM] = True

    self._add_common_template_values(template_data)

    self.render(data=template_data, template_path=os.path.join(path + '.html'))

  def post(self, path, feature_id, stage_id):
    user = users.get_current_user()
    if user is None or (user and not self._is_user_whitelisted(user)):
      common.handle_401(self.request, self.response, Exception)
      return

    if feature_id:
      feature = models.Feature.get_by_id(long(feature_id))
      if feature is None:
        self.abort(404)

    logging.info('POST is %r', self.request.POST)

    if self.touched('spec_link'):
      feature.spec_link = self.__FullQualifyLink('spec_link')

    if self.touched('explainer_links'):
      feature.explainer_links = self.split_input('explainer_links')

    if self.touched('bug_url'):
      feature.bug_url = self.__FullQualifyLink('bug_url')

    if self.touched('intent_to_implement_url'):
      feature.intent_to_implement_url = self.__FullQualifyLink(
          'intent_to_implement_url')

    if self.touched('origin_trial_feedback_url'):
      feature.origin_trial_feedback_url = self.__FullQualifyLink(
          'origin_trial_feedback_url')

    # Cast incoming milestones to ints.
    # TODO(jrobbins): Consider supporting milestones that are not ints.
    if self.touched('shipped_milestone = self'):
      feature.shipped_milestone = self.__ToInt('shipped_milestone')

    if self.touched('shipped_android_milestone'):
      feature.shipped_android_milestone = self.__ToInt(
          'shipped_android_milestone')

    if self.touched('shipped_ios_milestone'):
      feature.shipped_ios_milestone = self.__ToInt('shipped_ios_milestone')

    if self.touched('shipped_webview_milestone'):
      feature.shipped_webview_milestone = self.__ToInt(
          'shipped_webview_milestone')

    if self.touched('shipped_opera_milestone'):
      feature.shipped_opera_milestone = self.__ToInt('shipped_opera_milestone')

    if self.touched('shipped_opera_android'):
      feature.shipped_opera_android_milestone = self.__ToInt(
          'shipped_opera_android_milestone')

    if self.touched('owner'):
      owner_addrs = self.split_input('owner', delim=',')
      feature.owner = [db.Email(addr) for addr in owner_addrs]

    if self.touched('doc_links'):
      feature.doc_links = self.split_input('doc_links')

    if self.touched('sample_links'):
      feature.sample_links = self.split_input('sample_links')

    if self.touched('search_tags'):
      feature.search_tags = self.split_input('search_tags', delim=',')

    if self.touched('blink_components'):
      feature.blink_components = (
          self.split_input('blink_components', delim=',') or
          models.BlinkComponent.DEFAULT_COMPONENT)

    if self.touched('devrel'):
      devrel_addrs = self.split_input('devrel', delim=',')
      feature.devrel = [db.Email(addr) for addr in devrel_addrs]

    if self.touched('process'):
      feature.process = int(self.request.get('process'))
    if self.touched('intent_stage'):
      feature.intent_stage = int(self.request.get('intent_stage'))

    if self.touched('category'):
      feature.category = int(self.request.get('category'))
    if self.touched('name'):
      feature.name = self.request.get('name')
    if self.touched('summary'):
      feature.summary = self.request.get('summary')
    if self.touched('motivation'):
      feature.motivation = self.request.get('motivation')
    if self.touched('impl_status_chrome'):
      feature.impl_status_chrome = int(self.request.get('impl_status_chrome'))
    if self.touched('footprint'):
      feature.footprint = int(self.request.get('footprint'))
    if self.touched('interop_compat_risks'):
      feature.interop_compat_risks = self.request.get('interop_compat_risks')
    if self.touched('ergonomics_risks'):
      feature.ergonomics_risks = self.request.get('ergonomics_risks')
    if self.touched('activation_risks'):
      feature.activation_risks = self.request.get('activation_risks')
    if self.touched('security_risks'):
      feature.security_risks = self.request.get('security_risks')
    if self.touched('debuggability'):
      feature.debuggability = self.request.get('debuggability')
    if self.touched('all_platforms'):
      feature.all_platforms = self.request.get('all_platforms') == 'on'
    if self.touched('all_platforms_descr'):
      feature.all_platforms_descr = self.request.get('all_platforms_descr')
    if self.touched('wpt'):
      feature.wpt = self.request.get('wpt') == 'on'
    if self.touched('wpt_descr'):
      feature.wpt_descr = self.request.get('wpt_descr')
    if self.touched('visibility'):
      feature.visibility = int(self.request.get('visibility'))
    if self.touched('ff_views'):
      feature.ff_views = int(self.request.get('ff_views'))
    if self.touched('ff_views_link'):
      feature.ff_views_link = self.__FullQualifyLink('ff_views_link')
    if self.touched('ff_views_notes'):
      feature.ff_views_notes = self.request.get('ff_views_notes')
    if self.touched('ie_views'):
      feature.ie_views = int(self.request.get('ie_views'))
    if self.touched('ie_views_link'):
      feature.ie_views_link = self.__FullQualifyLink('ie_views_link')
    if self.touched('ie_views_notes'):
      feature.ie_views_notes = self.request.get('ie_views_notes')
    if self.touched('safari_views'):
      feature.safari_views = int(self.request.get('safari_views'))
    if self.touched('safari_views_link'):
      feature.safari_views_link = self.__FullQualifyLink('safari_views_link')
    if self.touched('safari_views_notes'):
      feature.safari_views_notes = self.request.get('safari_views_notes')
    if self.touched('web_dev_views'):
      feature.web_dev_views = int(self.request.get('web_dev_views'))
    if self.touched('web_dev_views'):
      feature.web_dev_views_link = self.__FullQualifyLink('web_dev_views_link')
    if self.touched('web_dev_views_notes'):
      feature.web_dev_views_notes = self.request.get('web_dev_views_notes')
    if self.touched('prefixed'):
      feature.prefixed = self.request.get('prefixed') == 'on'
    if self.touched('tag_review'):
      feature.tag_review = self.request.get('tag_review')
    if self.touched('standardization'):
      feature.standardization = int(self.request.get('standardization'))
    if self.touched('unlisted'):
      feature.unlisted = self.request.get('unlisted') == 'on'
    if self.touched('comments'):
      feature.comments = self.request.get('comments')
    if self.touched('experiment_goals'):
      feature.experiment_goals = self.request.get('experiment_goals')
    if self.touched('experiment_timeline'):
      feature.experiment_timeline = self.request.get('experiment_timeline')
    if self.touched('experiment_risks'):
      feature.experiment_risks = self.request.get('experiment_risks')
    if self.touched('experiment_extension_reason'):
      feature.experiment_extension_reason = self.request.get(
          'experiment_extension_reason')
    if self.touched('ongoing_constraints'):
      feature.ongoing_constraints = self.request.get('ongoing_constraints')

    params = []
    if self.request.get('create_launch_bug') == 'on':
      params.append(self.LAUNCH_PARAM)
    if self.request.get('intent_to_implement') == 'on':
      params.append(self.INTENT_PARAM)

      feature.intent_template_use_count += 1

    key = feature.put()

    # TODO(jrobbins): enumerate and remove only the relevant keys.
    memcache.flush_all()

    redirect_url = '/guide/edit/' + str(key.id())

    if len(params):
      redirect_url = '%s/%s?%s' % (self.LAUNCH_URL, key.id(),
                                   '&'.join(params))

    return self.redirect(redirect_url)


app = webapp2.WSGIApplication([
  ('/(guide/new)', FeatureNew),
  ('/(guide/edit)/([0-9]*)', ProcessOverview),
  # TODO(jrobbins): ('/(guide/delete)/([0-9]*)', FeatureDelete),
  ('/(guide/stage)/([0-9]*)/([0-9]*)', FeatureEditStage),
], debug=settings.DEBUG)
