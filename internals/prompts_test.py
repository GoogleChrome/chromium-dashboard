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


import testing_config  # Must be imported before the module under test.

import unittest
from pathlib import Path
from flask import Flask, render_template
import settings

# WARNING: Only do this when you are sure the output is correct!
REGENERATE_GOLDENS = False

test_app = Flask(__name__,
  template_folder=settings.get_flask_template_path())

TESTDATA = testing_config.Testdata(__file__)


def assert_matches_golden(
  test_case: unittest.TestCase,
  actual_output: str,
  golden_name: str,
) -> None:
  """Handles checking golden assertions and updates."""
  # If we are in 'update' mode, write the file and skip assertion
  if REGENERATE_GOLDENS:
    TESTDATA.make_golden(actual_output, golden_name)
    return

  test_case.assertMultiLineEqual(TESTDATA[golden_name], actual_output)


class TestAIPromptTemplatesHandler(unittest.TestCase):

  def setUp(self):
    self.maxDiff = None
    return super().setUp()

  def render_and_verify(self, template_path, context_data, golden_name):
    """Helper to render template and verify against golden."""

    # Render the template and verify against the snapshot.
    with test_app.app_context():
      rendered_body = render_template(template_path, **context_data)
    assert_matches_golden(self, rendered_body, golden_name)

  def test_prompt__unified_gap_analysis(self):
    """Ensure unified-gap-analysis renders correctly."""
    data = {
      'spec_url': 'https://example.com/spec',
      'spec_content': 'Some content.',
      'explainer_content': 'Some explainer content.',
      'feature_name': 'Feature One',
      'feature_summary': 'A generic feature',
      'test_files': [
        {'path': 'css/a.html', 'contents': 'contents of file a.html'},
        {'path': 'css/b.html', 'contents': 'contents of file b.html'},
      ],
      'dependency_files': [
        {'path': 'css/c.html', 'contents': 'contents of file c.html'},
        {'path': 'css/d.html', 'contents': 'contents of file d.html'},
        {'path': 'css/e.html', 'contents': 'contents of file e.html'},
      ],
    }
    self.render_and_verify(
      'prompts/unified-gap-analysis.html',
      data,
      'unified-gap-analysis.html'
    )

  def test_prompt__spec_synthesis(self):
    """Ensure spec-synthesis renders correctly."""
    data = {
      'spec_url': 'https://example.com/spec',
      'spec_content': 'The contents of the specification document.',
      'explainer_content': 'Some explainer content.',
      'feature_definition': 'The name and description of the feature.',
    }

    self.render_and_verify(
      'prompts/spec-synthesis.html',
      data,
      'spec-synthesis.html'
    )

  def test_prompt__test_analysis(self):
    """Ensure test-analysis renders correctly."""
    data = {
      'test_files': [
        {'path': 'css/a.html', 'contents': 'contents of file a.html'},
        {'path': 'css/b.html', 'contents': 'contents of file b.html'},
      ],
      'dependency_files': [
        {'path': 'css/c.html', 'contents': 'contents of file c.html'},
        {'path': 'css/d.html', 'contents': 'contents of file d.html'},
        {'path': 'css/e.html', 'contents': 'contents of file e.html'},
      ]
    }

    self.render_and_verify(
      'prompts/test-analysis.html',
      data,
      'test-analysis.html'
    )

  def test_prompt__gap_analysis(self):
    """Ensure gap-analysis renders correctly."""
    data = {
      'spec_synthesis': 'The summary of the spec',
      'test_summaries': ['Analysis of a.html', 'Analysis of b.html'],
    }

    self.render_and_verify(
      'prompts/gap-analysis.html',
      data,
      'gap-analysis.html'
    )
