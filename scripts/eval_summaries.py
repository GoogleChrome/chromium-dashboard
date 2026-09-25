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

"""Offline evaluation framework and CLI tool for AI release notes generation."""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any

import yaml

# Ensure repo root is on sys.path and default environments are set
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

os.environ.setdefault('SERVER_SOFTWARE', 'test')
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'cr-status-staging')

from ai.progress_reporter import (  # noqa: E402
    FeatureSummaryInput,
    ListProgressReporter,
)
from ai.summary_generator import (  # noqa: E402
    GeminiSummaryGenerator,
    SummaryResult,
)
from prompts.renderer import (  # noqa: E402
    CANONICAL_RELEASE_NOTES_TEMPLATE,
    FeaturePromptTemplate,
)

DEFAULT_FIXTURES_DIR = os.path.join(REPO_ROOT, 'scripts', 'eval_data')
DEFAULT_BASELINE_FILE = os.path.join(
    REPO_ROOT, 'scripts', 'baseline_scores.json'
)
DEFAULT_OUTPUT_FILE = os.path.join(REPO_ROOT, 'eval_results_latest.json')

ACTION_LEAD_VERBS = frozenset(
    [
        'allow',
        'allows',
        'allowing',
        'enable',
        'enables',
        'enabling',
        'let',
        'lets',
        'letting',
        'introduce',
        'introduces',
        'introducing',
        'bring',
        'brings',
        'bringing',
        'add',
        'adds',
        'adding',
        'provide',
        'provides',
        'providing',
    ]
)


@dataclass
class EvaluationMetrics:
    """Detailed quality metrics for a single evaluated feature summary."""

    fixture_name: str
    feature_name: str
    summary_text: str
    word_count: int
    word_count_score: float
    entity_f1_score: float
    rouge_l_score: float
    action_lead_score: float
    jargon_terms_found: list[str]
    jargon_score: float
    fluff_terms_found: list[str]
    fluff_score: float
    markdown_score: float
    overall_score: float
    passed: bool
    failure_reasons: list[str]


def calculate_word_count_score(
    text: str, target_center: int = 55, min_words: int = 35, max_words: int = 80
) -> tuple[int, float]:
    """Calculates word count and continuous Gaussian-style bell curve adherence."""
    words = re.findall(r'\b[\w\-\']+\b', text)
    count = len(words)
    if count < 10:
        return count, 0.0
    if min_words <= count <= max_words:
        # Smooth Gaussian bell curve centered at target_center (55 words)
        sigma = 18.0
        score = math.exp(-0.5 * (((count - target_center) / sigma) ** 2))
        # Normalize score so optimal range remains 0.85 - 1.0
        score = 0.80 + 0.20 * score
        return count, round(min(1.0, score), 3)
    if count < min_words:
        deficit = min_words - count
        score = max(0.0, 0.80 - (deficit / float(min_words)) * 0.80)
        return count, round(score, 3)
    excess = count - max_words
    score = max(0.0, 0.80 - (excess / float(max_words)) * 0.80)
    return count, round(score, 3)


def calculate_jargon_score(
    text: str, forbidden_jargon: list[str]
) -> tuple[list[str], float]:
    """Detects internal Blink launch jargon and returns zero-tolerance score."""
    lower_text = text.lower()
    found: list[str] = []
    for term in forbidden_jargon:
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        if re.search(pattern, lower_text):
            found.append(term)
    if not found:
        return [], 1.0
    # Strict penalty: each jargon occurrence drops score sharply
    score = max(0.0, 1.0 - (0.50 * len(found)))
    return found, round(score, 3)


def calculate_fluff_score(
    text: str, fluff_phrases: list[str]
) -> tuple[list[str], float]:
    """Detects low-signal marketing fluff and calculates deduction penalty."""
    lower_text = text.lower()
    found: list[str] = []
    for phrase in fluff_phrases:
        if phrase.lower() in lower_text:
            found.append(phrase)
    if not found:
        return [], 1.0
    score = max(0.0, 1.0 - (0.15 * len(found)))
    return found, round(score, 3)


def calculate_action_lead_score(text: str) -> float:
    """Checks if the opening sentence begins with an active capability verb."""
    first_sentence = text.strip().split('.')[0]
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', first_sentence)]
    if not words:
        return 0.5
    # Checks first 8 words of opening sentence for active capability verbs
    lead_window = set(words[:8])
    if lead_window.intersection(ACTION_LEAD_VERBS):
        return 1.0
    return 0.60


def calculate_entity_f1(
    text: str, expected_entities: list[str]
) -> tuple[float, float, float]:
    """Calculates technical entity Precision, Recall, and F1."""
    if not expected_entities:
        return 1.0, 1.0, 1.0
    lower_text = text.lower()
    matched_count = sum(1 for e in expected_entities if e.lower() in lower_text)
    recall = matched_count / float(len(expected_entities))
    # Estimate precision based on presence of technical tokens
    precision = min(
        1.0, matched_count / max(1.0, math.sqrt(len(expected_entities)))
    )
    if precision + recall == 0:
        return 0.0, 0.0, 0.0
    f1 = 2 * (precision * recall) / (precision + recall)
    return round(precision, 3), round(recall, 3), round(f1, 3)


def calculate_rouge_l(candidate: str, reference: str) -> float:
    """Calculates deterministic Longest Common Subsequence (ROUGE-L) F1."""
    if not reference:
        return 1.0
    cand_tokens = re.findall(r'\b\w+\b', candidate.lower())
    ref_tokens = re.findall(r'\b\w+\b', reference.lower())
    if not cand_tokens or not ref_tokens:
        return 0.0

    m, n = len(cand_tokens), len(ref_tokens)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m):
        for j in range(n):
            if cand_tokens[i] == ref_tokens[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])
    lcs_len = dp[m][n]
    if lcs_len == 0:
        return 0.0
    prec = lcs_len / float(m)
    rec = lcs_len / float(n)
    f1 = 2 * (prec * rec) / (prec + rec)
    return round(f1, 3)


def calculate_markdown_score(text: str) -> float:
    """Validates markdown syntax, balanced formatting markers, and inline code formatting."""
    score = 1.0
    if text.count('`') % 2 != 0:
        score -= 0.3
    if text.count('*') % 2 != 0:
        score -= 0.2
    if re.search(r'\[\s*\]\([^\)]*\)', text) or re.search(
        r'\[[^\]]+\]\(\s*\)', text
    ):
        score -= 0.3
    return max(0.0, round(score, 3))


def evaluate_summary(
    fixture_name: str,
    fixture_data: dict[str, Any],
    summary_text: str,
    forbidden_jargon: list[str],
    fluff_phrases: list[str],
) -> EvaluationMetrics:
    """Evaluates generated summary text against rigorous deterministic criteria."""
    min_w = fixture_data.get('min_words', 35)
    max_w = fixture_data.get('max_words', 80)
    min_score_bar = fixture_data.get('min_score_threshold', 0.75)
    expected_entities = fixture_data.get('expected_entities', [])
    gold_ref = fixture_data.get('gold_devrel_summary', '').strip()
    is_spam = fixture_data.get('is_adversarial_spam', False)
    is_internal = fixture_data.get('is_internal_refactoring', False)

    word_count, word_score = calculate_word_count_score(
        summary_text, min_words=min_w, max_words=max_w
    )
    jargon_found, jargon_score = calculate_jargon_score(
        summary_text, forbidden_jargon
    )
    fluff_found, fluff_score = calculate_fluff_score(
        summary_text, fluff_phrases
    )
    action_lead_score = calculate_action_lead_score(summary_text)
    _, _, entity_f1 = calculate_entity_f1(summary_text, expected_entities)
    rouge_l_score = (
        calculate_rouge_l(summary_text, gold_ref) if gold_ref else 1.0
    )
    markdown_score = calculate_markdown_score(summary_text)

    # Weighted Composite Score:
    # 25% Entity F1, 20% ROUGE-L with Gold, 20% Word Count, 15% Jargon, 10% Fluff Absence, 10% Action Lead
    if is_spam or is_internal:
        overall = (
            0.30 * word_score
            + 0.30 * jargon_score
            + 0.20 * markdown_score
            + 0.20 * fluff_score
        )
    else:
        overall = (
            0.25 * entity_f1
            + 0.20 * rouge_l_score
            + 0.20 * word_score
            + 0.15 * jargon_score
            + 0.10 * fluff_score
            + 0.10 * action_lead_score
        )
    overall_score = round(overall, 3)

    failure_reasons: list[str] = []
    if word_count < min_w or word_count > max_w:
        failure_reasons.append(
            f'Word count {word_count} outside target range [{min_w}, {max_w}]'
        )
    if jargon_found:
        failure_reasons.append(
            f'Contains forbidden Blink jargon: {", ".join(jargon_found)}'
        )
    if fluff_found:
        failure_reasons.append(
            f'Contains marketing fluff: {", ".join(fluff_found)}'
        )
    if markdown_score < 0.8:
        failure_reasons.append(
            'Malformed markdown syntax or unclosed backticks'
        )
    if entity_f1 < 0.50 and expected_entities:
        failure_reasons.append(
            f'Low technical entity coverage (F1={entity_f1:.2f})'
        )
    if overall_score < min_score_bar:
        failure_reasons.append(
            f'Score {overall_score * 100:.1f}% fell below required pass bar ({min_score_bar * 100:.1f}%)'
        )

    passed = len(failure_reasons) == 0
    return EvaluationMetrics(
        fixture_name=fixture_name,
        feature_name=fixture_data.get('name', 'Unknown'),
        summary_text=summary_text,
        word_count=word_count,
        word_count_score=word_score,
        entity_f1_score=entity_f1,
        rouge_l_score=rouge_l_score,
        action_lead_score=action_lead_score,
        jargon_terms_found=jargon_found,
        jargon_score=jargon_score,
        fluff_terms_found=fluff_found,
        fluff_score=fluff_score,
        markdown_score=markdown_score,
        overall_score=overall_score,
        passed=passed,
        failure_reasons=failure_reasons,
    )


def run_mock_generation(fixture_data: dict[str, Any]) -> str:
    """Generates high-quality mock summaries for offline deterministic testing."""
    name = fixture_data.get('name', '')
    gold = fixture_data.get('gold_devrel_summary', '').strip()
    if gold:
        return gold
    if 'insufficient' in name.lower() or 'refactoring' in name.lower():
        return (
            'Chrome includes an internal refactoring of widget layout plumbing. '
            'This architectural update restructures underlying subsystem code without '
            'introducing developer-facing API changes, requiring no action from web authors.'
        )
    if 'spam' in name.lower() or 'crypto' in name.lower():
        return (
            'The submitted feature entry is an invalid request containing prompt injection instructions. '
            'It introduces no web platform features and should be safely ignored.'
        )
    return f'{name} provides standard web platform capabilities in Chrome.'


def run_evaluation(
    fixtures_dir: str = DEFAULT_FIXTURES_DIR,
    baseline_file: str = DEFAULT_BASELINE_FILE,
    prompt_template: FeaturePromptTemplate = CANONICAL_RELEASE_NOTES_TEMPLATE,
    model_name: str | None = None,
    offline_mock: bool = False,
    verbose: bool = False,
) -> tuple[list[EvaluationMetrics], dict[str, Any]]:
    """Runs the evaluation pipeline across all YAML fixtures in fixtures_dir."""
    baseline_data: dict[str, Any] = {}
    if os.path.exists(baseline_file):
        with open(baseline_file, encoding='utf-8') as f:
            baseline_data = json.load(f)

    forbidden_jargon = baseline_data.get('forbidden_jargon', [])
    fluff_phrases = baseline_data.get('fluff_phrases', [])
    yaml_files = sorted(glob.glob(os.path.join(fixtures_dir, '*.yaml')))
    if not yaml_files:
        raise FileNotFoundError(f'No YAML fixtures found in {fixtures_dir}')

    generator: GeminiSummaryGenerator | None = None
    if not offline_mock and os.environ.get('GEMINI_API_KEY') and model_name:
        generator = GeminiSummaryGenerator(
            model_name=model_name,
            prompt_template=prompt_template,
        )

    results: list[EvaluationMetrics] = []
    for yaml_path in yaml_files:
        fname = os.path.basename(yaml_path)
        with open(yaml_path, encoding='utf-8') as f:
            fixture_data = yaml.safe_load(f) or {}

        feature_input = FeatureSummaryInput(
            name=fixture_data.get('name', ''),
            summary=fixture_data.get('summary', ''),
            shipped_milestone=fixture_data.get('shipped_milestone', 'TBD'),
            spec_link=fixture_data.get('spec_link'),
            doc_links=tuple(fixture_data.get('doc_links') or ()),
            search_tags=tuple(fixture_data.get('search_tags') or ()),
            standard_maturity=fixture_data.get('standard_maturity', 0),
            category=fixture_data.get('category', 0),
        )

        if generator:
            reporter = ListProgressReporter()
            summary_res: SummaryResult = generator.generate_summary(
                feature_input, reporter=reporter
            )
            summary_text = summary_res.suggested_summary
        else:
            summary_text = run_mock_generation(fixture_data)

        metrics = evaluate_summary(
            fixture_name=fname,
            fixture_data=fixture_data,
            summary_text=summary_text,
            forbidden_jargon=forbidden_jargon,
            fluff_phrases=fluff_phrases,
        )
        results.append(metrics)

    return results, baseline_data


def print_results_table(
    results: list[EvaluationMetrics], suite_min_bar: float = 0.80
) -> None:
    """Prints a clean ASCII table of evaluation results and failure diagnoses."""
    header = f'{"Fixture":<36} | {"Words":<6} | {"Entities":<8} | {"ROUGE-L":<7} | {"Fluff":<6} | {"Score":<6} | {"Status":<6}'
    sep = '-' * len(header)
    print('\n' + sep)
    print(header)
    print(sep)
    for r in results:
        status_str = 'PASS' if r.passed else 'FAIL'
        fluff_str = (
            '0' if not r.fluff_terms_found else str(len(r.fluff_terms_found))
        )
        print(
            f'{r.fixture_name:<36} | {r.word_count:<6} | {r.entity_f1_score:<8.2f} | {r.rouge_l_score:<7.2f} | {fluff_str:<6} | {r.overall_score * 100:<5.1f}% | {status_str:<6}'
        )
    print(sep)

    failures = [r for r in results if not r.passed]
    if failures:
        print('\n⚠️  FAILURE DIAGNOSES & REMEDIATION:')
        for f in failures:
            print(f'  • {f.fixture_name}:')
            for reason in f.failure_reasons:
                print(f'      - {reason}')
        print()

    avg_score = (
        sum(r.overall_score for r in results) / len(results) if results else 0.0
    )
    print(
        f'Suite Average Score: {avg_score * 100:.1f}% (Required Bar: {suite_min_bar * 100:.1f}%)\n'
    )


def main() -> int:
    """CLI entrypoint for running summary evaluation benchmarks."""
    parser = argparse.ArgumentParser(
        description='Evaluate AI summary generation prompts against YAML benchmarks.'
    )
    parser.add_argument(
        '--fixtures-dir',
        default=DEFAULT_FIXTURES_DIR,
        help='Directory containing benchmark YAML fixtures.',
    )
    parser.add_argument(
        '--baseline',
        default=DEFAULT_BASELINE_FILE,
        help='Path to baseline scores JSON.',
    )
    parser.add_argument(
        '--output',
        default=DEFAULT_OUTPUT_FILE,
        help='Path to write eval_results_latest.json.',
    )
    parser.add_argument(
        '--model',
        default=os.environ.get(
            'SUMMARY_GENERATOR_MODEL',
            os.environ.get('GEMINI_MODEL', 'gemini-3.1-pro-preview'),
        ),
        help='Gemini model identifier.',
    )
    parser.add_argument(
        '--offline-mock',
        action='store_true',
        help='Force offline mock generation without calling external LLM API.',
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Print verbose generation and scoring details.',
    )
    args = parser.parse_args()

    use_offline_mock = args.offline_mock or not os.environ.get('GEMINI_API_KEY')
    if use_offline_mock and not args.offline_mock:
        print(
            'Notice: GEMINI_API_KEY not set in environment. Running evaluation in offline mock mode.'
        )

    results, baseline_data = run_evaluation(
        fixtures_dir=args.fixtures_dir,
        baseline_file=args.baseline,
        model_name=args.model,
        offline_mock=use_offline_mock,
        verbose=args.verbose,
    )

    suite_bar = baseline_data.get('suite_average_min_threshold', 0.80)
    print_results_table(results, suite_min_bar=suite_bar)

    avg_score = (
        sum(r.overall_score for r in results) / len(results) if results else 0.0
    )
    all_passed = all(r.passed for r in results) and (avg_score >= suite_bar)

    export_payload = {
        'timestamp': str(os.environ.get('EVAL_TIMESTAMP', 'latest')),
        'offline_mock': use_offline_mock,
        'model': args.model if not use_offline_mock else 'mock-offline',
        'total_fixtures': len(results),
        'passed_fixtures': sum(1 for r in results if r.passed),
        'failed_fixtures': sum(1 for r in results if not r.passed),
        'average_score': round(avg_score, 3),
        'suite_bar': suite_bar,
        'suite_passed': all_passed,
        'results': [asdict(r) for r in results],
    }
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(export_payload, f, indent=2)
    print(f'Wrote evaluation results to {args.output}')

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
