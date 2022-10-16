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
from internals import approval_defs
from internals.core_models import Feature, FeatureEntry, MilestoneSet, Stage
from internals.review_models import Activity, Approval, Comment, Gate, Vote
from internals.core_enums import *

# Gate type enums (declared in approval_defs.py)
PROTOTYPE_ENUM = 1
OT_ENUM = 2
EXTEND_ENUM = 3
SHIP_ENUM = 4

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

  def get_template_data(self, **kwargs):
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

class MigrateEntities(FlaskHandler):

  def get_template_data(self, **kwargs):
    """Write FeatureEntry, Stage, Gate, and Vote entities"""
    self.require_cron_header()

    # Feature -> FeatureEntry mapping.
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
    return handle_migration(Feature, FeatureEntry, kwarg_mapping,
        self.special_handler)

  @classmethod
  def special_handler(cls, original_entity, kwargs):
    # updater_email will use the email from the updated_by field
    kwargs['updater_email'] = (original_entity.updated_by.email()
        if original_entity.updated_by else None)
    
    # If Feature is being migrated, then Stages, Gates, and Votes will need to
    # also be migrated.
    cls.write_stages_for_feature(original_entity)

  @classmethod
  def write_stages_for_feature(cls, feature):
    """Creates new Stage entities MilestoneSet entities based on Feature data"""
    stages, gates, votes = 0, 0, 0
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
    extension_mstones = MilestoneSet(
        desktop_last=feature.ot_milestone_desktop_end,
        android_last=feature.ot_milestone_android_end,
        webview_last=feature.ot_milestone_webview_end)
    ship_mstones = MilestoneSet(
        desktop_first=feature.shipped_milestone,
        android_first=feature.shipped_android_milestone,
        ios_first=feature.shipped_ios_milestone,
        webview_first=feature.shipped_webview_milestone)
    # Depending on the feature type,
    # create a different group of Stage entities.
    f_type = feature.feature_type
    if f_type == FEATURE_TYPE_INCUBATE_ID:
      stages, gates, votes = cls.write_incubate_stages(
          feature, devtrial_mstones, ot_mstones, extension_mstones, ship_mstones)
    elif f_type == FEATURE_TYPE_EXISTING_ID:
      stages, gates, votes = cls.write_existing_stages(
          feature, devtrial_mstones, ot_mstones, extension_mstones, ship_mstones)
    elif f_type == FEATURE_TYPE_CODE_CHANGE_ID:
      stages, gates, votes = cls.write_code_change_stages(
          feature, devtrial_mstones, ship_mstones)
    elif f_type == FEATURE_TYPE_DEPRECATION_ID:
      stages, gates, votes = cls.write_deprecation_stages(
          feature, devtrial_mstones, ot_mstones, extension_mstones, ship_mstones)
    else:
      logging.error(f'Invalid feature type {f_type} for {feature.name}')
    
    message = (f'Created {stages} stages, {gates} gates, and {votes} votes '
               f'for feature {feature.key.integer_id()}')
    logging.info(message)

  @classmethod
  def write_gate(cls, feature_id, stage, gate_type):
    """Writes a Gate entity to match the stage created."""
    gate = Gate(feature_id=feature_id, stage_id=stage.key.integer_id(),
        gate_type=gate_type, state=Vote.NA)
    # Determine the state the Gate should have.
    approvals: list = Approval.query().filter(Approval.feature_id == feature_id)
    if approval_defs.is_approved(approvals, gate_type):
      gate.state = Vote.APPROVED
    elif approval_defs.is_resolved(approvals, gate_type):
      gate.state = Vote.NOT_APPROVED
    gate.put()

    # Filter Approval entities by the gate type and write Vote entities.
    approvals = [
        appr for appr in approvals if appr.field_id == gate_type]
    num_votes = cls.write_votes(feature_id, gate.key.integer_id(), approvals)

    return 1, num_votes

  @classmethod
  def write_votes(cls, feature_id, gate_id, approvals):
    """Migrate Vote entities for given feature and gate IDs."""
    count = 0
    for appr in approvals:
      vote = Vote(feature_id=feature_id, gate_id=gate_id, state=appr.state,
          set_on=appr.set_on, set_by=appr.set_by)
      vote.put()
      count += 1
    
    return count

  @classmethod
  def write_incubate_stages(cls, feature, devtrial_mstones, ot_mstones,
      extension_mstones, ship_mstones):
    feature_id = feature.key.integer_id()
    kwargs = {'feature_id': feature_id, 'browser': 'Chrome'}
    num_gates, num_votes = 0, 0

    stage = Stage(stage_type=STAGE_BLINK_INCUBATE, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_BLINK_PROTOTYPE,
        intent_thread_url=feature.intent_to_implement_url, **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, PROTOTYPE_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    stage = Stage(stage_type=STAGE_BLINK_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_BLINK_EVAL_READINESS, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_BLINK_ORIGIN_TRIAL, milestones=ot_mstones,
        intent_thread_url=feature.intent_to_experiment_url,
        experiment_goals=feature.experiment_goals,
        origin_trial_feedback_url=feature.origin_trial_feedback_url, **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, OT_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    stage = Stage(stage_type=STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
        milestones=extension_mstones,
        intent_thread_url=feature.intent_to_extend_experiment_url,
        experiment_extension_reason=feature.experiment_extension_reason,
        ot_stage_id=stage.key.integer_id(), **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, EXTEND_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    stage = Stage(stage_type=STAGE_BLINK_SHIPPING, milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, SHIP_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    # Return number of Stage entities created.
    return 6, num_gates, num_votes

  @classmethod
  def write_existing_stages(cls, feature, devtrial_mstones, ot_mstones,
      extension_mstones, ship_mstones):
    feature_id = feature.key.integer_id()
    kwargs = {'feature_id': feature_id, 'browser': 'Chrome'}
    num_gates, num_votes = 0, 0

    stage = Stage(stage_type=STAGE_FAST_PROTOTYPE,
        intent_thread_url=feature.intent_to_implement_url, **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, PROTOTYPE_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    stage = Stage(stage_type=STAGE_FAST_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_FAST_ORIGIN_TRIAL, milestones=ot_mstones,
        intent_thread_url=feature.intent_to_experiment_url,
        experiment_goals=feature.experiment_goals,
        origin_trial_feedback_url=feature.origin_trial_feedback_url, **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, OT_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    stage = Stage(stage_type=STAGE_FAST_EXTEND_ORIGIN_TRIAL,
        milestones=extension_mstones,
        intent_thread_url=feature.intent_to_extend_experiment_url,
        experiment_extension_reason=feature.experiment_extension_reason,
        ot_stage_id=stage.key.integer_id(), **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, EXTEND_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    stage = Stage(stage_type=STAGE_FAST_SHIPPING,  milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, SHIP_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    # Return number of Stage entities created.
    return 4, num_gates, num_votes

  @classmethod
  def write_code_change_stages(cls, feature, devtrial_mstones, ship_mstones):
    feature_id = feature.key.integer_id()
    kwargs = {'feature_id': feature_id, 'browser': 'Chrome'}
    num_gates, num_votes = 0, 0

    stage = Stage(stage_type=STAGE_PSA_IMPLEMENT, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_PSA_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url,  **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_PSA_SHIPPING,  milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, SHIP_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    # Return number of Stage entities created.
    return 3, num_gates, num_votes

  @classmethod
  def write_deprecation_stages(cls, feature, devtrial_mstones, ot_mstones,
      extension_mstones, ship_mstones):
    feature_id = feature.key.integer_id()
    kwargs = {'feature_id': feature_id, 'browser': 'Chrome'}
    num_gates, num_votes = 0, 0

    stage = Stage(stage_type=STAGE_DEP_PLAN, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_DEP_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url, **kwargs)
    stage.put()
    stage = Stage(stage_type=STAGE_DEP_DEPRECATION_TRIAL, milestones=ot_mstones,
        intent_thread_url=feature.intent_to_experiment_url,
        experiment_goals=feature.experiment_goals,
        origin_trial_feedback_url=feature.origin_trial_feedback_url, **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, OT_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    stage = Stage(stage_type=STAGE_DEP_EXTEND_DEPRECATION_TRIAL,
        milestones=extension_mstones,
        intent_thread_url=feature.intent_to_extend_experiment_url,
        experiment_extension_reason=feature.experiment_extension_reason,
        ot_stage_id=stage.key.integer_id(), **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, EXTEND_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    stage = Stage(stage_type=STAGE_DEP_SHIPPING,  milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    totals = cls.write_gate(feature_id, stage, SHIP_ENUM)
    num_gates += totals[0]
    num_votes += totals[1]
    stage = Stage(stage_type=STAGE_DEP_REMOVE_CODE, **kwargs)
    stage.put()
    # Return number of Stage entities created.
    return 5, num_gates, num_votes
