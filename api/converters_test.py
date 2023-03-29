# Copyright 2022 Google Inc.
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

from datetime import datetime

from api import converters
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.review_models import Vote, Gate
from internals import approval_defs


class DelNoneTest(testing_config.CustomTestCase):

  def test_del_none(self):
    d = {}
    self.assertEqual(
        {},
        converters.del_none(d))

    d = {1: 'one', 2: None, 3: {33: None}, 4:{44: 44, 45: None}}
    self.assertEqual(
        {1: 'one', 3: {}, 4: {44: 44}},
        converters.del_none(d))


class FeatureConvertersTest(testing_config.CustomTestCase):

  def setUp(self):
    self.date = datetime.now()
    self.fe_1 = FeatureEntry(
        id=123, name='feature template', summary='sum',
        creator_email='creator@example.com',
        updater_email='updater@example.com', category=1,
        owner_emails=['feature_owner@example.com'], feature_type=0,
        editor_emails=['feature_editor@example.com', 'owner_1@example.com'],
        impl_status_chrome=5, blink_components=['Blink'],
        spec_link='https://example.com/spec',
        sample_links=['https://example.com/samples'], standard_maturity=1,
        ff_views=5, ff_views_link='https://example.com/ff_views',
        ff_views_notes='ff notes', safari_views=1,
        bug_url='https://example.com/bug',
        launch_bug_url='https://example.com/launch_bug',
        safari_views_link='https://example.com/safari_views',
        safari_views_notes='safari notes', web_dev_views=1,
        web_dev_views_link='https://example.com/web_dev',
        doc_links=['https://example.com/docs'], other_views_notes='other notes',
        devrel_emails=['devrel@example.com'], prefixed=False,
        intent_stage=1, tag_review_status=1, security_review_status=2,
        privacy_review_status=1, feature_notes='notes',
        updated=self.date, accurate_as_of=self.date, created=self.date)
    self.fe_1.put()

    # Write stages for the feature.
    stage_types = [110, 120, 130, 140, 150, 151, 160, 1061]
    for s_type in stage_types:
      s = Stage(feature_id=self.fe_1.key.integer_id(), stage_type=s_type,
          milestones=MilestoneSet(desktop_first=1,
              android_first=1, desktop_last=2),
          intent_thread_url=f'https://example.com/{s_type}')
      # Add stage-specific fields based on the stage ID.
      # 150 is the ID associated with the origin trial stage for feature type 0.
      if s_type == 150:
        s.experiment_goals = 'goals'
        s.experiment_risks = 'risks'
        s.announcement_url = 'https://example.com/announce'
      # 151 is the stage ID associated with the origin trial extension.
      elif s_type == 151:
        s.experiment_extension_reason = 'reason'
      # 151 is the ID associated with the shipping stage.
      elif s_type == 160:
        s.finch_url = 'https://example.com/finch'
      s.put()
    self.maxDiff = None

  def tearDown(self) -> None:
    self.fe_1.key.delete()
    for s in Stage.query():
      s.key.delete()

  def test_feature_entry_to_json_basic__normal(self):
    """Converts feature entry to basic JSON dictionary."""
    result = converters.feature_entry_to_json_basic(self.fe_1)
    expected_date = str(self.date)
    expected = {
      'id': 123,
      'name': 'feature template',
      'summary': 'sum',
      'unlisted': False,
      'blink_components': ['Blink'],
      'breaking_change': False,
      'is_released': True,
      'milestone': None,
      'resources': {
        'samples': ['https://example.com/samples'],
        'docs': ['https://example.com/docs'],
      },
      'created': {
        'by': 'creator@example.com',
        'when': expected_date
      },
      'updated': {
        'by': 'updater@example.com',
        'when': expected_date
      },
      'standards': {
        'spec': 'https://example.com/spec',
        'maturity': {
          'text': 'Unknown standards status - check spec link for status',
          'short_text': 'Unknown status',
          'val': 1,
        },
      },
      'browsers': {
        'chrome': {
          'bug': 'https://example.com/bug',
          'blink_components': ['Blink'],
          'devrel':['devrel@example.com'],
          'owners':['feature_owner@example.com'],
          'origintrial': False,
          'intervention': False,
          'prefixed': False,
          'flag': False,
          'status': {
            'text':'Enabled by default',
            'val': 5
          }
        },
        'ff': {
          'view': {
          'text': 'No signal',
          'val': 5,
          'url': 'https://example.com/ff_views',
          'notes': 'ff notes',
          }
        },
        'safari': {
          'view': {
          'text': 'Shipped/Shipping',
          'val': 1,
          'url': 'https://example.com/safari_views',
          'notes': 'safari notes',
          }
        },
        'webdev': {
          'view': {
          'text': 'Strongly positive',
          'val': 1,
          'url': 'https://example.com/web_dev',
          'notes': None,
          }
        },
        'other': {
          'view': {
            'notes': 'other notes',
          }
        }
      }
    }
    self.assertEqual(result, expected)

  def test_feature_entry_to_json_basic__feature_release(self):
    """Converts released feature entry to basic JSON dictionary."""
    stages = [Stage(feature_id=self.fe_1.key.integer_id(), stage_type=160,
          milestones=MilestoneSet(desktop_first=1,android_first=1, desktop_last=2))]
    result = converters.feature_entry_to_json_basic(self.fe_1, stages)
    expected_date = str(self.date)
    expected = {
      'id': 123,
      'name': 'feature template',
      'summary': 'sum',
      'unlisted': False,
      'blink_components': ['Blink'],
      'breaking_change': False,
      'is_released': True,
      'milestone': True,
      'resources': {
        'samples': ['https://example.com/samples'],
        'docs': ['https://example.com/docs'],
      },
      'created': {
        'by': 'creator@example.com',
        'when': expected_date
      },
      'updated': {
        'by': 'updater@example.com',
        'when': expected_date
      },
      'standards': {
        'spec': 'https://example.com/spec',
        'maturity': {
          'text': 'Unknown standards status - check spec link for status',
          'short_text': 'Unknown status',
          'val': 1,
        },
      },
      'browsers': {
        'chrome': {
          'bug': 'https://example.com/bug',
          'blink_components': ['Blink'],
          'devrel':['devrel@example.com'],
          'owners':['feature_owner@example.com'],
          'origintrial': False,
          'intervention': False,
          'prefixed': False,
          'flag': False,
          'status': {
            'text':'Enabled by default',
            'val': 5
          }
        },
        'ff': {
          'view': {
          'text': 'No signal',
          'val': 5,
          'url': 'https://example.com/ff_views',
          'notes': 'ff notes',
          }
        },
        'safari': {
          'view': {
          'text': 'Shipped/Shipping',
          'val': 1,
          'url': 'https://example.com/safari_views',
          'notes': 'safari notes',
          }
        },
        'webdev': {
          'view': {
          'text': 'Strongly positive',
          'val': 1,
          'url': 'https://example.com/web_dev',
          'notes': None,
          }
        },
        'other': {
          'view': {
            'notes': 'other notes',
          },
        },
      },
    }
    self.assertEqual(result, expected)

  def test_feature_entry_to_json_basic__bad_view_field(self):
    """Function handles if any views fields have deprecated values."""
    # Deprecated views enum value.
    self.fe_1.ff_views = 4
    self.fe_1.safari_views = 4
    self.fe_1.put()
    result = converters.feature_entry_to_json_basic(self.fe_1)
    self.assertEqual(5, result['browsers']['safari']['view']['val'])
    self.assertEqual(5, result['browsers']['ff']['view']['val'])

  def test_feature_entry_to_json_basic__empty_feature(self):
    """Function handles if FeatureEntry key is None."""
    empty_fe = FeatureEntry()

    result = converters.feature_entry_to_json_basic(empty_fe)

    self.assertEqual(result, {})

  def test_feature_entry_to_json_verbose__normal(self):
    """Converts feature entry to complete JSON with stage data."""
    result = converters.feature_entry_to_json_verbose(self.fe_1)
    # Remove the stages list for a more apt comparison.
    result.pop('stages')

    expected = {
      'id': 123,
      'name': 'feature template',
      'summary': 'sum',
      'unlisted': False,
      'api_spec': False,
      'breaking_change': False,
      'is_released': True,
      'category': 'Web Components',
      'category_int': 1,
      'feature_type': 'New feature incubation',
      'feature_type_int': 0,
      'is_enterprise_feature': False,
      'intent_stage': 'Start prototyping',
      'intent_stage_int': 1,
      'star_count': 0,
      'bug_url': 'https://example.com/bug',
      'launch_bug_url': 'https://example.com/launch_bug',
      'deleted': False,
      'devrel_emails': ['devrel@example.com'],
      'doc_links': ['https://example.com/docs'],
      'prefixed': False,
      'requires_embedder_support': False,
      'spec_link': 'https://example.com/spec',
      'sample_links': ['https://example.com/samples'],
      'created': {
        'by': 'creator@example.com',
        'when': str(self.date)
      },
      'updated': {
        'by': 'updater@example.com',
        'when': str(self.date)
      },
      'accurate_as_of': str(self.date),
      'resources': {
        'samples': ['https://example.com/samples'],
        'docs': ['https://example.com/docs'],
      },
      'standards': {
        'spec': 'https://example.com/spec',
        'maturity': {
          'text': 'Unknown standards status - check spec link for status',
          'short_text': 'Unknown status',
          'val': 1,
        },
      },

      'activation_risks': None,
      'active_stage_id': None,
      'adoption_expectation': None,
      'adoption_plan': None,
      'all_platforms': None,
      'all_platforms_descr': None,
      'anticipated_spec_changes': None,
      'availability_expectation': None,
      'blink_components': ['Blink'],

      'cc_emails': [],
      'cc_recipients': [],
      'creator_email': 'creator@example.com',
      'debuggability': None,
      'devtrial_instructions': None,
      'editor_emails': ['feature_editor@example.com', 'owner_1@example.com'],
      'enterprise_feature_categories': [],
      'ergonomics_risks': None,
      'experiment_timeline': None,
      'explainer_links': [],
      'feature_notes': 'notes',
      'ff_views': 5,
      'flag_name': None,
      'initial_public_proposal_url': None,
      'interop_compat_risks': None,
      'measurement': None,
      'motivation': None,
      'new_crbug_url': None,
      'non_oss_deps': None,
      'ongoing_constraints': None,
      'owner_emails': ['feature_owner@example.com'],
      'owner_emails': ['feature_owner@example.com'],
      'safari_views': 1,
      'search_tags': [],
      'security_risks': None,
      'spec_mentor_emails': [],
      'spec_mentors': [],
      'tag_review': None,
      'tags': [],
      'updated_display': None,
      'updater_email': 'updater@example.com',
      'web_dev_views': 1,
      'webview_risks': None,
      'wpt': None,
      'wpt_descr': None,

      'tag_review_status': 'Pending',
      'tag_review_status_int': 1,
      'security_review_status': 'Issues open',
      'security_review_status_int': 2,
      'privacy_review_status': 'Pending',
      'privacy_review_status_int': 1,
      'editors': ['feature_editor@example.com', 'owner_1@example.com'],
      'creator': 'creator@example.com',
      'comments': 'notes',
      'browsers': {
        'chrome': {
          'bug': 'https://example.com/bug',
          'blink_components': ['Blink'],
          'devrel':['devrel@example.com'],
          'owners':['feature_owner@example.com'],
          'desktop': 1,
          'android': 1,
          'ios': None,

          'origintrial': False,
          'intervention': False,
          'prefixed': False,
          'flag': False,
          'webview': None,
          'status': {
            'milestone_str': '1',
            'text': 'Enabled by default',
            'val': 5
          }
        },
        'ff': {
          'view': {
          'text': 'No signal',
          'val': 5,
          'url': 'https://example.com/ff_views',
          'notes': 'ff notes',
          }
        },
        'safari': {
          'view': {
          'text': 'Shipped/Shipping',
          'val': 1,
          'url': 'https://example.com/safari_views',
          'notes': 'safari notes',
          }
        },
        'webdev': {
          'view': {
          'notes': None,
          'text': 'Strongly positive',
          'val': 1,
          'url': 'https://example.com/web_dev',
          }
        },
        'other': {
          'view': {
            'notes': 'other notes',                                      
            'text': None,
            'url': None,
            'val': None,
          },
        },
      },
    }
    self.assertEqual(result, expected)

  def test_feature_entry_to_json_verbose__bad_view_field(self):
    """Function handles if any views fields have deprecated values."""
    # Deprecated views enum value.
    self.fe_1.safari_views = 4
    self.fe_1.ff_views = 4
    self.fe_1.put()
    result = converters.feature_entry_to_json_verbose(self.fe_1)
    self.assertEqual(5, result['browsers']['safari']['view']['val'])
    self.assertEqual(5, result['browsers']['ff']['view']['val'])

  def test_feature_entry_to_json_verbose__enterprise_feature(self):
    """Function handles if any views fields have deprecated values."""
    # Deprecated views enum value.
    self.fe_1.feature_type = 4 # FEATURE_TYPE_ENTERPRISE_ID
    self.fe_1.enterprise_feature_categories = ['1', '2']
    self.fe_1.put()
    result = converters.feature_entry_to_json_verbose(self.fe_1)
    self.assertTrue(result['is_enterprise_feature'])
    self.assertEqual(['1', '2'], result['enterprise_feature_categories'])

  def test_feature_entry_to_json_verbose__empty_feature(self):
    """Function handles an empty feature."""
    empty_fe = FeatureEntry()

    with self.assertRaises(Exception):
      converters.feature_entry_to_json_verbose(empty_fe)


class VoteConvertersTest(testing_config.CustomTestCase):

  def test_conversion(self):
    """We can convert a Vote entity to JSON."""
    vote = Vote(
        feature_id=1, gate_id=2, gate_type=3, state=4,
        set_on=datetime(2022, 12, 14, 1, 2, 3),
        set_by='user@example.com')
    actual = converters.vote_value_to_json_dict(vote)
    expected = {
      'feature_id': 1,
      'gate_id': 2,
      'gate_type': 3,
      'state': 4,
      'set_on': '2022-12-14 01:02:03',
      'set_by': 'user@example.com',
      }
    self.assertEqual(expected, actual)


class GateConvertersTest(testing_config.CustomTestCase):

  def tearDown(self) -> None:
    for g in Gate.query():
      g.key.delete()

  def test_minimal(self):
    """If a Gate has only required fields set, we can convert it to JSON."""
    gate = Gate(feature_id=1, stage_id=2, gate_type=3, state=4)
    gate.put()
    actual = converters.gate_value_to_json_dict(gate)
    appr_def = approval_defs.APPROVAL_FIELDS_BY_ID[gate.gate_type]
    expected = {
      'id': gate.key.integer_id(),
      'feature_id': 1,
      'stage_id': 2,
      'gate_type': 3,
      'team_name': appr_def.team_name,
      'gate_name': appr_def.name,
      'state': 4,
      'requested_on': None,
      'owners': [],
      'next_action': None,
      'additional_review': False,
      }
    self.assertEqual(expected, actual)

  def test_maxmimal(self):
    """If a Gate has all fields set, we can convert it to JSON."""
    gate = Gate(
        feature_id=1, stage_id=2, gate_type=3, state=4,
        requested_on=datetime(2022, 12, 14, 1, 2, 3),
        owners=['appr1@example.com', 'appr2@example.com'],
        next_action=datetime(2022, 12, 25),
        additional_review=True)
    gate.put()
    actual = converters.gate_value_to_json_dict(gate)
    appr_def = approval_defs.APPROVAL_FIELDS_BY_ID[gate.gate_type]
    expected = {
      'id': gate.key.integer_id(),
      'feature_id': 1,
      'stage_id': 2,
      'gate_type': 3,
      'team_name': appr_def.team_name,
      'gate_name': appr_def.name,
      'state': 4,
      'requested_on': '2022-12-14 01:02:03',
      'owners': ['appr1@example.com', 'appr2@example.com'],
      'next_action': '2022-12-25',
      'additional_review': True,
      }
    self.assertEqual(expected, actual)
