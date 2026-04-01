# Copyright 2026 Google Inc.
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

"""Internal business logic, models, and core services for chromium-dashboard.

The internals package contains the primary domain models (Cloud NDB Datastore entities),
business rules, internal services, and helper functions that drive the application.
It sits between the framework/API layer and the Datastore layer.

Modules in this package handle:
- Core data models and enums (core_models.py, core_enums.py, *_models.py)
- Feature launch processes and stages (processes.py, stage_helpers.py)
- Review and approval workflows (approval_defs.py, slo.py)
- Search and metrics fetching (search.py, search_queries.py, fetchmetrics.py)
- Notifications and reminders (notifier.py, reminders.py)
"""
