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


# Forms to be used for each stage of the process.
STAGE_FORMS = {
    models.INTENT_NONE: guideforms.Incubate,
    models.INTENT_IMPLEMENT: guideforms.Prototype,
    models.INTENT_EXPERIMENT: guideforms.DevTrial,
    models.INTENT_EXTEND_TRIAL: guideforms.OriginTrial,
}


class FeatureNew(common.ContentHandler):

  def get(self, path):
    user = users.get_current_user()
    if user is None:
      return self.redirect(users.create_login_url(self.request.uri))

    if not self._is_user_whitelisted(user):
      common.handle_401(self.request, self.response, Exception)
      return

    template_data = {
        'overview_form': guideforms.OverviewForm(),
        }

    self._add_common_template_values(template_data)

    self.render(data=template_data, template_path=os.path.join(path + '.html'))

  def post(self, path):
    user = users.get_current_user()
    if user is None or (user and not self._is_user_whitelisted(user)):
      common.handle_401(self.request, self.response, Exception)
      return

    feature = models.Feature(
        category=int(self.request.get('category')),
        name=self.request.get('name'),
        intent_stage=models.INTENT_NONE,
        summary=self.request.get('summary'),
        impl_status_chrome=models.NO_ACTIVE_DEV,
        visibility=models.WARRANTS_ARTICLE,
        standardization=models.EDITORS_DRAFT,
        web_dev_views=models.DEV_NO_SIGNALS)
    key = feature.put()

    # TODO(ericbidelman): enumerate and remove only the relevant keys.
    memcache.flush_all()

    redirect_url = '/guide/edit/' + str(key.id())
    return self.redirect(redirect_url)


class ProcessOverview(common.ContentHandler):

  def get(self, path, feature_id):
    user = users.get_current_user()
    if user is None:
      # Redirect to public URL for unauthenticated users.
      return self.redirect(self.DEFAULT_URL + '/' + feature_id)

    # TODO(ericbidelman): This creates a additional call to
    # _is_user_whitelisted() (also called in common.py), resulting in another
    # db query.
    if not self._is_user_whitelisted(user):
      common.handle_401(self.request, self.response, Exception)
      return

    template_data = {
        'overview_form': guideforms.OverviewForm(),
        'process_json': json.dumps(
            [stage._asdict() for stage in processes.BLINK_PROCESS]),
        'progress_so_far': [],
        }

    f = models.Feature.get_by_id(long(feature_id))
    if f is None:
      return self.redirect(self.ADD_NEW_URL)

    progress_so_far = []  # An unordered list of progress item strings.
    # TODO(jrobbins): Replace this constant with a call to apply a bunch
    # of tiny functions to detect each bit of progress.
    progress_so_far = ['Explainer', 'API design']

    # Provide new or populated form to template.
    template_data.update({
        'feature': f,
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
    user = users.get_current_user()
    if user is None:
      # Redirect to public URL for unauthenticated users.
      return self.redirect(self.DEFAULT_URL + '/' + feature_id)

    if not self._is_user_whitelisted(user):
      common.handle_401(self.request, self.response, Exception)
      return

    template_data = {
        }

    f = models.Feature.get_by_id(long(feature_id))
    if f is None:
      return self.redirect(self.ADD_NEW_URL)

    detail_form_class = STAGE_FORMS.get(int(stage_id), models.FeatureForm)

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

    spec_link = self.__FullQualifyLink('spec_link')

    explainer_links = self.request.get('explainer_links') or []
    if explainer_links:
      explainer_links = filter(bool, [x.strip() for x in re.split('\\r?\\n', explainer_links)])

    bug_url = self.__FullQualifyLink('bug_url')
    intent_to_implement_url = self.__FullQualifyLink('intent_to_implement_url')
    origin_trial_feedback_url = self.__FullQualifyLink('origin_trial_feedback_url')

    ff_views_link = self.__FullQualifyLink('ff_views_link')
    ie_views_link = self.__FullQualifyLink('ie_views_link')
    safari_views_link = self.__FullQualifyLink('safari_views_link')
    web_dev_views_link = self.__FullQualifyLink('web_dev_views_link')

    # Cast incoming milestones to ints.
    # TODO(jrobbins): Consider supporting milestones that are not ints.
    shipped_milestone = self.__ToInt('shipped_milestone')
    shipped_android_milestone = self.__ToInt('shipped_android_milestone')
    shipped_ios_milestone = self.__ToInt('shipped_ios_milestone')
    shipped_webview_milestone = self.__ToInt('shipped_webview_milestone')
    shipped_opera_milestone = self.__ToInt('shipped_opera_milestone')
    shipped_opera_android_milestone = self.__ToInt('shipped_opera_android_milestone')

    owners = self.request.get('owner') or []
    if owners:
      owners = [db.Email(x.strip()) for x in owners.split(',')]

    doc_links = self.request.get('doc_links') or []
    if doc_links:
      doc_links = filter(bool, [x.strip() for x in re.split('\\r?\\n', doc_links)])

    sample_links = self.request.get('sample_links') or []
    if sample_links:
      sample_links = filter(bool, [x.strip() for x in re.split('\\r?\\n', sample_links)])

    search_tags = self.request.get('search_tags') or []
    if search_tags:
      search_tags = filter(bool, [x.strip() for x in search_tags.split(',')])

    blink_components = self.request.get('blink_components') or models.BlinkComponent.DEFAULT_COMPONENT
    if blink_components:
      blink_components = filter(bool, [x.strip() for x in blink_components.split(',')])

    devrel = self.request.get('devrel') or []
    if devrel:
      devrel = [db.Email(x.strip()) for x in devrel.split(',')]

    try:
      intent_stage = int(self.request.get('intent_stage'))
    except:
      logging.error('Invalid intent_stage \'{}\'' \
                    .format(self.request.get('intent_stage')))

      # Default the intent stage to 1 (Prototype) if we failed to get a valid
      # intent stage from the request. This should be removed once we
      # understand what causes this.
      intent_stage = 1

    if feature_id: # /guide/edit/1234
      feature = models.Feature.get_by_id(long(feature_id))

      if feature is None:
        return self.redirect(self.request.path)

      if 'delete' in path:
        feature.delete()
        memcache.flush_all()
        return # Bomb out early for AJAX delete. No need to redirect.

      # Update properties of existing feature.
      feature.category = int(self.request.get('category'))
      feature.name = self.request.get('name')
      feature.intent_stage = intent_stage
      feature.summary = self.request.get('summary')
      feature.intent_to_implement_url = intent_to_implement_url
      feature.origin_trial_feedback_url = origin_trial_feedback_url
      feature.motivation = self.request.get('motivation')
      feature.explainer_links = explainer_links
      feature.owner = owners
      feature.bug_url = bug_url
      feature.blink_components = blink_components
      feature.devrel = devrel
      feature.impl_status_chrome = int(self.request.get('impl_status_chrome'))
      feature.shipped_milestone = shipped_milestone
      feature.shipped_android_milestone = shipped_android_milestone
      feature.shipped_ios_milestone = shipped_ios_milestone
      feature.shipped_webview_milestone = shipped_webview_milestone
      feature.shipped_opera_milestone = shipped_opera_milestone
      feature.shipped_opera_android_milestone = shipped_opera_android_milestone
      feature.footprint = int(self.request.get('footprint'))
      feature.interop_compat_risks = self.request.get('interop_compat_risks')
      feature.ergonomics_risks = self.request.get('ergonomics_risks')
      feature.activation_risks = self.request.get('activation_risks')
      feature.security_risks = self.request.get('security_risks')
      feature.debuggability = self.request.get('debuggability')
      feature.all_platforms = self.request.get('all_platforms') == 'on'
      feature.all_platforms_descr = self.request.get('all_platforms_descr')
      feature.wpt = self.request.get('wpt') == 'on'
      feature.wpt_descr = self.request.get('wpt_descr')
      feature.visibility = int(self.request.get('visibility'))
      feature.ff_views = int(self.request.get('ff_views'))
      feature.ff_views_link = ff_views_link
      feature.ff_views_notes = self.request.get('ff_views_notes')
      feature.ie_views = int(self.request.get('ie_views'))
      feature.ie_views_link = ie_views_link
      feature.ie_views_notes = self.request.get('ie_views_notes')
      feature.safari_views = int(self.request.get('safari_views'))
      feature.safari_views_link = safari_views_link
      feature.safari_views_notes = self.request.get('safari_views_notes')
      feature.web_dev_views = int(self.request.get('web_dev_views'))
      feature.web_dev_views_link = web_dev_views_link
      feature.web_dev_views_notes = self.request.get('web_dev_views_notes')
      feature.prefixed = self.request.get('prefixed') == 'on'
      feature.spec_link = spec_link
      feature.tag_review = self.request.get('tag_review')
      feature.standardization = int(self.request.get('standardization'))
      feature.doc_links = doc_links
      feature.sample_links = sample_links
      feature.search_tags = search_tags
      feature.comments = self.request.get('comments')
      feature.experiment_goals = self.request.get('experiment_goals')
      feature.experiment_timeline = self.request.get('experiment_timeline')
      feature.experiment_risks = self.request.get('experiment_risks')
      feature.experiment_extension_reason = self.request.get('experiment_extension_reason')
      feature.ongoing_constraints = self.request.get('ongoing_constraints')

    params = []
    if self.request.get('create_launch_bug') == 'on':
      params.append(self.LAUNCH_PARAM)
    if self.request.get('intent_to_implement') == 'on':
      params.append(self.INTENT_PARAM)

      feature.intent_template_use_count += 1

    key = feature.put()

    # TODO(ericbidelman): enumerate and remove only the relevant keys.
    memcache.flush_all()

    redirect_url = '/feature/' + str(key.id())

    if len(params):
      redirect_url = '%s/%s?%s' % (self.LAUNCH_URL, key.id(),
                                   '&'.join(params))

    return self.redirect(redirect_url)


app = webapp2.WSGIApplication([
  ('/(guide/new)', FeatureNew),
  ('/(guide/edit)/([0-9]*)', ProcessOverview),
  ('/(guide/stage)/([0-9]*)/([0-9]*)', FeatureEditStage),
], debug=settings.DEBUG)
