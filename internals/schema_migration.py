# Copyright 2022 Google Inc.
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

import logging

from framework.basehandlers import FlaskHandler
from internals.review_models import Activity, Comment

class MigrateCommentsToActivities(FlaskHandler):

  def get_template_data(self):
    """Writes an Activity entity for each unmigrated Comment entity."""
    self.require_cron_header()
    q = Comment.query()
    comments = q.fetch()
    migration_count = 0
    for comment in comments:
      if comment.migrated:
        continue

      kwargs = {
        'feature_id': comment.feature_id,
        'gate_id': comment.field_id,
        'author': comment.author,
        'content': comment.content,
        'deleted_by': comment.deleted_by,
        'created': comment.created
      }
      activity = Activity(**kwargs)
      activity.put()
      comment.migrated = True
      comment.put()
      migration_count += 1

    message = f'{migration_count} comments migrated to activity entities.'
    logging.info(message)
    return message
