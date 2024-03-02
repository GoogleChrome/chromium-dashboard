# Copyright 2024 Google Inc.
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

from chromestatus_openapi.models.feature_link import FeatureLink
from chromestatus_openapi.models.spec_mentor import SpecMentor

from framework import basehandlers
from internals.core_models import FeatureEntry


class SpecMentorsAPI(basehandlers.APIHandler):
  """Implements the OpenAPI /spec_mentors path."""

  def do_get(self, **kwargs):
    """Get a list of matching spec mentors.

    Returns:
      A list of data on all public origin trials.
    """
    after_param: str | None = self.request.args.get('after', None)
    after: datetime | None = None
    if after_param is not None:
      try:
        after = datetime.fromisoformat(after_param)
      except ValueError:
        self.abort(400, f'invalid ?after parameter {after_param}')

    # Every non-empty string is greater than '', so this will find all entries with any spec mentors
    # set. (!= is interpreted as "less or greater".)
    # We can't have NDB sort the results because it can only sort by the inequality condition.
    query = FeatureEntry.query(FeatureEntry.spec_mentor_emails > '')
    features: list[FeatureEntry] = query.fetch()
    if after is not None:
      # Do this in Python rather than the NDB query because NDB queries only support one inequality.
      features = [feature for feature in features if feature.updated > after]
    features.sort(key=lambda f: f.updated, reverse=True)

    mentors: dict[str, list[FeatureLink]] = {}
    for feature in features:
      if feature.unlisted:
        # TODO: Consider showing these when the caller is logged in and has the right to see them.
        continue
      for mentor in feature.spec_mentor_emails:
        mentors.setdefault(mentor,
                           []).append(FeatureLink(id=feature.key.integer_id(), name=feature.name))

    return [
        SpecMentor(email, features).to_dict()
        for email, features in sorted(mentors.items())
    ]
