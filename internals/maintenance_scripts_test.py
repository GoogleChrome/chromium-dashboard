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

import logging
from google.cloud import ndb  # type: ignore
import testing_config
from internals.core_models import FeatureEntry, Stage, MilestoneSet
from internals import maintenance_scripts
from internals import core_enums


class MarkdownMigrationTest(testing_config.CustomTestCase):
    """Unit tests verifying the safe Markdown converter, de-converter, and paginated migration script."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.feature_1 = FeatureEntry(
            id=1001,
            name='Feature One',
            summary='This is a plain summary with *asterisks* and <HTML_tags>.',
            category=1,
        )
        self.feature_1.put()

        # Create a Stage to link the feature to milestone 120
        self.stage_1 = Stage(
            feature_id=1001,
            stage_type=core_enums.STAGE_BLINK_SHIPPING,
            milestones=MilestoneSet(desktop_first=120)
        )
        self.stage_1.put()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.feature_1.key.delete()
        self.stage_1.key.delete()

    def test_safe_plain_text_to_markdown__escaping_and_idempotency(self):
        """Verify that plain text is escaped correctly, HTML tags are entity-escaped, and escaping is idempotent."""
        original_text = 'Hello *world*! Here is some code: `x = y`. Also, a tag <script>alert(1)</script> and a backslash \\.'
        
        # 1. First Escape Pass
        escaped_1 = maintenance_scripts.safe_plain_text_to_markdown(original_text)
        
        # Assertions
        self.assertIn(r'\*world\*', escaped_1)
        self.assertIn(r'\`x = y\`', escaped_1)
        self.assertIn(r'&lt;script&gt;', escaped_1)
        self.assertIn(r'&lt;/script&gt;', escaped_1)
        self.assertIn(r'\\', escaped_1)  # Raw backslash becomes \\
        
        # 2. Second Escape Pass (Idempotency Check)
        escaped_2 = maintenance_scripts.safe_plain_text_to_markdown(escaped_1)
        self.assertEqual(escaped_1, escaped_2, "Escaping is NOT idempotent! Double-escaping occurred.")

    def test_markdown_to_plain_text__split_revert(self):
        """Verify that markdown_to_plain_text perfectly reverses safe_plain_text_to_markdown."""
        original_text = 'Hello *world*! Here is some code: `x = y`. Also, a tag <script>alert(1)</script> and a backslash \\.'
        
        escaped = maintenance_scripts.safe_plain_text_to_markdown(original_text)
        reverted = maintenance_scripts.markdown_to_plain_text(escaped)
        
        self.assertEqual(original_text, reverted, "Reversion is not symmetrical! Original text was not fully restored.")

    def test_migrate_milestone_summaries_to_markdown(self):
        """Verify that the migration script correctly queries features via Stage milestones and batch-updates them."""
        # Setup: Feature has plain text summary and no summary in markdown_fields
        self.assertFalse(self.feature_1.markdown_fields and 'summary' in self.feature_1.markdown_fields)
        
        # Run Dry-Run (No changes committed)
        res_dry = maintenance_scripts.migrate_milestone_summaries_to_markdown(milestone=120, dry_run=True)
        self.assertEqual(res_dry['processed'], 1)
        self.assertEqual(res_dry['updated'], 1)
        
        # Verify DB untouched
        feat_check = FeatureEntry.get_by_id(1001)
        self.assertEqual(feat_check.summary, 'This is a plain summary with *asterisks* and <HTML_tags>.')
        self.assertFalse(feat_check.markdown_fields and 'summary' in feat_check.markdown_fields)
        
        # Run Live Migration (Changes committed)
        res_live = maintenance_scripts.migrate_milestone_summaries_to_markdown(milestone=120, dry_run=False)
        self.assertEqual(res_live['processed'], 1)
        self.assertEqual(res_live['updated'], 1)
        
        # Verify DB updated correctly
        migrated_feat = FeatureEntry.get_by_id(1001)
        self.assertIn(r'\*asterisks\*', migrated_feat.summary)
        self.assertIn(r'&lt;HTML\_tags&gt;', migrated_feat.summary)
        self.assertTrue(migrated_feat.markdown_fields and 'summary' in migrated_feat.markdown_fields)
        
        # Run Migration again (Should skip because it is already migrated!)
        res_repeat = maintenance_scripts.migrate_milestone_summaries_to_markdown(milestone=120, dry_run=False)
        self.assertEqual(res_repeat['processed'], 1)
        self.assertEqual(res_repeat['updated'], 0)  # 0 updated!
