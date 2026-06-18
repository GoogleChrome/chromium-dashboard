# -*- coding: utf-8 -*-
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

"""Local CLI test script to run the AI summary generator agent by fetching feature data via HTTP API."""

from __future__ import annotations

import argparse
import json
import os
import sys

import requests

# Ensure project root is in path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)

import datetime

from google.cloud import ndb

# Populate dummy SERVER_SOFTWARE to satisfy settings.py checks
os.environ['SERVER_SOFTWARE'] = 'test'

from framework.summary_generator import generate_summary_for_feature
from internals import core_enums
from internals.core_models import FeatureEntry, FeatureSummarySuggestion


def run_test() -> None:
    """Run local generation test using HTTP feature data from a specific host."""
    parser = argparse.ArgumentParser(
        description='Run local AI summary generator against a specific host and feature ID.'
    )
    parser.add_argument(
        '--host',
        default='http://localhost:8080',
        help='The server host protocol and domain (e.g. https://chromestatus.com or http://localhost:8080)',
    )
    parser.add_argument(
        '--feature_id',
        type=int,
        required=True,
        help='The database ID of the feature entry to process.',
    )
    parser.add_argument(
        '--write',
        action='store_true',
        help='Simulate writing the generated draft suggestion back to the server.',
    )
    args = parser.parse_args()

    url = f'{args.host.rstrip("/")}/api/v0/features/{args.feature_id}'
    print(f'Fetching feature details from: {url}...')

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(
                f'Failed to fetch feature: HTTP {resp.status_code} - {resp.text}'
            )
            sys.exit(1)

        text = resp.text
        if text.startswith(")]}'"):
            text = text[4:].lstrip()
        data = json.loads(text)
    except Exception as e:
        print(f'Network error fetching feature details: {e}')
        sys.exit(1)

    # Convert API JSON format fields back to database model fields
    # The API might serialize some fields under different names or formats
    name = data.get('name', 'Unknown Feature')
    summary = data.get('summary', '')
    category = data.get('category', 0)
    # Ensure category is integer ID
    if isinstance(category, dict):
        category = category.get('id', 0)
    elif isinstance(category, str):
        # We try to map back to category ID if it's a string, or fallback to 0
        category = 0

    explainer_links = data.get('explainer_links', [])
    if isinstance(explainer_links, str):
        explainer_links = [explainer_links]

    spec_link = data.get('spec_link', '')

    # Construct local unpersisted FeatureEntry
    mock_feature = FeatureEntry(
        name=name,
        category=int(category),
        summary=summary,
        explainer_links=explainer_links,
        spec_link=spec_link,
    )

    print('\n--- Fetched Feature Details ---')
    print(f'Name: {mock_feature.name}')
    print(f'Category ID: {mock_feature.category}')
    print(f'Summary: {mock_feature.summary[:150]}...')
    print('---------------------------------')
    print('Running ADK Agent generation...')

    result = generate_summary_for_feature(mock_feature)

    print('\n--- Generation Result ---')
    print(f'Suggested Summary: {result.suggested_summary}')
    print(f'Suggested Doc Links: {result.suggested_doc_links}')
    print(f'Baseline Status: {result.baseline_status}')
    print('-------------------------')

    if args.write:
        print(
            f'\nWriting AI suggestion draft back to Datastore for feature {args.feature_id}...'
        )
        client = ndb.Client()
        with client.context():
            fe = FeatureEntry.get_by_id(args.feature_id)
            if not fe:
                print(
                    f'Feature {args.feature_id} not found in local datastore. Saving fetched entry first...'
                )
                mock_feature.key = ndb.Key(FeatureEntry, args.feature_id)
                mock_feature.put()

            baseline_enum = None
            if result.baseline_status:
                try:
                    baseline_enum = core_enums.WebdxFeatureBaselineStatus(
                        result.baseline_status
                    )
                except ValueError:
                    print(
                        f'Warning: unknown baseline status string: {result.baseline_status}'
                    )

            suggestion = FeatureSummarySuggestion(
                id=args.feature_id,
                suggested_summary=result.suggested_summary,
                suggested_doc_links=result.suggested_doc_links,
                baseline_status=baseline_enum,
                status=core_enums.SummarySuggestionStatus.COMPLETE,
                status_timestamp=datetime.datetime.utcnow(),
                version_token=1,
            )
            suggestion.put()
            print('AI Suggestion draft saved successfully in local Datastore!')


if __name__ == '__main__':
    run_test()
