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

from datetime import datetime
from google.cloud import ndb
from urllib.parse import urljoin
import argparse
import logging
import os
import pprint
import requests
import sys

sys.path = [os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            ] + sys.path
os.environ['DATASTORE_EMULATOR_HOST'] = 'localhost:15606'
os.environ['GAE_ENV'] = 'localdev'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'cr-status-staging'
os.environ['SERVER_SOFTWARE'] = 'gunicorn'

from internals.core_enums import MISC
from internals.core_models import FeatureEntry
from internals.user_models import AppUser

parser = argparse.ArgumentParser(description='seed the development datastore')
parser.add_argument(
    '--server',
    help='the root of a chrome status server, or "" to skip importing',
    default='https://cr-status-staging.appspot.com/')
parser.add_argument('--admin',
                    help='email address of the user to make a site admin')
parser.add_argument(
    '--after',
    type=datetime.fromisoformat,
    help='only add features that have been updated since AFTER',
    default='0001-01-01')

args = parser.parse_args()
client = ndb.Client()
with client.context():
    if args.server:
        target = urljoin(args.server, 'features.json')
        logging.info('Fetching features from %s.', target)
        features = requests.get(target, timeout=120)
        features.raise_for_status()

        parsed_features = features.json()
        recent_features = [
            f for f in parsed_features
            if args.after < datetime.fromisoformat(f['updated']['when'])
        ]
        logging.info('Adding %d recent features of %d total to the datastore.',
                     len(recent_features), len(parsed_features))

        for f in recent_features:
            fe = FeatureEntry(
                id=f['id'],
                created=datetime.fromisoformat(f['created']['when']),
                updated=datetime.fromisoformat(f['updated']['when']))
            fe.name = f['name']
            fe.summary = f['summary']
            fe.category = f.get('category_int', MISC)
            # fe.feature_type = f['feature_type']  # Not available from the dump?
            fe.impl_status_chrome = f['browsers']['chrome']['status']['val']
            fe.standard_maturity = f['standards']['maturity']['val']
            fe.ff_views = f['browsers']['ff']['view']['val']
            fe.safari_views = f['browsers']['safari']['view']['val']
            fe.web_dev_views = f['browsers']['webdev']['view']['val']

            x = ({
                'unlisted': fe.unlisted,
                'breaking_change': fe.breaking_change,
                'blink_components': fe.blink_components or [],
                'resources': {
                    'samples': fe.sample_links or [],
                    'docs': fe.doc_links or [],
                },
                'created': {
                    'by': fe.creator_email,
                },
                'updated': {
                    'by': fe.updater_email,
                },
                'standards': {
                    'spec': fe.spec_link,
                },
                'browsers': {
                    'chrome': {
                        'bug': fe.bug_url,
                        'blink_components': fe.blink_components or [],
                        'devrel': fe.devrel_emails or [],
                        'owners': fe.owner_emails or [],
                        'prefixed': fe.prefixed,
                    },
                    'ff': {
                        'view': {
                            'url': fe.ff_views_link,
                            'notes': fe.ff_views_notes,
                        }
                    },
                    'safari': {
                        'view': {
                            'url': fe.safari_views_link,
                            'notes': fe.safari_views_notes,
                        }
                    },
                    'webdev': {
                        'view': {
                            'url': fe.web_dev_views_link,
                            'notes': fe.web_dev_views_notes,
                        }
                    },
                    'other': {
                        'view': {
                            'notes': fe.other_views_notes,
                        }
                    },
                }
            })
            fe.put()

    if args.admin:
        logging.info('Making %s an admin.', args.admin)
        user = AppUser()
        user.email = args.admin
        user.is_admin = True
        user.put()
