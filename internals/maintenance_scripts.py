# ruff: noqa: D205
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

"""Cron handlers for background maintenance tasks like updating gate statuses and backfilling entities."""

import collections
import csv
import logging
from datetime import date, datetime, timedelta
from io import StringIO
from typing import Any

import json5
import requests
from google.cloud import ndb, storage  # type: ignore
from webstatus_openapi import (
    ApiClient,
    ApiException,
    Configuration,
    DefaultApi,
    Feature,
)

import settings
from api import converters
from framework import cloud_tasks_helpers, origin_trials_client, utils
from framework.basehandlers import FlaskHandler
from internals import approval_defs, core_enums, feature_helpers, stage_helpers
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.feature_links import batch_index_feature_entries
from internals.review_models import Activity, Amendment, Gate, Vote
from internals.webdx_feature_models import WebdxFeatures


class EvaluateGateStatus(FlaskHandler):
    """Handler to evaluate and set gate status."""

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
                gate, votes_by_gate[gate.key.integer_id()]
            ):
                batch.append(gate)
                count += 1
                if len(batch) > BATCH_SIZE:
                    ndb.put_multi(batch)
                    batch = []

        ndb.put_multi(batch)
        return f'{count} Gate entities updated.'


class WriteMissingGates(FlaskHandler):
    """Handler to write missing gates for features."""

    GATES_TO_CREATE_PER_RUN = 5000

    GATE_RULES: dict[int, dict[int, list[int]]] = {
        fe_type: dict(stages_and_gates)
        for fe_type, stages_and_gates in core_enums.STAGES_AND_GATES_BY_FEATURE_TYPE.items()
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
            if any(
                eg for eg in existing_gates if eg.gate_type == needed_gate_type
            ):
                continue
            earliest = stage_helpers.find_earliest_milestone([stage])
            phase_in_starting = core_enums.GATE_PHASE_IN.get(
                needed_gate_type, 0
            )
            if earliest and earliest < phase_in_starting:
                continue
            gate = Gate(
                feature_id=stage.feature_id,
                stage_id=stage.key.integer_id(),
                gate_type=needed_gate_type,
                state=Gate.PREPARING,
            )
            new_gates.append(gate)
        return new_gates

    def get_template_data(self, **kwargs) -> str:
        """Create a chunk of needed gates for all features."""
        self.require_cron_header()

        all_feature_entries = FeatureEntry.query().fetch()
        fe_by_id = {fe.key.integer_id(): fe for fe in all_feature_entries}
        existing_gates_by_stage_id = collections.defaultdict(list)
        for gate in Gate.query():
            existing_gates_by_stage_id[gate.stage_id].append(gate)

        gates_to_write: list[Gate] = []
        for stage in Stage.query():
            new_gates = self.make_needed_gates(
                fe_by_id.get(stage.feature_id),
                stage,
                existing_gates_by_stage_id[stage.key.integer_id()],
            )
            gates_to_write.extend(new_gates)
            if len(gates_to_write) > self.GATES_TO_CREATE_PER_RUN:
                break  # Stop early if we risk exceeding GAE timeout.

        ndb.put_multi(gates_to_write)

        return f'{len(gates_to_write)} missing gates created for stages.'


class BackfillRespondedOn(FlaskHandler):
    """Handler to backfill the responded_on field for gates."""

    def update_responded_on(self, gate) -> bool:
        """Update gate.responded_on and return True if an update was needed."""
        gate_id = gate.key.integer_id()
        earliest_response = datetime.max

        approvers = approval_defs.get_approvers(gate.gate_type)
        activities = Activity.get_activities(
            gate.feature_id, gate_id=gate_id, comments_only=True
        )
        for a in activities:
            if gate.requested_on < a.created < earliest_response:
                if a.author in approvers:
                    earliest_response = a.created
                    logging.info(
                        f'Set feature {gate.feature_id} gate {gate_id} '
                        f'to {a.created} because of comment'
                    )

        votes = Vote.get_votes(gate_id=gate_id)
        for v in votes:
            if gate.requested_on < v.set_on < earliest_response:
                earliest_response = v.set_on
                logging.info(
                    f'Set feature {gate.feature_id} gate {gate_id} '
                    f'to {v.set_on} because of vote'
                )

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
    """Handler to backfill the created date for stages."""

    def get_template_data(self, **kwargs) -> str:
        """Backfill created dates for existing stages."""
        self.require_cron_header()
        count = 0
        batch = []
        BATCH_SIZE = 100
        stages: ndb.Query = Stage.query()
        for stage in stages:
            feature_entry = FeatureEntry.get_by_id(stage.feature_id)
            if feature_entry is None or stage.created is not None:
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
    """Handler to backfill feature links."""

    def get_template_data(self, **kwargs) -> str:
        """Backfill feature links for existing feature entries."""
        self.require_cron_header()
        all_feature_entries = FeatureEntry.query().fetch()
        count = batch_index_feature_entries(all_feature_entries, True)
        return f'{len(all_feature_entries)} FeatureEntry entities backfilled of {count} feature links.'


class AssociateOTs(FlaskHandler):
    """Handler to associate Origin Trials with features."""

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
        if (
            not getattr(trial_stage, stage_field_name)
            and trial_data[trial_field_name]
        ):
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
        if (
            getattr(trial_stage.milestones, stage_field_name) is None
            and trial_data[trial_field_name] is not None
        ):
            setattr(
                trial_stage.milestones,
                stage_field_name,
                int(trial_data[trial_field_name]),
            )
            return True
        return False

    def write_fields_for_trial_stage(
        self, trial_stage: Stage, trial_data: dict[str, Any]
    ) -> bool:
        """Check if any OT stage fields are unfilled and populate them with
        the matching trial data.
        """
        stage_changed = False
        stage_changed = (
            self.write_field(trial_stage, trial_data, 'origin_trial_id', 'id')
            or stage_changed
        )
        stage_changed = (
            self.write_field(
                trial_stage,
                trial_data,
                'ot_chromium_trial_name',
                'origin_trial_feature_name',
            )
            or stage_changed
        )
        stage_changed = (
            self.write_field(
                trial_stage,
                trial_data,
                'ot_feedback_submission_url',
                'feedback_url',
            )
            or stage_changed
        )
        stage_changed = (
            self.write_field(
                trial_stage,
                trial_data,
                'ot_documentation_url',
                'documentation_url',
            )
            or stage_changed
        )
        stage_changed = (
            self.write_field(
                trial_stage,
                trial_data,
                'intent_thread_url',
                'intent_to_experiment_url',
            )
            or stage_changed
        )
        stage_changed = (
            self.write_field(
                trial_stage, trial_data, 'display_name', 'display_name'
            )
            or stage_changed
        )
        stage_changed = (
            self.write_field(
                trial_stage, trial_data, 'ot_display_name', 'display_name'
            )
            or stage_changed
        )
        stage_changed = (
            self.write_field(
                trial_stage,
                trial_data,
                'ot_has_third_party_support',
                'allow_third_party_origins',
            )
            or stage_changed
        )
        stage_changed = (
            self.write_milestone_field(
                trial_stage, trial_data, 'desktop_first', 'start_milestone'
            )
            or stage_changed
        )
        stage_changed = (
            self.write_milestone_field(
                trial_stage,
                trial_data,
                'desktop_last',
                'original_end_milestone',
            )
            or stage_changed
        )

        if not trial_stage.ot_is_deprecation_trial:
            trial_stage.ot_is_deprecation_trial = (
                trial_data['type'] == 'DEPRECATION'
            )
            stage_changed = True

        # Clear the trial creation request if it's active.
        if trial_stage.ot_action_requested:
            trial_stage.ot_action_requested = False
            stage_changed = True

        # Set the setup status to complete if the trial is created or activated.
        trial_activated = (
            trial_data['status'] == 'ACTIVE'
            or trial_data['status'] == 'COMPLETE'
        )
        if (
            trial_stage.ot_setup_status != core_enums.OT_ACTIVATED
            and trial_activated
        ):
            trial_stage.ot_setup_status = core_enums.OT_ACTIVATED
            stage_changed = True

        return stage_changed

    def parse_feature_id(self, chromestatus_url: str | None) -> int | None:
        """Parse feature id."""
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
                f'Unable to parse ID from ChromeStatus URL: {chromestatus_url}'
            )
            return None
        return chromestatus_id

    def find_unassociated_trial_stage(self, feature_id: int) -> Stage | None:
        """Find unassociated trial stage."""
        fe: FeatureEntry | None = FeatureEntry.get_by_id(feature_id)
        if fe is None:
            logging.info(f'No feature found for ChromeStatus ID: {feature_id}')
            return None

        trial_stage_type = core_enums.STAGE_TYPES_ORIGIN_TRIAL[fe.feature_type]
        trial_stages: list[Stage] = Stage.query(
            Stage.stage_type == trial_stage_type, Stage.feature_id == feature_id
        ).fetch()
        # Look for a stage that does not already have an origin trial associated
        # with it.
        unassociated_trial_stages = [
            s for s in trial_stages if not s.origin_trial_id
        ]
        if len(unassociated_trial_stages) > 1:
            logging.info(
                'Multiple origin trial stages found for feature '
                f'{feature_id}. Cannot discern which stage to associate '
                'trial with.'
            )
            return None
        if len(unassociated_trial_stages) == 0:
            logging.info(
                f'No unassociated OT stages found for feature ID: {feature_id}'
            )
            return None
        return unassociated_trial_stages[0]

    def clear_extension_requests(
        self, ot_stage: Stage, trial_data: dict
    ) -> int:
        """Clear any trial extension requests if they have been processed."""
        extension_stages: list[Stage] = Stage.query(
            Stage.ot_action_requested == True,  # noqa: E712
            Stage.ot_stage_id == ot_stage.key.integer_id(),
        ).fetch()
        if len(extension_stages) == 0:
            return 0
        extension_stages_to_update = []
        for extension_stage in extension_stages:
            # skip the stage if it doesn't have an end milestone explicitly defined.
            if (
                extension_stage.milestones is None
                or not extension_stage.milestones.desktop_last
            ):
                continue
            extension_end = extension_stage.milestones.desktop_last
            # If the end milestone of the trial is equal or greater than the
            # requested end milestone on the extension stage, we can assume the
            # extension request has been processed.
            if int(trial_data['end_milestone']) >= extension_end:
                extension_stage.ot_action_requested = False
                extension_stages_to_update.append(extension_stage)

        if extension_stages_to_update:
            ndb.put_multi(extension_stages_to_update)
        return len(extension_stages_to_update)

    def get_template_data(self, **kwargs) -> str:
        """Link existing origin trials with their ChromeStatus entry."""
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
                Stage.origin_trial_id == trial_data['id']
            ).get()
            if stage and stage.key.integer_id() in unique_entities_to_write:
                logging.info(
                    f'Already writing to Stage entity {stage.key.integer_id()}'
                )
                continue

            # If this trial is already associated with a ChromeStatus stage,
            # just see if any unfilled fields need to be populated and clear
            # any pending extension requests.
            if stage:
                stage_changed = self.write_fields_for_trial_stage(
                    stage, trial_data
                )
                if stage_changed:
                    unique_entities_to_write.add(stage.key.integer_id())
                    entities_to_write.append(stage)
                extensions_cleared += self.clear_extension_requests(
                    stage, trial_data
                )
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

            stage_changed = self.write_fields_for_trial_stage(
                ot_stage, trial_data
            )
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

        return (
            f'{len(entities_to_write)} Stages updated with trial data.\n'
            f'{extensions_cleared} extension requests cleared.'
        )


class BackfillFeatureEnterpriseImpact(FlaskHandler):
    """Handler to backfill the enterprise_impact field for features."""

    def get_template_data(self, **kwargs) -> str:
        """Backfill enterprise_impact firld for all features."""
        self.require_cron_header()
        count = 0
        batch = []
        BATCH_SIZE = 100
        updated_feature_ids = set()
        features_by_id = {}

        stages: ndb.Query = Stage.query(
            Stage.stage_type == core_enums.STAGE_ENT_ROLLOUT,
            Stage.archived == False,  # noqa: E501, E712, F405
        )
        for stage in stages:
            if stage.feature_id in features_by_id:
                continue
            features_by_id[stage.feature_id] = FeatureEntry.get_by_id(
                stage.feature_id
            )
        # Update enterprise_impact to be the highest impact set on any of the rollout steps.
        for stage in stages:
            feature_entry = features_by_id[stage.feature_id]
            if feature_entry is None:
                continue
            new_impact = stage.rollout_impact + 1
            if new_impact <= feature_entry.enterprise_impact:
                continue
            feature_entry.enterprise_impact = new_impact
            updated_feature_ids.add(stage.feature_id)

        # Set all enterprise features and former breaking changes to have a low impact if no rollout step was step.
        features: ndb.Query = FeatureEntry.query(
            FeatureEntry.enterprise_impact == core_enums.ENTERPRISE_IMPACT_NONE,
            ndb.OR(
                FeatureEntry.feature_type
                == core_enums.FEATURE_TYPE_ENTERPRISE_ID,
                FeatureEntry.breaking_change == True,  # noqa: E501, E712, F405
            ),
        )
        for feature_entry in features:
            if feature_entry.key.id() in updated_feature_ids:
                continue
            features_by_id[feature_entry.key.id()] = feature_entry
            updated_feature_ids.add(feature_entry.key.id())
            feature_entry.enterprise_impact = (
                core_enums.ENTERPRISE_IMPACT_MEDIUM
            )

        for feature_id in updated_feature_ids:
            batch.append(features_by_id[feature_id])
            count += 1
            if len(batch) > BATCH_SIZE:
                ndb.put_multi(batch)
                logging.info(
                    f'Feature updated: Finished a batch of {BATCH_SIZE}'
                )
                batch = []

        ndb.put_multi(batch)

        return f'{count} Feature entities updated of {len(features_by_id)} available features.'


class CreateOriginTrials(FlaskHandler):
    """Handler to create Origin Trials."""

    def _send_creation_result_notification(
        self, task_path: str, stage: Stage, params: dict | None = None
    ) -> None:
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
            stage
        )
        if origin_trial_id:
            stage.origin_trial_id = origin_trial_id
        if error_text:
            logging.warning(
                'Origin trial could not be created for stage '
                f'{stage.key.integer_id()}'
            )
            stage.ot_setup_status = core_enums.OT_CREATION_FAILED
            self._send_creation_result_notification(
                '/tasks/email-ot-creation-request-failed',
                stage,
                {'error_text': error_text},
            )
            return False
        else:
            stage.ot_setup_status = core_enums.OT_CREATED
            logging.info(
                f'Origin trial created for stage {stage.key.integer_id()}'
            )
        return True

    def handle_activation(self, stage: Stage) -> None:
        """Send trial activation request."""
        try:
            origin_trials_client.activate_origin_trial(stage.origin_trial_id)
            stage.ot_setup_status = core_enums.OT_ACTIVATED
            self._send_creation_result_notification(
                '/tasks/email-ot-activated', stage
            )
        except requests.RequestException:
            # The activation still needs to occur,
            # so the activation date is set for current date.
            stage.ot_activation_date = date.today()
            stage.ot_setup_status = core_enums.OT_ACTIVATION_FAILED
            self._send_creation_result_notification(
                '/tasks/email-ot-activation-failed', stage
            )

    def _get_today(self) -> date:
        return date.today()

    def prepare_for_activation(self, stage: Stage) -> None:
        """Set up activation date or activate trial now."""
        mstone_info = utils.get_chromium_milestone_info(
            stage.milestones.desktop_first
        )
        date = datetime.strptime(
            mstone_info['mstones'][0]['branch_point'],
            utils.CHROMIUM_SCHEDULE_DATE_FORMAT,
        ).date()
        if date <= self._get_today():
            print(
                'sending for activation. Today:',
                self._get_today(),
                'branch_date: ',
                date,
            )
            self.handle_activation(stage)
        else:
            stage.ot_activation_date = date
            stage.ot_setup_status = core_enums.OT_CREATED
            self._send_creation_result_notification(
                '/tasks/email-ot-creation-processed', stage
            )

    @ndb.transactional()
    def _claim_stage_for_creation(self, stage_id: int) -> Stage | None:
        """Transactionally claim a stage for creation processing."""
        stage: Stage | None = Stage.get_by_id(stage_id)
        if stage and stage.ot_setup_status == core_enums.OT_READY_FOR_CREATION:
            stage.ot_setup_status = core_enums.OT_CREATION_PROCESSING
            stage.ot_action_requested = False
            stage.put()
            return stage
        return None

    def get_template_data(self, **kwargs) -> str:
        """Create any origin trials that are flagged for creation."""
        self.require_cron_header()
        if not settings.AUTOMATED_OT_CREATION:
            return 'Automated OT creation process is not active.'

        # OT stages that are flagged to process a trial creation.
        ot_stage_keys: list[ndb.Key] = Stage.query(
            Stage.ot_setup_status == core_enums.OT_READY_FOR_CREATION
        ).fetch(keys_only=True)

        count = 0
        for key in ot_stage_keys:
            stage = self._claim_stage_for_creation(key.integer_id())
            if not stage:
                continue

            creation_success = self.handle_creation(stage)
            if creation_success:
                self.prepare_for_activation(stage)
            stage.put()
            count += 1

        return f'{count} trial creation request(s) processed.'


class ActivateOriginTrials(FlaskHandler):
    """Handler to activate Origin Trials."""

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
            Stage.stage_type.IN(core_enums.ALL_ORIGIN_TRIAL_STAGE_TYPES),
            Stage.ot_setup_status == core_enums.OT_CREATED,
        ).fetch()
        for stage in ot_stages:
            # Only process stages with a delayed activation date set.
            if stage.ot_activation_date is None:
                continue
            # A stage with an activation date but no origin trial ID shouldn't be
            # possible.
            if stage.origin_trial_id is None:
                logging.exception(
                    'Stage has a set activation date with no set origin '
                    f'trial ID. stage={stage.key.integer_id()}'
                )
                continue
            if today >= stage.ot_activation_date:
                logging.info(f'Activating trial {stage.origin_trial_id}')
                try:
                    origin_trials_client.activate_origin_trial(
                        stage.origin_trial_id
                    )
                except requests.RequestException:
                    cloud_tasks_helpers.enqueue_task(
                        '/tasks/email-ot-activation-failed',
                        {'stage': converters.stage_to_json_dict(stage)},
                    )
                    stage.ot_setup_status = core_enums.OT_ACTIVATION_FAILED
                    stage.put()
                    fail_count += 1
                else:
                    cloud_tasks_helpers.enqueue_task(
                        '/tasks/email-ot-activated',
                        {'stage': converters.stage_to_json_dict(stage)},
                    )
                    stage.ot_activation_date = None
                    stage.ot_setup_status = core_enums.OT_ACTIVATED
                    stage.put()
                    success_count += 1

        return (
            f'{success_count} activation(s) successfully processed and '
            f'{fail_count} activation(s) failed to process.'
        )


class DeleteEmptyExtensionStages(FlaskHandler):
    """Delete any extension stages that have no information filled out."""

    def get_template_data(self, **kwargs) -> str:
        """Get template data."""
        self.require_cron_header()

        # Fetch all extension stages.
        extension_stages: list[Stage] = Stage.query(
            Stage.stage_type.IN(
                [
                    core_enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL,
                    core_enums.STAGE_FAST_EXTEND_ORIGIN_TRIAL,
                    core_enums.STAGE_DEP_EXTEND_DEPRECATION_TRIAL,
                ]
            )
        ).fetch()

        keys_to_delete = []
        counter = 0
        for es in extension_stages:
            # If an extension stage has no relevant information filled out yet,
            # delete it.
            has_milestone = es.milestones and es.milestones.desktop_last
            if (
                not es.intent_thread_url
                and not es.experiment_extension_reason
                and not has_milestone
            ):
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

        return f'{counter} empty extension stages deleted.'


class BackfillShippingYear(FlaskHandler):
    """Handler to backfill shipping year for features."""

    def calc_all_shipping_years(self) -> dict[int, int]:
        """Load all shipping stages and record their earliest milestone."""
        shipping_stages = (
            stage_helpers.get_all_shipping_stages_with_milestones()
        )
        stages_by_fid = stage_helpers.organize_all_stages_by_feature(
            shipping_stages
        )
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


class BackfillActivityLogType(FlaskHandler):
    """Handler to backfill activity log types."""

    def get_template_data(self, **kwargs) -> str:
        """Backfill log_type for all Activity entities."""
        self.require_cron_header()

        count = 0
        batch: list[Activity] = []
        BATCH_SIZE = 100

        for activity in Activity.query():
            if activity.log_type is not None:
                continue
            # 1. If the content field is null, the log_type field should be USER_CHANGE.
            if not activity.content:
                activity.log_type = Activity.USER_CHANGE
            # 2. If the content field is not null and the string starts with "Shipping/Rollout milestones were unset", the log_type field should be MILESTONE_RESET.
            elif activity.content.startswith(
                'Shipping/Rollout milestones were unset'
            ):
                activity.log_type = Activity.MILESTONE_RESET
            # 3. If the content field is not null and the amendments field is not empty, the log_type field should be SYSTEM_CHANGE.
            elif activity.content and activity.amendments:
                activity.log_type = Activity.SYSTEM_CHANGE
            # 4. If the content field is not null and the amendments field is empty, the log_type field should be USER_COMMENT.
            elif activity.content and not activity.amendments:
                activity.log_type = Activity.USER_COMMENT
            # 5. The fallback type should be USER_CHANGE.
            else:
                activity.log_type = Activity.USER_CHANGE

            batch.append(activity)
            count += 1
            if len(batch) >= BATCH_SIZE:
                ndb.put_multi(batch)
                batch = []

        if batch:
            ndb.put_multi(batch)

        return f'{count} Activity entities updated.'


class BackfillGateDates(FlaskHandler):
    """Handler to backfill dates for gates."""

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

    def calc_resolved_on(
        self, gate: Gate, votes: list[Vote]
    ) -> datetime | None:
        """Return the date on which the gate was resolved, or None."""
        if gate.state not in Gate.FINAL_STATES:
            return None
        if gate.resolved_on:
            return None

        return max(v.set_on for v in votes if v.state in Gate.FINAL_STATES)

    def calc_needs_work_started_on(
        self, gate: Gate, votes: list[Vote]
    ) -> datetime | None:
        """Return the latest date on which the gate entered NEEDS_WORK."""
        if gate.state != Vote.NEEDS_WORK:
            return None
        if gate.needs_work_started_on:
            return None

        return max(v.set_on for v in votes if v.state == Vote.NEEDS_WORK)


class FetchWebdxFeatureId(FlaskHandler):
    """Handler to fetch WebDX feature IDs."""

    def get_template_data(self, **kwargs) -> str:
        """Fetch the complete list of Webdx feature ID available from
        webstatus.dev APIs and store them in datastore.
        """
        self.require_cron_header()

        client = DefaultApi(
            ApiClient(Configuration(settings.API_WEBSTATUS_DEV_URL))
        )

        all_data_list: list[Feature] = []
        page_token: str | None = None
        is_first: bool = True
        while is_first or page_token:
            try:
                resp = client.list_features(
                    page_token=page_token, page_size=100
                )
                all_data_list.extend(resp.data)
                page_token = resp.metadata.next_page_token
                is_first = False
            except ApiException as e:
                logging.error(
                    'Could not fetch from %s?page_token=%s: %s',
                    settings.API_WEBSTATUS_DEV_URL,
                    page_token,
                    e,
                )
                return 'Running FetchWebdxFeatureId() job failed.'

        feature_ids_list = [
            feature_data.feature_id for feature_data in all_data_list
        ]
        WebdxFeatures.store_webdx_feature_id_list(feature_ids_list)
        return f'{len(feature_ids_list)} feature ids are successfully stored.'


class SendManualOTCreatedEmail(FlaskHandler):
    """Manually send an email to origin trial contacts that an origin trial has
    been created but not yet activated.
    """

    def get_template_data(self, **kwargs):
        """Get template data."""
        self.require_cron_header()

        stage_id = kwargs.get('stage_id')
        stage: Stage | None = Stage.get_by_id(stage_id)
        if not stage:
            return f'Stage {stage_id} not found'
        if stage.stage_type not in core_enums.ALL_ORIGIN_TRIAL_STAGE_TYPES:
            return f'Stage {stage_id} is not an origin trial stage'
        if not stage.ot_owner_email and not stage.ot_emails:
            return f'Stage {stage_id} has no OT contacts set'
        if not stage.ot_display_name:
            return f'Stage {stage_id} does not have ot_display_name set'
        if stage.ot_activation_date is None:
            return f'Stage {stage_id} does not have ot_activation_date set'

        cloud_tasks_helpers.enqueue_task(
            '/tasks/email-ot-creation-processed',
            {'stage': converters.stage_to_json_dict(stage)},
        )
        return 'Email task enqueued'


class SendManualOTActivatedEmail(FlaskHandler):
    """Manually send an email to origin trial contacts that an origin trial has
    been created and also activated.
    """

    def get_template_data(self, **kwargs):
        """Get template data."""
        self.require_cron_header()

        stage_id = kwargs.get('stage_id')
        stage: Stage | None = Stage.get_by_id(stage_id)
        if not stage:
            return f'Stage {stage_id} not found'
        if stage.stage_type not in core_enums.ALL_ORIGIN_TRIAL_STAGE_TYPES:
            return f'Stage {stage_id} is not an origin trial stage'
        if not stage.ot_owner_email and not stage.ot_emails:
            return f'Stage {stage_id} has no OT contacts set'
        if not stage.ot_display_name:
            return f'Stage {stage_id} does not have ot_display_name set'

        cloud_tasks_helpers.enqueue_task(
            '/tasks/email-ot-activated',
            {'stage': converters.stage_to_json_dict(stage)},
        )
        return 'Email task enqueued'


class GenerateReviewActivityFile(FlaskHandler):
    """Generate a CSV file with all review activity in ChromeStatus."""

    DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
    VOTE_VALUE_MAPPING: dict[str, core_enums.SkyhookDashStatus] = {
        'na': core_enums.SkyhookDashStatus.FYI,
        'review_requested': core_enums.SkyhookDashStatus.PENDING_REVIEW,
        'review_started': core_enums.SkyhookDashStatus.PENDING_REVIEW,
        'needs_work': core_enums.SkyhookDashStatus.NEEDS_WORK,
        'approved': core_enums.SkyhookDashStatus.APPROVED,
        'denied': core_enums.SkyhookDashStatus.DENIED,
        'internal_review': core_enums.SkyhookDashStatus.PENDING_REVIEW,
        'na (self-certified)': core_enums.SkyhookDashStatus.FYI,
        'na_requested': core_enums.SkyhookDashStatus.PENDING_REVIEW,
        'na (verified)': core_enums.SkyhookDashStatus.FYI,
        'no_response': core_enums.SkyhookDashStatus.PENDING_REVIEW,
    }

    def _get_skyhook_status(self, review_status: str | None) -> str:
        if review_status is None:
            logging.warning('Event changed review status to null value.')
            return ''
        if review_status not in self.VOTE_VALUE_MAPPING:
            logging.warning(
                f'No status mapping found for status {review_status}.'
            )
            return ''
        return self.VOTE_VALUE_MAPPING[review_status].value

    def _generate_new_activities(
        self, start_timestamp: datetime, end_timestamp: datetime
    ) -> list[list[str]]:
        """Generate a list of rows to add to the review activity CSV."""
        # Note: We assume that anyone may view approval comments.
        activities: list[Activity] = (
            Activity.query(
                Activity.created > start_timestamp,
                Activity.created <= end_timestamp,
            )
            .order(Activity.created)
            .fetch()
        )

        # Filter deleted activities the user can't see, and activities that have
        # no gate ID, meaning they do not represent review activity.
        # TODO(DanielRyanSmith): Confirm if deleted features should deleted features
        # should have existing activity filtered and handle accordingly.
        activities = list(
            filter(
                lambda a: a.deleted_by is None and a.gate_id is not None,
                activities,
            )
        )
        if activities is None:
            return []

        gate_ids = set(a.gate_id for a in activities)
        gates = ndb.get_multi(ndb.Key('Gate', g_id) for g_id in gate_ids)
        gates_dict: dict[int, Gate] = {
            g.key.integer_id(): g for g in gates if g
        }

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
                    review_status = self._get_skyhook_status(
                        a.amendments[0].new_value
                    )
                if a.amendments[0].field_name == 'review_assignee':
                    review_assignee = a.amendments[0].new_value
            csv_rows.append(
                [
                    f'{settings.SITE_URL}feature/{a.feature_id}',
                    approval_defs.APPROVAL_FIELDS_BY_ID[
                        gate.gate_type
                    ].team_name,
                    a.amendments[0].field_name
                    if len(a.amendments)
                    else 'comment',
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
        activities.
        """
        blob = bucket.blob('review-activity-last-timestamp.txt')
        if blob.exists():
            with blob.open('r') as f:
                timestamp_str = f.read()
            return datetime.strptime(timestamp_str, self.DATE_FORMAT)
        # If no previous timestamp exists, start from the beginning.
        return datetime(2000, 1, 1)

    def _write_csv(self, bucket, csv_io: StringIO) -> None:
        """Append the rows to the review activity CSV, or create a new CSV if it
        does not exist.
        """
        blob = bucket.blob('chromestatus-review-activity.csv')
        blob.upload_from_string(csv_io.getvalue())

    def _write_last_run_timestamp(self, bucket, timestamp: datetime) -> None:
        """Store the date of the last review activity run."""
        blob = bucket.blob('review-activity-last-timestamp.txt')
        blob.upload_from_string(timestamp.strftime(self.DATE_FORMAT))

    def get_template_data(self, **kwargs):
        """Get template data."""
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

        return (
            f'{len(csv_rows)} '
            'new rows added to chromestatus-review-activity.csv uploaded.'
        )


class GenerateStaleFeaturesFile(FlaskHandler):
    """Generate a CSV file with all stale features that have upcoming shipping milestones."""

    DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

    def _gather_stale_features(
        self, current_milestone: int
    ) -> list[FeatureEntry]:
        """Generate a list of stale features that have an upcoming shipping milestone."""
        # Get all features that have not been verified for accuracy in over a month.
        now = datetime.now()
        one_month_ago = now - timedelta(weeks=4)
        stale_features: list[FeatureEntry] = FeatureEntry.query(
            ndb.OR(
                FeatureEntry.accurate_as_of < one_month_ago,
                FeatureEntry.accurate_as_of == None,  # noqa: E711
            ),
        ).fetch()

        stale_features_with_upcoming_ship_stages: list[FeatureEntry] = []
        for f in stale_features:
            # We should only surface features we have sent notifications about.
            # (This cannot be added to the query, since only 1 inequality is allowed per query.)
            if f.outstanding_notifications == 0:
                continue
            shipping_stage_type = core_enums.STAGE_TYPES_SHIPPING[
                f.feature_type
            ]
            upcoming_ship_stages = Stage.query(
                Stage.feature_id == f.key.integer_id(),
                ndb.OR(
                    Stage.stage_type == core_enums.STAGE_ENT_ROLLOUT,
                    Stage.stage_type == shipping_stage_type,
                ),
                ndb.OR(
                    Stage.milestones.desktop_first == current_milestone,
                    Stage.milestones.android_first == current_milestone,
                    Stage.milestones.ios_first == current_milestone,
                    Stage.milestones.webview_first == current_milestone,
                ),
            ).fetch()
            if upcoming_ship_stages:
                stale_features_with_upcoming_ship_stages.append(f)
        logging.info(
            f'{len(stale_features_with_upcoming_ship_stages)} stale features found.'
        )

        return stale_features_with_upcoming_ship_stages

    def _gather_milestone_reset_features(self) -> list[FeatureEntry]:
        """Generate a list of features that have had their milestones reset."""
        activities = Activity.query(
            Activity.log_type == Activity.MILESTONE_RESET
        ).fetch()
        feature_ids = list(set(a.feature_id for a in activities))
        features = ndb.get_multi(
            [ndb.Key('FeatureEntry', fid) for fid in feature_ids]
        )
        return [f for f in features if f]

    def _generate_rows(
        self, features: list[FeatureEntry], current_milestone: int
    ) -> tuple[list[list[str]], list[list[str]]]:
        """Generate rows for the two tables representing stale features."""
        # We generate a table for the stale features, and another for the owners of
        # those stale features.
        feature_csv_rows: list[list[str]] = []
        owner_csv_rows: list[list[str]] = []
        for f in features:
            for email in f.owner_emails:
                owner_csv_rows.append([str(f.key.integer_id()), email])
            accurate_as_of_str = ''
            if f.accurate_as_of:
                accurate_as_of_str = str(
                    datetime.strftime(f.accurate_as_of, self.DATE_FORMAT)
                )
            feature_csv_rows.append(
                [
                    str(f.key.integer_id()),
                    str(current_milestone),
                    f.name,
                    f'{settings.SITE_URL}feature/{f.key.integer_id()}',
                    accurate_as_of_str,
                    str(f.outstanding_notifications),
                ]
            )

        return feature_csv_rows, owner_csv_rows

    def _write_csv(
        self,
        bucket,
        feature_csv_rows: list[list[str]],
        owner_csv_rows: list[list[str]],
        reset_feature_csv_rows: list[list[str]],
    ) -> None:
        """Write stale features CSV and owners CSV to the GCP bucket."""
        csv_io = StringIO()
        writer = csv.writer(csv_io, lineterminator='\n')
        # Write header row.
        writer.writerow(
            [
                'id',
                'current_milestone',
                'name',
                'chromestatus_url',
                'accurate_as_of',
                'outstanding_notifications',
            ]
        )
        for row in feature_csv_rows:
            writer.writerow(row)

        blob = bucket.blob('chromestatus-stale-features.csv')
        blob.upload_from_string(csv_io.getvalue())

        # Do the same process for the owners file.
        csv_io = StringIO()
        writer = csv.writer(csv_io, lineterminator='\n')
        writer.writerow(['id', 'owner_email'])
        for row in owner_csv_rows:
            writer.writerow(row)
        blob = bucket.blob('chromestatus-stale-feature-owners.csv')
        blob.upload_from_string(csv_io.getvalue())

        # Do the same process for the milestone reset features file.
        csv_io = StringIO()
        writer = csv.writer(csv_io, lineterminator='\n')
        writer.writerow(['name', 'id', 'chromestatus_url'])
        for row in reset_feature_csv_rows:
            writer.writerow(row)
        blob = bucket.blob('chromestatus-milestone-reset-features.csv')
        blob.upload_from_string(csv_io.getvalue())

    def get_template_data(self, **kwargs) -> str:
        """Get template data."""
        self.require_cron_header()

        current_milestone_info = utils.get_current_milestone_info('current')
        current_milestone = int(current_milestone_info['mstone'])
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.FILES_BUCKET)

        stale_features = self._gather_stale_features(current_milestone)
        feature_csv_rows, owner_csv_rows = self._generate_rows(
            stale_features, current_milestone
        )

        reset_features = self._gather_milestone_reset_features()
        reset_feature_csv_rows = []
        for f in reset_features:
            reset_feature_csv_rows.append(
                [
                    f.name,
                    str(f.key.integer_id()),
                    f'{settings.SITE_URL}feature/{f.key.integer_id()}',
                ]
            )
            for email in f.owner_emails:
                owner_csv_rows.append([str(f.key.integer_id()), email])

        # Deduplicate owner rows to avoid duplicates if a feature is in both lists.
        owner_csv_rows = [
            list(r) for r in dict.fromkeys(tuple(row) for row in owner_csv_rows)
        ]

        self._write_csv(
            bucket, feature_csv_rows, owner_csv_rows, reset_feature_csv_rows
        )

        return f'{len(feature_csv_rows)} rows added to chromestatus-stale-features.csv and {len(reset_feature_csv_rows)} rows added to chromestatus-milestone-reset-features.csv'


class GenerateShippingFeaturesFile(FlaskHandler):
    """Generate a CSV file with all shipping features and information about their missing fields."""

    DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

    FILENAME_FEATURES = 'chromestatus-shipping-features.csv'
    FILENAME_OWNERS = 'chromestatus-shipping-feature-owners.csv'
    FILENAME_MISSING = 'chromestatus-shipping-feature-missing-criteria.csv'

    def _get_shipping_stages(self, milestone: int) -> list[Stage]:
        shipping_stage_types = [
            st for st in core_enums.STAGE_TYPES_SHIPPING.values() if st
        ]

        return Stage.query(
            Stage.stage_type.IN(shipping_stage_types),
            ndb.OR(
                Stage.milestones.desktop_first == milestone,
                Stage.milestones.android_first == milestone,
                Stage.milestones.ios_first == milestone,
                Stage.milestones.webview_first == milestone,
            ),
        ).fetch()

    def _get_feature_info(
        self,
        shipping_stages: list[Stage],
    ) -> tuple[
        list[feature_helpers.ShippingFeatureInfo],
        list[tuple[feature_helpers.ShippingFeatureInfo, list[str]]],
    ]:

        enabled_features_file = utils.get_chromium_file(
            core_enums.ENABLED_FEATURES_FILE_URL
        )
        enabled_features_json = json5.loads(enabled_features_file)
        content_features_file = utils.get_chromium_file(
            core_enums.CONTENT_FEATURES_FILE
        )

        return feature_helpers.aggregate_shipping_features(
            shipping_stages, enabled_features_json, content_features_file
        )

    def _generate_rows(
        self, shipping_stages: list[Stage], current_milestone: int
    ) -> tuple[list[list[str]], list[list[str]], list[list[str]]]:
        """Generate rows for the two tables representing shipping features."""
        # We generate a table for the shipping features, another for the owners of
        # those shipping features, and a final one for the missing criteria of each
        # shipping feature.

        complete_features, incomplete_features = self._get_feature_info(
            shipping_stages
        )

        feature_csv_rows: list[list[str]] = []
        owner_csv_rows: list[list[str]] = []
        missing_criteria_csv_rows: list[list[str]] = []

        for f in complete_features:
            feature_csv_rows.append(
                [
                    str(f['id']),
                    str(current_milestone),
                    f['name'],
                    f['chromestatus_url'],
                    'complete',
                ]
            )
            for email in f['owner_emails']:
                owner_csv_rows.append([str(f['id']), email])

        for f, missing_criteria in incomplete_features:
            feature_csv_rows.append(
                [
                    str(f['id']),
                    str(current_milestone),
                    f['name'],
                    f['chromestatus_url'],
                    'incomplete',
                ]
            )
            for email in f['owner_emails']:
                owner_csv_rows.append([str(f['id']), email])
            for criteria in missing_criteria:
                missing_criteria_csv_rows.append([str(f['id']), criteria])

        return feature_csv_rows, owner_csv_rows, missing_criteria_csv_rows

    def _upload_csv(
        self, bucket, filename: str, header: list[str], rows: list[list[str]]
    ) -> None:
        """Helper to write rows to a CSV in memory and upload to GCS."""
        csv_io = StringIO()
        writer = csv.writer(csv_io, lineterminator='\n')
        writer.writerow(header)
        writer.writerows(rows)  # Bulk write is cleaner

        blob = bucket.blob(filename)
        blob.upload_from_string(csv_io.getvalue())

    def _write_csv(
        self,
        bucket,
        feature_csv_rows: list[list[str]],
        owner_csv_rows: list[list[str]],
        missing_criteria_csv_rows: list[list[str]],
    ) -> None:
        """Write shipping features CSV, owners CSV, and missing criteria CSV to the GCP bucket."""
        self._upload_csv(
            bucket,
            self.FILENAME_FEATURES,
            ['id', 'current_milestone', 'name', 'chromestatus_url', 'status'],
            feature_csv_rows,
        )

        self._upload_csv(
            bucket, self.FILENAME_OWNERS, ['id', 'owner_email'], owner_csv_rows
        )

        self._upload_csv(
            bucket,
            self.FILENAME_MISSING,
            ['id', 'missing_criteria'],
            missing_criteria_csv_rows,
        )

    def get_template_data(self, **kwargs) -> str:
        """Get template data."""
        self.require_cron_header()

        current_milestone_info = utils.get_current_milestone_info('current')
        current_milestone = int(current_milestone_info['mstone'])

        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.FILES_BUCKET)

        shipping_stages = self._get_shipping_stages(current_milestone)

        (feature_rows, owner_rows, missing_rows) = self._generate_rows(
            shipping_stages, current_milestone
        )

        self._write_csv(bucket, feature_rows, owner_rows, missing_rows)

        return f'{len(feature_rows)} rows added to {self.FILENAME_FEATURES}'


class MigrateRolloutMilestones(FlaskHandler):
    """Migrate the rollout milestone field to be stored in the 'milestones' field."""

    def get_template_data(self, **kwargs):
        """Get template data."""
        self.require_cron_header()
        stages: list[Stage] = Stage.query(
            Stage.stage_type == core_enums.STAGE_ENT_ROLLOUT
        ).fetch()
        changed_stages: list[Stage] = []
        count = 0
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
                count += len(changed_stages)
                changed_stages = []
        if changed_stages:
            ndb.put_multi(changed_stages)
            count += len(changed_stages)

        return f'{count} rollout_milestone fields migrated'


class ResetOutstandingNotifications(FlaskHandler):
    """Reset the FeatureEntry.outstanding_notifications counter for all features."""

    def get_template_data(self, **kwargs) -> str:
        """Get template data."""
        self.require_cron_header()
        notified_features: list[FeatureEntry] = FeatureEntry.query(
            FeatureEntry.outstanding_notifications > 0
        ).fetch()
        for f in notified_features:
            logging.info(
                f'Setting outstanding notifications for feature {f.key.integer_id()} '
                f'from {f.outstanding_notifications} to 0.'
            )
            f.outstanding_notifications = 0
        ndb.put_multi(notified_features)
        return (
            f'{len(notified_features)} reverted to 0 outstanding notifications.'
        )


class ResetStaleShippingMilestones(FlaskHandler):
    """Reset the shipping milestones of features have not been verified after 4+ notifications."""

    def _reset_milestone(
        self,
        stage: Stage,
        field: str,
        current_milestone: int,
        activity: Activity,
    ):
        old_value = (
            getattr(stage.milestones, field) if stage.milestones else None
        )
        # Only reset milestones that fall in the current milestone range.
        if (
            old_value
            and current_milestone <= old_value <= current_milestone + 2
        ):
            # Capture the old value in an Amendment.
            activity.amendments.append(
                Amendment(
                    field_name=field, old_value=str(old_value), new_value=None
                )
            )
            setattr(stage.milestones, field, None)

    def get_template_data(self, **kwargs) -> str:
        """Get template data."""
        self.require_cron_header()

        num_features_reset = 0
        stale_features: list[FeatureEntry] = FeatureEntry.query(
            FeatureEntry.outstanding_notifications >= 4
        ).fetch()
        current_milestone_info = utils.get_current_milestone_info('current')
        current_milestone = int(current_milestone_info['mstone'])
        entities_to_update: list[ndb.Model] = []
        for f in stale_features:
            # Get all the shipping stages of the stale feature and reset any
            # milestones that are set.
            stages: list[Stage] = Stage.query(
                Stage.feature_id == f.key.integer_id(),
                ndb.OR(
                    Stage.stage_type
                    == core_enums.STAGE_TYPES_SHIPPING[f.feature_type],
                    Stage.stage_type == core_enums.STAGE_ENT_ROLLOUT,
                ),
            ).fetch()
            for s in stages:
                # Create an activity that shows all the shipping milestones have been set to null.
                activity = Activity(
                    log_type=Activity.MILESTONE_RESET,
                    feature_id=f.key.integer_id(),
                    amendments=[],
                    content='Shipping/Rollout milestones were unset due to failure to verify accuracy.',
                )
                if s.milestones:
                    self._reset_milestone(
                        s,
                        'desktop_first',
                        current_milestone,
                        activity,
                    )
                    self._reset_milestone(
                        s, 'android_first', current_milestone, activity
                    )
                    self._reset_milestone(
                        s, 'ios_first', current_milestone, activity
                    )
                    self._reset_milestone(
                        s, 'webview_first', current_milestone, activity
                    )
                    # Only update the stage and save the activity if some milestones were unset.
                    if activity.amendments:
                        entities_to_update.append(s)
                        entities_to_update.append(activity)

            f.outstanding_notifications = 0
            entities_to_update.append(f)
            num_features_reset += 1
            cloud_tasks_helpers.enqueue_task(
                '/tasks/email-reset-shipping-milestones',
                {'feature_id': f.key.integer_id()},
            )
        if entities_to_update:
            ndb.put_multi(entities_to_update)

        return f'{num_features_reset} features with shipping milestones reset.'


class DeleteWPTCoverageReport(FlaskHandler):
    """Handler to delete old WPT coverage reports."""

    BATCH_SIZE = 100
    RETENTION_DAYS = 180

    def get_template_data(self, **kwargs) -> str:
        """Delete WPT coverage reports older than 180 days."""
        self.require_cron_header()
        batch = []
        count = 0

        # Calculate the date threshold
        date_threshold = datetime.now() - timedelta(days=self.RETENTION_DAYS)

        # Query for features with a WPT evaluation timestamp older than the threshold.
        query = FeatureEntry.query(
            FeatureEntry.ai_test_eval_status_timestamp <= date_threshold
        )

        for feature in query:
            # We check for the report's existence here, instead of in the query,
            # because the `ai_test_eval_report` field is not indexed.
            if feature.ai_test_eval_report:
                activity = Activity(
                    log_type=Activity.SYSTEM_CHANGE,
                    feature_id=feature.key.integer_id(),
                    content=(
                        f'WPT coverage report was deleted due to {self.RETENTION_DAYS}-day '
                        'retention policy.'
                    ),
                    amendments=[],
                )
                batch.append(activity)
                feature.ai_test_eval_report = None
                feature.ai_test_eval_run_status = (
                    core_enums.AITestEvaluationStatus.DELETED
                )
                # Update the timestamp to reflect when this cron job ran.
                feature.ai_test_eval_status_timestamp = datetime.now()
                batch.append(feature)
                count += 1
                if len(batch) >= self.BATCH_SIZE:
                    ndb.put_multi(batch)
                    batch = []
                    logging.info(
                        f'Deleted a batch of {self.BATCH_SIZE} reports.'
                    )

        if batch:
            ndb.put_multi(batch)

        logging.info(
            f'Finished. Deleted a total of {count} old WPT coverage reports.'
        )
        return f'{count} WPT coverage reports deleted.'
