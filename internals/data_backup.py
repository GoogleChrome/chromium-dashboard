# Copyright 2022 Google LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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
import logging

from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
import settings

from framework import basehandlers

class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


class BackupExportHandler(basehandlers.FlaskHandler):
  """Triggers a new Datastore export."""

  def get_template_data(self):
    self.require_cron_header()
    bucket = f'gs://{settings.BACKUP_BUCKET}'
    # The default cache (file_cache) is unavailable when using oauth2client >= 4.0.0 or google-auth,
    # and it will log worrisome messages unless given another interface to use.
    datastore = build('datastore', 'v1', cache=MemoryCache())
    project_id = settings.APP_ID

    # No entity filters are used to back up all entities.
    request_body = {'outputUrlPrefix': bucket, 'entityFilter': {}}

    export_request = datastore.projects().export(
      projectId=project_id, body=request_body
    )
    response = export_request.execute()
    logging.info(str(response))
    return 'Success'
