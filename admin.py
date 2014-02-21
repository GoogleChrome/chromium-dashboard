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
import sys
import webapp2

# Appengine imports.
from google.appengine.api import files
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext.webapp import blobstore_handlers

# File imports.
import common
import models
import settings
import uma


# uma.googleplex.com/data/histograms/ids-chrome-histograms.txt
BIGSTORE_BUCKET = '/gs/uma-dashboards/'
BIGSTORE_RESTFUL_URI = 'https://uma-dashboards.storage.googleapis.com/'

CSSPROPERITES_BS_HISTOGRAM_ID = str(0xbfd59b316a6c31f1)
ANIMATIONPROPS_BS_HISTOGRAM_ID = str(0xbee14b73f4fdde73)
FEATURE_OBSERVER_BS_HISTOGRAM_ID = str(0x2e44945129413683)

# For fetching files from the production BigStore during development.
OAUTH2_CREDENTIALS_FILENAME = os.path.join(
    settings.ROOT_DIR, 'scripts', 'oauth2.data')


class YesterdayHandler(blobstore_handlers.BlobstoreDownloadHandler):
  """Loads yesterday's UMA data from BigStore."""

  MODEL_CLASS = {
    CSSPROPERITES_BS_HISTOGRAM_ID: models.StableInstance,
    ANIMATIONPROPS_BS_HISTOGRAM_ID: models.AnimatedProperty,
    FEATURE_OBSERVER_BS_HISTOGRAM_ID: models.FeatureObserver,
  }

  def _SaveData(self, data, yesterday, histogram_id):
    try:
      model_class = self.MODEL_CLASS[histogram_id]
    except Exception, e:
      logging.error('Invalid CSS property bucket id used: %s' % histogram_id)
      return

    # Response format is "bucket-bucket+1=hits".
    # Example: 10-11=2175995,11-12=56635467,12-13=2432539420
    #values_list = data['kTempHistograms'][CSSPROPERITES_BS_HISTOGRAM_ID]['b'].split(',')
    values_list = data['kTempHistograms'][histogram_id]['b'].split(',')

    #sum_total = int(data['kTempHistograms'][CSSPROPERITES_BS_HISTOGRAM_ID]['s']) # TODO: use this.

    # Stores a hit count for each CSS property (properties_dict[bucket] = hits).
    properties_dict = {}

    for val in values_list:
      bucket_range, hits_string = val.split('=') # e.g. "10-11=2175995"

      parts = bucket_range.split('-')

      beginning_range = int(parts[0])
      end_range = int(parts[1])

      # Range > 1 indicates malformed data. Skip it.
      if end_range - beginning_range > 1:
        continue

      # beginning_range is our bucket number; the stable CSSPropertyID.
      properties_dict[beginning_range] = int(hits_string)

    # For CSSPROPERITES_BS_HISTOGRAM_ID, bucket 1 is total pages visited for
    # stank rank histogram. We're guaranteed to have it.
    # For the FEATURE_OBSERVER_BS_HISTOGRAM_ID, the PageVisits bucket_id is 52
    # See uma.py. The actual % is calculated from the count / this number.
    # For ANIMATIONPROPS_BS_HISTOGRAM_ID, we have to calculate the total count.
    if 1 in properties_dict and histogram_id == CSSPROPERITES_BS_HISTOGRAM_ID:
      total_pages = properties_dict.get(1)
    elif (uma.PAGE_VISITS_BUCKET_ID in properties_dict and
          histogram_id == FEATURE_OBSERVER_BS_HISTOGRAM_ID):
      total_pages = properties_dict.get(uma.PAGE_VISITS_BUCKET_ID)

      # Don't include PageVisits results.
      del properties_dict[uma.PAGE_VISITS_BUCKET_ID]
    else:
      total_pages = sum(properties_dict.values())

    for bucket_id, num_hits in properties_dict.items():
      # If the id is not in the map, use 'ERROR' for the name.
      # TODO(ericbidelman): Non-matched bucket ids are likely new properties
      # that have been added and need to be updated in uma.py. Find way to
      # autofix these values with the appropriate property_name later.
      property_map = uma.CSS_PROPERTY_BUCKETS
      if histogram_id == FEATURE_OBSERVER_BS_HISTOGRAM_ID:
        property_map = uma.FEATUREOBSERVER_BUCKETS

      property_name = property_map.get(bucket_id, 'ERROR')

      query = model_class.all()
      query.filter('bucket_id = ', bucket_id)
      query.filter('date =', yesterday)

      # Only add this entity if one doesn't already exist with the same
      # bucket_id and date.
      if query.count() > 0:
        logging.info('Cron data was already fetched for this date')
        continue

      # TODO(ericbidelman): Calculate a rolling average here
      # This will be done using a GQL query to grab information
      # for the past 6 days.
      # We average those past 6 days with the new day's data
      # and store the result in rolling_percentage

      entity = model_class(
          property_name=property_name,
          bucket_id=bucket_id,
          date=yesterday,
          #hits=num_hits,
          #total_pages=total_pages,
          day_percentage=(num_hits * 1.0 / total_pages)
          #rolling_percentage=
          )
      entity.put()

  def get(self):
    """Loads the data file located at |filename|.

    Args:
      filename: The filename for the data file to be loaded.
    """
    yesterday = datetime.date.today() - datetime.timedelta(1)
    yesterday_formatted = yesterday.strftime("%Y.%m.%d")

    filename = 'histograms/daily/%s/Everything' % (yesterday_formatted)

    if settings.PROD:
      try:
        with files.open(BIGSTORE_BUCKET + filename, 'r') as unused_f:
          pass
      except files.file.ExistenceError, e:
        self.response.write(e)
        return

      # The file exists; serve it.
      blob_key = blobstore.create_gs_key(BIGSTORE_BUCKET + filename)
      blob_reader = blobstore.BlobReader(blob_key, buffer_size=3510000)
      try:
        result = blob_reader.read()
      finally:
        blob_reader.close()
    else:
      # From the development server, use the RESTful API to read files from the
      # production BigStore instance, rather than needing to stage them to the
      # local BigStore instance.
      result, response_code = self._FetchFromBigstoreREST(filename)

      if response_code != 200:
        self.error(response_code)
        self.response.out.write(
            ('%s - Error doing BigStore API request. '
             'Try refreshing your OAuth token?' % response_code))
        return

    if result:
      data = json.loads(result)

      for bucket_id in self.MODEL_CLASS.keys():
        self._SaveData(data, yesterday, bucket_id)

  def _FetchFromBigstoreREST(self, filename):
    # Read the OAuth2 access token from disk.
    try:
      with open(OAUTH2_CREDENTIALS_FILENAME, 'r') as f:
        credentials_json = json.load(f)
    except IOError, e:
      logging.error(e)
      return [None, 404]

    # Attempt to fetch the file from the production BigStore instance.
    url = BIGSTORE_RESTFUL_URI + filename

    headers = {
        'x-goog-api-version': '2',
        'Authorization': 'OAuth ' + credentials_json.get('access_token', '')
        }
    result = urlfetch.fetch(url, headers=headers)
    return (result.content, result.status_code)


class FeatureHandler(common.ContentHandler):

  DEFAULT_URL = '/features'
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

  def get(self, path, feature_id=None):
    # Remove trailing slash from URL and redirect. e.g. /metrics/ -> /metrics
    if path[-1] == '/':
      return self.redirect(self.request.path.rstrip('/'))

    # TODO(ericbidelman): This creates a additional call to
    # _is_user_whitelisted() (also called in common.py), resulting in another
    # db query.
    if not self._is_user_whitelisted(users.get_current_user()):
      #TODO(ericbidelman): Use render(status=401) instead.
      #self.render(data={}, template_path=os.path.join(path + '.html'), status=401)
      common.handle_401(self.request, self.response, Exception)
      return

    if not feature_id and not 'new' in path:
      # /features/edit|launch -> /features/new
      return self.redirect(self.ADD_NEW_URL)
    elif feature_id and 'new' in path:
      return self.redirect(self.ADD_NEW_URL)

    feature = None

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
    spec_link = self.__FullQualifyLink('spec_link')
    bug_url = self.__FullQualifyLink('bug_url')

    ff_views_link = self.__FullQualifyLink('ff_views_link')
    ie_views_link = self.__FullQualifyLink('ie_views_link')
    safari_views_link = self.__FullQualifyLink('safari_views_link')

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

    redirect_url = self.DEFAULT_URL

    # Update/delete existing feature.
    if feature_id: # /admin/edit/1234
      feature = models.Feature.get_by_id(long(feature_id))
      if feature is None:
        return self.redirect(self.request.path)

      if not 'delete' in path:
        feature.category = int(self.request.get('category'))
        feature.name = self.request.get('name')
        feature.summary = self.request.get('summary')
        feature.owner = owners
        feature.bug_url = bug_url
        feature.impl_status_chrome = int(self.request.get('impl_status_chrome'))
        feature.shipped_milestone = shipped_milestone
        feature.shipped_android_milestone = shipped_android_milestone
        feature.shipped_ios_milestone = shipped_ios_milestone
        feature.shipped_webview_milestone = shipped_webview_milestone
        feature.shipped_opera_milestone = shipped_opera_milestone
        feature.shipped_opera_android_milestone = shipped_opera_android_milestone
        feature.footprint = int(self.request.get('footprint'))
        feature.visibility = int(self.request.get('visibility'))
        feature.ff_views = int(self.request.get('ff_views'))
        feature.ff_views_link = ff_views_link
        feature.ie_views = int(self.request.get('ie_views'))
        feature.ie_views_link = ie_views_link
        feature.safari_views = int(self.request.get('safari_views'))
        feature.safari_views_link = safari_views_link
        feature.prefixed = self.request.get('prefixed') == 'on'
        feature.spec_link = spec_link
        feature.standardization = int(self.request.get('standardization'))
        feature.comments = self.request.get('comments')
        feature.web_dev_views = int(self.request.get('web_dev_views'))
    else:
      feature = models.Feature(
          category=int(self.request.get('category')),
          name=self.request.get('name'),
          summary=self.request.get('summary'),
          owner=owners,
          bug_url=bug_url,
          impl_status_chrome=int(self.request.get('impl_status_chrome')),
          shipped_milestone=shipped_milestone,
          shipped_android_milestone=shipped_android_milestone,
          shipped_ios_milestone=shipped_ios_milestone,
          shipped_webview_milestone=shipped_webview_milestone,
          shipped_opera_milestone=shipped_opera_milestone,
          shipped_opera_android_milestone=shipped_opera_android_milestone,
          footprint=int(self.request.get('footprint')),
          visibility=int(self.request.get('visibility')),
          ff_views=int(self.request.get('ff_views')),
          ff_views_link=ff_views_link,
          ie_views=int(self.request.get('ie_views')),
          ie_views_link=ie_views_link,
          safari_views=int(self.request.get('safari_views')),
          safari_views_link=safari_views_link,
          prefixed=self.request.get('prefixed') == 'on',
          spec_link=spec_link,
          standardization=int(self.request.get('standardization')),
          comments=self.request.get('comments'),
          web_dev_views=int(self.request.get('web_dev_views')),
          )

    if 'delete' in path:
      feature.delete()
      memcache.flush_all()
      return # Bomb out early for AJAX delete. No need for extra redirect below.
    else:
      key = feature.put()

      # TODO(ericbidelman): enumerate and remove only the relevant keys.
      memcache.flush_all()

      params = []
      if self.request.get('create_launch_bug') == 'on':
        params.append(self.LAUNCH_PARAM)
      if self.request.get('intent_to_implement') == 'on':
        params.append(self.INTENT_PARAM)

      if len(params):
        redirect_url = '%s/%s?%s' % (self.LAUNCH_URL, key.id(),
                                     '&'.join(params))

    return self.redirect(redirect_url)


app = webapp2.WSGIApplication([
  ('/cron/metrics', YesterdayHandler),
  ('/(.*)/([0-9]*)', FeatureHandler),
  ('/(.*)', FeatureHandler),
], debug=settings.DEBUG)

