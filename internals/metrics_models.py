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


from google.cloud import ndb as ndb


# UMA metrics.
class StableInstance(ndb.Model):
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)

  property_name = ndb.StringProperty(required=True)
  bucket_id = ndb.IntegerProperty(required=True)
  date = ndb.DateProperty(verbose_name='When the data was fetched',
                         required=True)
  day_percentage = ndb.FloatProperty()
  rolling_percentage = ndb.FloatProperty()


class AnimatedProperty(StableInstance):
  pass


class FeatureObserver(StableInstance):
  pass


class HistogramModel(ndb.Model):
  """Container for a histogram."""

  bucket_id = ndb.IntegerProperty(required=True)
  property_name = ndb.StringProperty(required=True)

  @classmethod
  def get_all(self):
    output = {}
    buckets = self.query().fetch(None)
    for bucket in buckets:
      output[bucket.bucket_id] = bucket.property_name
    return output

class CssPropertyHistogram(HistogramModel):
  pass

class FeatureObserverHistogram(HistogramModel):
  pass
