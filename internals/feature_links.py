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

import logging
from typing import Any
from internals.core_models import FeatureEntry
from internals.link_helpers import Link

from google.cloud import ndb  # type: ignore


class FeatureLinks(ndb.Model):
  """Links that occur in the fields of the feature. 
  This helps show a preview of information of linked pages, saving users the trouble of clicking.
  """
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now=True)
  feature_ids = ndb.IntegerProperty(repeated=True)
  url = ndb.StringProperty(required=True)
  type = ndb.StringProperty(required=True)
  information = ndb.JsonProperty()


def update_feature_links(fe: FeatureEntry, changed_fields: list[tuple[str, Any, Any]]) -> None:
  """Update the links in the given feature entry."""
  for _, old_val, new_val in changed_fields:
    if new_val != old_val:
      if old_val is None and not bool(new_val):
        continue
      if isinstance(old_val, str) and Link.get_type(old_val):
        link = Link(old_val)
        fe_dict = fe.to_dict()
        if link.url not in list(fe_dict.values()):
          # if the link is not in other fields, then remove it
          _remove_link(link, fe)
      if isinstance(new_val, str) and Link.get_type(new_val):
        link = Link(new_val)
        _index_link(link, fe)
      elif isinstance(new_val, list):
        # TODO: check if new_val/new_val is a list of links, if so, then index/un-index each link.
        # TODO: check if new_val/new_val is a long text with links, if so, then index/un-index each link.
        pass


def _index_link(link: Link, fe: FeatureEntry) -> None:
  """Index the given link."""
  logging.info(f'Indexing link {link.url} for feature {fe.key.integer_id()}')
  feature_id = fe.key.integer_id()
  feature_links = FeatureLinks.query(FeatureLinks.url == link.url).fetch(None)
  feature_link: FeatureLinks = feature_links[0] if feature_links else None
  if hasattr(feature_link, 'feature_ids'):
    if feature_id not in feature_link.feature_ids:
      feature_link.feature_ids.append(feature_id)
      feature_link.type = link.type
      logging.info(f'Add feature {feature_id} to existing link {link.url}')
  else:
    # we only want to parse the link if it is new,
    # for existing links, we will use a cron job to update the information
    link.parse()
    if link.information is None:
      logging.info(f'Could not parse link {link.url}')
    feature_link = FeatureLinks(
        feature_ids=[feature_id],
        type=link.type,
        url=link.url,
        information=link.information
    )
    logging.info(f'Created link {link.url}')
  logging.info(f'Indexed link {link.url} for feature {feature_id}')
  feature_link.put()


def _remove_link(link: Link, fe: FeatureEntry) -> None:
  """Un-index the given link."""
  feature_id = fe.key.integer_id()
  feature_links = FeatureLinks.query(FeatureLinks.url == link.url).fetch(None)
  feature_link: FeatureLinks = feature_links[0] if feature_links else None
  if hasattr(feature_link, 'feature_ids'):
    if feature_id in feature_link.feature_ids:
      feature_link.feature_ids.remove(feature_id)
      if feature_link.feature_ids:
        feature_link.put()
        logging.info(f'Updated indexed link {link.url}')
      else:
        # delete the link if it is not used by any feature
        feature_link.key.delete()
        logging.info(f'Delete indexed link {link.url}')


def _get_feature_links(feature_id: int) -> list[FeatureLinks]:
  """Return a list of FeatureLinks for a given feature id"""
  feature_links = FeatureLinks.query(
      FeatureLinks.feature_ids == feature_id).fetch(None)
  return feature_links if feature_links else []


def get_by_feature_id(feature_id: int) -> list[dict[str, Any]]:
  """Return a list of dicts of FeatureLinks for a given feature id
  The returned dicts only include the url, type, and information fields.
  This is used by the api to return json to the client.
  """
  feature_links = _get_feature_links(feature_id)
  return [link.to_dict(include=['url', 'type', 'information']) for link in feature_links]


def _index_feature_links(fe: FeatureEntry) -> None:
  """index the links in the given feature entry."""
  pass


def _batch_index_feature_links(fes: list[FeatureEntry]) -> None:
  """index the links in the given feature entries."""
  pass
