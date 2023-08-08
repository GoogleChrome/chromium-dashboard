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
import datetime
from framework import cloud_tasks_helpers
from framework import basehandlers
from typing import Any
from urllib.parse import urlparse
from internals.core_models import FeatureEntry
from internals.link_helpers import Link
from collections import Counter

from google.cloud import ndb  # type: ignore

LINK_STALE_MINUTES = 30


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
  is_error = ndb.BooleanProperty(default=False)
  http_error_code = ndb.IntegerProperty()


def update_feature_links(fe: FeatureEntry, changed_fields: list[tuple[str, Any, Any]]) -> None:
  """Update the links in the given feature entry."""
  for field, old_val, new_val in changed_fields:
    if new_val != old_val:
      if old_val is None and not bool(new_val):
        continue
      old_val_urls = Link.extract_urls_from_value(old_val)
      new_val_urls = Link.extract_urls_from_value(new_val)
      urls_to_remove = set(old_val_urls) - set(new_val_urls)
      urls_to_add = set(new_val_urls) - set(old_val_urls)
      fe_values = fe.to_dict(exclude=[field]).values()
      all_urls = [url for value in fe_values for url in Link.extract_urls_from_value(value)]
      for url in urls_to_remove:
        if url not in all_urls:
          # if the url is not in any other field in this feature, then remove it from the index
          link = Link(url)
          _remove_link(link, fe)
      for url in urls_to_add:
        link = Link(url)
        if link.type:
          feature_link = _get_index_link(link, fe, should_parse_new_link=True)
          if feature_link:
            feature_link.put()
            logging.info(f'Indexed feature_link {feature_link.url} to {feature_link.key.integer_id()} for feature {fe.key.integer_id()}')

def _get_index_link(link: Link, fe: FeatureEntry, should_parse_new_link: bool = False) -> FeatureLinks | None:
  """
  indexes a given link for a specific feature by creating or updating a `FeatureLinks` object.
  Returns the `FeatureLinks` object or None.
  """

  feature_id = fe.key.integer_id()
  feature_links = FeatureLinks.query(FeatureLinks.url == link.url).fetch(None)
  feature_link: FeatureLinks = feature_links[0] if feature_links else None
  if hasattr(feature_link, 'feature_ids'):
    if feature_id not in feature_link.feature_ids:
      feature_link.feature_ids.append(feature_id)
      feature_link.type = link.type
  else:
    if should_parse_new_link:
      link.parse()
      if link.is_error:
        return None
    feature_link = FeatureLinks(
        feature_ids=[feature_id],
        type=link.type,
        url=link.url,
        information=link.information,
        is_error=link.is_error,
        http_error_code=link.http_error_code
    )

  return feature_link


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


def get_by_feature_id(feature_id: int, update_stale_links: bool) -> tuple[list[dict], bool]:
  """Return a list of dicts of FeatureLinks for a given feature id
  The returned dicts only include the url, type, and information fields.
  This is used by the api to return json to the client.
  update_stale_links: if True, then trigger a background task to update the information of the links.
  """
  feature_links = _get_feature_links(feature_id)
  stale_time = datetime.datetime.now(
      tz=datetime.timezone.utc) - datetime.timedelta(minutes=LINK_STALE_MINUTES)
  stale_time = stale_time.replace(tzinfo=None)
  stale_feature_links = [
      link for link in feature_links if link.updated < stale_time]
  has_stale_links = len(stale_feature_links) > 0

  if has_stale_links and update_stale_links:
    logging.info(
        f'Found {len(stale_feature_links)} stale links for feature_id {feature_id}, send links to cloud task')

    feature_link_ids = [link.key.id() for link in stale_feature_links]
    cloud_tasks_helpers.enqueue_task(
        '/tasks/update-feature-links', {
            'feature_link_ids': feature_link_ids
        })
  return [link.to_dict(include=['url', 'type', 'information', 'http_error_code']) for link in feature_links], has_stale_links


class FeatureLinksUpdateHandler(basehandlers.FlaskHandler):
  """This task handles update feature links information with the given ids."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self, **kwargs):
    self.require_task_header()

    logging.info('Starting indexing feature links')

    feature_link_ids = self.get_param('feature_link_ids')

    _index_feature_links_by_ids(feature_link_ids)
    logging.info('Finished indexing feature links')
    return {'message': 'Done'}


def _index_feature_links_by_ids(feature_link_ids: list[Any]) -> None:
  """index the links in the given feature links ids"""
  for feature_link_id in feature_link_ids:
    feature_link: FeatureLinks = FeatureLinks.get_by_id(feature_link_id)
    if feature_link:
      link = Link(feature_link.url)
      link.parse()
      if link.is_error:
        feature_link.is_error = link.is_error
      else:
        # only update the information if it is not an error
        feature_link.information = link.information

      if link.http_error_code:
        feature_link.http_error_code = link.http_error_code
      feature_link.type = link.type
      feature_link.put()

    logging.info(f'Update information for indexed link {link.url}')


def _extract_feature_urls(fe: FeatureEntry) -> list[str]:
  fe_values = fe.to_dict().values()
  all_urls = [url for value in fe_values for url in Link.extract_urls_from_value(value)]
  return list(set(all_urls))


def batch_index_feature_entries(fes: list[FeatureEntry], skip_existing: bool) -> int:
  """
  The function `batch_index_feature_entries` takes a list of `FeatureEntry` objects, generates feature
  links for each entry, and stores them in batches in the database, skipping existing entries if
  specified.

  :param fes: fes is a list of FeatureEntry
  :param skip_existing: A boolean value indicating whether to skip feature entries that already have
  existing feature links
  """

  link_count = 0

  for fe in fes:
    if skip_existing:
      feature_links = _get_feature_links(fe.key.integer_id())
      if len(feature_links) > 0:
        continue

    urls = _extract_feature_urls(fe)
    feature_links = []
    for url in urls:
      link = Link(url)
      if link.type:
        fl = _get_index_link(link, fe, should_parse_new_link=False)
        if fl:
          feature_links.append(fl)

    ndb.put_multi(feature_links)
    link_count += len(feature_links)
    logging.info(f'Feature {fe.key.integer_id()} indexed {len(feature_links)} urls')

  return link_count


def get_domain_with_scheme(url):
  try:
    parse_result = urlparse(url)
    scheme = parse_result.scheme
    host = parse_result.netloc
  except ValueError as e:
    return 'Invalid: ' + url[:30]
  return f"{scheme}://{host}"


def get_feature_links_summary():
  """
  The function `get_feature_links_summary` retrieves feature links from a database, groups them by
  type and uncovered domains, and returns a summary of the counts and types of links.
  """
  MAX_RESULTS = 100

  feature_links = FeatureLinks.query().fetch(
      projection=[
          FeatureLinks.feature_ids,
          FeatureLinks.url,
          FeatureLinks.type,
          FeatureLinks.is_error,
          FeatureLinks.http_error_code,
      ]
  )
  links = [item.to_dict() for item in feature_links]
  uncovered_links = [link for link in links if link['type'] == 'web']

  link_types_counter = Counter(item['type'] for item in links)
  uncovered_link_domains_counter = Counter(get_domain_with_scheme(item['url']) for item in uncovered_links)

  link_types = [{'key': k, 'count': c} for (k, c) in link_types_counter.most_common(MAX_RESULTS)]
  uncovered_link_domains = [{'key': k, 'count': c} for (k, c) in uncovered_link_domains_counter.most_common(MAX_RESULTS)]

  return {
      "total_count": len(links),
      "covered_count": len(links) - len(uncovered_links),
      "uncovered_count": len(uncovered_links),
      "link_types": link_types,
      "uncovered_link_domains": uncovered_link_domains,
  }
