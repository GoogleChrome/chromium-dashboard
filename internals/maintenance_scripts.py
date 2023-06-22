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
from google.cloud import ndb  # type: ignore

from framework.basehandlers import FlaskHandler
from internals import approval_defs
from internals.core_models import FeatureEntry, Stage
from internals.review_models import Gate, Vote, Activity
from internals.core_enums import *


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
