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

"""Unit tests for offline evaluation framework and mathematical metrics."""

import unittest

from scripts.eval_summaries import (
    calculate_action_lead_score,
    calculate_entity_f1,
    calculate_fluff_score,
    calculate_jargon_score,
    calculate_markdown_score,
    calculate_rouge_l,
    calculate_word_count_score,
    evaluate_summary,
    run_evaluation,
)


class EvalSummariesTest(unittest.TestCase):
    """Unit tests verifying scoring algorithms and evaluation pipeline."""

    def test_calculate_word_count_score__optimal_range(self):
        """Verifies that word counts near 55 words receive optimal bell curve score."""
        text = ' '.join(['word'] * 55)
        count, score = calculate_word_count_score(
            text, min_words=35, max_words=80
        )
        self.assertEqual(count, 55)
        self.assertGreaterEqual(score, 0.95)

    def test_calculate_word_count_score__too_short(self):
        """Verifies penalty for severely undersized summaries."""
        text = 'Only five short words here.'
        count, score = calculate_word_count_score(
            text, min_words=35, max_words=80
        )
        self.assertEqual(count, 5)
        self.assertEqual(score, 0.0)

    def test_calculate_jargon_score__clean(self):
        """Verifies 100% score when no forbidden jargon is present."""
        text = 'CSS Anchor Positioning lets you tether elements declaratively.'
        jargon, score = calculate_jargon_score(
            text, ['intent to ship', 'blink-dev']
        )
        self.assertEqual(jargon, [])
        self.assertEqual(score, 1.0)

    def test_calculate_jargon_score__detected(self):
        """Verifies zero score and term detection when forbidden jargon is present."""
        text = 'This feature sent an intent to ship on blink-dev yesterday.'
        jargon, score = calculate_jargon_score(
            text, ['intent to ship', 'blink-dev']
        )
        self.assertIn('intent to ship', jargon)
        self.assertIn('blink-dev', jargon)
        self.assertEqual(score, 0.0)

    def test_calculate_fluff_score(self):
        """Verifies deduction penalty for marketing fluff phrases."""
        clean_text = 'Adds rule property to CSS grid.'
        fluff_text = 'This is vastly improving developer ergonomics for all.'
        _, clean_score = calculate_fluff_score(
            clean_text, ['vastly improving developer ergonomics']
        )
        found, fluff_score = calculate_fluff_score(
            fluff_text, ['vastly improving developer ergonomics']
        )
        self.assertEqual(clean_score, 1.0)
        self.assertEqual(found, ['vastly improving developer ergonomics'])
        self.assertLess(fluff_score, 1.0)

    def test_calculate_action_lead_score(self):
        """Verifies that active capability lead verbs score higher than passive verbs."""
        active_text = (
            'CSS Gap Decorations allows developers to draw rules between gaps.'
        )
        passive_text = (
            'The internal pipeline of the rendering engine was updated.'
        )
        self.assertEqual(calculate_action_lead_score(active_text), 1.0)
        self.assertLess(calculate_action_lead_score(passive_text), 1.0)

    def test_calculate_entity_f1(self):
        """Verifies precision, recall, and F1 calculations for technical entities."""
        text = 'Uses `anchor-name`, `position-anchor`, and `position-area`.'
        expected = [
            'anchor-name',
            'position-anchor',
            'position-area',
            'popover',
        ]
        p, r, f1 = calculate_entity_f1(text, expected)
        self.assertGreater(r, 0.70)
        self.assertGreater(f1, 0.70)

    def test_calculate_rouge_l(self):
        """Verifies ROUGE-L longest common subsequence against gold reference."""
        cand = 'CSS Anchor Positioning allows you to position an element relative to another.'
        ref = 'CSS Anchor Positioning lets you position an element relative to another.'
        rouge_l = calculate_rouge_l(cand, ref)
        self.assertGreater(rouge_l, 0.80)

    def test_calculate_markdown_score(self):
        """Verifies detection of unclosed markdown markers."""
        valid_md = 'Uses `popover` and **bold** syntax.'
        invalid_md = 'Uses `unclosed backtick.'
        self.assertEqual(calculate_markdown_score(valid_md), 1.0)
        self.assertLess(calculate_markdown_score(invalid_md), 1.0)

    def test_evaluate_summary__passes_quality_bar(self):
        """Verifies that high-quality summaries pass the composite evaluation bar."""
        fixture_data = {
            'name': 'CSS Anchor Positioning',
            'expected_entities': ['anchor-name', 'position-anchor', 'anchor'],
            'gold_devrel_summary': 'CSS Anchor Positioning lets you tether positioned elements using `anchor-name`.',
            'min_words': 10,
            'max_words': 50,
            'min_score_threshold': 0.75,
        }
        summary = 'CSS Anchor Positioning allows developers to position elements with `anchor-name` and `position-anchor`.'
        metrics = evaluate_summary(
            'test.yaml',
            fixture_data,
            summary,
            ['intent to ship'],
            ['a game changer'],
        )
        self.assertTrue(metrics.passed)
        self.assertGreaterEqual(metrics.overall_score, 0.75)

    def test_run_evaluation__offline_mock(self):
        """Verifies that the offline mock evaluation run completes with 100% pass."""
        results, baseline = run_evaluation(offline_mock=True)
        self.assertGreater(len(results), 0)
        self.assertTrue(all(r.passed for r in results))


if __name__ == '__main__':
    unittest.main()
