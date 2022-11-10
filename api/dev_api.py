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

from datetime import datetime
import json
import logging
from google.cloud import ndb  # type: ignore

from framework.basehandlers import APIHandler
from internals.core_models import Feature, FeatureEntry, MilestoneSet, Stage
from internals.review_models import Activity, Approval, Comment, Gate, Vote
from internals.core_enums import *
import settings

class ClearEntities(APIHandler):

  def do_get(self, **kwargs):

    if not settings.DEV_MODE:
      self.abort(status=403,
          msg="This can only be used in a development environment.")
    
    kinds: list[ndb.Model] = [Feature, FeatureEntry, MilestoneSet,
        Stage, Activity, Approval, Comment, Gate, Vote]
    
    for kind in kinds:
      for entity in kind.query():
        entity.key.delete()


class WriteDevData(APIHandler):

  DATE_FORMAT = '%Y-%m-%d'

  def do_get(self, **kwargs):

    if not settings.DEV_MODE:
      self.abort(status=403,
          msg="This can only be used in a development environment.")

    with open('data/dev_data.json') as f:
      info = json.load(f)
      for d in info['feature_entries']:
        f_id = d.pop('id')
        created = datetime.strptime(d.pop('created'), self.DATE_FORMAT)
        updated = datetime.strptime(d.pop('updated'), self.DATE_FORMAT)
        accurate_as_of = datetime.strptime(
            d.pop('accurate_as_of'), self.DATE_FORMAT)

        fe = FeatureEntry(id=f_id, created=created, updated=updated,
            accurate_as_of=accurate_as_of)
        for field, value in d.items():
          setattr(fe, field, value)
        fe.put()

      for d in info['stages']:
        stage = Stage(id=d.pop('id'))
        for field, value in d.items():
          setattr(stage, field, value)
        stage.put()
      
      for d in info['gates']:
        gate = Gate(id=d.pop('id'))
        for field, value in d.items():
          setattr(gate, field, value)
        gate.put()
    
    return {'message': 'Done'}
