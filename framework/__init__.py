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

"""Core infrastructure and shared utility components for chromium-dashboard.

This package provides foundational systems used throughout the backend, including:
- Base request handlers for standardizing API responses and routing.
- Authentication, authorization, and XSRF protection.
- Integration clients for external services (e.g., Gemini, Origin Trials).
- Common utilities for caching, email sending, secrets management, and CSP.
"""
