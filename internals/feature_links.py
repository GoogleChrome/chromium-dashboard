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

import datetime
import logging
from collections import Counter
from typing import Any, Optional
from urllib.parse import urlparse

from google.cloud import ndb  # type: ignore

from framework import cloud_tasks_helpers
from framework.basehandlers import FlaskHandler
from internals.core_models import FeatureEntry, ReviewResultProperty
from internals.link_helpers import (
  GECKO_REVIEW_URL_PATTERN,
  LINK_TYPE_GITHUB_ISSUE,
  TAG_REVIEW_URL_PATTERN,
  WEBKIT_REVIEW_URL_PATTERN,
  Link,
)

LINK_STALE_MINUTES = 30
CRON_JOB_LINK_STALE_DAYS = 8


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

      # Clear the denormalized fields that get filled from feature links; they'll get updated below
      # with their new values.
      if field == 'safari_views_link':
        fe.safari_views_link_result = None
      if field == 'ff_views_link':
        fe.ff_views_link_result = None
      if field == 'tag_review':
        fe.tag_review_resolution = None
      fe.put()

      old_val_urls = Link.extract_urls_from_value(old_val)
      new_val_urls = Link.extract_urls_from_value(new_val)
      urls_to_remove = set(old_val_urls) - set(new_val_urls)
      urls_to_add = set(new_val_urls) - set(old_val_urls)
      if urls_to_remove or urls_to_add:
        fe_values = fe.to_dict(exclude=[field]).values()
        all_urls = [
          url for value in fe_values for url in Link.extract_urls_from_value(value)
        ]
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
              logging.info(
                f'Indexed feature_link {feature_link.url} to {feature_link.key.integer_id()} for feature {fe.key.integer_id()}'
              )


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

  _denormalize_feature_link_into_entries(feature_link, [fe])
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


def _get_review_result_from_feature_link(
  feature_link: FeatureLinks, position_prefix: str
) -> Optional[str]:
  """Returns the external reviewer's views expressed in feature_link.

  Params:
    position_prefix: The lowercase prefix this organization uses for their opinion labels.
  """
  if feature_link.information is None:
    return None
  for label in feature_link.information.get('labels', []):
    if label.lower().startswith(position_prefix):
      return label[len(position_prefix) :]
  if feature_link.information.get('state', None) == 'closed':
    return ReviewResultProperty.CLOSED_WITHOUT_POSITION
  return None


def _put_if_changed(model: ndb.Model, field: str, new_val) -> None:
  old_val = getattr(model, field)
  if old_val != new_val:
    setattr(model, field, new_val)
    logging.info(
      'Denormalized %s=%s into %s %s', field, new_val, model.key.kind(), model.key.id()
    )
    model.put()


def _denormalize_feature_link_into_entries(
  feature_link: FeatureLinks, possible_entries: list[FeatureEntry] | None = None
) -> None:
  """Fills information from feature_link into relevant fields in the FeatureEntries it appears in.

  Params:
    possible_entries: If the caller knows which FeatureEntries might need updating, pass that list here.
  """
  if feature_link.type == LINK_TYPE_GITHUB_ISSUE:
    if possible_entries is None:
      possible_entries = ndb.get_multi(
        keys=[ndb.Key('FeatureEntry', id) for id in feature_link.feature_ids]
      )
    for fe in possible_entries:
      if fe is None:
        continue
      if (
        TAG_REVIEW_URL_PATTERN.search(feature_link.url)
        and fe.tag_review == feature_link.url
      ):
        _put_if_changed(
          fe,
          'tag_review_resolution',
          _get_review_result_from_feature_link(feature_link, 'resolution: '),
        )
      if (
        GECKO_REVIEW_URL_PATTERN.search(feature_link.url)
        and fe.ff_views_link == feature_link.url
      ):
        _put_if_changed(
          fe,
          'ff_views_link_result',
          _get_review_result_from_feature_link(feature_link, 'position: '),
        )
      if (
        WEBKIT_REVIEW_URL_PATTERN.search(feature_link.url)
        and fe.safari_views_link == feature_link.url
      ):
        _put_if_changed(
          fe,
          'safari_views_link_result',
          _get_review_result_from_feature_link(feature_link, 'position: '),
        )


def _get_feature_links(feature_ids: list[int]) -> list[FeatureLinks]:
  """Return a list of FeatureLinks for the given feature ids"""
  feature_links = FeatureLinks.query(
      FeatureLinks.feature_ids.IN(feature_ids)).fetch(None) if feature_ids else []
  return feature_links if feature_links else []


def get_by_feature_id(feature_id: int, update_stale_links: bool) -> tuple[list[dict], bool]:
  """Return a list of dicts of FeatureLinks for a given feature id
  The returned dicts only include the url, type, and information fields.
  This is used by the api to return json to the client.
  update_stale_links: if True, then trigger a background task to update the information of the links.
  """
  return get_by_feature_ids([feature_id], update_stale_links)


def get_by_feature_ids(
  feature_ids: list[int], update_stale_links: bool
) -> tuple[list[dict], bool]:
  """Return a list of dicts of FeatureLinks for the given feature ids
  The returned dicts only include the url, type, and information fields.
  This is used by the api to return json to the client.
  update_stale_links: if True, then trigger a background task to update the information of the links.
  """
  feature_links = _get_feature_links(feature_ids)
  stale_time = datetime.datetime.now(
      tz=datetime.timezone.utc) - datetime.timedelta(minutes=LINK_STALE_MINUTES)
  stale_time = stale_time.replace(tzinfo=None)
  stale_feature_links = [
      link for link in feature_links if link.updated < stale_time]
  has_stale_links = len(stale_feature_links) > 0

  if has_stale_links and update_stale_links:
    logging.info(
        f'Found {len(stale_feature_links)} stale links for feature_ids {feature_ids}, send links to cloud task')

    feature_link_ids = [link.key.id() for link in stale_feature_links]
    cloud_tasks_helpers.enqueue_task(
        '/tasks/update-feature-links', {
            'feature_link_ids': feature_link_ids,
            'should_notify_on_error': False
        })
  return [link.to_dict(include=['url', 'type', 'information', 'http_error_code']) for link in feature_links], has_stale_links


class FeatureLinksUpdateHandler(FlaskHandler):
  """This task handles update feature links information with the given ids."""

  IS_INTERNAL_HANDLER = True

  def process_post_data(self, **kwargs):
    self.require_task_header()

    logging.info('Starting indexing feature links')

    feature_link_ids = self.get_param('feature_link_ids')
    should_notify_on_error = self.get_bool_param('should_notify_on_error', False)

    _index_feature_links_by_ids(feature_link_ids, should_notify_on_error=should_notify_on_error)
    logging.info('Finished indexing feature links')
    return {'message': 'Done'}


def _index_feature_links_by_ids(
        feature_link_ids: list[Any], should_notify_on_error: bool) -> None:
  """index the links in the given feature links ids"""
  for feature_link_id in feature_link_ids:
    feature_link: FeatureLinks = FeatureLinks.get_by_id(feature_link_id)
    if feature_link:
      logging.info(f'processing {feature_link.url}')
      link = Link(feature_link.url)
      link.parse()
      if link.is_error:
        if not feature_link.is_error and should_notify_on_error:
          # TODO: if feature_link turns from no-error to error, notify users
          pass
        if link.http_error_code:
          feature_link.http_error_code = link.http_error_code
        feature_link.is_error = link.is_error
        logging.info(f'Update indexed link {feature_link_id} {feature_link.url} encountered error')
      else:
        # update the information if it is not an error
        feature_link.information = link.information
        feature_link.is_error = False
        feature_link.http_error_code = None
        logging.info(f'Update indexed link {feature_link_id} {feature_link.url} successfully')
        _denormalize_feature_link_into_entries(feature_link)

      feature_link.type = link.type
      feature_link.put()


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
      feature_links = _get_feature_links([fe.key.integer_id()])
      if len(feature_links) > 0:
        continue

    urls = _extract_feature_urls(fe)
    feature_links = []
    for url in urls:
      link = Link(url)
      if link.type:
        fl = _get_index_link(link, fe, should_parse_new_link=True)
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
  error_links = [link for link in links if link['is_error']]
  http_error_links = [link for link in links if link['http_error_code']]

  link_types_counter = Counter(item['type'] for item in links)
  uncovered_link_domains_counter = Counter(get_domain_with_scheme(item['url']) for item in uncovered_links)
  error_link_domains_counter = Counter(get_domain_with_scheme(item['url']) for item in error_links)

  link_types = [{'key': k, 'count': c} for (k, c) in link_types_counter.most_common(MAX_RESULTS)]
  uncovered_link_domains = [{'key': k, 'count': c} for (k, c) in uncovered_link_domains_counter.most_common(MAX_RESULTS)]
  error_link_domains = [{'key': k, 'count': c} for (k, c) in error_link_domains_counter.most_common(MAX_RESULTS)]

  return {
      "total_count": len(links),
      "covered_count": len(links) - len(uncovered_links),
      "uncovered_count": len(uncovered_links),
      "error_count": len(error_links),
      "http_error_count": len(http_error_links),
      "link_types": link_types,
      "uncovered_link_domains": uncovered_link_domains,
      "error_link_domains": error_link_domains
  }


def get_feature_links_samples(domain: str, type: str | None, is_error: bool | None):
  """retrieves a list of feature links based on the specified domain, type, and error status."""

  MAX_SAMPLES = 100
  filters = [
      FeatureLinks.url >= domain,
  ]
  if type:
    filters.append(FeatureLinks.type == type)
  if is_error:
    filters.append(FeatureLinks.is_error == is_error)
  feature_links = FeatureLinks.query(
      *filters
  ).fetch(MAX_SAMPLES)

  # filter out links that do not start with the specified domain and convert to dict
  feature_links = [
      fl.to_dict(include=['url', 'type', 'feature_ids', 'is_error', 'http_error_code'])
      for fl in feature_links if fl.url.startswith(domain)
  ]

  # flatten feature links like projection in get_feature_links_summary
  flattened_feature_links = []
  for feature_link in feature_links:
    for feature_id in feature_link['feature_ids']:
      flattened_feature_links.append({
          **feature_link,
          'feature_ids': feature_id
      })

  return flattened_feature_links


class UpdateAllFeatureLinksHandlers(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """
    retrieves feature links from a database, identifies which links need to be updated based on certain conditions,
    and enqueues tasks to update those links in batches.
    """

    self.require_cron_header()

    should_notify_on_error = self.get_bool_arg('should_notify_on_error', True)
    no_filter = self.get_bool_arg('no_filter', False)

    feature_links = FeatureLinks.query().fetch(
        projection=[
            FeatureLinks.url,
            FeatureLinks.type,
            FeatureLinks.is_error,
            FeatureLinks.http_error_code,
            FeatureLinks.updated,
        ]
    )

    ids_to_update = []

    if no_filter:
      # for backfill purposes
      ids_to_update = [fe.key.integer_id() for fe in feature_links]
    else:
      stale_time = datetime.datetime.now(
          tz=datetime.timezone.utc) - datetime.timedelta(days=CRON_JOB_LINK_STALE_DAYS)
      stale_time = stale_time.replace(tzinfo=None)
      for fe in feature_links:
        # if stale
        if fe.updated < stale_time:
          ids_to_update.append(fe.key.integer_id())
        # if error exists
        elif fe.is_error or fe.http_error_code:
          ids_to_update.append(fe.key.integer_id())
        # if type changed since last update
        elif fe.type != Link.get_type(fe.url):
          ids_to_update.append(fe.key.integer_id())

    BATCH_SIZE = 100
    batch_update_ids = [ids_to_update[i:i+BATCH_SIZE] for i in range(0, len(ids_to_update), BATCH_SIZE)]

    for batch in batch_update_ids:
      cloud_tasks_helpers.enqueue_task(
          '/tasks/update-feature-links',
          {
              'feature_link_ids': batch,
              'should_notify_on_error': should_notify_on_error
          }
      )

    msg = f'Started updating {len(ids_to_update)} Feature Links in {len(batch_update_ids)} batches'
    logging.info(msg)
    return msg
