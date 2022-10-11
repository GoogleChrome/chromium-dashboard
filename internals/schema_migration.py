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
from internals.core_models import Feature, FeatureEntry, MilestoneSet, Stage
from internals.review_models import Activity, Approval, Comment, Vote
from internals.core_enums import *

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

class MigrateApprovalsToVotes(FlaskHandler):

  def get_template_data(self):
    """Writes a Vote entity for each unmigrated Approval entity."""
    self.require_cron_header()

    kwarg_mapping = [
        ('feature_id', 'feature_id'),
        ('gate_id', 'field_id'),
        ('state', 'state'),
        ('set_on', 'set_on'),
        ('set_by', 'set_by')]
    return handle_migration(Approval, Vote, kwarg_mapping)

class MigrateFeaturesToFeatureEntries(FlaskHandler):

  def get_template_data(self):
    """Writes a FeatureEntry entity for each unmigrated Feature entity"""
    self.require_cron_header()

    kwarg_mapping = [
        ('created', 'created'),
        ('updated', 'updated'),
        ('accurate_as_of', 'accurate_as_of'),
        ('creator_email', 'creator'),  # Renamed
        ('owner_emails', 'owner'),  # Renamed
        ('editor_emails', 'editors'),  # Renamed
        ('unlisted', 'unlisted'),
        ('cc_emails', 'cc_recipients'),  # Renamed
        ('feature_notes', 'comments'),  # Renamed
        ('deleted', 'deleted'),
        ('name', 'name'),
        ('summary', 'summary'),
        ('category', 'category'),
        ('blink_components', 'blink_components'),
        ('star_count', 'star_count'),
        ('search_tags', 'search_tags'),
        ('feature_type', 'feature_type'),
        ('intent_stage', 'intent_stage'),
        ('bug_url', 'bug_url'),
        ('launch_bug_url', 'launch_bug_url'),
        ('impl_status_chrome', 'impl_status_chrome'),
        ('flag_name', 'flag_name'),
        ('ongoing_constraints', 'ongoing_constraints'),
        ('motivation', 'motivation'),
        ('devtrial_instructions', 'devtrial_instructions'),
        ('activation_risks', 'activation_risks'),
        ('measurement', 'measurement'),
        ('initial_public_proposal_url', 'initial_public_proposal_url'),
        ('explainer_links', 'explainer_links'),
        ('requires_embedder_support', 'requires_embedder_support'),
        ('standard_maturity', 'standard_maturity'),
        ('spec_link', 'spec_link'),
        ('api_spec', 'api_spec'),
        ('spec_mentor_emails', 'spec_mentors'),  # Renamed
        ('interop_compat_risks', 'interop_compat_risks'),
        ('prefixed', 'prefixed'),
        ('all_platforms', 'all_platforms'),
        ('all_platforms_descr', 'all_platforms_descr'),
        ('tag_review', 'tag_review'),
        ('tag_review_status', 'tag_review_status'),
        ('non_oss_deps', 'non_oss_deps'),
        ('anticipated_spec_changes', 'anticipated_spec_changes'),
        ('ff_views', 'ff_views'),
        ('safari_views', 'safari_views'),
        ('web_dev_views', 'web_dev_views'),
        ('ff_views_link', 'ff_views_link'),
        ('safari_views_link', 'safari_views_link'),
        ('web_dev_views_link', 'web_dev_views_link'),
        ('ff_views_notes', 'ff_views_notes'),
        ('safari_views_notes', 'safari_views_notes'),
        ('web_dev_views_notes', 'web_dev_views_notes'),
        ('other_views_notes', 'other_views_notes'),
        ('security_risks', 'security_risks'),
        ('security_review_status', 'security_review_status'),
        ('privacy_review_status', 'privacy_review_status'),
        ('ergonomics_risks', 'ergonomics_risks'),
        ('wpt', 'wpt'),
        ('wpt_descr', 'wpt_descr'),
        ('webview_risks', 'webview_risks'),
        ('devrel_emails', 'devrel'),  # Renamed
        ('debuggability', 'debuggability'),
        ('doc_links', 'doc_links'),
        ('sample_links', 'sample_links'),
        ('experiment_timeline', 'experiment_timeline')]
    return handle_migration(Feature, FeatureEntry,kwarg_mapping,
        self.special_handler)

  @classmethod
  def special_handler(cls, original_entity, kwargs):
    # updater_email will use the email from the updated_by field
    kwargs['updater_email'] = (original_entity.updated_by.email()
        if original_entity.updated_by else None)

class MigrateStages(FlaskHandler):

  def get_template_data(self):
    """Creates new Stage entities MilestoneSet entities based on Feature data"""
    self.require_cron_header()

    features = Feature.query().fetch()
    num_stages_created = 0
    num_features_migrated = 0
    for feature in features:
      # Do not create more stages if the data in this feature has been migrated.
      if feature.stages_migrated:
        continue
      # Create MilestoneSets for each major paradigm.
      devtrial_mstones = MilestoneSet(
          desktop_first=feature.dt_milestone_desktop_start,
          android_first=feature.dt_milestone_android_start,
          ios_first=feature.dt_milestone_ios_start,
          webview_first=feature.dt_milestone_webview_start)
      ot_mstones = MilestoneSet(
          desktop_first=feature.ot_milestone_desktop_start,
          desktop_last=feature.ot_milestone_desktop_end,
          android_first=feature.ot_milestone_android_start,
          android_last=feature.ot_milestone_android_end,
          webview_first=feature.ot_milestone_webview_start,
          webview_last=feature.ot_milestone_webview_end)
      ship_mstones = MilestoneSet(
          desktop_first=feature.shipped_milestone,
          android_first=feature.shipped_android_milestone,
          ios_first=feature.shipped_ios_milestone,
          webview_first=feature.shipped_webview_milestone)
      # Depending on the feature type,
      # create a different group of Stage entities.
      if feature.feature_type == FEATURE_TYPE_INCUBATE_ID:
        num_stages_created += self.write_incubate_stages(
            feature, devtrial_mstones, ot_mstones, ship_mstones)
      if feature.feature_type == FEATURE_TYPE_EXISTING_ID:
        num_stages_created += self.write_existing_stages(
            feature, devtrial_mstones, ot_mstones, ship_mstones)
      if feature.feature_type == FEATURE_TYPE_CODE_CHANGE_ID:
        num_stages_created += self.write_code_change_stages(
            feature, devtrial_mstones, ship_mstones)
      if feature.feature_type == FEATURE_TYPE_DEPRECATION_ID:
        num_stages_created += self.write_deprecation_stages(
            feature, devtrial_mstones, ot_mstones, ship_mstones)
      feature.stages_migrated = True
      feature.put()
      num_features_migrated += 1
    
    message = (f'{num_stages_created} Stage entities created '
        f'for {num_features_migrated} Feature entities.')
    logging.info(message)
    return message
    
  
  def write_incubate_stages(self, feature, devtrial_mstones, ot_mstones,
      ship_mstones):
    kwargs = {'feature_id': feature.key.integer_id(), 'browser': 'Chrome'}
    stage = Stage(stage_type=STAGE_BLINK_INCUBATE, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_BLINK_PROTOTYPE,
        intent_thread_url=feature.intent_to_implement_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_BLINK_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_BLINK_EVAL_READINESS, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_BLINK_ORIGIN_TRIAL, milestones=ot_mstones,
        **kwargs, intent_thread_url=feature.intent_to_experiment_url,
        experiment_goals=feature.experiment_goals,
        experiment_extension_reason=feature.experiment_extension_reason,
        origin_trial_feedback_url=feature.origin_trial_feedback_url)
    stage.put()
    stage = Stage(stage_type=STAGE_BLINK_SHIPPING, milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    # Return number of Stage entities created.
    return 6
  
  def write_existing_stages(self, feature, devtrial_mstones, ot_mstones,
      ship_mstones):
    kwargs = {'feature_id': feature.key.integer_id(), 'browser': 'Chrome'}
    stage = Stage(stage_type=STAGE_FAST_PROTOTYPE,
        intent_thread_url=feature.intent_to_implement_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_FAST_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_FAST_ORIGIN_TRIAL, milestones=ot_mstones,
        intent_thread_url=feature.intent_to_experiment_url,
        experiment_goals=feature.experiment_goals,
        experiment_extension_reason=feature.experiment_extension_reason,
        origin_trial_feedback_url=feature.origin_trial_feedback_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_FAST_SHIPPING,  milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    # Return number of Stage entities created.
    return 4

  def write_code_change_stages(self, feature, devtrial_mstones, ship_mstones):
    kwargs = {'feature_id': feature.key.integer_id(), 'browser': 'Chrome'}
    stage = Stage(stage_type=STAGE_PSA_IMPLEMENT, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_PSA_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url,  **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_PSA_SHIPPING,  milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    # Return number of Stage entities created.
    return 3
  
  def write_deprecation_stages(self, feature, devtrial_mstones, ot_mstones,
      ship_mstones):
    kwargs = {'feature_id': feature.key.integer_id(), 'browser': 'Chrome'}
    stage = Stage(stage_type=STAGE_DEP_PLAN, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_DEP_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_DEP_DEPRECATION_TRIAL, milestones=ot_mstones,
        **kwargs, intent_thread_url=feature.intent_to_experiment_url,
        experiment_goals=feature.experiment_goals,
        experiment_extension_reason=feature.experiment_extension_reason,
        origin_trial_feedback_url=feature.origin_trial_feedback_url)
    stage.put()
    stage = Stage(stage_type=STAGE_DEP_SHIPPING,  milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_DEP_REMOVE_CODE, **kwargs)
    stage.put()
    # Return number of Stage entities created.
    return 5
