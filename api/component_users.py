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

from framework import basehandlers
from framework import permissions
from internals import user_models

class ComponentUsersAPI(basehandlers.APIHandler):

  def __update_subscribers_list(
      self, add=True, user_id=None, blink_component_id=None, primary=False):
    if not user_id or not blink_component_id:
      return False

    user = user_models.FeatureOwner.get_by_id(int(user_id))
    if not user:
      return True

    if primary:
      if add:
        user.add_as_component_owner(blink_component_id)
      else:
        user.remove_as_component_owner(blink_component_id)
    else:
      if add:
        user.add_to_component_subscribers(blink_component_id)
      else:
        user.remove_from_component_subscribers(blink_component_id)

    return True

  def do_get(self, **kwargs):
    """In the future, this could be implemented."""
    self.abort(405, valid_methods=['PUT', 'DELETE'])

  @permissions.require_admin_site
  def do_put(self, **kwargs) -> tuple[dict, int]:
    params = self.request.get_json(force=True)
    self.__update_subscribers_list(True, user_id=kwargs.get('user_id', None),
                                   blink_component_id=kwargs.get('component_id', None),
                                   primary=params.get('owner'))
    return {}, 200

  @permissions.require_admin_site
  def do_delete(self, **kwargs) -> tuple[dict, int]:
    params = self.request.get_json(force=True)
    self.__update_subscribers_list(False, user_id=kwargs.get('user_id', None),
                                   blink_component_id=kwargs.get('component_id', None),
                                   primary=params.get('owner'))
    return {}, 200