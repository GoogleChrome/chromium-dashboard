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

"""Backend API modules for the chromium-dashboard application.

This package contains the Flask-based API endpoints and handlers that
serve the frontend SPA and external clients. These modules correspond
to the OpenAPI specification and handle business logic, Datastore
interactions (via Cloud NDB), and request/response formatting for
entities such as features, stages, users, and reviews.
"""
