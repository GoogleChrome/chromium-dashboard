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
import statistics
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

# Evaluation Gatekeeping Constants
MIN_ACCEPTABLE_AVG = 4.0
MIN_ACCEPTABLE_SCORE = 3.0
REGRESSION_TOLERANCE = 0.5  # Margins of error for LLM judge non-determinism in N=3 runs


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
    parser.add_argument(
        '--iterations',
        type=int,
        default=1,
        help='Number of times to run generation and grading per feature to compute statistical metrics.',
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

    # Force use of real generator instead of local mock during evaluation
    settings.USE_MOCK_SUMMARY_GENERATOR = False
    os.environ['USE_MOCK_SUMMARY_GENERATOR'] = 'false'

    print(
        f'Starting LLM-as-a-Judge Evaluation (Dataset: {os.path.basename(args.dataset)}, Prompt: v{args.prompt_version}.md)...\n'
    )

    total_clarity = 0
    total_accuracy = 0
    total_links_baseline = 0
    count = len(dataset)
    iterations = getattr(args, 'iterations', 1)
    evaluation_results = []

    for i, gt in enumerate(dataset, 1):
        print(f'=== Feature {i}/{count}: {gt.get("name", "Unknown")} ===')

        feature_clarity_runs = []
        feature_accuracy_runs = []
        feature_links_runs = []
        run_details = []

        # Create unpersisted FeatureEntry model
        feature = FeatureEntry(
            name=gt.get('name'),
            category=int(gt.get('category', 0)),
            summary=gt.get('summary'),
            explainer_links=gt.get('explainer_links', []),
            spec_link=gt.get('spec_link'),
        )

        for run in range(1, iterations + 1):
            run_prefix = f'[Run {run}/{iterations}] ' if iterations > 1 else ''
            try:
                if iterations > 1:
                    print(f'{run_prefix}Generating summary suggestion...')
                else:
                    print('Generating summary suggestion...')
                
                result = generate_summary_for_feature(
                    feature, prompt_version=args.prompt_version
                )

                if iterations == 1:
                    print(f'AI Summary: {result.suggested_summary}')
                    print(f'AI Links: {result.suggested_doc_links}')
                    print(f'AI Baseline: {result.baseline_status}')
                    print('Calling LLM Judge...')
                else:
                    print(f'{run_prefix}Calling LLM Judge...')

                # Assemble judge prompt
                judge_prompt = f"""You are an expert technical editor for Google Developer Relations. Your task is to evaluate the quality of an AI-generated release notes summary for a web platform feature compared to a human-authored ground truth reference.

Evaluate the AI suggestion based on the following three criteria, scoring each on a 1-5 scale:

1. CLARITY & STYLE (Score 1-5):
   - The summary should be exactly 2-3 sentences.
   - It must be benefits-driven, objective, and developer-focused.
   - It should NOT contain prohibited marketing jargon (e.g., "introducing", "revolutionary", "exciting").
   - Scoring guide:
     5 (Excellent): Exactly 2-3 sentences. Perfectly objective, professional, and developer-focused. Highlights clear benefits. Absolutely zero marketing jargon or prohibited words.
     4 (Good): Exactly 2-3 sentences. Objective and developer-focused, but contains minor wordiness or slightly less punchy benefit phrasing. No prohibited jargon.
     3 (Satisfactory): Length is 2-3 sentences, but the tone is dry/passive (reads like a bulleted feature list rather than a benefits-driven summary). Alternatively, is exactly 4 sentences but otherwise perfect.
     2 (Poor): Contains minor marketing jargon/fluff, or length is highly deviant (1 sentence or >= 4 sentences).
     1 (Unacceptable): Heavy marketing hype, placeholders (e.g., "This is a mock..."), or completely wrong length.

2. ACCURACY & DRIFT (Score 1-5):
   - The summary must accurately reflect the technical details of the raw summary.
   - It must NOT hallucinate details or compatibility findings.
   - Scoring guide:
     5 (Excellent): 100% accurate. Correctly captures the core technology, specific JS/CSS namespaces, properties, and browser engine behaviors. Zero hallucinations, omissions, or factual drift.
     4 (Good): Accurate on all major points. May omit one minor technical detail or contain extremely minor over-simplifications that do not mislead web developers.
     3 (Satisfactory): Captures the high-level intent, but has noticeable omissions of important details (e.g., misses progressive enhancement support) or contains minor technical inaccuracies.
     2 (Poor): Contains major technical inaccuracies, incorrect property/API names (hallucinations), or completely misrepresents a key technical aspect of the feature.
     1 (Unacceptable): Catastrophic drift. Severe hallucinations, placeholders, or completely wrong technical details.

3. LINKS & BASELINE (Score 1-5):
   - Discovered MDN links must be highly relevant.
   - The Baseline status (limited, newly, widely) must match the ground truth or be highly justifiable based on documentation.
   - Scoring guide:
     5 (Excellent): Discovered MDN/web.dev links are highly relevant, active, and correct. Baseline status matches the ground truth exactly.
     4 (Good): Links are highly relevant and active, but might point to a slightly different (but still valid) guide or reference than the ground truth. Baseline status matches exactly.
     3 (Satisfactory): Links are correct but somewhat generic or tangential (e.g., pointing to a generic Web/API landing page instead of the specific property page). Baseline status is off by one level (e.g., "newly" instead of "widely") but has a plausible justification.
     2 (Poor): Includes dead/404 links, or baseline status is off by more than one level.
     1 (Unacceptable): All links are broken/generic, or baseline status is completely wrong (e.g., "widely" vs "limited") without any justification.

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

                feature_clarity_runs.append(clarity)
                feature_accuracy_runs.append(accuracy)
                feature_links_runs.append(links_baseline)

                run_details.append({
                    'run': run,
                    'summary': result.suggested_summary,
                    'links': result.suggested_doc_links,
                    'baseline': result.baseline_status,
                    'scores': {
                        'clarity': clarity,
                        'accuracy': accuracy,
                        'links_baseline': links_baseline
                    },
                    'justification': justification
                })

                if iterations == 1:
                    print(f'-> Clarity Score: {clarity}/5')
                    print(f'-> Accuracy Score: {accuracy}/5')
                    print(f'-> Links & Baseline Score: {links_baseline}/5')
                    print(f'-> Justification: {justification}\n')

            except Exception as e:
                print(f'{run_prefix}Error evaluating feature {gt.get("name")} in run {run}: {e}\n')

        if not feature_clarity_runs:
            print(f'Error: All runs failed for feature {gt.get("name")}\n')
            continue

        # Compute stats for this feature
        stats = {
            'clarity': {
                'min': min(feature_clarity_runs),
                'max': max(feature_clarity_runs),
                'avg': sum(feature_clarity_runs) / len(feature_clarity_runs),
                'median': statistics.median(feature_clarity_runs)
            },
            'accuracy': {
                'min': min(feature_accuracy_runs),
                'max': max(feature_accuracy_runs),
                'avg': sum(feature_accuracy_runs) / len(feature_accuracy_runs),
                'median': statistics.median(feature_accuracy_runs)
            },
            'links_baseline': {
                'min': min(feature_links_runs),
                'max': max(feature_links_runs),
                'avg': sum(feature_links_runs) / len(feature_links_runs),
                'median': statistics.median(feature_links_runs)
            }
        }

        # Accumulate averages for the dataset-wide final summary
        total_clarity += stats['clarity']['avg']
        total_accuracy += stats['accuracy']['avg']
        total_links_baseline += stats['links_baseline']['avg']

        if iterations > 1:
            print(f'-> Clarity & Style   [Min/Avg/Med/Max]: {stats["clarity"]["min"]}/{stats["clarity"]["avg"]:.2f}/{stats["clarity"]["median"]:.1f}/{stats["clarity"]["max"]}')
            print(f'-> Accuracy & Drift   [Min/Avg/Med/Max]: {stats["accuracy"]["min"]}/{stats["accuracy"]["avg"]:.2f}/{stats["accuracy"]["median"]:.1f}/{stats["accuracy"]["max"]}')
            print(f'-> Links & Baseline  [Min/Avg/Med/Max]: {stats["links_baseline"]["min"]}/{stats["links_baseline"]["avg"]:.2f}/{stats["links_baseline"]["median"]:.1f}/{stats["links_baseline"]["max"]}\n')

        # Add to results
        evaluation_results.append(
            {
                'feature_name': gt.get('name'),
                'iterations': iterations,
                'stats': stats,
                'runs': run_details if iterations > 1 else None,
                'scores': {
                    'clarity': stats['clarity']['avg'],
                    'accuracy': stats['accuracy']['avg'],
                    'links_baseline': stats['links_baseline']['avg'],
                }
            }
        )

    print('=== Final Evaluation Summary ===')
    print(f'Average Clarity & Style: {total_clarity / count:.2f}/5')
    print(f'Average Accuracy & Drift: {total_accuracy / count:.2f}/5')
    print(f'Average Links & Baseline: {total_links_baseline / count:.2f}/5\n')

    # === Pass/Fail Gatekeeping Logic ===
    print('=== E2E Gatekeeping Report ===')
    passed = True
    failure_reasons = []

    # Gate 1: Absolute Quality Floor (Average)
    avg_clarity = total_clarity / count
    avg_accuracy = total_accuracy / count
    if avg_clarity < 4.0:
        passed = False
        failure_reasons.append(f'Clarity & Style average ({avg_clarity:.2f}) is below the quality floor of 4.0')
    if avg_accuracy < 4.0:
        passed = False
        failure_reasons.append(f'Accuracy & Drift average ({avg_accuracy:.2f}) is below the quality floor of 4.0')

    # Gate 2: Robustness Floor (Minimum)
    for result in evaluation_results:
        name = result['feature_name']
        stats = result['stats']
        min_clarity = stats['clarity']['min']
        min_accuracy = stats['accuracy']['min']
        
        if min_clarity < 3.0:
            passed = False
            failure_reasons.append(f'Feature "{name}" had a Clarity score of {min_clarity} (below robustness floor of 3.0)')
        if min_accuracy < 3.0:
            passed = False
            failure_reasons.append(f'Feature "{name}" had an Accuracy score of {min_accuracy} (below robustness floor of 3.0)')

    # Gate 3: Regression Check
    has_regression = False
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

                print('--- Regression Checks ---')
                for item in evaluation_results:
                    name = item['feature_name']
                    if name in baseline_dict:
                        base = baseline_dict[name]

                        # Check both average scores (stored in item['scores'])
                        for metric in ['clarity', 'accuracy', 'links_baseline']:
                            old_score = base.get('scores', {}).get(metric, 1)
                            new_score = item['scores'].get(metric, 1)
                            diff = new_score - old_score
                            
                            # We allow a tolerance (default -0.5) due to judge variance
                            if diff < -REGRESSION_TOLERANCE:
                                passed = False
                                has_regression = True
                                failure_reasons.append(
                                    f'Regression in "{name}" for "{metric}": {old_score:.2f} -> {new_score:.2f} (drop of {diff:.2f} exceeds tolerance of -{REGRESSION_TOLERANCE:.1f})'
                                )
                                print(f'[-] "{name}" {metric}: {old_score:.2f} -> {new_score:.2f} ({diff:.2f}) [FAILED]')
                            elif diff < 0:
                                print(f'[!] "{name}" {metric}: {old_score:.2f} -> {new_score:.2f} ({diff:.2f}) [WARNING: Minor drop within tolerance]')
                            else:
                                print(f'[+] "{name}" {metric}: {old_score:.2f} -> {new_score:.2f} (+{diff:.2f}) [PASSED]')
                    else:
                        print(f'[?] "{name}": New test case, no baseline to compare.')
                print('-------------------------')
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

    # Final Pass/Fail Verdict
    print('\n' + '=' * 50)
    if passed:
        print('✅ E2E EVALUATION PASSED SUCCESFULLY!')
        print('All quality, robustness, and regression gates satisfied.')
        print('=' * 50)
        
        # Save latest results by default to a temp file for reference
        try:
            with open('scripts/eval_results_latest.json', 'w', encoding='utf-8') as f:
                json.dump(evaluation_results, f, indent=2)
        except Exception:
            pass
            
        sys.exit(0)
    else:
        print('❌ E2E EVALUATION FAILED!')
        print('\n--- Violations Detected ---')
        for reason in failure_reasons:
            print(f'  * {reason}')
            
        print('\n--- Debugging: Low-Scoring Run Justifications ---')
        for result in evaluation_results:
            name = result['feature_name']
            runs = result.get('runs') or []
            # If iterations == 1, there might not be a 'runs' list, so we handle both
            if not runs:
                runs = [{
                    'run': 1,
                    'scores': result['scores'],
                    'justification': result.get('justification', 'No justification saved.')
                }]
                
            printed_feature_header = False
            for r in runs:
                c = r['scores'].get('clarity', 5)
                a = r['scores'].get('accuracy', 5)
                l = r['scores'].get('links_baseline', 5)
                
                # If any score is low, print the justification to help the developer
                if c < MIN_ACCEPTABLE_AVG or a < MIN_ACCEPTABLE_AVG or l < MIN_ACCEPTABLE_SCORE:
                    if not printed_feature_header:
                        print(f'\nFeature: "{name}"')
                        printed_feature_header = True
                    print(f'  [Run {r["run"]}] Scores: Clarity={c}, Accuracy={a}, Links={l}')
                    print(f'  Justification: {r["justification"]}')
                    
        print('\n' + '=' * 50)
        
        # Save latest results by default to a temp file for reference
        try:
            with open('scripts/eval_results_latest.json', 'w', encoding='utf-8') as f:
                json.dump(evaluation_results, f, indent=2)
            print('Saved detailed run justifications to: scripts/eval_results_latest.json')
        except Exception:
            pass
            
        sys.exit(1)


if __name__ == '__main__':
    run_evaluation()
