from __future__ import division
from __future__ import print_function

# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc.
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

__author__ = 'ericbidelman@chromium.org (Eric Bidelman)'


import datetime
import json
import logging
import os
import re
import sys
import webapp2
from bs4 import BeautifulSoup
from HTMLParser import HTMLParser
from xml.dom import minidom

# Appengine imports.
import cloudstorage
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.api import taskqueue
from google.appengine.ext.webapp import blobstore_handlers

# File imports.
import common
import models
import settings

UMA_QUERY_SERVER = 'https://uma-export.appspot.com/chromestatus/'

HISTOGRAMS_URL = 'https://chromium.googlesource.com/chromium/src/+/master/' \
    'tools/metrics/histograms/enums.xml?format=TEXT'

# Path to a local cookie to supply when running dev_appserver
# Go to https://uma-export.appspot.com/login and login then copy the
# value of SACSID from browser and write this to a cookie file.
COOKIE_FILENAME = os.path.join(settings.ROOT_DIR, 'cookie')


def _FetchWithCookie(url):
  if settings.PROD:
    # follow_redirects=False according to https://cloud.google.com/appengine/docs/python/appidentity/#asserting_identity_to_other_app_engine_apps
    return urlfetch.fetch(url, deadline=60, follow_redirects=False)
  try:
    with open(COOKIE_FILENAME, 'r') as f:
      cookie = f.readline()
  except IOError, e:
    logging.error(e)
  return urlfetch.fetch(
      url, headers={'cookie': 'SACSID=' + cookie}, deadline=60)


class UmaQuery(object):
  """Reads and stores stats from UMA."""

  def __init__(self, query_name, model_class, property_map_class):
    self.query_name = query_name
    self.model_class = model_class
    self.property_map_class = property_map_class

  def _FetchData(self, date):
    params = '?date=%s' % date.strftime('%Y%m%d')
    url = UMA_QUERY_SERVER + self.query_name + params
    result = _FetchWithCookie(url)

    if (result.status_code != 200):
      logging.error('Unable to retrieve UMA data from %s. Error: %s' % (url, result.status_code))
      return (None, 404)

    json_content = result.content.split('\n', 1)[1]
    j = json.loads(json_content)
    if not j.has_key('r'):
      logging.error(
          '%s results do not have an "r" key in the response' % self.query_name)
      return (None, 404)
    return (j['r'], result.status_code)

  def _SaveData(self, data, date):
    property_map = self.property_map_class.get_all()

    for bucket_str, bucket_dict in data.iteritems():
      bucket_id = int(bucket_str)

      query = self.model_class.all()
      query.filter('bucket_id = ', bucket_id)
      query.filter('date =', date)

      # Only add this entity if one doesn't already exist with the same
      # bucket_id and date.
      if query.count() > 0:
        logging.info('Cron data was already fetched for this date')
        continue

      # If the id is not in the map, use 'ERROR' for the name.
      # TODO(ericbidelman): Non-matched bucket ids are likely new properties
      # that have been added and will be updated in cron/histograms.
      property_name = property_map.get(bucket_id, 'ERROR')

      entity = self.model_class(
          property_name=property_name,
          bucket_id=bucket_id,
          date=date,
          #hits=num_hits,
          #total_pages=total_pages,
          day_percentage=bucket_dict['rate']
          #day_milestone=bucket_dict['milestone']
          #low_volume=bucket_dict['low_volume']
          #rolling_percentage=
          )
      entity.put()

  def FetchAndSaveData(self, date):
    data, response_code = self._FetchData(date)
    if response_code == 200:
      self._SaveData(data, date)
    return response_code


UMA_QUERIES = [
  UmaQuery(query_name='usecounter.features',
           model_class=models.FeatureObserver,
           property_map_class=models.FeatureObserverHistogram),
  UmaQuery(query_name='usecounter.cssproperties',
           model_class=models.StableInstance,
           property_map_class=models.CssPropertyHistogram),
  UmaQuery(query_name='usecounter.animatedcssproperties',
           model_class=models.AnimatedProperty,
           property_map_class=models.CssPropertyHistogram),
]


class YesterdayHandler(webapp2.RequestHandler):
  """Loads yesterday's UMA data."""
  def get(self):
    """Loads the data file located at |filename|.

    Args:
      filename: The filename for the data file to be loaded.
    """
    yesterday = datetime.date.today() - datetime.timedelta(1)

    for query in UMA_QUERIES:
      response_code = query.FetchAndSaveData(yesterday)
      if response_code != 200:
        self.error(response_code)
        self.response.out.write(
            ('%s - Error fetching usage data' % response_code))


class HistogramsHandler(webapp2.RequestHandler):

  MODEL_CLASS = {
    'FeatureObserver': models.FeatureObserverHistogram,
    'MappedCSSProperties': models.CssPropertyHistogram,
  }

  def _SaveData(self, data, histogram_id):
    try:
      model_class = self.MODEL_CLASS[histogram_id]
    except Exception:
      logging.error('Invalid Histogram id used: %s' % histogram_id)
      return

    bucket_id = int(data['bucket_id'])
    property_name = data['property_name']
    key_name = '%s_%s' % (bucket_id, property_name)

    # Bucket ID 1 is reserved for number of CSS Pages Visited. So don't add it.
    if (model_class == models.CssPropertyHistogram and bucket_id == 1):
      return

    model_class.get_or_insert(key_name,
      bucket_id=bucket_id,
      property_name=property_name
    )

  def get(self):
    # Attempt to fetch enums mapping file.
    result = urlfetch.fetch(HISTOGRAMS_URL, deadline=60)

    if (result.status_code != 200):
      logging.error('Unable to retrieve chromium histograms mapping file.')
      return

    histograms_content = result.content.decode('base64')
    dom = minidom.parseString(histograms_content)

    # The enums.xml file looks like this:
    # <enum name="FeatureObserver">
    #   <int value="0" label="OBSOLETE_PageDestruction"/>
    #   <int value="1" label="LegacyNotifications"/>

    enum_tags = dom.getElementsByTagName('enum')

    # Save bucket ids for each histogram type, FeatureObserver and MappedCSSProperties.
    for histogram_id in self.MODEL_CLASS.keys():
      enum = filter(lambda enum: enum.attributes['name'].value == histogram_id, enum_tags)[0]
      for child in enum.getElementsByTagName('int'):
        self._SaveData({
          'bucket_id': child.attributes['value'].value,
          'property_name': child.attributes['label'].value
        }, histogram_id)



class FeatureHandler(common.ContentHandler):

  DEFAULT_URL = '/feature'
  ADD_NEW_URL = '/admin/features/new'
  EDIT_URL = '/admin/features/edit'
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

  def __get_blink_component_from_bug(self, blink_components, bug_url):
    if blink_components[0] == models.BlinkComponent.DEFAULT_COMPONENT and bug_url:
      result = urlfetch.fetch(bug_url)
      if result.status_code == 200:
        soup = BeautifulSoup(result.content, 'html.parser')
        components = soup.find_all(string=re.compile('^Blink'))

        h = HTMLParser()
        return [h.unescape(unicode(c)) for c in components]
    return blink_components

  def get(self, path, feature_id=None):
    user = users.get_current_user()
    if user is None:
      if feature_id:
        # Redirect to public URL for unauthenticated users.
        return self.redirect(self.DEFAULT_URL + '/' + feature_id)
      else:
        return self.redirect(users.create_login_url(self.request.uri))

    # Remove trailing slash from URL and redirect. e.g. /metrics/ -> /metrics
    if path[-1] == '/':
      return self.redirect(self.request.path.rstrip('/'))

    # TODO(ericbidelman): This creates a additional call to
    # _is_user_whitelisted() (also called in common.py), resulting in another
    # db query.
    if not self._is_user_whitelisted(user):
      #TODO(ericbidelman): Use render(status=401) instead.
      #self.render(data={}, template_path=os.path.join(path + '.html'), status=401)
      common.handle_401(self.request, self.response, Exception)
      return

    if not feature_id and not 'new' in path:
      # /features/edit|launch -> /features/new
      return self.redirect(self.ADD_NEW_URL)
    elif feature_id and 'new' in path:
      return self.redirect(self.ADD_NEW_URL)

    template_data = {
        'feature_form': models.FeatureForm()
        }

    if feature_id:
      f = models.Feature.get_by_id(long(feature_id))
      if f is None:
        return self.redirect(self.ADD_NEW_URL)

      # Provide new or populated form to template.
      template_data.update({
          'feature': f.format_for_template(),
          'feature_form': models.FeatureForm(f.format_for_edit()),
          'default_url': '%s://%s%s/%s' % (self.request.scheme, self.request.host,
                                           self.DEFAULT_URL, feature_id),
          'edit_url': '%s://%s%s/%s' % (self.request.scheme, self.request.host,
                                        self.EDIT_URL, feature_id)
          })

    if self.LAUNCH_PARAM in self.request.params:
      template_data[self.LAUNCH_PARAM] = True
    if self.INTENT_PARAM in self.request.params:
      template_data[self.INTENT_PARAM] = True

    self._add_common_template_values(template_data)

    self.render(data=template_data, template_path=os.path.join(path + '.html'))

  def post(self, path, feature_id=None):
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

    try:
      intent_stage = int(self.request.get('intent_stage'))
    except:
      logging.error('Invalid intent_stage \'{}\'' \
                    .format(self.request.get('intent_stage')))

      # Default the intent stage to 1 (Prototype) if we failed to get a valid
      # intent stage from the request. This should be removed once we
      # understand what causes this.
      intent_stage = 1

    if feature_id: # /admin/edit/1234
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
      feature.experiment_goal = self.request.get('experiment_goal')
      feature.experiment_timeline = self.request.get('experiment_timeline')
      feature.experiment_risks = self.request.get('experiment_risks')
      feature.experiment_extension_reason = self.request.get('experiment_extension_reason')
      feature.ongoing_constraints = self.request.get('ongoing_constraints')
    else:
      # Check bug for existing blink component(s) used to label the bug. If
      # found, use the first component name instead of the generic "Blink" name.
      try:
        blink_components = self.__get_blink_component_from_bug(blink_components, bug_url)
      except Exception:
        pass

      feature = models.Feature(
          category=int(self.request.get('category')),
          name=self.request.get('name'),
          intent_stage=intent_stage,
          summary=self.request.get('summary'),
          intent_to_implement_url=intent_to_implement_url,
          origin_trial_feedback_url=origin_trial_feedback_url,
          motivation=self.request.get('motivation'),
          explainer_links=explainer_links,
          owner=owners,
          bug_url=bug_url,
          blink_components=blink_components,
          impl_status_chrome=int(self.request.get('impl_status_chrome')),
          shipped_milestone=shipped_milestone,
          shipped_android_milestone=shipped_android_milestone,
          shipped_ios_milestone=shipped_ios_milestone,
          shipped_webview_milestone=shipped_webview_milestone,
          shipped_opera_milestone=shipped_opera_milestone,
          shipped_opera_android_milestone=shipped_opera_android_milestone,
          interop_compat_risks=self.request.get('interop_compat_risks'),
          ergonomics_risks=self.request.get('ergonomics_risks'),
          activation_risks=self.request.get('activation_risks'),
          security_risks=self.request.get('security_risks'),
          debuggability=self.request.get('debuggability'),
          all_platforms=self.request.get('all_platforms') == 'on',
          all_platforms_descr=self.request.get('all_platforms_descr'),
          wpt=self.request.get('wpt') == 'on',
          wpt_descr=self.request.get('wpt_descr'),
          footprint=int(self.request.get('footprint')),
          visibility=int(self.request.get('visibility')),
          ff_views=int(self.request.get('ff_views')),
          ff_views_link=ff_views_link,
          ff_views_notes=self.request.get('ff_views_notes'),
          ie_views=int(self.request.get('ie_views')),
          ie_views_link=ie_views_link,
          ie_views_notes=self.request.get('ie_views_notes'),
          safari_views=int(self.request.get('safari_views')),
          safari_views_link=safari_views_link,
          safari_views_notes=self.request.get('safari_views_notes'),
          web_dev_views=int(self.request.get('web_dev_views')),
          web_dev_views_link=web_dev_views_link,
          web_dev_views_notes=self.request.get('web_dev_views_notes'),
          prefixed=self.request.get('prefixed') == 'on',
          spec_link=spec_link,
          tag_review=self.request.get('tag_review'),
          standardization=int(self.request.get('standardization')),
          doc_links=doc_links,
          sample_links=sample_links,
          search_tags=search_tags,
          comments=self.request.get('comments'),
          experiment_goal=self.request.get('experiment_goal'),
          experiment_timeline=self.request.get('experiment_timeline'),
          experiment_risks=self.request.get('experiment_risks'),
          experiment_extension_reason=self.request.get('experiment_extension_reason'),
          ongoing_constraints=self.request.get('ongoing_constraints'),
          )

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


class BlinkComponentHandler(webapp2.RequestHandler):
  """Updates the list of Blink components in the db."""
  def get(self):
    models.BlinkComponent.update_db()
    self.response.out.write('Blink components updated')


app = webapp2.WSGIApplication([
  ('/cron/metrics', YesterdayHandler),
  ('/cron/histograms', HistogramsHandler),
  ('/cron/update_blink_components', BlinkComponentHandler),
  ('/(.*)/([0-9]*)', FeatureHandler),
  ('/(.*)', FeatureHandler),
], debug=settings.DEBUG)
