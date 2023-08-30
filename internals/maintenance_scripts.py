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

import datetime
import logging
from typing import Any
from google.cloud import ndb  # type: ignore

from framework.basehandlers import FlaskHandler
from framework import origin_trials_client
from internals import approval_defs
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Gate, Vote, Activity
from internals.core_enums import *
from internals.feature_links import batch_index_feature_entries

class EvaluateGateStatus(FlaskHandler):

  def get_template_data(self, **kwargs):
    """Evaluate all existing Gate entities and set correct state."""
    self.require_cron_header()

    gates: ndb.Query = Gate.query()
    count = 0
    batch = []
    BATCH_SIZE = 100
    for gate in gates:
      if approval_defs.update_gate_approval_state(gate):
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

  def make_needed_gates(self, fe, stage, existing_gates):
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

  def get_template_data(self, **kwargs):
    """Create a chunk of needed gates for all features."""
    self.require_cron_header()

    all_feature_entries = FeatureEntry.query().fetch()
    fe_by_id = {fe.key.integer_id(): fe
                for fe in all_feature_entries}
    existing_gates_by_stage_id = collections.defaultdict(list)
    for gate in Gate.query():
      existing_gates_by_stage_id[gate.stage_id].append(gate)

    gates_to_write: list(Gate) = []
    for stage in Stage.query():
      new_gates = self.make_needed_gates(
          fe_by_id.get(stage.feature_id), stage,
          existing_gates_by_stage_id[stage.key.integer_id()])
      gates_to_write.extend(new_gates)
      if len(gates_to_write) > self.GATES_TO_CREATE_PER_RUN:
        break  # Stop early if we risk exceeding GAE timeout.

    ndb.put_multi(gates_to_write)

    return f'{len(gates_to_write)} missing gates created for stages.'


class MigrateGeckoViews(FlaskHandler):

  MAPPING = {
      GECKO_IMPORTANT: PUBLIC_SUPPORT,
      GECKO_WORTH_PROTOTYPING: PUBLIC_SUPPORT,
      GECKO_NONHARMFUL: NEUTRAL,
      GECKO_HARMFUL: OPPOSED,
      }

  def update_ff_views(self, fe):
    """Update ff_views and return True if update was needed."""
    if fe.ff_views in self.MAPPING:
      fe.ff_views = self.MAPPING[fe.ff_views]
      return True

    return False

  def get_template_data(self, **kwargs):
    """Change gecko views from old options to a more common list."""
    self.require_cron_header()

    features: ndb.Query = FeatureEntry.query(
        FeatureEntry.ff_views != NO_PUBLIC_SIGNALS)
    count = 0
    batch = []
    BATCH_SIZE = 100
    for fe in features:
      if self.update_ff_views(fe):
        batch.append(fe)
        count += 1
        if len(batch) > BATCH_SIZE:
          ndb.put_multi(batch)
          batch = []

    ndb.put_multi(batch)
    return f'{count} FeatureEntry entities updated.'


class BackfillRespondedOn(FlaskHandler):

  def update_responded_on(self, gate):
    """Update gate.responded_on and return True if an update was needed."""
    gate_id = gate.key.integer_id()
    earliest_response = datetime.datetime.max

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

    if earliest_response != datetime.datetime.max:
      gate.responded_on = earliest_response
      return True
    else:
      return False

  def get_template_data(self, **kwargs):
    """Backfill responded_on dates for existing gates."""
    self.require_cron_header()
    gates: ndb.Query = Gate.query(Gate.requested_on != None)
    count = 0
    batch = []
    BATCH_SIZE = 100
    for g in gates:
      if g.responded_on:
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
  def get_template_data(self, **kwargs):
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
  def get_template_data(self, **kwargs):
    """Backfill feature links for existing feature entries."""
    self.require_cron_header()
    all_feature_entries = FeatureEntry.query().fetch()
    count = batch_index_feature_entries(all_feature_entries, True)
    return f'{len(all_feature_entries)} FeatureEntry entities backfilled of {count} feature links.'


class AssociateOTs(FlaskHandler):

  def write_fields_for_trial_stage(self, trial_stage: Stage, trial_data: dict[str, Any]):
    """Check if any OT stage fields are unfilled and populate them with
    the matching trial data.
    """
    if trial_stage.origin_trial_id is None:
      trial_stage.origin_trial_id = trial_data['id']

    if trial_stage.ot_chromium_trial_name is None:
      trial_stage.ot_chromium_trial_name = trial_data['origin_trial_feature_name']

    if trial_stage.milestones is None:
      trial_stage.milestones = MilestoneSet()
    if (trial_stage.milestones.desktop_first is None and
        trial_data['start_milestone'] is not None):
      trial_stage.milestones.desktop_first = int(trial_data['start_milestone'])
    if trial_stage.milestones.desktop_last is None:
      # An original end milestone is kept if the trial has had extensions.
      # TODO(DanielRyanSmith): Extension milestones in the trial data
      # should be associated with new extension stages for data accuracy.
      if trial_data['original_end_milestone'] is not None:
        trial_stage.milestones.desktop_last = (
            int(trial_data['original_end_milestone']))
      elif trial_data['end_milestone'] is not None:
        trial_stage.milestones.desktop_last = (
            int(trial_data['end_milestone']))

    if trial_stage.display_name is None:
      trial_stage.display_name = trial_data['display_name']

    if trial_stage.intent_thread_url is None:
      trial_stage.intent_thread_url = trial_data['intent_to_experiment_url']

    if trial_stage.origin_trial_feedback_url is None:
      trial_stage.origin_trial_feedback_url = trial_data['feedback_url']

    if trial_stage.ot_documentation_url is None:
      trial_stage.ot_documentation_url = trial_data['documentation_url']

    if trial_stage.ot_has_third_party_support:
      trial_stage.ot_has_third_party_support = trial_data['allow_third_party_origins']

    if not trial_stage.ot_is_deprecation_trial:
      trial_stage.ot_is_deprecation_trial = trial_data['type'] == 'DEPRECATION'

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

  def find_trial_stage(self, feature_id: int) -> Stage|None:
      fe: FeatureEntry|None = FeatureEntry.get_by_id(feature_id)
      if fe is None:
        logging.info(f'No feature found for ChromeStatus ID: {feature_id}')
        return None

      trial_stage_type = STAGE_TYPES_ORIGIN_TRIAL[fe.feature_type]
      trial_stages = Stage.query(
          Stage.stage_type == trial_stage_type,
          Stage.feature_id == feature_id).fetch()
      # If there are no OT stages for the feature, we can't associate the
      # trial with any stages.
      if len(trial_stages) == 0:
        logging.info(f'No OT stages found for feature ID: {feature_id}')
        return None
      # If there is currently more than one origin trial stage for the
      # feature, we don't know which one represents the given trial.
      if len(trial_stages) > 1:
        logging.info('Multiple origin trial stages found for feature '
                     f'{feature_id}. Cannot discern which stage to associate '
                     'trial with.')
        return None
      return trial_stages[0]

  def get_template_data(self, **kwargs):
    """Link existing origin trials with their ChromeStatus entry"""
    self.require_cron_header()

    trials_list = origin_trials_client.get_trials_list()
    entities_to_write: list[Stage] = []
    trials_with_no_feature: list[str] = []
    for trial_data in trials_list:
      stage = Stage.query(
          Stage.origin_trial_id == trial_data['id']).get()
      # If this trial is already associated with a ChromeStatus stage,
      # just see if any unfilled fields need to be populated.
      if stage:
        self.write_fields_for_trial_stage(stage, trial_data)
        entities_to_write.append(stage)
        continue

      feature_id = self.parse_feature_id(trial_data['chromestatus_url'])
      if feature_id is None:
        trials_with_no_feature.append(trial_data)
        continue

      ot_stage = self.find_trial_stage(feature_id)
      if ot_stage is None:
        trials_with_no_feature.append(trial_data)
        continue

      self.write_fields_for_trial_stage(ot_stage, trial_data)
      entities_to_write.append(ot_stage)

    # List any origin trials that did not get associated with a feature entry.
    if len(trials_with_no_feature) > 0:
      logging.info('Trials not associated with a ChromeStatus feature:')
    else:
      logging.info('All trials associated with a ChromeStatus feature!')
    for trial_data in trials_with_no_feature:
      logging.info(f'{trial_data["id"]} {trial_data["display_name"]}')

    # Update all the stages at the end. Note that there is a chance
    # the stage entities have not changed any values if all fields already
    # had a value.
    logging.info(f'{len(entities_to_write)} stages to update.')
    if len(entities_to_write) > 0:
      ndb.put_multi(entities_to_write)

    return f'{len(entities_to_write)} Stages updated with trial data.'
