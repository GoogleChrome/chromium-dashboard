#!/bin/bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

# Local development script to manually trigger AI summary generation for a specific feature
# and save it to the local Datastore emulator.

if [ -z "$1" ]; then
  echo "Usage: ./scripts/manual_test_summary.sh <feature_id>"
  exit 1
fi

FEATURE_ID="$1"

export DATASTORE_EMULATOR_HOST=localhost:15606
export GEMINI_API_KEY=$(cat gemini_api_key.txt 2>/dev/null || echo "$GEMINI_API_KEY")

if [ -z "$GEMINI_API_KEY" ]; then
  echo "Error: GEMINI_API_KEY is not set. Please create gemini_api_key.txt in project root or set it in your environment."
  exit 1
fi

echo "Activating virtual environment..."
source cs-env/bin/activate

echo "Running summary generation and writing to Datastore..."
python3 scripts/generate_summary.py --feature_id "$FEATURE_ID" --write

echo "Done! Suggestion status is COMPLETE and visible on Releases Page."
