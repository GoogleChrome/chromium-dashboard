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
from internals.core_models import Feature, FeatureEntry
from internals.review_models import Activity, Comment

def handle_migration(original_cls, new_cls, kwarg_mapping,
    special_handler=None):
  originals = original_cls.query().fetch()
  new_keys = new_cls.query().fetch(keys_only=True)
  new_ids = set(key.integer_id() for key in new_keys)
  migration_count = 0
  for original in originals:
    # Check if a new entity with the same ID has already been created.
    # If so, do not create the entity again.
    if original.key.integer_id() in new_ids:
      continue

    kwargs = {new_field : getattr(original, old_field)
        for (new_field, old_field) in kwarg_mapping}
    kwargs['id'] = original.key.integer_id()

    # If any fields need special mapping, handle them in the given method.
    if callable(special_handler):
      special_handler(original, kwargs)

    new_entity = new_cls(**kwargs)
    new_entity.put()
    migration_count += 1

  message = (f'{migration_count} {original_cls.__name__} entities migrated '
      f'to {new_cls.__name__} entities.')
  logging.info(message)
  return message

class MigrateCommentsToActivities(FlaskHandler):

  def get_template_data(self):
    """Writes an Activity entity for each unmigrated Comment entity."""
    self.require_cron_header()

    logging.info(self._remove_bad_id_activities())

    kwarg_mapping = [
        ('feature_id', 'feature_id'),
        ('gate_id', 'field_id'),
        ('author', 'author'),
        ('content', 'content'),
        ('deleted_by', 'deleted_by'),
        ('created', 'created')]
    return handle_migration(Comment, Activity, kwarg_mapping)

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

class MigrateFeaturesToFeatureEntries(FlaskHandler):

  def get_template_data(self):
    """Writes a FeatureEntry entity for each unmigrated Feature entity"""
    self.require_cron_header()
    features = Feature.query().fetch()
    feature_entry_keys = FeatureEntry.query().fetch(keys_only=True)
    feature_entry_ids = set(key.integer_id() for key in feature_entry_keys)
    migration_count = 0
    for feature in features:
      # If a FeatureEntry exists with the same ID, it has already been migrated.
      if feature.key.integer_id() in feature_entry_ids:
        continue

      updater = feature.updated_by.email() if feature.updated_by else None
      kwargs = {
          'id': feature.key.integer_id(),
          'created': feature.created,
          'updated': feature.updated,
          'accurate_as_of': feature.accurate_as_of,
          'creator': feature.creator,
          'updater': updater,
          'owners': feature.owner,
          'editors': feature.editors,
          'unlisted': feature.unlisted,
          'cc_recipients': feature.cc_recipients,
          'feature_notes': feature.comments,
          'deleted': feature.deleted,
          'name': feature.name,
          'summary': feature.summary,
          'category': feature.category,
          'blink_components': feature.blink_components,
          'star_count': feature.star_count,
          'search_tags': feature.search_tags,
          'feature_type': feature.feature_type,
          'intent_stage': feature.intent_stage,
          'bug_url': feature.bug_url,
          'launch_bug_url': feature.launch_bug_url,
          'impl_status_chrome': feature.impl_status_chrome,
          'flag_name': feature.flag_name,
          'ongoing_constraints': feature.ongoing_constraints,
          'motivation': feature.motivation,
          'devtrial_instructions': feature.devtrial_instructions,
          'activation_risks': feature.activation_risks,
          'measurement': feature.measurement,
          'initial_public_proposal_url': feature.initial_public_proposal_url,
          'explainer_links': feature.explainer_links,
          'requires_embedder_support': feature.requires_embedder_support,
          'standard_maturity': feature.standard_maturity,
          'spec_link': feature.spec_link,
          'api_spec': feature.api_spec,
          'spec_mentors': feature.spec_mentors,
          'interop_compat_risks': feature.interop_compat_risks,
          'prefixed': feature.prefixed,
          'all_platforms': feature.all_platforms,
          'all_platforms_descr': feature.all_platforms_descr,
          'tag_review': feature.tag_review,
          'tag_review_status': feature.tag_review_status,
          'non_oss_deps': feature.non_oss_deps,
          'anticipated_spec_changes': feature.anticipated_spec_changes,
          'ff_views': feature.ff_views,
          'safari_views': feature.safari_views,
          'web_dev_views': feature.web_dev_views,
          'ff_views_link': feature.ff_views_link,
          'safari_views_link': feature.safari_views_link,
          'web_dev_views_link': feature.web_dev_views_link,
          'ff_views_notes': feature.ff_views_notes,
          'safari_views_notes': feature.safari_views_notes,
          'web_dev_views_notes': feature.web_dev_views_notes,
          'other_views_notes': feature.other_views_notes,
          'security_risks': feature.security_risks,
          'security_review_status': feature.security_review_status,
          'privacy_review_status': feature.privacy_review_status,
          'ergonomics_risks': feature.ergonomics_risks,
          'wpt': feature.wpt,
          'wpt_descr': feature.wpt_descr,
          'webview_risks': feature.webview_risks,
          'devrel': feature.devrel,
          'debuggability': feature.debuggability,
          'doc_links': feature.doc_links,
          'sample_links': feature.sample_links}

      feature_entry = FeatureEntry(**kwargs)
      feature_entry.put()
      migration_count += 1

    message = f'{migration_count} features migrated to FeatureEntry entities.'
    logging.info(message)
    return message
