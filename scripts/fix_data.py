#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Google Inc. All Rights Reserved.

import models
import uma


def CorrectPropertyName(bucket_id):
  if bucket_id in uma.CSS_PROPERTY_BUCKETS:
    return uma.CSS_PROPERTY_BUCKETS[bucket_id]
  return None

def FetchAllPropertiesWithError(bucket_id=None):
  q = models.StableInstance.all()
  if bucket_id:
    q.filter('bucket_id =', bucket_id)
  q.filter('property_name =', 'ERROR')

  props = q.fetch(None)

  # Bucket 1 for CSS properties is total pages visited
  props = [p for p in props if p.bucket_id > 1]
  
  return props


if __name__ == '__main__':
  props = FetchAllPropertiesWithError()

  print 'Found', str(len(props)), 'properties tagged "ERROR"'

  need_correcting = {}
  for p in props:
    correct_name = CorrectPropertyName(p.bucket_id)
    if correct_name is not None:
      need_correcting[p.bucket_id] = correct_name

  for p in props:
    if p.bucket_id in need_correcting:
      new_name = need_correcting[p.bucket_id]
      print p.bucket_id, p.property_name, '->', new_name
      p.property_name = new_name
      p.put()

  print 'Done'

