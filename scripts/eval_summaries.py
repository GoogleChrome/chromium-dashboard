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

"""LLM-as-a-Judge evaluation script for AI release notes summary quality."""

from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure project root is in path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)

# Populate dummy SERVER_SOFTWARE to satisfy settings.py checks
os.environ['SERVER_SOFTWARE'] = 'test'

from google.genai import Client

import settings
from framework import secrets
from framework.summary_generator import generate_summary_for_feature
from internals.core_models import FeatureEntry


def run_evaluation() -> None:
    """Run the evaluation pipeline against ground-truth and output LLM judge scores."""
    parser = argparse.ArgumentParser(
        description='Evaluate AI summary generation quality against a ground-truth dataset.'
    )
    parser.add_argument(
        '--dataset',
        default=os.path.join(settings.ROOT_DIR, 'scripts', 'eval_data'),
        help='Path to the JSON file or directory containing the ground truth dataset.',
    )
    parser.add_argument(
        '--prompt-version',
        type=int,
        default=1,
        help='The version integer of the prompt template file to test (e.g. 1 loads v1.md).',
    )
    parser.add_argument(
        '--output-results',
        help='Optional path to output the evaluation scores as a JSON file.',
    )
    parser.add_argument(
        '--compare-with',
        help='Optional path to a previous evaluation results JSON file to check for regressions.',
    )
    args = parser.parse_args()

    # Load dataset
    if not os.path.exists(args.dataset):
        print(f'Error: Dataset path not found at: {args.dataset}')
        sys.exit(1)

    dataset = []
    if os.path.isdir(args.dataset):
        json_files = [
            os.path.join(args.dataset, f)
            for f in os.listdir(args.dataset)
            if f.endswith('.json')
        ]
        if not json_files:
            print(
                f'Error: No .json files found in dataset directory: {args.dataset}'
            )
            sys.exit(1)

        for file_path in sorted(json_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        dataset.extend(data)
                    else:
                        dataset.append(data)
            except Exception as e:
                print(f'Error loading dataset JSON file {file_path}: {e}')
                sys.exit(1)
    else:
        try:
            with open(args.dataset, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    dataset.extend(data)
                else:
                    dataset.append(data)
        except Exception as e:
            print(f'Error loading dataset JSON file: {e}')
            sys.exit(1)

    if not dataset:
        print('Error: Dataset must contain a non-empty list of test objects.')
        sys.exit(1)

    # Load Gemini API key
    secrets.load_gemini_api_key()
    api_key = settings.GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print(
            'Error: GEMINI_API_KEY is not configured in settings or environment. '
            'Create gemini_api_key.txt in project root.'
        )
        sys.exit(1)

    os.environ['GEMINI_API_KEY'] = api_key
    client = Client(api_key=api_key)

    print(
        f'Starting LLM-as-a-Judge Evaluation (Dataset: {os.path.basename(args.dataset)}, Prompt: v{args.prompt_version}.md)...\n'
    )

    total_clarity = 0
    total_accuracy = 0
    total_links_baseline = 0
    count = len(dataset)
    evaluation_results = []

    for i, gt in enumerate(dataset, 1):
        print(f'=== Feature {i}/{count}: {gt.get("name", "Unknown")} ===')

        # Create unpersisted FeatureEntry model
        feature = FeatureEntry(
            name=gt.get('name'),
            category=int(gt.get('category', 0)),
            summary=gt.get('summary'),
            explainer_links=gt.get('explainer_links', []),
            spec_link=gt.get('spec_link'),
        )

        try:
            print('Generating summary suggestion...')
            result = generate_summary_for_feature(
                feature, prompt_version=args.prompt_version
            )

            print(f'AI Summary: {result.suggested_summary}')
            print(f'AI Links: {result.suggested_doc_links}')
            print(f'AI Baseline: {result.baseline_status}')
            print('Calling LLM Judge...')

            # Assemble judge prompt
            judge_prompt = f"""You are an expert technical editor for Google Developer Relations. Your task is to evaluate the quality of an AI-generated release notes summary for a web platform feature compared to a human-authored ground truth reference.

Evaluate the AI suggestion based on the following three criteria, scoring each on a 1-5 scale:

1. CLARITY & STYLE (Score 1-5):
   - The summary should be exactly 2-3 sentences.
   - It must be benefits-driven, objective, and developer-focused.
   - It should NOT contain prohibited marketing jargon (e.g., "introducing", "revolutionary", "exciting").
   - Scoring guide:
     5: Perfect style, concise, benefits-driven, no jargon, exactly 2-3 sentences.
     3: Correct length, but slightly wordy or lacks a clear benefit.
     1: Too long/short, contains marketing fluff or forbidden jargon.

2. ACCURACY & DRIFT (Score 1-5):
   - The summary must accurately reflect the technical details of the raw summary.
   - It must NOT hallucinate details or compatibility findings.
   - Scoring guide:
     5: Totally accurate, no hallucinations or technical errors.
     3: Minor inaccuracies or over-simplifications that don't change core meaning.
     1: Severe technical errors, hallucinations, or major factual drift.

3. LINKS & BASELINE (Score 1-5):
   - Discovered MDN links must be highly relevant.
   - The Baseline status (limited, newly, widely) must match the ground truth or be highly justifiable based on documentation.
   - Scoring guide:
     5: MDN links are highly relevant and accurate, Baseline status matches ground truth exactly.
     3: MDN links are correct but slightly tangential, or Baseline status is off by one level but arguable.
     1: Wrong or broken links, or Baseline status is completely wrong (e.g. wide vs limited).

Inputs:
Feature Name: {gt.get('name')}
Raw Summary: {gt.get('summary')}
Ground Truth Summary: {gt.get('gt_summary')}
Ground Truth Doc Links: {gt.get('gt_links')}
Ground Truth Baseline: {gt.get('gt_baseline')}

AI Suggestion:
Suggested Summary: {result.suggested_summary}
Suggested Doc Links: {result.suggested_doc_links}
Baseline Status: {result.baseline_status}

Response Format:
You must respond with a JSON object containing the scores and a brief justification:
{{
  "clarity_score": <int>,
  "accuracy_score": <int>,
  "links_baseline_score": <int>,
  "justification": "Detailed notes on what went well or what failed."
}}

Do not wrap the response in markdown code blocks. Output the raw JSON string directly.
"""

            response = client.models.generate_content(
                model=settings.SUMMARY_GENERATOR_MODEL,
                contents=judge_prompt,
            )

            # Clean and parse judge response
            clean_str = response.text.strip()
            if clean_str.startswith('```json'):
                clean_str = clean_str[7:]
            if clean_str.endswith('```'):
                clean_str = clean_str[:-3]

            judge_data = json.loads(clean_str.strip())
            clarity = int(judge_data.get('clarity_score', 1))
            accuracy = int(judge_data.get('accuracy_score', 1))
            links_baseline = int(judge_data.get('links_baseline_score', 1))
            justification = judge_data.get('justification', '')

            print(f'-> Clarity Score: {clarity}/5')
            print(f'-> Accuracy Score: {accuracy}/5')
            print(f'-> Links & Baseline Score: {links_baseline}/5')
            print(f'-> Justification: {justification}\n')

            total_clarity += clarity
            total_accuracy += accuracy
            total_links_baseline += links_baseline

            # Add to results
            evaluation_results.append(
                {
                    'feature_name': gt.get('name'),
                    'scores': {
                        'clarity': clarity,
                        'accuracy': accuracy,
                        'links_baseline': links_baseline,
                    },
                    'justification': justification,
                }
            )

        except Exception as e:
            print(f'Error evaluating feature {gt.get("name")}: {e}\n')

    print('=== Final Evaluation Summary ===')
    print(f'Average Clarity & Style: {total_clarity / count:.2f}/5')
    print(f'Average Accuracy & Drift: {total_accuracy / count:.2f}/5')
    print(f'Average Links & Baseline: {total_links_baseline / count:.2f}/5\n')

    # Handle regression check comparison
    if args.compare_with:
        if not os.path.exists(args.compare_with):
            print(
                f'Warning: Baseline file for comparison not found at: {args.compare_with}'
            )
        else:
            try:
                with open(args.compare_with, 'r', encoding='utf-8') as f:
                    baseline_data = json.load(f)

                # Turn baseline list into dict by feature name
                baseline_dict = {
                    item['feature_name']: item for item in baseline_data
                }

                print('=== Regression Comparison ===')
                has_regression = False
                for item in evaluation_results:
                    name = item['feature_name']
                    if name in baseline_dict:
                        base = baseline_dict[name]

                        regressions = []
                        for metric in ['clarity', 'accuracy', 'links_baseline']:
                            old_score = base['scores'].get(metric, 1)
                            new_score = item['scores'].get(metric, 1)
                            diff = new_score - old_score
                            if diff < 0:
                                regressions.append(
                                    f'{metric}: {old_score} -> {new_score} ({diff})'
                                )
                                has_regression = True

                        if regressions:
                            print(f'[-] REGRESSION in feature "{name}":')
                            for r in regressions:
                                print(f'    * {r}')
                        else:
                            print(
                                f'[+] Feature "{name}": No regressions detected.'
                            )
                    else:
                        print(
                            f'[?] Feature "{name}": New test case, no baseline to compare.'
                        )

                print('')
                if has_regression:
                    print(
                        '⚠️  WARNING: Regressions detected! Check console outputs above.'
                    )
                else:
                    print(
                        '✅ SUCCESS: No regressions detected compared to baseline!'
                    )

            except Exception as e:
                print(f'Error running regression comparison: {e}')

    # Output JSON results if requested
    if args.output_results:
        try:
            with open(args.output_results, 'w', encoding='utf-8') as f:
                json.dump(evaluation_results, f, indent=2)
            print(f'Saved evaluation results to: {args.output_results}')
        except Exception as e:
            print(f'Error saving evaluation results JSON file: {e}')


if __name__ == '__main__':
    run_evaluation()
