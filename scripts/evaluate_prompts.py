#!/usr/bin/env python3
# Copyright 2026 Google Inc. All rights reserved.
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

"""CLI tool for benchmarking and comparing multiple candidate prompt templates."""

from __future__ import annotations

import argparse
import os
import sys

# Ensure repo root is on sys.path and default environments are set
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

os.environ.setdefault('SERVER_SOFTWARE', 'test')
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'cr-status-staging')

from prompts.renderer import (  # noqa: E402
    CANONICAL_RELEASE_NOTES_TEMPLATE,
    FeaturePromptTemplate,
)
from scripts.eval_summaries import (  # noqa: E402
    DEFAULT_BASELINE_FILE,
    DEFAULT_FIXTURES_DIR,
    run_evaluation,
)


def compare_prompts(
    prompt_paths: list[str],
    fixtures_dir: str = DEFAULT_FIXTURES_DIR,
    baseline_file: str = DEFAULT_BASELINE_FILE,
    model_name: str | None = None,
    offline_mock: bool = False,
) -> None:
    """Evaluates and compares multiple prompt templates across the benchmark suite."""
    print(
        f'Benchmarking {len(prompt_paths)} prompt template(s) against fixtures in {fixtures_dir}...\n'
    )

    header = f'{"Prompt Template":<42} | {"Pass Rate":<10} | {"Avg Words":<10} | {"Avg Score":<10}'
    sep = '=' * len(header)
    print(sep)
    print(header)
    print(sep)

    for p_path in prompt_paths:
        template_name = os.path.basename(p_path)
        if os.path.exists(p_path):
            template = FeaturePromptTemplate(template_name=template_name)
        else:
            template = CANONICAL_RELEASE_NOTES_TEMPLATE

        results, _ = run_evaluation(
            fixtures_dir=fixtures_dir,
            baseline_file=baseline_file,
            prompt_template=template,
            model_name=model_name,
            offline_mock=offline_mock,
        )

        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        pass_rate = (passed_count / total * 100) if total else 0.0
        avg_words = (
            (sum(r.word_count for r in results) / total) if total else 0.0
        )
        avg_score = (
            (sum(r.overall_score for r in results) / total * 100)
            if total
            else 0.0
        )

        print(
            f'{template_name:<42} | {pass_rate:<9.1f}% | {avg_words:<10.1f} | {avg_score:<9.1f}%'
        )

    print(sep + '\n')


def main() -> int:
    """CLI entrypoint for prompt template comparison tool."""
    parser = argparse.ArgumentParser(
        description='Compare candidate prompt templates on benchmark features.'
    )
    parser.add_argument(
        '--prompts',
        nargs='+',
        default=[
            os.path.join(REPO_ROOT, 'prompts', 'generate_release_notes.md')
        ],
        help='List of prompt template markdown files to compare.',
    )
    parser.add_argument(
        '--fixtures-dir',
        default=DEFAULT_FIXTURES_DIR,
        help='Directory containing YAML fixtures.',
    )
    parser.add_argument(
        '--baseline',
        default=DEFAULT_BASELINE_FILE,
        help='Path to baseline scores JSON.',
    )
    parser.add_argument(
        '--model',
        default=os.environ.get(
            'SUMMARY_GENERATOR_MODEL',
            os.environ.get('GEMINI_MODEL', 'gemini-3.1-pro-preview'),
        ),
        help='Gemini model name.',
    )
    parser.add_argument(
        '--offline-mock', action='store_true', help='Run in offline mock mode.'
    )
    args = parser.parse_args()

    use_offline = args.offline_mock or not os.environ.get('GEMINI_API_KEY')
    compare_prompts(
        prompt_paths=args.prompts,
        fixtures_dir=args.fixtures_dir,
        baseline_file=args.baseline,
        model_name=args.model,
        offline_mock=use_offline,
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
