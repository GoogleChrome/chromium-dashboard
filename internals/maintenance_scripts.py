# Copyright 2023 Google Inc.
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

import collections
import csv
from datetime import date, datetime
from io import StringIO
import logging
from typing import Any
from google.cloud import ndb, storage  # type: ignore
import requests

from api import converters, channels_api
from framework.basehandlers import FlaskHandler
from framework import cloud_tasks_helpers
from framework import origin_trials_client
from framework import utils
from internals import approval_defs
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote, Activity
from internals.core_enums import *
from internals.feature_links import batch_index_feature_entries
from internals import stage_helpers
from internals.webdx_feature_models import WebdxFeatures
from webstatus_openapi import ApiClient, DefaultApi, Configuration, ApiException, Feature
import settings

class EvaluateGateStatus(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """Evaluate all existing Gate entities and set correct state."""
    self.require_cron_header()

    count = 0
    batch = []
    BATCH_SIZE = 100
    votes_by_gate = collections.defaultdict(list)
    for vote in Vote.query():
      votes_by_gate[vote.gate_id].append(vote)
    for gate in Gate.query():
      if approval_defs.update_gate_approval_state(
          gate, votes_by_gate[gate.key.integer_id()]):
        batch.append(gate)
        count += 1
        if len(batch) > BATCH_SIZE:
          ndb.put_multi(batch)
          batch = []

    ndb.put_multi(batch)
    return f'{count} Gate entities updated.'


class WriteMissingGates(FlaskHandler):

  GATES_TO_CREATE_PER_RUN = 5000

  GATE_RULES: dict[int, dict[int, list[int]]] = {
      fe_type: dict(stages_and_gates)
      for fe_type, stages_and_gates in STAGES_AND_GATES_BY_FEATURE_TYPE.items()
  }

  def make_needed_gates(self, fe, stage, existing_gates) -> list[Gate]:
    """Instantiate and return any needed gates for the given stage."""
    if not fe:
      logging.info(f'Stage {stage.key.integer_id()} has no feature entry')
      return []
    if fe.feature_type not in self.GATE_RULES:
      logging.info(f'Skipping stage of bad feature {fe.key.integer_id()}')
      return []
    if stage.stage_type not in self.GATE_RULES[fe.feature_type]:
      logging.info(f'Skipping bad stage {stage.key.integer_id()} ')
      return []


    new_gates: list[Gate] = []
    needed_gates = self.GATE_RULES[fe.feature_type][stage.stage_type]
    for needed_gate_type in needed_gates:
      if not any(eg for eg in existing_gates
                 if eg.gate_type == needed_gate_type):
        gate = Gate(
            feature_id=stage.feature_id,
            stage_id=stage.key.integer_id(),
            gate_type=needed_gate_type,
            state=Gate.PREPARING)
        new_gates.append(gate)
    return new_gates

  def get_template_data(self, **kwargs) -> str:
    """Create a chunk of needed gates for all features."""
    self.require_cron_header()

    all_feature_entries = FeatureEntry.query().fetch()
    fe_by_id = {fe.key.integer_id(): fe
                for fe in all_feature_entries}
    existing_gates_by_stage_id = collections.defaultdict(list)
    for gate in Gate.query():
      existing_gates_by_stage_id[gate.stage_id].append(gate)

    gates_to_write: list[Gate] = []
    for stage in Stage.query():
      new_gates = self.make_needed_gates(
          fe_by_id.get(stage.feature_id), stage,
          existing_gates_by_stage_id[stage.key.integer_id()])
      gates_to_write.extend(new_gates)
      if len(gates_to_write) > self.GATES_TO_CREATE_PER_RUN:
        break  # Stop early if we risk exceeding GAE timeout.

    ndb.put_multi(gates_to_write)

    return f'{len(gates_to_write)} missing gates created for stages.'


class BackfillRespondedOn(FlaskHandler):

  def update_responded_on(self, gate) -> bool:
    """Update gate.responded_on and return True if an update was needed."""
    gate_id = gate.key.integer_id()
    earliest_response = datetime.max

    approvers = approval_defs.get_approvers(gate.gate_type)
    activities = Activity.get_activities(
        gate.feature_id, gate_id=gate_id, comments_only=True)
    for a in activities:
      if gate.requested_on < a.created < earliest_response:
        if a.author in approvers:
          earliest_response = a.created
          logging.info(f'Set feature {gate.feature_id} gate {gate_id} '
                       f'to {a.created} because of comment')

    votes = Vote.get_votes(gate_id=gate_id)
    for v in votes:
      if gate.requested_on < v.set_on < earliest_response:
        earliest_response = v.set_on
        logging.info(f'Set feature {gate.feature_id} gate {gate_id} '
                     f'to {v.set_on} because of vote')

    if earliest_response != datetime.max:
      gate.responded_on = earliest_response
      return True
    else:
      return False

  def get_template_data(self, **kwargs) -> str:
    """Backfill responded_on dates for existing gates."""
    self.require_cron_header()
    gates: ndb.Query = Gate.query()
    count = 0
    batch = []
    BATCH_SIZE = 100
    for g in gates:
      if g.responded_on or g.requested_on:
        continue
      if self.update_responded_on(g):
        batch.append(g)
        count += 1
        if len(batch) > BATCH_SIZE:
          ndb.put_multi(batch)
          logging.info(f'Finished a batch of {BATCH_SIZE}')
          batch = []

    ndb.put_multi(batch)
    return f'{count} Gates entities updated.'

class BackfillStageCreated(FlaskHandler):
  def get_template_data(self, **kwargs) -> str:
    """Backfill created dates for existing stages."""
    self.require_cron_header()
    count = 0
    batch = []
    BATCH_SIZE = 100
    stages: ndb.Query = Stage.query()
    for stage in stages:
      feature_entry = FeatureEntry.get_by_id(stage.feature_id)
      if feature_entry == None or stage.created != None:
        continue
      stage.created = feature_entry.created
      batch.append(stage)
      count += 1
      if len(batch) > BATCH_SIZE:
        ndb.put_multi(batch)
        logging.info(f'Finished a batch of {BATCH_SIZE}')
        batch = []

    ndb.put_multi(batch)
    return f'{count} Stages entities updated of {stages.count()} available stages.'

class BackfillFeatureLinks(FlaskHandler):
  def get_template_data(self, **kwargs) -> str:
    """Backfill feature links for existing feature entries."""
    self.require_cron_header()
    all_feature_entries = FeatureEntry.query().fetch()
    count = batch_index_feature_entries(all_feature_entries, True)
    return f'{len(all_feature_entries)} FeatureEntry entities backfilled of {count} feature links.'


class AssociateOTs(FlaskHandler):

  def write_field(
      self,
      trial_stage: Stage,
      trial_data: dict[str, Any],
      stage_field_name: str,
      trial_field_name: str,
    ) -> bool:
    """Set the OT stage value to the value from the OT console if it is unset.

    Returns:
      boolean value of whether or not the value was changed on the stage.
    """
    if (not getattr(trial_stage, stage_field_name)
        and trial_data[trial_field_name]):
      setattr(trial_stage, stage_field_name, trial_data[trial_field_name])
      return True
    return False

  def write_milestone_field(
      self,
      trial_stage: Stage,
      trial_data: dict[str, Any],
      stage_field_name: str,
      trial_field_name: str,
    ) -> bool:
    """Set an OT milestone value to the value from the OT console
    if it is unset.

    Returns:
      boolean value of whether or not the value was changed on the stage.
    """
    if trial_stage.milestones is None:
      trial_stage.milestones = MilestoneSet()
    if (getattr(trial_stage.milestones, stage_field_name) is None and
        trial_data[trial_field_name] is not None):
      setattr(trial_stage.milestones,
              stage_field_name, int(trial_data[trial_field_name]))
      return True
    return False

  def write_fields_for_trial_stage(
      self, trial_stage: Stage, trial_data: dict[str, Any]) -> bool:
    """Check if any OT stage fields are unfilled and populate them with
    the matching trial data.
    """
    stage_changed = False
    stage_changed = (self.write_field(
        trial_stage, trial_data, 'origin_trial_id', 'id') or stage_changed)
    stage_changed = (self.write_field(
        trial_stage, trial_data,
        'ot_chromium_trial_name', 'origin_trial_feature_name') or stage_changed)
    stage_changed = (self.write_field(
        trial_stage, trial_data,
        'ot_feedback_submission_url', 'feedback_url') or stage_changed)
    stage_changed = (self.write_field(
        trial_stage, trial_data,
        'ot_documentation_url', 'documentation_url') or stage_changed)
    stage_changed = (self.write_field(
        trial_stage, trial_data,
        'intent_thread_url', 'intent_to_experiment_url') or stage_changed)
    stage_changed = (self.write_field(
        trial_stage, trial_data,
        'display_name', 'display_name') or stage_changed)
    stage_changed = (self.write_field(
        trial_stage, trial_data,
        'ot_display_name', 'display_name') or stage_changed)
    stage_changed = (self.write_field(
        trial_stage, trial_data,
        'ot_has_third_party_support', 'allow_third_party_origins') or
        stage_changed)
    stage_changed = (self.write_milestone_field(
            trial_stage, trial_data,
            'desktop_first', 'start_milestone') or stage_changed)
    stage_changed = (self.write_milestone_field(
            trial_stage, trial_data,
            'desktop_last', 'original_end_milestone') or stage_changed)

    if not trial_stage.ot_is_deprecation_trial:
      trial_stage.ot_is_deprecation_trial = trial_data['type'] == 'DEPRECATION'
      stage_changed = True

    # Clear the trial creation request if it's active.
    if trial_stage.ot_action_requested:
      trial_stage.ot_action_requested = False
      stage_changed = True

    # Set the setup status to complete if the trial is created or activated.
    trial_activated = (trial_data['status'] == 'ACTIVE' or
                       trial_data['status'] == 'COMPLETE')
    if trial_stage.ot_setup_status != OT_ACTIVATED and trial_activated:
      trial_stage.ot_setup_status = OT_ACTIVATED
      stage_changed = True

    return stage_changed

  def parse_feature_id(self, chromestatus_url: str|None) -> int|None:
      if chromestatus_url is None:
        return None
      # The ChromeStatus feature ID is pulled out of the ChromeStatus URL.
      chromestatus_id_start = chromestatus_url.rfind('/')
      if chromestatus_id_start == -1:
        logging.info(f'Bad ChromeStatus URL: {chromestatus_url}')
        return None
      # Add 1 to index, which is the start index of the ID.
      chromestatus_id_start += 1
      chromestatus_id_str = chromestatus_url[chromestatus_id_start:]
      try:
        chromestatus_id = int(chromestatus_id_str)
      except ValueError:
        logging.info(
            f'Unable to parse ID from ChromeStatus URL: {chromestatus_url}')
        return None
      return chromestatus_id

  def find_unassociated_trial_stage(self, feature_id: int) -> Stage|None:
      fe: FeatureEntry|None = FeatureEntry.get_by_id(feature_id)
      if fe is None:
        logging.info(f'No feature found for ChromeStatus ID: {feature_id}')
        return None

      trial_stage_type = STAGE_TYPES_ORIGIN_TRIAL[fe.feature_type]
      trial_stages: list[Stage] = Stage.query(
          Stage.stage_type == trial_stage_type,
          Stage.feature_id == feature_id).fetch()
      # Look for a stage that does not already have an origin trial associated
      # with it.
      unassociated_trial_stages =  [s for s in trial_stages
                                    if not s.origin_trial_id]
      if len(unassociated_trial_stages) > 1:
        logging.info('Multiple origin trial stages found for feature '
                     f'{feature_id}. Cannot discern which stage to associate '
                     'trial with.')
        return None
      if len(unassociated_trial_stages) == 0:
        logging.info(f'No unassociated OT stages found for feature ID: '
                     f'{feature_id}')
        return None
      return unassociated_trial_stages[0]

  def clear_extension_requests(self, ot_stage: Stage, trial_data: dict) -> int:
    """Clear any trial extension requests if they have been processed"""
    extension_stages: list[Stage] = Stage.query(
        Stage.ot_action_requested == True,
        Stage.ot_stage_id == ot_stage.key.integer_id()).fetch()
    if len(extension_stages) == 0:
      return 0
    extension_stages_to_update = []
    for extension_stage in extension_stages:
      # skip the stage if it doesn't have an end milestone explicitly defined.
      if (extension_stage.milestones is None or
          not extension_stage.milestones.desktop_last):
        continue
      extension_end = extension_stage.milestones.desktop_last
      # If the end milestone of the trial is equal or greater than the
      # requested end milestone on the extension stage, we can assume the
      # extension request has been processed.
      if (int(trial_data['end_milestone']) >= extension_end):
        extension_stage.ot_action_requested = False
        extension_stages_to_update.append(extension_stage)

    if extension_stages_to_update:
      ndb.put_multi(extension_stages_to_update)
    return len(extension_stages_to_update)

  def get_template_data(self, **kwargs) -> str:
    """Link existing origin trials with their ChromeStatus entry"""
    self.require_cron_header()

    trials_list = origin_trials_client.get_trials_list()
    entities_to_write: list[Stage] = []
    extensions_cleared = 0
    # Keep track of stages we're writing to so we avoid trying to write
    # to the same Stage entity twice in the same batch.
    unique_entities_to_write: set[int] = set()
    trials_with_no_feature: list[dict[str, Any]] = []
    for trial_data in trials_list:
      stage: Stage | None = Stage.query(
          Stage.origin_trial_id == trial_data['id']).get()
      if stage and stage.key.integer_id() in unique_entities_to_write:
        logging.info('Already writing to Stage entity '
                     f'{stage.key.integer_id()}')
        continue

      # If this trial is already associated with a ChromeStatus stage,
      # just see if any unfilled fields need to be populated and clear
      # any pending extension requests.
      if stage:
        stage_changed = self.write_fields_for_trial_stage(stage, trial_data)
        if stage_changed:
          unique_entities_to_write.add(stage.key.integer_id())
          entities_to_write.append(stage)
        extensions_cleared += self.clear_extension_requests(stage, trial_data)
        continue

      feature_id = self.parse_feature_id(trial_data['chromestatus_url'])
      if feature_id is None:
        trials_with_no_feature.append(trial_data)
        continue

      ot_stage = self.find_unassociated_trial_stage(feature_id)
      if ot_stage is None:
        trials_with_no_feature.append(trial_data)
        continue

      ot_stage_id = ot_stage.key.integer_id()
      if ot_stage_id in unique_entities_to_write:
        logging.info(f'Already writing to Stage entity {ot_stage_id}')
        continue

      stage_changed = self.write_fields_for_trial_stage(ot_stage, trial_data)
      if stage_changed:
        unique_entities_to_write.add(ot_stage_id)
        entities_to_write.append(ot_stage)

    # List any origin trials that did not get associated with a feature entry.
    if len(trials_with_no_feature) > 0:
      logging.info('Trials not associated with a ChromeStatus feature:')
    else:
      logging.info('All trials associated with a ChromeStatus feature!')
    for trial_data in trials_with_no_feature:
      logging.info(f'{trial_data["id"]} {trial_data["display_name"]}')

    # Update all the stages at the end.
    logging.info(f'{len(entities_to_write)} stages to update.')
    if len(entities_to_write) > 0:
      ndb.put_multi(entities_to_write)

    return (f'{len(entities_to_write)} Stages updated with trial data.\n'
            f'{extensions_cleared} extension requests cleared.')

class BackfillFeatureEnterpriseImpact(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """Backfill enterprise_impact firld for all features."""
    self.require_cron_header()
    count = 0
    batch = []
    BATCH_SIZE = 100
    updated_feature_ids = set()
    features_by_id = {}

    stages: ndb.Query = Stage.query(Stage.stage_type == STAGE_ENT_ROLLOUT, Stage.archived == False)
    for stage in stages:
      if stage.feature_id in features_by_id:
        continue
      features_by_id[stage.feature_id] = FeatureEntry.get_by_id(stage.feature_id)
    # Update enterprise_impact to be the highest impact set on any of the rollout steps.
    for stage in stages:
      feature_entry = features_by_id[stage.feature_id]
      if feature_entry == None:
        continue
      new_impact = stage.rollout_impact + 1
      if new_impact <= feature_entry.enterprise_impact:
        continue
      feature_entry.enterprise_impact = new_impact
      updated_feature_ids.add(stage.feature_id)

    # Set all enterprise features and former breaking changes to have a low impact if no rollout step was step.
    features: ndb.Query = FeatureEntry.query(
      FeatureEntry.enterprise_impact == ENTERPRISE_IMPACT_NONE,
      ndb.OR(FeatureEntry.feature_type == FEATURE_TYPE_ENTERPRISE_ID, FeatureEntry.breaking_change == True))
    for feature_entry in features:
      if feature_entry.key.id() in updated_feature_ids:
        continue
      features_by_id[feature_entry.key.id()] = feature_entry
      updated_feature_ids.add(feature_entry.key.id())
      feature_entry.enterprise_impact = ENTERPRISE_IMPACT_MEDIUM

    for feature_id in updated_feature_ids:
      batch.append(features_by_id[feature_id])
      count += 1
      if len(batch) > BATCH_SIZE:
        ndb.put_multi(batch)
        logging.info(f'Feature updated: Finished a batch of {BATCH_SIZE}')
        batch = []

    ndb.put_multi(batch)

    return f'{count} Feature entities updated of {len(features_by_id)} available features.'


class CreateOriginTrials(FlaskHandler):

  def _send_creation_result_notification(
      self, task_path: str, stage: Stage, params: dict|None = None) -> None:
    if not params:
      params = {}
    print('sending email task to', task_path, 'with params', params)
    stage_dict = converters.stage_to_json_dict(stage)
    params['stage'] = stage_dict
    cloud_tasks_helpers.enqueue_task(task_path, params)

  def handle_creation(self, stage: Stage) -> bool:
    """Send a flagged creation request for processing to the Origin Trials
    API.
    """
    origin_trial_id, error_text = origin_trials_client.create_origin_trial(
        stage)
    if origin_trial_id:
      stage.origin_trial_id = origin_trial_id
    if error_text:
      logging.warning('Origin trial could not be created for stage '
                     f'{stage.key.integer_id()}')
      stage.ot_setup_status = OT_CREATION_FAILED
      self._send_creation_result_notification(
          '/tasks/email-ot-creation-request-failed',
          stage,
          {'error_text': error_text})
      return False
    else:
      stage.ot_setup_status = OT_CREATED
      logging.info(f'Origin trial created for stage {stage.key.integer_id()}')
    return True

  def handle_activation(self, stage: Stage) -> None:
    """Send trial activation request."""
    try:
      origin_trials_client.activate_origin_trial(stage.origin_trial_id)
      stage.ot_setup_status = OT_ACTIVATED
      self._send_creation_result_notification(
          '/tasks/email-ot-activated', stage)
    except requests.RequestException:
      # The activation still needs to occur,
      # so the activation date is set for current date.
      stage.ot_activation_date = date.today()
      stage.ot_setup_status = OT_ACTIVATION_FAILED
      self._send_creation_result_notification(
          '/tasks/email-ot-activation-failed', stage)

  def _get_today(self) -> date:
    return date.today()

  def prepare_for_activation(self, stage: Stage) -> None:
    """Set up activation date or activate trial now."""
    mstone_info = utils.get_chromium_milestone_info(
        stage.milestones.desktop_first)
    date = datetime.strptime(
        mstone_info['mstones'][0]['branch_point'],
        utils.CHROMIUM_SCHEDULE_DATE_FORMAT).date()
    if date <= self._get_today():
      print('sending for activation. Today:', self._get_today(), 'branch_date: ', date)
      self.handle_activation(stage)
    else:
      stage.ot_activation_date = date
      stage.ot_setup_status = OT_CREATED
      self._send_creation_result_notification(
          '/tasks/email-ot-creation-processed', stage)

  def get_template_data(self, **kwargs) -> str:
    """Create any origin trials that are flagged for creation."""
    self.require_cron_header()
    if not settings.AUTOMATED_OT_CREATION:
      return 'Automated OT creation process is not active.'

    # OT stages that are flagged to process a trial creation.
    ot_stages: list[Stage] = Stage.query(
        Stage.ot_setup_status == OT_READY_FOR_CREATION).fetch()
    for stage in ot_stages:
      stage.ot_action_requested = False
      creation_success = self.handle_creation(stage)
      if creation_success:
        self.prepare_for_activation(stage)
      stage.put()

    return f'{len(ot_stages)} trial creation request(s) processed.'


class ActivateOriginTrials(FlaskHandler):

  def _get_today(self) -> date:
    return date.today()

  def get_template_data(self, **kwargs) -> str:
    """Check for origin trials that are scheduled for activation and activate
    them.
    """
    self.require_cron_header()
    if not settings.AUTOMATED_OT_CREATION:
      return 'Automated OT creation process is not active.'

    success_count, fail_count = 0, 0
    today = self._get_today()
    # Get all OT stages.
    ot_stages: list[Stage] = Stage.query(
        Stage.stage_type.IN(ALL_ORIGIN_TRIAL_STAGE_TYPES),
        Stage.ot_setup_status == OT_CREATED).fetch()
    for stage in ot_stages:
      # Only process stages with a delayed activation date set.
      if stage.ot_activation_date is None:
        continue
      # A stage with an activation date but no origin trial ID shouldn't be
      # possible.
      if stage.origin_trial_id is None:
        logging.exception('Stage has a set activation date with no set origin '
                          f'trial ID. stage={stage.key.integer_id()}')
        continue
      if today >= stage.ot_activation_date:
        logging.info(f'Activating trial {stage.origin_trial_id}')
        try:
          origin_trials_client.activate_origin_trial(stage.origin_trial_id)
        except requests.RequestException:
          cloud_tasks_helpers.enqueue_task(
              '/tasks/email-ot-activation-failed',
              {'stage': converters.stage_to_json_dict(stage)})
          stage.ot_setup_status = OT_ACTIVATION_FAILED
          stage.put()
          fail_count += 1
        else:
          cloud_tasks_helpers.enqueue_task(
              '/tasks/email-ot-activated',
              {'stage': converters.stage_to_json_dict(stage)})
          stage.ot_activation_date = None
          stage.ot_setup_status = OT_ACTIVATED
          stage.put()
          success_count += 1

    return (f'{success_count} activation(s) successfully processed and '
            f'{fail_count} activation(s) failed to process.')


class DeleteEmptyExtensionStages(FlaskHandler):
  """Delete any extension stages that have no information filled out."""

  def get_template_data(self, **kwargs) -> str:
    self.require_cron_header()

    # Fetch all extension stages.
    extension_stages: list[Stage] = Stage.query(
        Stage.stage_type.IN(
            [STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
             STAGE_FAST_EXTEND_ORIGIN_TRIAL,
             STAGE_DEP_EXTEND_DEPRECATION_TRIAL]
        )
    ).fetch()

    keys_to_delete = []
    counter = 0
    for es in extension_stages:
      # If an extension stage has no relevant information filled out yet,
      # delete it.
      has_milestone = (es.milestones and es.milestones.desktop_last)
      if (not es.intent_thread_url and not es.experiment_extension_reason and
          not has_milestone):
        counter += 1
        keys_to_delete.append(es.key)
        # Query for the gate associated with the extension and delete that too.
        gate = Gate.query(Gate.stage_id == es.key.integer_id()).get()
        if gate:
          keys_to_delete.append(gate.key)

      # Delete entities in batches of 200.
      if len(keys_to_delete) >= 200:
        ndb.delete_multi(keys_to_delete)
        keys_to_delete = []

    # Finally, delete the last entities marked for deletion.
    if len(keys_to_delete) > 0:
      ndb.delete_multi(keys_to_delete)

    return  (f'{counter} empty extension stages deleted.')


class BackfillShippingYear(FlaskHandler):

  def calc_all_shipping_years(self) -> dict[int, int]:
    """Load all shipping stages and record their earliest milestone."""
    shipping_stages = stage_helpers.get_all_shipping_stages_with_milestones()
    stages_by_fid = stage_helpers.organize_all_stages_by_feature(
        shipping_stages)
    all_features_shipping_year = {}
    for fid, feature_stages in stages_by_fid.items():
      earliest = stage_helpers.find_earliest_milestone(feature_stages)
      if earliest:
        year = stage_helpers.look_up_year(earliest)
        all_features_shipping_year[fid] = year

    return all_features_shipping_year

  def get_template_data(self, **kwargs) -> str:
    """Fill in shipping_year for any Feature Entry that has a milestone."""
    self.require_cron_header()

    all_features_shipping_year = self.calc_all_shipping_years()
    count = 0
    batch = []
    BATCH_SIZE = 100
    all_feature_entries = FeatureEntry.query().fetch()
    for fe in all_feature_entries:
      fid = fe.key.integer_id()
      if fid not in all_features_shipping_year:
        continue
      year_based_on_milestones = all_features_shipping_year[fid]
      if fe.shipping_year != year_based_on_milestones:
        fe.shipping_year = year_based_on_milestones
        batch.append(fe)
        count += 1
        if len(batch) > BATCH_SIZE:
          ndb.put_multi(batch)
          batch = []
          logging.info('Updated %r so far', count)

    ndb.put_multi(batch)
    return f'{count} Features entities updated.'


class BackfillGateDates(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """Backfill resolved_on and needs_work_started_on for all Gates."""
    self.require_cron_header()

    count = 0
    batch: list[Gate] = []
    BATCH_SIZE = 100
    votes_by_gate = collections.defaultdict(list)
    for vote in Vote.query():
      votes_by_gate[vote.gate_id].append(vote)
    for gate in Gate.query():
      gate_votes = votes_by_gate.get(gate.key.integer_id()) or []
      if self.calc_dates(gate, gate_votes):
        batch.append(gate)
        count += 1
        if len(batch) > BATCH_SIZE:
          ndb.put_multi(batch)
          batch = []

    ndb.put_multi(batch)
    return f'{count} Gate entities updated.'

  def calc_dates(self, gate: Gate, votes: list[Vote]) -> bool:
    """Set resolved_on and needs_work_started_on if needed."""
    if not votes:
      return False
    new_resolved_on = self.calc_resolved_on(gate, votes)
    new_needs_work_started_on = self.calc_needs_work_started_on(gate, votes)
    if new_resolved_on is not None:
      gate.resolved_on = new_resolved_on
    if new_needs_work_started_on is not None:
      gate.needs_work_started_on = new_needs_work_started_on
    return bool(new_resolved_on or new_needs_work_started_on)

  def calc_resolved_on(self, gate: Gate, votes: list[Vote]) -> datetime | None:
    """Return the date on which the gate was resolved, or None."""
    if gate.state not in Gate.FINAL_STATES:
      return None
    if gate.resolved_on:
      return None

    return max(v.set_on for v in votes
               if v.state in Gate.FINAL_STATES)

  def calc_needs_work_started_on(
      self, gate: Gate, votes: list[Vote]) -> datetime | None:
    """Return the latest date on which the gate entered NEEDS_WORK."""
    if gate.state != Vote.NEEDS_WORK:
      return None
    if gate.needs_work_started_on:
      return None

    return max(v.set_on for v in votes
               if v.state == Vote.NEEDS_WORK)


class FetchWebdxFeatureId(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """Fetch the complete list of Webdx feature ID available from
    webstatus.dev APIs and store them in datastore.
    """
    self.require_cron_header()

    client = DefaultApi(ApiClient(Configuration(settings.API_WEBSTATUS_DEV_URL)))

    all_data_list: list[Feature] = []
    page_token: str | None = None
    is_first: bool = True
    while is_first or page_token:
      try:
        resp = client.list_features(page_token=page_token, page_size=100)
        all_data_list.extend(resp.data)
        page_token = resp.metadata.next_page_token
        is_first = False
      except ApiException as e:
        logging.error(
            'Could not fetch from %s?page_token=%s: %s',
            settings.API_WEBSTATUS_DEV_URL, page_token, e)
        return 'Running FetchWebdxFeatureId() job failed.'

    feature_ids_list = [feature_data.feature_id for feature_data in all_data_list]
    WebdxFeatures.store_webdx_feature_id_list(feature_ids_list)
    return (f'{len(feature_ids_list)} feature ids are successfully stored.')


class SendManualOTCreatedEmail(FlaskHandler):
  """Manually send an email to origin trial contacts that an origin trial has
  been created but not yet activated."""

  def get_template_data(self, **kwargs):
    self.require_cron_header()

    stage_id = kwargs.get('stage_id')
    stage: Stage|None = Stage.get_by_id(stage_id)
    if not stage:
      return f'Stage {stage_id} not found'
    if stage.stage_type not in ALL_ORIGIN_TRIAL_STAGE_TYPES:
      return f'Stage {stage_id} is not an origin trial stage'
    if not stage.ot_owner_email and not stage.ot_emails:
      return f'Stage {stage_id} has no OT contacts set'
    if not stage.ot_display_name:
      return f'Stage {stage_id} does not have ot_display_name set'
    if stage.ot_activation_date is None:
      return f'Stage {stage_id} does not have ot_activation_date set'

    cloud_tasks_helpers.enqueue_task(
        '/tasks/email-ot-creation-processed',
        {'stage': converters.stage_to_json_dict(stage)})
    return 'Email task enqueued'


class SendManualOTActivatedEmail(FlaskHandler):
  """Manually send an email to origin trial contacts that an origin trial has
  been created and also activated."""

  def get_template_data(self, **kwargs):
    self.require_cron_header()

    stage_id = kwargs.get('stage_id')
    stage: Stage|None = Stage.get_by_id(stage_id)
    if not stage:
      return f'Stage {stage_id} not found'
    if stage.stage_type not in ALL_ORIGIN_TRIAL_STAGE_TYPES:
      return f'Stage {stage_id} is not an origin trial stage'
    if not stage.ot_owner_email and not stage.ot_emails:
      return f'Stage {stage_id} has no OT contacts set'
    if not stage.ot_display_name:
      return f'Stage {stage_id} does not have ot_display_name set'

    cloud_tasks_helpers.enqueue_task(
        '/tasks/email-ot-activated',
        {'stage': converters.stage_to_json_dict(stage)})
    return 'Email task enqueued'


class GenerateReviewActivityFile(FlaskHandler):
  """Generate a CSV file with all review activity in ChromeStatus."""
  DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
  VOTE_VALUE_MAPPING: dict[str, SkyhookDashStatus] = {
      'na': SkyhookDashStatus.FYI,
      'review_requested': SkyhookDashStatus.PENDING_REVIEW,
      'review_started': SkyhookDashStatus.PENDING_REVIEW,
      'needs_work': SkyhookDashStatus.NEEDS_WORK,
      'approved': SkyhookDashStatus.APPROVED,
      'denied': SkyhookDashStatus.DENIED,
      'internal_review': SkyhookDashStatus.PENDING_REVIEW,
      'na (self-certified)': SkyhookDashStatus.FYI,
      'na_requested': SkyhookDashStatus.PENDING_REVIEW,
      'na (verified)': SkyhookDashStatus.FYI,
      'no_response': SkyhookDashStatus.PENDING_REVIEW,
  }

  def _get_skyhook_status(self, review_status: str | None) -> str:
    if review_status is None:
      logging.warning('Event changed review status to null value.')
      return ''
    if review_status not in self.VOTE_VALUE_MAPPING:
      logging.warning(f'No status mapping found for status {review_status}.')
      return ''
    return self.VOTE_VALUE_MAPPING[review_status].value

  def _generate_new_activities(
    self,
    start_timestamp: datetime,
    end_timestamp: datetime
  ) -> list[list[str]]:
    """Generate a list of rows to add to the review activity CSV."""
    # Note: We assume that anyone may view approval comments.
    activities: list[Activity] = Activity.query(
      Activity.created > start_timestamp,
      Activity.created <= end_timestamp,
    ).order(Activity.created).fetch()

    # Filter deleted activities the user can't see, and activities that have
    # no gate ID, meaning they do not represent review activity.
    # TODO(DanielRyanSmith): Confirm if deleted features should deleted features
    # should have existing activity filtered and handle accordingly.
    activities = list(filter(
      lambda a: (a.deleted_by is None
                 and a.gate_id is not None),
      activities))
    if activities is None:
      return []

    gate_ids = set(a.gate_id for a in activities)
    gates = ndb.get_multi(ndb.Key('Gate', g_id) for g_id in gate_ids)
    gates_dict: dict[int, Gate] = {g.key.integer_id(): g for g in gates if g}

    csv_rows: list[list[str]] = []
    for a in activities:
      if a.gate_id not in gates_dict:
        logging.warning(f'No gate found for gate ID {a.gate_id}')
        continue
      gate = gates_dict[a.gate_id]
      review_status = ''
      review_assignee = ''
      comment = a.content or ''
      if len(a.amendments):
        # There should only be 1 amendment for review changes.
        if a.amendments[0].field_name == 'review_status':
          review_status = self._get_skyhook_status(a.amendments[0].new_value)
        if a.amendments[0].field_name == 'review_assignee':
          review_assignee = a.amendments[0].new_value
      csv_rows.append(
        [
          f'{settings.SITE_URL}feature/{a.feature_id}',
          approval_defs.APPROVAL_FIELDS_BY_ID[gate.gate_type].team_name,
          a.amendments[0].field_name if len(a.amendments) else 'comment',
          str(datetime.strftime(a.created, self.DATE_FORMAT)),
          review_status,
          review_assignee,
          a.author or '',
          comment,
          'chromestatus',
        ]
      )

    return csv_rows

  def _get_activities_csv(self, bucket):
    blob = bucket.blob('chromestatus-review-activity.csv')
    csv_io = StringIO()
    if blob.exists():
      with blob.open('r') as f:
        csv_rows = csv.reader(f, lineterminator='\n')
        row_count = 0
        activities_csv = csv.writer(csv_io, lineterminator='\n')
        for row in csv_rows:
          row_count += 1
          activities_csv.writerow(row)
        logging.info(f'Existing csv is {row_count} lines long')
        return activities_csv, csv_io

    writer = csv.writer(csv_io, lineterminator='\n')
    writer.writerow(
      [
        'launch_id',
        'reviewer_name',
        'event_type',
        'date',
        'status',
        'assignee',
        'author',
        'content',
        'source',
       ]
    )
    return writer, csv_io

  def _get_last_run_timestamp(self, bucket):
    """Get the timestamp for the starting interval of querying for new
    activities."""
    blob = bucket.blob('review-activity-last-timestamp.txt')
    if blob.exists():
      with blob.open('r') as f:
        timestamp_str = f.read()
      return datetime.strptime(timestamp_str, self.DATE_FORMAT)
    # If no previous timestamp exists, start from the beginning.
    return datetime(2000, 1, 1)

  def _write_csv(self, bucket, csv_io: StringIO) -> None:
    """Append the rows to the review activity CSV, or create a new CSV if it
    does not exist."""
    blob = bucket.blob('chromestatus-review-activity.csv')
    blob.upload_from_string(csv_io.getvalue())

  def _write_last_run_timestamp(self, bucket, timestamp: datetime) -> None:
    """Store the date of the last review activity run."""
    blob = bucket.blob('review-activity-last-timestamp.txt')
    blob.upload_from_string(timestamp.strftime(self.DATE_FORMAT))

  def get_template_data(self, **kwargs):
    self.require_cron_header()

    storage_client = storage.Client()
    bucket = storage_client.bucket(settings.FILES_BUCKET)

    last_run_timestamp = self._get_last_run_timestamp(bucket)
    now = datetime.now()
    csv_rows = self._generate_new_activities(last_run_timestamp, now)
    logging.info(f'{len(csv_rows)} new rows to add to CSV.')
    if csv_rows:
      activities_csv, csv_io = self._get_activities_csv(bucket)
      for row in csv_rows:
        activities_csv.writerow(row)
      self._write_csv(bucket, csv_io)
    self._write_last_run_timestamp(bucket, now)

    return (f'{len(csv_rows)} '
            'new rows added to chromestatus-review-activity.csv uploaded.')


class MigrateRolloutMilestones(FlaskHandler):
  """Migrate the rollout milestone field to be stored in the 'milestones' field."""

  def get_template_data(self, **kwargs):
    self.require_cron_header()
    stages: list[Stage] = Stage.query(Stage.stage_type == STAGE_ENT_ROLLOUT).fetch()
    changed_stages: list[Stage] = []
    for stage in stages:
      if stage.milestones and stage.milestones.desktop_first:
        continue
      if not stage.milestones:
        stage.milestones = MilestoneSet()
      # desktop_first will be considered the default "start" milestone.
      stage.milestones.desktop_first = stage.rollout_milestone
      changed_stages.append(stage)
      if len(changed_stages) >= 200:
        ndb.put_multi(changed_stages)
        changed_stages = []
    if changed_stages:
      ndb.put_multi(changed_stages)
