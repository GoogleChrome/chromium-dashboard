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
from google.cloud import ndb

from framework.basehandlers import FlaskHandler
from internals.review_models import Activity, Comment

class MigrateCommentsToActivities(FlaskHandler):

  def get_template_data(self):
    """Writes an Activity entity for each unmigrated Comment entity."""
    self.require_cron_header()

    logging.info(self._remove_bad_id_activities())

    q = Comment.query()
    comments = q.fetch()
    migration_count = 0
    for comment in comments:
      # Check if an Activity with the same ID has already been created.
      # If so, do not create this activity again.
      q = Activity.query().filter(
          Activity.key == ndb.Key(Activity, comment.key.integer_id()))
      activities = q.fetch()
      if len(activities) > 0:
        continue

      kwargs = {
        'id': comment.key.integer_id(),
        'feature_id': comment.feature_id,
        'gate_id': comment.field_id,
        'author': comment.author,
        'content': comment.content,
        'deleted_by': comment.deleted_by,
        'created': comment.created
      }
      activity = Activity(**kwargs)
      activity.put()
      migration_count += 1

    message = f'{migration_count} comments migrated to activity entities.'
    logging.info(message)
    return message
  
  def _remove_bad_id_activities(self):
    """Deletes old Activity entities that do not have a matching comment ID."""
    q = Activity.query()
    activities = q.fetch()

    old_migrations_deleted = 0
    for activity in activities:
      # Non-empty content field means this is an Activity entity
      # that represents a comment.
      if activity.content:
        # Check if there is a Comment entity with a matching ID.
        q = Comment.query().filter(
            Comment.key == ndb.Key(Comment, activity.key.integer_id()))
        comments_with_same_id = q.fetch()
        if len(comments_with_same_id) != 1:
          # If not, it is from the old migration and it can be deleted.
          activity.key.delete()
          old_migrations_deleted += 1
    
    return (f'{old_migrations_deleted} Activities deleted '
        'from previous migration.')
