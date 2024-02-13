#!/usr/bin/env python
#
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Fetches features from the staging or live dashboard site, and inserts them into the development
datastore.

This script can also set a user as admin, to facilitate testing those parts of the site.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from urllib.parse import urljoin

import requests
from google.cloud import ndb  # type: ignore

sys.path = [os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            ] + sys.path
os.environ.setdefault('DATASTORE_EMULATOR_HOST', 'localhost:15606')
os.environ.setdefault('GAE_ENV', 'localdev')
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'cr-status-staging')
os.environ.setdefault('SERVER_SOFTWARE', 'gunicorn')

# pylint: disable=wrong-import-position
# ruff: noqa: E402
from internals.core_enums import MISC
from internals.core_models import FeatureEntry, MilestoneSet, Stage
from internals.user_models import AppUser
from pages.guide import FeatureCreateHandler


def add_features(server: str, after: datetime, detailsAfter: datetime):
  """Fetches features from `server` and inserts them into the dev datastore."""
  target = urljoin(server, 'features.json')
  logging.info('Fetching features from %s.', target)
  features = requests.get(target, timeout=120)
  features.raise_for_status()

  parsed_features = features.json()
  recent_features = [
      f for f in parsed_features
      if after < datetime.fromisoformat(f['updated']['when'])
  ]
  logging.info('Adding %d recent features of %d total to the datastore.',
               len(recent_features), len(parsed_features))

  for f in recent_features:
    fe = FeatureEntry(id=f['id'],
                      created=datetime.fromisoformat(f['created']['when']),
                      updated=datetime.fromisoformat(f['updated']['when']))
    fe.name = f['name']
    fe.summary = f['summary']
    fe.category = MISC
    fe.breaking_change = f['breaking_change']
    fe.first_enterprise_notification_milestone = f[
        'first_enterprise_notification_milestone']
    fe.blink_components = f['blink_components']
    fe.sample_links = f['resources']['samples']
    fe.doc_links = f['resources']['docs']
    fe.creator_email = f['created']['by']
    fe.updater_email = f['updated']['by']

    fe.impl_status_chrome = f['browsers']['chrome']['status']['val']
    fe.bug_url = f['browsers']['chrome']['bug']
    fe.devrel_emails = f['browsers']['chrome']['devrel']
    fe.owner_emails = f['browsers']['chrome']['owners']
    fe.prefixed = f['browsers']['chrome']['prefixed']
    fe.spec_link = f['standards']['spec']
    fe.standard_maturity = f['standards']['maturity']['val']
    fe.ff_views = f['browsers']['ff']['view']['val']
    fe.ff_views_link = f['browsers']['ff']['view']['url']
    fe.ff_views_notes = f['browsers']['ff']['view']['notes']
    fe.safari_views = f['browsers']['safari']['view']['val']
    fe.safari_views_link = f['browsers']['safari']['view']['url']
    fe.safari_views_notes = f['browsers']['safari']['view']['notes']
    fe.web_dev_views = f['browsers']['webdev']['view']['val']
    fe.web_dev_views_link = f['browsers']['webdev']['view']['url']
    fe.web_dev_views_notes = f['browsers']['webdev']['view']['notes']
    fe.other_views_notes = f['browsers']['other']['view']['notes']

    details = None
    if fe.updated > detailsAfter:
      url = urljoin(server, f'api/v0/features/{f["id"]}')
      result = requests.get(url)
      if 400 <= result.status_code:
        logging.error('Could not fetch details for %r', url)
        continue
      result.raise_for_status()
      details = json.loads(result.text[5:])

      fe.star_count = details['star_count']
      fe.search_tags = details['search_tags']
      fe.category = details['category_int']
      fe.feature_notes = details['feature_notes']
      fe.enterprise_feature_categories = details[
          'enterprise_feature_categories']
      if details['accurate_as_of'] is not None:
        fe.accurate_as_of = datetime.fromisoformat(details['accurate_as_of'])
      fe.editor_emails = details['editor_emails']
      fe.cc_emails = details['cc_emails']
      fe.spec_mentor_emails = details['spec_mentor_emails']
      fe.deleted = details['deleted']
      fe.feature_type = details['feature_type_int']
      fe.intent_stage = details['intent_stage_int']
      fe.active_stage_id = details['active_stage_id']
      fe.bug_url = details['bug_url']
      fe.launch_bug_url = details['launch_bug_url']
      fe.screenshot_links = details['screenshot_links']
      fe.first_enterprise_notification_milestone = details[
          'first_enterprise_notification_milestone']
      fe.flag_name = details['flag_name']
      fe.finch_name = details['finch_name']
      fe.non_finch_justification = details['non_finch_justification']
      fe.ongoing_constraints = details['ongoing_constraints']
      fe.motivation = details['motivation']
      fe.devtrial_instructions = details['devtrial_instructions']
      fe.activation_risks = details['activation_risks']
      fe.measurement = details['measurement']
      fe.availability_expectation = details['availability_expectation']
      fe.adoption_expectation = details['adoption_expectation']
      fe.adoption_plan = details['adoption_plan']
      fe.initial_public_proposal_url = details['initial_public_proposal_url']
      fe.explainer_links = details['explainer_links']
      fe.requires_embedder_support = details['requires_embedder_support']
      fe.api_spec = details['api_spec']
      fe.interop_compat_risks = details['interop_compat_risks']
      fe.all_platforms = details['all_platforms']
      fe.all_platforms_descr = details['all_platforms_descr']
      fe.non_oss_deps = details['non_oss_deps']
      fe.anticipated_spec_changes = details['anticipated_spec_changes']
      fe.security_risks = details['security_risks']
      fe.ergonomics_risks = details['ergonomics_risks']
      fe.wpt = details['wpt']
      fe.wpt_descr = details['wpt_descr']
      fe.webview_risks = details['webview_risks']
      fe.devrel_emails = details['devrel_emails']
      fe.debuggability = details['debuggability']
      fe.doc_links = details['doc_links']
      fe.sample_links = details['sample_links']
      fe.search_tags = details['tags']
      fe.tag_review = details['tag_review']
      fe.tag_review_status = details['tag_review_status_int']
      fe.security_review_status = details['security_review_status_int']
      fe.privacy_review_status = details['privacy_review_status_int']

      fe.experiment_timeline = details['experiment_timeline']

      for stage in details['stages']:
        s = Stage(id=stage['id'],
                  feature_id=stage['feature_id'],
                  stage_type=stage['stage_type'])
        s.created = datetime.fromisoformat(stage['created'])
        s.ot_description = stage['ot_description']
        s.display_name = stage['display_name']
        s.pm_emails = stage['pm_emails']
        s.tl_emails = stage['tl_emails']
        s.ux_emails = stage['ux_emails']
        s.te_emails = stage['te_emails']
        s.intent_thread_url = stage['intent_thread_url']

        s.announcement_url = stage['announcement_url']
        s.experiment_goals = stage['experiment_goals']
        s.experiment_risks = stage['experiment_risks']
        s.origin_trial_id = stage['origin_trial_id']
        s.origin_trial_feedback_url = stage['origin_trial_feedback_url']
        s.ot_action_requested = stage['ot_action_requested']
        s.ot_approval_buganizer_component = stage[
            'ot_approval_buganizer_component']
        s.ot_approval_criteria_url = stage['ot_approval_criteria_url']
        s.ot_approval_group_email = stage['ot_approval_group_email']
        s.ot_chromium_trial_name = stage['ot_chromium_trial_name']
        s.ot_description = stage['ot_description']
        s.ot_display_name = stage['ot_display_name']
        s.ot_documentation_url = stage['ot_documentation_url']
        s.ot_emails = stage['ot_emails']
        s.ot_feedback_submission_url = stage['ot_feedback_submission_url']
        s.ot_has_third_party_support = stage['ot_has_third_party_support']
        s.ot_is_critical_trial = stage['ot_is_critical_trial']
        s.ot_is_deprecation_trial = stage['ot_is_deprecation_trial']
        s.ot_owner_email = stage['ot_owner_email']
        s.ot_require_approvals = stage['ot_require_approvals']
        s.ot_webfeature_use_counter = stage['ot_webfeature_use_counter']
        s.experiment_extension_reason = stage['experiment_extension_reason']
        s.ot_stage_id = stage['ot_stage_id']
        s.finch_url = stage['finch_url']

        s.rollout_milestone = stage['rollout_milestone']
        s.rollout_platforms = stage['rollout_platforms']
        s.rollout_details = stage['rollout_details']
        s.rollout_impact = stage['rollout_impact']
        s.enterprise_policies = stage['enterprise_policies']

        s.milestones = MilestoneSet()
        s.milestones.desktop_first = stage['desktop_first']
        s.milestones.android_first = stage['android_first']
        s.milestones.ios_first = stage['ios_first']
        s.milestones.webview_first = stage['webview_first']
        s.milestones.desktop_last = stage['desktop_last']
        s.milestones.android_last = stage['android_last']
        s.milestones.ios_last = stage['ios_last']
        s.milestones.webview_last = stage['webview_last']

        s.put()

    fe.put()

    if details is None:
      FeatureCreateHandler().write_gates_and_stages_for_feature(
          fe.key.id(), fe.feature_type)


def add_admin(email: str):
  """Makes the user named `email` an admin."""
  user = AppUser()
  user.email = email
  user.is_admin = True
  user.put()


parser = argparse.ArgumentParser(description='seed the development datastore')
parser.add_argument(
    '--server',
    help='the root URL of a chrome status server, or "" to skip importing',
    default='https://cr-status-staging.appspot.com/')
parser.add_argument('--admin',
                    help='email address of the user to make a site admin')
parser.add_argument(
    '--after',
    type=datetime.fromisoformat,
    help=
    'only add features that have been updated since AFTER (in ISO date format)',
    default='0001-01-01')
parser.add_argument(
    '--details-after',
    type=datetime.fromisoformat,
    help=
    'fetch more details for each feature that was updated since DETAILS-AFTER',
    default='9999-01-01')

args = parser.parse_args()
client = ndb.Client()
with client.context():
  if args.server:
    add_features(server=args.server,
                 after=args.after,
                 detailsAfter=args.details_after)

  if args.admin:
    logging.info('Making %s an admin.', args.admin)
    add_admin(args.admin)
