# -*- coding: utf-8 -*-
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

"""API endpoint for retrieving the status of feature implementation processes."""

import dataclasses

from chromestatus_openapi.models import Process

from framework import basehandlers
from internals import core_enums, processes


class ProcessesAPI(basehandlers.APIHandler):
    """Processes contain details about the feature status"""  # noqa: D415

    def do_get(self, **kwargs):
        """Return the process of the feature."""
        # Load feature directly from NDB so as to never get a stale cached copy.
        fe = self.get_specified_feature(**kwargs)

        feature_process = processes.ALL_PROCESSES.get(
            fe.feature_type, processes.BLINK_LAUNCH_PROCESS
        )
        process_model = Process.from_dict(
            processes.process_to_dict(feature_process)
        )  # noqa: E501
        result = process_model.to_dict()
        if (
            fe.feature_type != core_enums.FEATURE_TYPE_ENTERPRISE_ID
            and fe.enterprise_impact > core_enums.ENTERPRISE_IMPACT_NONE
        ):
            result['stages'].insert(
                -1, dataclasses.asdict(processes.FEATURE_ROLLOUT_STAGE)
            )  # noqa: E501
            result['stages'][-1]['incoming_stage'] = core_enums.INTENT_ROLLOUT

        return result
