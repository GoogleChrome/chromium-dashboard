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

import base64
import datetime
import json
import logging
from xml.dom import minidom
import requests

from google.auth.transport import requests as reqs
import google.oauth2.id_token

from framework import basehandlers
from framework import rediscache
from framework import utils
from internals import metrics_models
from internals import user_models
import settings


UMA_QUERY_SERVER = 'https://uma-export.appspot.com/chromestatus/'

HISTOGRAMS_URL = 'https://chromium.googlesource.com/chromium/src/+/main/' \
    'tools/metrics/histograms/enums.xml?format=TEXT'

# After we have processed all metrics data for a given kind on a given day,
# we create a capstone entry with this otherwise unused bucket_id.  Later
# we check for a capstone entry to avoid retrieving metrics for that
# same day again.
CAPSTONE_BUCKET_ID = -1


@utils.retry(3, delay=30, backoff=2)
def _FetchMetrics(url):
  if settings.PROD or settings.STAGING:
    # follow_redirects=False according to
    # https://cloud.google.com/appengine/docs/python/appidentity/#asserting_identity_to_other_app_engine_apps
    # GAE request limit is 60s, but it could go longer due to start-up latency.
    logging.info('Requesting metrics from: %r', url)
    token = google.oauth2.id_token.fetch_id_token(reqs.Request(), url)
    logging.info('token is %r', token)
    return requests.request(
        'GET', url, timeout=120.0, allow_redirects=False,
        headers={'Authorization': 'Bearer {}'.format(token)})
  else:
    logging.info('Prod would get metrics from: %r', url)
    return None  # dev instances cannot access uma-export.


class UmaQuery(object):
  """Reads and stores stats from UMA."""

  def __init__(self, query_name, model_class, property_map_class):
    self.query_name = query_name
    self.model_class = model_class
    self.property_map_class = property_map_class

  def _HasCapstone(self, date):
    query = self.model_class.query()
    query = query.filter(self.model_class.bucket_id == CAPSTONE_BUCKET_ID)
    query = query.filter(self.model_class.date == date)
    if query.count() > 0:
      logging.info('Found existing capstone entry for %r', date)
      return True
    else:
      logging.info('No capstone entry for %r, will request', date)
      return False

  def _SetCapstone(self, date):
    entity = self.model_class(
        property_name='capstone value',
        bucket_id=CAPSTONE_BUCKET_ID,
        date=date)
    entity.put()
    logging.info('Set capstone entry for %r', date)
    return entity

  def _FetchData(self, date):
    params = '?date=%s' % date.strftime('%Y%m%d')
    url = UMA_QUERY_SERVER + self.query_name + params
    result = _FetchMetrics(url)

    if not result or result.status_code != 200:
      logging.error('Unable to retrieve UMA data from %s. Error: %s' % (
          url, result.status_code))
      return (None, result.status_code)

    full_response_content = result.content.decode()
    logging.info('full response: %r',
                 full_response_content[:settings.MAX_LOG_LINE])
    # Skip XSSI protection line.
    json_content = full_response_content.split('\n', 1)[1]
    j = json.loads(json_content)
    for key, val in j.items():
      logging.info('key: %r', key)
      logging.info('val: %r', repr(val)[:settings.MAX_LOG_LINE])
    if 'r' not in j or not j['r']:
      logging.info('Note: uma-export can take 2 days to produce metrics')
      return (None, 404)
    if 'e' in j:
      logging.error('uma-export gave an error message: %r', j['e'])
      return (None, 404)
    return (j['r'], result.status_code)

  def _SaveData(self, data, date):
    property_map = self.property_map_class.get_all()

    date_query = self.model_class.query()
    date_query = date_query.filter(self.model_class.date == date)
    existing_saved_data = date_query.fetch(None)
    existing_saved_bucket_ids = set()
    for existing_datapoint in existing_saved_data:
      existing_saved_bucket_ids.add(existing_datapoint.bucket_id)

    for bucket_str, bucket_dict in data.items():
      bucket_id = int(bucket_str)

      # Only add this entity if one doesn't already exist with the same
      # bucket_id and date.
      if bucket_id in existing_saved_bucket_ids:
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

    self._SetCapstone(date)

  def FetchAndSaveData(self, date):
    if self._HasCapstone(date):
      return 200
    data, response_code = self._FetchData(date)
    if response_code == 200:
      self._SaveData(data, date)
    return response_code


UMA_QUERIES = [
  UmaQuery(query_name='usecounter.features',
           model_class=metrics_models.FeatureObserver,
           property_map_class=metrics_models.FeatureObserverHistogram),
  UmaQuery(query_name='usecounter.cssproperties',
           model_class=metrics_models.StableInstance,
           property_map_class=metrics_models.CssPropertyHistogram),
  UmaQuery(query_name='usecounter.animatedcssproperties',
           model_class=metrics_models.AnimatedProperty,
           property_map_class=metrics_models.CssPropertyHistogram),
]


class YesterdayHandler(basehandlers.FlaskHandler):
  """Loads yesterday's UMA data."""

  def get_template_data(self, **kwargs):
    """Loads the data file located at |filename|.

    Args:
      filename: The filename for the data file to be loaded.
      today: date passed in for testing, defaults to today.
    """
    self.require_cron_header()
    days = []
    date_str = self.request.args.get('date')
    if date_str:
      try:
        # We accept the same format that is used by uma-export
        specified_day = datetime.datetime.strptime(date_str, '%Y%m%d').date()
        days.append(specified_day)
      except ValueError:
        self.abort(400, msg='Failed to parse date string.')

    else:
      today = kwargs.get('today', datetime.date.today())
      days = [today - datetime.timedelta(days_ago)
              for days_ago in [1, 2, 3, 4, 5]]

    for i, query_day in enumerate(days):
      for query in UMA_QUERIES:
        response_code = query.FetchAndSaveData(query_day)
        if response_code not in (200, 404):
          error_message = (
              'Got error %d while fetching usage data' % response_code)
          if i > 2:
            logging.error(
                'WebStatusAlert-1: Failed to get metrics even after 2 days')
          return error_message, 500

    # The code above calls FetchAndSaveData() which calls _SaveData(),
    # which calls put() a bunch of times to add a new entity for each metrics datapoint.
    # Separately, when a request comes in get get metrics data, the file api/metricsdata.py
    # does a query on those datapoints and caches the result. If we don't invalidate when
    # we add datapoints, the cached query result will be lacking the new datapoints.
    # This is run once every 6 hours.
    rediscache.delete_keys_with_prefix('metrics')
    return 'Success'


class HistogramsHandler(basehandlers.FlaskHandler):

  MODEL_CLASS = {
    'FeatureObserver': metrics_models.FeatureObserverHistogram,
    'MappedCSSProperties': metrics_models.CssPropertyHistogram,
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
    if (model_class == metrics_models.CssPropertyHistogram and bucket_id == 1):
      return

    model_class.get_or_insert(key_name,
      bucket_id=bucket_id,
      property_name=property_name
    )

  def get_template_data(self, **kwargs):
    self.require_cron_header()
    # Attempt to fetch enums mapping file.
    response = requests.get(HISTOGRAMS_URL, timeout=60)

    if (response.status_code != 200):
      logging.error('Unable to retrieve chromium histograms mapping file.')
      return

    histograms_content = base64.b64decode(response.content).decode()
    dom = minidom.parseString(histograms_content)

    # The enums.xml file looks like this:
    # <enum name="FeatureObserver">
    #   <int value="0" label="OBSOLETE_PageDestruction"/>
    #   <int value="1" label="LegacyNotifications"/>

    enum_tags = dom.getElementsByTagName('enum')

    # Save bucket ids for each histogram type, FeatureObserver and
    # MappedCSSProperties.
    for histogram_id in list(self.MODEL_CLASS.keys()):
      enum = [enum for enum in enum_tags
              if enum.attributes['name'].value == histogram_id][0]
      for child in enum.getElementsByTagName('int'):
        self._SaveData({
          'bucket_id': child.attributes['value'].value,
          'property_name': child.attributes['label'].value
        }, histogram_id)

    return 'Success'


class BlinkComponentHandler(basehandlers.FlaskHandler):
  """Updates the list of Blink components in the db."""
  def get_template_data(self, **kwargs):
    self.require_cron_header()
    user_models.BlinkComponent.update_db()
    return 'Blink components updated'
