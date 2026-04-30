#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""Seed local datastore with demo data for /myfeatures/editable."""

import argparse
import os
import sys

from google.cloud import ndb  # type: ignore

sys.path = [
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
] + sys.path
os.environ.setdefault('DATASTORE_EMULATOR_HOST', 'localhost:15606')
os.environ.setdefault('GAE_ENV', 'localdev')
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'cr-status-staging')
os.environ.setdefault('SERVER_SOFTWARE', 'gunicorn')

# pylint: disable=wrong-import-position
# ruff: noqa: E402
from internals import core_enums
from internals.core_models import FeatureEntry
from internals.user_models import AppUser, UserPref


def seed_demo(email: str):
    app_user = AppUser.get_app_user(email)
    if not app_user:
        app_user = AppUser(email=email, is_admin=True)
    else:
        app_user.is_admin = True
    app_user.put()

    user_pref = UserPref.get_signed_in_user_pref()
    if not user_pref:
        user_pref = UserPref(email=email)

    features = [
        FeatureEntry(
            name='Demo Editable Feature - Active',
            summary='Recent feature that should stay visible.',
            category=core_enums.MISC,
            feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
            owner_emails=[email],
            editor_emails=[email],
        ),
        FeatureEntry(
            name='Demo Editable Feature - Old Cleanup',
            summary='Older feature to mark done and hide by default.',
            category=core_enums.MISC,
            feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
            owner_emails=[email],
            editor_emails=[email],
        ),
        FeatureEntry(
            name='Demo Editable Feature - Very Old',
            summary='Another old feature to mark done.',
            category=core_enums.MISC,
            feature_type=core_enums.FEATURE_TYPE_INCUBATE_ID,
            owner_emails=[email],
            editor_emails=[email],
        ),
    ]

    created_ids = []
    for fe in features:
        key = fe.put()
        created_ids.append(key.id())

    # Pre-mark one feature as done so you can verify toggle behavior quickly.
    user_pref.editable_done_feature_ids = [created_ids[2]]
    user_pref.put()

    print('Seeded demo data for:', email)
    print('Feature IDs:', created_ids)
    print('Pre-marked done:', user_pref.editable_done_feature_ids)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', required=True)
    args = parser.parse_args()

    # Needed because get_signed_in_user_pref depends on current user.
    # For this script we write UserPref directly when needed.
    client = ndb.Client()
    with client.context():
        # Directly create preference for email.
        pref = UserPref.query().filter(UserPref.email == args.email).get()
        if not pref:
            pref = UserPref(email=args.email)
            pref.put()
        seed_demo(args.email)
