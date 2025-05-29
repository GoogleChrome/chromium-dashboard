# Copyright 2025 Google Inc.
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
from google.cloud import ndb  # type: ignore

from framework import basehandlers
from internals.approval_defs import APPROVAL_FIELDS_BY_ID
from internals.review_models import Activity, Gate

from chromestatus_openapi.models import (
  ReviewActivity as ReviewActivityModel,
  GetReviewActivitiesResponse,
)

class ReviewActivitiesAPI(basehandlers.APIHandler):
  """View existing review activity events in Chromestatus for all features."""
  REQUEST_DATE_FORMAT = '%Y-%m-%d'
  RESPONSE_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

  def do_get(self, **kwargs) -> GetReviewActivitiesResponse:
    """Return a list of all review activity events in Chromestatus."""
    time_start = self.request.args.get('start')
    if time_start is None:
      self.abort(400, msg='No start timestamp provided.')
    try:
      formatted_time = datetime.strptime(time_start, self.REQUEST_DATE_FORMAT)
    except ValueError:
      self.abort(400, msg='Bad date format. Format should be YYYY-MM-DD')

    # Note: We assume that anyone may view approval comments.
    activities: list[Activity] = Activity.query(
        Activity.created >= formatted_time).order(Activity.created).fetch(5000)

    # Filter deleted activities the user can't see, and activities that have
    # no gate ID, meaning they do not represent review activity.
    activities = list(filter(
      lambda a: (a.deleted_by is None
                 and a.gate_id is not None),
      activities))
    gate_ids = set([a.gate_id for a in activities])
    gates = ndb.get_multi([ndb.Key('Gate', g_id) for g_id in gate_ids])
    gates_dict: dict[int, Gate] = {g.key.integer_id(): g for g in gates}

    activities_formatted: list[ReviewActivityModel] = []
    for a in activities:
      review_status = None
      review_assignee = None
      gate_type = gates_dict[a.gate_id].gate_type
      if len(a.amendments):
        # There should only be 1 amendment for review changes.
        if a.amendments[0].field_name == 'review_status':
          review_status = a.amendments[0].new_value
        if a.amendments[0].field_name == 'review_assignee':
          review_assignee = a.amendments[0].new_value
      activities_formatted.append(
        ReviewActivityModel(
          feature_id=a.feature_id,
          team_name=APPROVAL_FIELDS_BY_ID[gate_type].team_name,
          event_type=(a.amendments[0].field_name
                      if len(a.amendments) else 'comment'),
          event_date=datetime.strftime(a.created, self.RESPONSE_DATETIME_FORMAT),
          review_status=review_status,
          review_assignee=review_assignee,
          author=a.author,
          content=a.content,
        ))

    return GetReviewActivitiesResponse(activities=activities_formatted)
