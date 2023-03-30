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
from internals import approval_defs
from internals.core_models import FeatureEntry, Stage
from internals.legacy_models import Feature
from internals.review_models import Gate, Vote
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
