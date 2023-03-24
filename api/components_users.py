# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
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

from chromestatus_openapi.models import (
  ComponentsUsersResponse,
  OwnersAndSubscribersOfComponent,
  ComponentsUser)

from google.cloud import ndb

from framework import basehandlers
from framework import permissions
from internals import user_models

class ComponentsUsersAPI(basehandlers.APIHandler):
  """The list of owners and subscribers for each component."""

  @permissions.require_admin_site
  def do_get(self, **kwargs) -> dict:
    """Returns a dict with 1) subscribers for each component and 2) each component."""
    components: list[user_models.BlinkComponent] = user_models.BlinkComponent.query().order(
        user_models.BlinkComponent.name).fetch(None)
    possible_subscribers: list[user_models.FeatureOwner] = user_models.FeatureOwner.query().order(
        user_models.FeatureOwner.name).fetch(None)

    users = [
        ComponentsUser(
          id=fo.key.integer_id(), email=fo.email, name=fo.name)
        for fo in possible_subscribers]

    component_to_subscribers: dict[ndb.Key, list[int]] = {
      c.key: [] for c in components}
    component_to_owners: dict[ndb.Key, list[int]] = {
      c.key: [] for c in components}
    for ps in possible_subscribers:
      for subed_component_key in ps.blink_components:
        component_to_subscribers[subed_component_key].append(ps.key.integer_id())
      for owned_component_key in ps.primary_blink_components:
        component_to_owners[owned_component_key].append(ps.key.integer_id())

    returned_components: list[OwnersAndSubscribersOfComponent] = []
    for c in components:
      returned_components.append(
        OwnersAndSubscribersOfComponent(
          id=c.key.integer_id(),
          name=c.name,
          subscriber_ids=component_to_subscribers[c.key],
          owner_ids=component_to_owners[c.key]))

    return ComponentsUsersResponse(
      users=users,
      components=returned_components[1:], # ditch generic "Blink" component
      ).to_dict()
