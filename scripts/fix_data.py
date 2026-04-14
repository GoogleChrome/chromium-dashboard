#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Google LLC
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

"""When new UMA data is collected without a corresponding histogram in
the db, the entry is saved with a property_name === 'ERROR'. The
histogram buckets are updated by a nightly cron job
(/cron/histograms), but sometimes changes to the enums.xml can cause
data not make it into a proper bucket. This script finds the invalid.
entities in the datastore and corrects their bucket_id.

How to use:
Copy and paste this script into the interactive GAE console. If there are
deadline errors, run it a few times until there's no more.

"""  # noqa: D205

from internals import metrics_models

allCssPropertyHistograms = metrics_models.CssPropertyHistogram.get_all()
allFeatureObserverHistograms = metrics_models.FeatureObserverHistogram.get_all()


def CorrectCSSPropertyName(bucket_id):
    """Returns the correct CSS property name for a given bucket ID."""
    if bucket_id in allCssPropertyHistograms:
        return allCssPropertyHistograms[bucket_id]
    return None


def CorrectFeaturePropertyName(bucket_id):
    """Returns the correct feature property name for a given bucket ID."""
    if bucket_id in allFeatureObserverHistograms:
        return allFeatureObserverHistograms[bucket_id]
    return None


def FetchAllCSSPropertiesWithError(bucket_id=None):
    """Fetches all StableInstance records with an ERROR property for CSS."""
    q = metrics_models.StableInstance.query()
    if bucket_id:
        q = q.filter(metrics_models.StableInstance.bucket_id == bucket_id)
    q = q.filter(metrics_models.StableInstance.property_name == 'ERROR')

    props = q.fetch(None)

    # Bucket 1 for CSS properties is total pages visited
    props = [p for p in props if p.bucket_id > 1]

    return props


def FetchAllFeaturesWithError(bucket_id=None):
    """Fetch all FeatureObserver entities with a property_name of 'ERROR'."""
    q = metrics_models.FeatureObserver.query()
    if bucket_id:
        q = q.filter(metrics_models.FeatureObserver.bucket_id == bucket_id)
    q = q.filter(metrics_models.FeatureObserver.property_name == 'ERROR')
    return q.fetch(None)


def fix_up(props, corrector_func):
    """Correct the property names for a list of metrics entities."""
    need_correcting = {}
    for p in props:
        correct_name = corrector_func(p.bucket_id)
        if correct_name is not None:
            need_correcting[p.bucket_id] = correct_name

    for p in props:
        if p.bucket_id in need_correcting:
            new_name = need_correcting[p.bucket_id]
            print(p.bucket_id, p.property_name, '->', new_name)
            p.property_name = new_name
            # p.put() # uncomment commit to the db changes.


props = FetchAllFeaturesWithError()
print('Found', str(len(props)), 'properties tagged "ERROR"')
fix_up(props, corrector_func=CorrectFeaturePropertyName)

css_props = FetchAllCSSPropertiesWithError()
print('Found', str(len(css_props)), 'css properties tagged "ERROR"')
fix_up(css_props, corrector_func=CorrectCSSPropertyName)

print('Done')
