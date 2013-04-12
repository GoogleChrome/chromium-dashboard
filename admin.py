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

__author__ = ('ericbidelman@chromium.org (Eric Bidelman), '
              'kassycoan@google.com (Kassy Coan)')


import datetime
import json
import logging
import os
import sys
import webapp2

# Appengine imports.
from google.appengine.api import files
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

# File imports.
import common
import models
import settings
import uma


BIGSTORE_BUCKET = '/gs/uma-dashboards/'
BIGSTORE_RESTFUL_URI = 'https://uma-dashboards.storage.googleapis.com/'
BIGSTORE_HISTOGRAM_ID = str(0xb7f3cf359f13d209)

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

  def get(self, path):
    # feature = models.Feature(
    #         type=models.Resource.Type.ARTICLE, #TODO: use correct type for content.
    #         title=doc.title(),
    #         text=doc.summary(),#.decode('utf-8').decode('ascii','ignore'),
    #         publication_date=datetime.datetime.today(), #TODO: save real date.
    #         url=db.Link(result.final_url or url),
    #         #fetch_date=datetime.date.today(),
    #         #sharers
    #         )

    # Remove trailing slash from URL and redirect. e.g. /metrics/ -> /metrics
    if path[-1] == '/':
      return self.redirect('/' + path.rstrip('/'))

    template_file = path + '.html'
    template_data = {
      'feature_form': models.FeatureForm()
    }

    self.render(data=template_data, template_path=os.path.join(template_file))

app = webapp2.WSGIApplication([
  ('/cron/metrics', YesterdayHandler),
  ('/(.*)', FeatureHandler),
], debug=settings.DEBUG)

