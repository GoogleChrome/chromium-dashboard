from __future__ import division
from __future__ import print_function

#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Google Inc. All Rights Reserved.

"""When new UMA data is collected without a corresponding histogram in the db, the
entry is saved with a property_name === 'ERROR'. The histogram buckets are updated
by a nightly cron job (/cron/histograms), but sometimes changes to the enums.xml
can cause data not make it into a proper bucket. This script finds the invalid.
entities in the datastore and corrects their bucket_id.

How to use:
Copy and paste this script into the interactive GAE console. If there are
deadline errors, run it a few times until there's no more.
"""

from internals import models

allCssPropertyHistograms = models.CssPropertyHistogram.get_all()
allFeatureObserverHistograms = models.FeatureObserverHistogram.get_all()

def CorrectCSSPropertyName(bucket_id):
  if bucket_id in allCssPropertyHistograms:
    return allCssPropertyHistograms[bucket_id]
  return None

def CorrectFeaturePropertyName(bucket_id):
  if bucket_id in allFeatureObserverHistograms:
    return allFeatureObserverHistograms[bucket_id]
  return None


def FetchAllCSSPropertiesWithError(bucket_id=None):
  q = models.StableInstance.query()
  if bucket_id:
    q.filter(models.StableInstance.bucket_id == bucket_id)
  q.filter(models.StableInstance.property_name == 'ERROR')

  props = q.fetch(None)

  # Bucket 1 for CSS properties is total pages visited
  props = [p for p in props if p.bucket_id > 1]

  return props

def FetchAllFeaturesWithError(bucket_id=None):
  q = models.FeatureObserver.query()
  if bucket_id:
    q.filter(models.FeatureObserver.bucket_id == bucket_id)
  q.filter(models.FeatureObserver.property_name == 'ERROR')
  return q.fetch(None)

def fix_up(props, corrector_func):

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
      #p.put() # uncomment commit to the db changes.

props = FetchAllFeaturesWithError()
print('Found', str(len(props)), 'properties tagged "ERROR"')
fix_up(props, corrector_func=CorrectFeaturePropertyName)

css_props = FetchAllCSSPropertiesWithError()
print('Found', str(len(css_props)), 'css properties tagged "ERROR"')
fix_up(css_props, corrector_func=CorrectCSSPropertyName)

print('Done')
