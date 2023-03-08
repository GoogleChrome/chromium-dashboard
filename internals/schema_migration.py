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
from google.cloud import ndb  # type: ignore

from framework.basehandlers import FlaskHandler
from internals import approval_defs, stage_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.legacy_models import Feature, Approval, Comment
from internals.review_models import Activity, Gate, Vote
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
      cls.write_incubate_stages(
          feature, devtrial_mstones, ot_mstones, extension_mstones, ship_mstones)
    elif f_type == FEATURE_TYPE_EXISTING_ID:
      cls.write_existing_stages(
          feature, devtrial_mstones, ot_mstones, extension_mstones, ship_mstones)
    elif f_type == FEATURE_TYPE_CODE_CHANGE_ID:
      cls.write_code_change_stages(
          feature, devtrial_mstones, ship_mstones)
    elif f_type == FEATURE_TYPE_DEPRECATION_ID:
      cls.write_deprecation_stages(
          feature, devtrial_mstones, ot_mstones, extension_mstones, ship_mstones)
    else:
      logging.error(f'Invalid feature type {f_type} for {feature.name}')

  @classmethod
  def write_gate(cls, feature_id, stage_id, gate_type):
    """Writes a Gate entity to match the stage created."""
    gate = Gate(feature_id=feature_id, stage_id=stage_id,
        gate_type=gate_type, state=Vote.NA)
    gate.put()

  @classmethod
  def write_incubate_stages(cls, feature, devtrial_mstones, ot_mstones,
      extension_mstones, ship_mstones):
    feature_id = feature.key.integer_id()
    kwargs = {'feature_id': feature_id, 'browser': 'Chrome'}

    stage = Stage(stage_type=STAGE_BLINK_INCUBATE, **kwargs)
    stage.put()

    stage = Stage(stage_type=STAGE_BLINK_PROTOTYPE,
        intent_thread_url=feature.intent_to_implement_url, **kwargs)
    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), PROTOTYPE_ENUM)

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
    cls.write_gate(feature_id, stage.key.integer_id(), OT_ENUM)

    stage = Stage(stage_type=STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
        milestones=extension_mstones,
        intent_thread_url=feature.intent_to_extend_experiment_url,
        experiment_extension_reason=feature.experiment_extension_reason,
        ot_stage_id=stage.key.integer_id(), **kwargs)
    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), EXTEND_ENUM)
    stage = Stage(stage_type=STAGE_BLINK_SHIPPING, milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)

    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), SHIP_ENUM)

  @classmethod
  def write_existing_stages(cls, feature, devtrial_mstones, ot_mstones,
      extension_mstones, ship_mstones):
    feature_id = feature.key.integer_id()
    kwargs = {'feature_id': feature_id, 'browser': 'Chrome'}

    stage = Stage(stage_type=STAGE_FAST_PROTOTYPE,
        intent_thread_url=feature.intent_to_implement_url, **kwargs)
    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), PROTOTYPE_ENUM)

    stage = Stage(stage_type=STAGE_FAST_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url, **kwargs)
    stage.put()

    stage = Stage(stage_type=STAGE_FAST_ORIGIN_TRIAL, milestones=ot_mstones,
        intent_thread_url=feature.intent_to_experiment_url,
        experiment_goals=feature.experiment_goals,
        origin_trial_feedback_url=feature.origin_trial_feedback_url, **kwargs)
    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), OT_ENUM)

    stage = Stage(stage_type=STAGE_FAST_EXTEND_ORIGIN_TRIAL,
        milestones=extension_mstones,
        intent_thread_url=feature.intent_to_extend_experiment_url,
        experiment_extension_reason=feature.experiment_extension_reason,
        ot_stage_id=stage.key.integer_id(), **kwargs)
    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), EXTEND_ENUM)

    stage = Stage(stage_type=STAGE_FAST_SHIPPING,  milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), SHIP_ENUM)

  @classmethod
  def write_code_change_stages(cls, feature, devtrial_mstones, ship_mstones):
    feature_id = feature.key.integer_id()
    kwargs = {'feature_id': feature_id, 'browser': 'Chrome'}

    stage = Stage(stage_type=STAGE_PSA_IMPLEMENT, **kwargs)
    stage.put()

    stage = Stage(stage_type=STAGE_PSA_DEV_TRIAL, milestones=devtrial_mstones,
        announcement_url=feature.ready_for_trial_url,  **kwargs)
    stage.put()

    stage = Stage(stage_type=STAGE_PSA_SHIPPING,  milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), SHIP_ENUM)

  @classmethod
  def write_deprecation_stages(cls, feature, devtrial_mstones, ot_mstones,
      extension_mstones, ship_mstones):
    feature_id = feature.key.integer_id()
    kwargs = {'feature_id': feature_id, 'browser': 'Chrome'}

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

    cls.write_gate(feature_id, stage.key.integer_id(), OT_ENUM)

    stage = Stage(stage_type=STAGE_DEP_EXTEND_DEPRECATION_TRIAL,
        milestones=extension_mstones,
        intent_thread_url=feature.intent_to_extend_experiment_url,
        experiment_extension_reason=feature.experiment_extension_reason,
        ot_stage_id=stage.key.integer_id(), **kwargs)
    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), EXTEND_ENUM)

    stage = Stage(stage_type=STAGE_DEP_SHIPPING,  milestones=ship_mstones,
        intent_thread_url=feature.intent_to_ship_url,
        finch_url=feature.finch_url, **kwargs)
    stage.put()
    cls.write_gate(feature_id, stage.key.integer_id(), SHIP_ENUM)

    stage = Stage(stage_type=STAGE_DEP_REMOVE_CODE, **kwargs)
    stage.put()


class MigrateApprovalsToVotes(FlaskHandler):

  def get_template_data(self, **kwargs):
    """Migrate all Approval entities to Vote entities."""
    self.require_cron_header()

    approvals: ndb.Query = Approval.query()
    count = 0
    for approval in approvals:
      vote = Vote.get_by_id(approval.key.integer_id())
      if vote:
        continue

      gates = Gate.query(
          Gate.feature_id == approval.feature_id,
          Gate.gate_type == approval.field_id).fetch()
      # Skip if no gate is found for the given approval.
      if len(gates) == 0:
        continue
      gate_id = gates[0].key.integer_id()
      gate_type = gates[0].gate_type
      vote = Vote(id=approval.key.integer_id(), feature_id=approval.feature_id,
          gate_id=gate_id, gate_type=gate_type, state=approval.state,
          set_on=approval.set_on, set_by=approval.set_by)
      vote.put()
      count += 1

    return f'{count} Approval entities migrated to Vote entities.'


class EvaluateGateStatus(FlaskHandler):

  def get_template_data(self, **kwargs):
    """Evaluate all existing Gate entities and set correct state."""
    self.require_cron_header()

    gates: ndb.Query = Gate.query()
    count = 0
    for gate in gates:
      approval_defs.update_gate_approval_state(gate)
      count += 1

    return f'{count} Gate entities reevaluated.'


class DeleteNewEntities(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """Deletes every entity for each kind in the new schema."""
    self.require_cron_header()

    kinds: list[ndb.Model] = [FeatureEntry, Gate, Stage, Vote]
    count = 0
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()
        count += 1

    return f'{count} entities deleted.'

class WriteUpdatedField(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """Sets the FeatureEntry updated field if it is not initialized."""
    self.require_cron_header()

    count = 0
    for fe in FeatureEntry.query():
      if fe.updated is None:
        fe.updated = fe.created
        fe.put()
        count += 1

    return f'{count} FeatureEntry entities given updated field values.'


class UpdateDeprecatedViews(FlaskHandler):

  def get_template_data(self, **kwargs):
    """Migrates deprecated feature views fields to their new values"""
    self.require_cron_header()

    for fe in FeatureEntry.query():
      fe_changed = False
      if fe.ff_views == MIXED_SIGNALS:
        fe_changed = True
        fe.ff_views = NO_PUBLIC_SIGNALS
      elif fe.ff_views == PUBLIC_SKEPTICISM:
        fe_changed = True
        fe.ff_views = OPPOSED

      if fe.safari_views == MIXED_SIGNALS:
        fe_changed = True
        fe.safari_views = NO_PUBLIC_SIGNALS
      elif fe.safari_views == PUBLIC_SKEPTICISM:
        fe_changed = True
        fe.safari_views = OPPOSED

      if fe_changed:
        fe.put()

    for f in Feature.query():
      f_changed = False
      if f.ff_views == MIXED_SIGNALS:
        f_changed = True
        f.ff_views = NO_PUBLIC_SIGNALS
      if f.ff_views == PUBLIC_SKEPTICISM:
        f_changed = True
        f.ff_views = OPPOSED

      if f.ie_views == MIXED_SIGNALS:
        f_changed = True
        f.ie_views = NO_PUBLIC_SIGNALS
      elif f.ie_views == PUBLIC_SKEPTICISM:
        f_changed = True
        f.ie_views = OPPOSED

      if f.safari_views == MIXED_SIGNALS:
        f_changed = True
        f.safari_views = NO_PUBLIC_SIGNALS
      elif f.safari_views == PUBLIC_SKEPTICISM:
        f_changed = True
        f.safari_views = OPPOSED

      if f_changed:
        f.put()

    return 'Feature and FeatureEntry view fields updated.'


class WriteMissingGates(FlaskHandler):

  def write_gate_if_missing(
      self, existing_gates, stage, gate_type):
    """If there is no existing gate, create it and return 1."""
    stage_id = stage.key.integer_id()
    if any(ex.stage_id == stage_id
           for ex in existing_gates):
      return 0

    gate = Gate(feature_id=stage.feature_id, stage_id=stage_id,
                gate_type=gate_type, state=Gate.PREPARING)
    gate.put()
    return 1

  def get_template_data(self, **kwargs):
    """Write gates for code change implement stages (previously not written)."""
    self.require_cron_header()

    existing_api_prototype_gates = Gate.query(
        Gate.gate_type == GATE_API_PROTOTYPE).fetch()
    existing_privacy_ot_gates = Gate.query(
        Gate.gate_type == GATE_PRIVACY_ORIGIN_TRIAL).fetch()
    existing_privacy_ship_gates = Gate.query(
        Gate.gate_type == GATE_PRIVACY_SHIP).fetch()
    existing_security_ot_gates = Gate.query(
        Gate.gate_type == GATE_SECURITY_ORIGIN_TRIAL).fetch()
    existing_security_ship_gates = Gate.query(
        Gate.gate_type == GATE_SECURITY_SHIP).fetch()

    gates_created = 0
    for stage in Stage.query(Stage.stage_type == STAGE_PSA_IMPLEMENT):
      gates_created += self.write_gate_if_missing(
          existing_api_prototype_gates, stage, GATE_API_PROTOTYPE)

    for stage in Stage.query(Stage.stage_type.IN([
        STAGE_BLINK_ORIGIN_TRIAL, STAGE_FAST_ORIGIN_TRIAL,
        STAGE_DEP_DEPRECATION_TRIAL])):
      gates_created += self.write_gate_if_missing(
          existing_privacy_ot_gates, stage, GATE_PRIVACY_ORIGIN_TRIAL)
      gates_created += self.write_gate_if_missing(
          existing_security_ot_gates, stage, GATE_SECURITY_ORIGIN_TRIAL)

    for stage in Stage.query(Stage.stage_type.IN([
        STAGE_BLINK_SHIPPING, STAGE_FAST_SHIPPING, STAGE_PSA_SHIPPING,
        STAGE_DEP_SHIPPING])):
      gates_created += self.write_gate_if_missing(
          existing_privacy_ship_gates, stage, GATE_PRIVACY_SHIP)
      gates_created += self.write_gate_if_missing(
          existing_security_ship_gates, stage, GATE_SECURITY_SHIP)

    return f'{gates_created} missing gates created for stages.'



class CalcActiveStages(FlaskHandler):

  def get_template_data(self, **kwargs):
    """Calculates the active stage of features based on the intent stage."""
    self.require_cron_header()

    active_stages_set = 0
    stages_created = 0

    for fe in FeatureEntry.query():
      # Don't try to detect active stage if it's already set.
      if fe.active_stage_id is not None:
        continue

      feature_id = fe.key.integer_id()
      # Check which stage type is associated with the active intent stage.
      active_stage_type = (
        STAGE_TYPES_BY_INTENT_STAGE[fe.feature_type].get(fe.intent_stage))

      # If a matching stage type isn't found, don't set it.
      if active_stage_type is None:
        continue
      else:
        active_stage = Stage.query(
            Stage.stage_type == active_stage_type,
            Stage.feature_id == feature_id).get()

        # Find the stage ID and set active stage field to this ID.
        if active_stage:
          fe.active_stage_id = active_stage.key.integer_id()
        else:
          # If the stage doesn't exist, create it.
          # This probably shouldn't need to happen if everything is
          # migrated correctly.
          stage = Stage(feature_id=feature_id, stage_type=active_stage_type)
          stage.put()
          stages_created += 1
          fe.active_stage_id = stage.key.integer_id()
        active_stages_set += 1
      fe.put()

    return (f'{active_stages_set} active stages set for features and '
        f'{stages_created} stages created for features.')


class CreateTrialExtensionStages(FlaskHandler):

  def get_template_data(self, **kwargs):
    """Associate trial extension stages with the correct origin trial stages."""
    self.require_cron_header()

    stages_created = 0

    # Query for all origin trial stages.
    ot_queries = [
        Stage.query(Stage.stage_type == STAGE_BLINK_ORIGIN_TRIAL),
        Stage.query(Stage.stage_type == STAGE_FAST_ORIGIN_TRIAL),
        Stage.query(Stage.stage_type == STAGE_DEP_DEPRECATION_TRIAL)]

    for q in ot_queries:
      for s in q:
        stage_id = s.key.integer_id()
        # Query for an extension stage associated with this trial stage.
        # There should typically be one for now until trial extension
        # functionality is available to all users.
        extension_stage = (
            Stage.query(Stage.ot_stage_id == stage_id).get())
        # If there isn't an extension stage, create one and associate it with
        # this trial stage.
        if extension_stage is None:
          extension_stage = Stage(feature_id=s.feature_id,
              stage_type=OT_EXTENSION_STAGE_TYPES_MAPPING[s.stage_type],
              ot_stage_id=stage_id)
          extension_stage.put()
          stages_created += 1

    return (f'{stages_created} extension stages created for '
        'existing trial stages.')


class MigrateSubjectLineField(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """Migrates old Feature subject line fields to their respective stages."""
    self.require_cron_header()

    count = 0
    for f in Feature.query():
      f_id = f.key.integer_id()
      f_type = f.feature_type

      # If there are no subject line fields present, no need to migrate.
      if (not f.intent_to_implement_subject_line and
          not f.intent_to_ship_subject_line and
          not f.intent_to_experiment_subject_line and
          not f.intent_to_extend_experiment_subject_line):
        continue

      stages_to_update = []
      stages = stage_helpers.get_feature_stages(f_id)

      # Check each corresponding FeatureEntry stage to migrate the
      # intent subject line if needed.
      proto_stage_type = STAGE_TYPES_PROTOTYPE[f_type] or -1
      prototype_stages = stages.get(proto_stage_type, [])
      if (f.intent_to_implement_subject_line and
          # If there are more than 1 stage for a specific stage type,
          # we can't be sure which is the correct intent, so don't migrate.
          # (this should be very rare).
          len(prototype_stages) == 1 and
          not prototype_stages[0].intent_subject_line):
        prototype_stages[0].intent_subject_line = (
            f.intent_to_implement_subject_line)
        stages_to_update.append(prototype_stages[0])

      ship_stage_type = STAGE_TYPES_SHIPPING[f_type] or -1
      ship_stages = stages.get(ship_stage_type, [])
      if (f.intent_to_ship_subject_line and
          len(ship_stages) == 1 and
          not ship_stages[0].intent_subject_line):
        ship_stages[0].intent_subject_line = (
            f.intent_to_ship_subject_line)
        stages_to_update.append(ship_stages[0])

      ot_stage_type = STAGE_TYPES_ORIGIN_TRIAL[f_type] or -1
      ot_stages = stages.get(ot_stage_type, [])
      if (f.intent_to_experiment_subject_line and
          len(ot_stages) == 1 and
          not ot_stages[0].intent_subject_line):
        ot_stages[0].intent_subject_line = (
            f.intent_to_experiment_subject_line)
        stages_to_update.append(ot_stages[0])

      extension_stage_type = STAGE_TYPES_EXTEND_ORIGIN_TRIAL[f_type] or -1
      extension_stages = stages.get(extension_stage_type, [])
      if (f.intent_to_extend_experiment_subject_line and
          len(extension_stages) == 1 and
          not extension_stages[0].intent_subject_line):
        extension_stages[0].intent_subject_line = (
            f.intent_to_extend_experiment_subject_line)
        stages_to_update.append(extension_stages[0])

      # Save changes to all updated Stage entities.
      if stages_to_update:
        ndb.put_multi(stages_to_update)
        count += len(stages_to_update)

    return f'{count} subject line fields migrated.'


class MigrateLGTMFields(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """Migrates old Feature subject lgtms to their respective votes."""
    self.require_cron_header()

    count = 0
    votes_to_create = []
    vote_dict = self.get_vote_dict()
    features = Feature.query()
    for f in features:
      if not f.i2e_lgtms:
        continue
      for email in f.i2e_lgtms:
        if self.has_existing_vote(email, GATE_API_ORIGIN_TRIAL, f, vote_dict):
          continue

        # i2e_lgtms (Intent to Experiment)'s gate_type is GATE_API_ORIGIN_TRIAL.
        votes_to_create.append(self.create_new_vote(
            email, GATE_API_ORIGIN_TRIAL, f))
        count += 1

    for f in features:
      if not f.i2s_lgtms:
        continue
      for email in f.i2s_lgtms:
        if self.has_existing_vote(email, GATE_API_SHIP, f, vote_dict):
          continue

        # i2s_lgtms (Intent to Ship)'s gate_type is GATE_API_SHIP.
        votes_to_create.append(self.create_new_vote(
            email, GATE_API_SHIP, f))
        count += 1

    # Only create 100 votes at a time.
    votes_to_create = votes_to_create[:100]
    for new_vote in votes_to_create:
      approval_defs.set_vote(new_vote.feature_id, new_vote.gate_type,
                             new_vote.state, new_vote.set_by)
    return f'{len(votes_to_create)} of {count} lgtms fields migrated.'

  def get_vote_dict(self):
    vote_dict = {}
    votes = Vote.query().fetch(None)
    for vote in votes:
      if vote.feature_id in vote_dict:
        vote_dict[vote.feature_id].append(vote)
      else:
        vote_dict[vote.feature_id] = [vote]
    return vote_dict

  def has_existing_vote(self, email, gate_type, f, vote_dict):
    f_id = f.key.integer_id()
    if f_id not in vote_dict:
      return False

    for v in vote_dict[f_id]:
      # Check if set by the same reviewer and the same gate_type.
      if v.set_by == email and v.gate_type == gate_type:
        return True

    return False

  def create_new_vote(self, email, gate_type, f):
    f_id = f.key.integer_id()
    vote = Vote(feature_id=f_id, gate_type=gate_type,
                state=Vote.APPROVED, set_by=email)
    return vote
