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


BIGSTORE_BUCKET = '/gs/uma-dashboards/'
BIGSTORE_RESTFUL_URI = 'https://uma-dashboards.storage.googleapis.com/'
BIGSTORE_HISTOGRAM_ID = str(0xbfd59b316a6c31f1)

# For fetching files from the production BigStore during development.
OAUTH2_CREDENTIALS_FILENAME = os.path.join(
    settings.ROOT_DIR, 'scripts', 'oauth2.data')


class YesterdayHandler(blobstore_handlers.BlobstoreDownloadHandler):
  """Loads yesterday's UMA data from BigStore."""

  def _SaveData(self, data, yesterday):
    # Response format is "bucket-bucket+1=hits".
    # Example: 10-11=2175995,11-12=56635467,12-13=2432539420
    values_list = data['kTempHistograms'][BIGSTORE_HISTOGRAM_ID]['b'].split(',')

    #sum_total = int(data['kTempHistograms'][BIGSTORE_HISTOGRAM_ID]['s']) # TODO: use this.
    
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

    # Bucket 1 is total pages visited. We're guaranteed to have it.
    # TODO(ericbidelman): If we don't have it, don't set to 1!
    total_pages = properties_dict.get(1, 1)

    for bucket_id, num_hits in properties_dict.items():
      # If the id is not in the map, the name will be 'ERROR'.
      # TODO(ericbidelman): Probably better to leave non-matched bucket ids out.
      property_name = uma.CSS_PROPERTY_BUCKETS.get(bucket_id, 'ERROR')

      query = models.StableInstance.all()
      query.filter('bucket_id = ', bucket_id)
      query.filter('date =', yesterday)

      # Only add this entity if one doesn't already exist with the same
      # bucket_id and date.
      if query.count() > 0:
        continue

      # TODO(ericbidelman): Calculate a rolling average here
      # This will be done using a GQL query to grab information
      # for the past 6 days.
      # We average those past 6 days with the new day's data
      # and store the result in rolling_percentage

      entity = models.StableInstance(
          property_name=property_name,
          bucket_id=bucket_id,
          date=yesterday,
          hits=num_hits,
          total_pages=total_pages,
          day_percentage=float("%.2f" % (num_hits / total_pages))
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
      self._SaveData(data, yesterday)

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

  def __FullQualifyLink(self, param_name):
    link = self.request.get(param_name) or None
    if link:
      if not link.startswith('http'):
        link = db.Link('http://' + link)
      else:
        link = db.Link(link)
    return link

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

    feature = None
    if feature_id: # /admin/edit/1234
      f = models.Feature.get_by_id(long(feature_id))
      if f is None or (f and 'edit' not in path):
        return self.redirect('/admin/features/new')

      feature = f.format_for_edit()
    elif 'edit' in path:
      # /features/edit -> /features/new
      return self.redirect(self.request.path.replace('edit', 'new'))

    template_data = {
      'feature_form': models.FeatureForm(feature),
      'id': feature_id
    }

    self._add_common_template_values(template_data)

    self.render(data=template_data, template_path=os.path.join(path + '.html'))

  def post(self, path, feature_id=None):
    spec_link = self.__FullQualifyLink('spec_link')
    bug_url = self.__FullQualifyLink('bug_url')

    safari_views_link = self.__FullQualifyLink('safari_views_link')
    ff_views_link = self.__FullQualifyLink('ff_views_link')
    ie_views_link = self.__FullQualifyLink('ie_views_link')

    owners = self.request.get('owner') or []
    if owners:
      owners = [db.Email(x.strip()) for x in owners.split(',')]

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
        feature.shipped_milestone = self.request.get('shipped_milestone')
        feature.footprint = int(self.request.get('footprint'))
        feature.visibility = int(self.request.get('visibility'))
        feature.safari_views = int(self.request.get('safari_views'))
        feature.safari_views_link = safari_views_link
        feature.ff_views = int(self.request.get('ff_views'))
        feature.ff_views_link = ff_views_link
        feature.ie_views = int(self.request.get('ie_views'))
        feature.ie_views_link = ie_views_link
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
          shipped_milestone=self.request.get('shipped_milestone'),
          footprint=int(self.request.get('footprint')),
          visibility=int(self.request.get('visibility')),
          safari_views=int(self.request.get('safari_views')),
          safari_views_link=safari_views_link,
          ff_views=int(self.request.get('ff_views')),
          ff_views_link=ff_views_link,
          ie_views=int(self.request.get('ie_views')),
          ie_views_link=ie_views_link,
          prefixed=self.request.get('prefixed') == 'on',
          spec_link=spec_link,
          standardization=int(self.request.get('standardization')),
          comments=self.request.get('comments'),
          web_dev_views=int(self.request.get('web_dev_views')),
          )

    memcache.delete(models.Feature.MEMCACHE_KEY)

    # TODO(ericbidelman): Prevent memcache race condition where key isn't
    # deleted and we get stale data on the redirect.
    #time.sleep(1)

    if 'delete' in path:
      feature.delete()
      return # Bomb out early on delete. Don't want the extra redirect.
    else: 
      feature.put()

    return self.redirect('/features')


app = webapp2.WSGIApplication([
  ('/cron/metrics', YesterdayHandler),
  ('/(.*)/([0-9]*)', FeatureHandler),
  ('/(.*)', FeatureHandler),
], debug=settings.DEBUG)

