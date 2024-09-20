# -*- coding: utf-8 -*-
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

import collections
import logging
import re
from typing import Any, Optional

from google.cloud import ndb  # type: ignore

from framework.basehandlers import FlaskHandler
from internals.core_models import FeatureEntry
from internals.feature_helpers import (
    get_future_results,
    get_entries_by_id_async)


# We consider all words that have three or more letters.
# That includes underscores (_) and digits.
WORD_RE = re.compile(r'\w\w\w+')

# We ignore stop words because they return too many results to be useful.
STOP_WORDS = frozenset((
    'the and has have was will are were with but can this that than then '
    'for not now '
    'http https www com net org web bugs blink '
    'gmail google chromium github ').split())


class FeatureWords(ndb.Model):
  """A bag of words that occur in the fulltext of the feature."""

  feature_id = ndb.IntegerProperty(required=True)
  words = ndb.StringProperty(repeated=True)


def _get_strings_dict(fe: FeatureEntry) -> dict[str, list[str|None]]:
  return {
      'creator': [fe.creator_email],
      'updater': [fe.updater_email],
      'owner': fe.owner_emails,
      'editor': fe.editor_emails,
      'cc': fe.cc_emails,

      'name': [fe.name],
      'summary': [fe.summary],
      # TODO: category
      'browsers.chrome.blink_component': fe.blink_components,
      'tag': fe.search_tags,
      'feature_notes': [fe.feature_notes],

      'browsers.chrome.bug': [fe.bug_url],
      'launch_bug_url': [fe.launch_bug_url],
      'shipping_year': [str(fe.shipping_year or '')],

      # TODO: impl_status_Chrome
      'browsers.chrome.flag_name': [fe.flag_name],
      'browsers.chrome.finch_name': [fe.finch_name],
      'browsers.chrome.non_finch_justification': [fe.non_finch_justification],
      'ongoing_constraints': [fe.ongoing_constraints],

      'motivation': [fe.motivation],
      'devtrial_instructions': [fe.devtrial_instructions],
      'activation_risks': [fe.activation_risks],
      'measurement': [fe.measurement],

      'initial_public_proposal_url': [fe.initial_public_proposal_url],
      'explainer': fe.explainer_links,
      # TODO: standard_maturity
      'standards.spec': [fe.spec_link],
      'spec_mentors': fe.spec_mentor_emails,
      'interop_compat_risks': [fe.interop_compat_risks],
      'all_platforms_descr': [fe.all_platforms_descr],
      'tag_review.url': [fe.tag_review],
      # TODO: tag_review_status
      'non_oss_deps': [fe.non_oss_deps],
      'standards.anticipated_spec_changes': [fe.anticipated_spec_changes],

      # TODO: ff_views
      # TODO: safari_views
      # TODO: web_dev_views
      'browsers.ff.view.url': [fe.ff_views_link],
      'browsers.safari.view.url': [fe.safari_views_link],
      'browsers.webdev.view.url': [fe.web_dev_views_link],
      'browsers.ff.view.notes': [fe.ff_views_notes],
      'browsers.safari.view.notes': [fe.safari_views_notes],
      'browsers.webdev.view.notes': [fe.web_dev_views_notes],
      'other_views_notes': [fe.other_views_notes],

      'security_risks': [fe.security_risks],
      # TODO: security_review_status
      # TODO: privacy_review_status

      'ergonomics_risks': [fe.ergonomics_risks],
      'wpt_descr': [fe.wpt_descr],
      'webview_risks': [fe.webview_risks],

      'devrel_emails': fe.devrel_emails,
      'debuggability': [fe.debuggability],
      'resources.doc': fe.doc_links,
      'resources.sample': fe.sample_links,
      }


def get_strings(fe: FeatureEntry, field_name: str|None = None) -> list[str]:
  """Return a list of separate string values in the given feature entry."""
  strings_dict = _get_strings_dict(fe)
  if field_name and field_name in strings_dict:
    strings = strings_dict[field_name]
  else:
    strings = [s for s_list in strings_dict.values() for s in s_list]

  # Skip missing fields.
  non_empty_strings = [s for s in strings if s]
  return non_empty_strings


FULLTEXT_FIELDS = frozenset(
    _get_strings_dict(FeatureEntry()).keys())


def parse_words(strings : list[str]) -> tuple[set[str], int]:
  """Return set of all searchable words in the given strings and the count."""
  word_set = set()
  count = 0
  for s in strings:
    # eliminate apostrophes
    s = s.lower().replace("'", "")
    words = WORD_RE.findall(s)
    count += len(words)
    word_set.update(words)

  word_set.difference_update(STOP_WORDS)
  return word_set, count


def batch_index_features(
    fe_list: list[FeatureEntry], existing_fw_list: list[FeatureWords]
    ) -> list[FeatureWords]:
  """Process FeatureEntries to make word bags, but don't save to NDB."""
  existing_fw_dict = {
      fw.feature_id: fw
      for fw in existing_fw_list}
  updated_fw_list = []

  for fe in fe_list:
    feature_id = fe.key.integer_id()
    feature_words = (existing_fw_dict.get(feature_id) or
                     FeatureWords(feature_id=feature_id))

    word_set, unused_num_words = parse_words(get_strings(fe))
    words = sorted(word_set)
    logging.info('feature %r has words %r', feature_id, words)
    feature_words.words = words
    updated_fw_list.append(feature_words)

  return updated_fw_list


def index_feature(fe: FeatureEntry) -> None:
  """Create or update a word bag for the given feature entry."""
  feature_id = fe.key.integer_id()
  query = FeatureWords.query(FeatureWords.feature_id == feature_id)
  existing_fw_list = query.fetch(None)
  updated_fw_list = batch_index_features([fe], existing_fw_list)
  updated_fw_list[0].put()


def canonicalize_string(s: str) -> str:
  """Return a string of lowercase words separated by single spaces."""
  lower_s = s.lower().replace("'", "")
  words = WORD_RE.findall(lower_s)
  canonicalized = ' '.join(w for w in words if w not in STOP_WORDS)
  return ' ' + canonicalized + ' '  # Avoids matching partial words.


def post_process_phrase(
    phrase: str, feature_ids: list[int],
    field_name: str|None = None) -> list[int]:
  """Fetch the given features and check if they really have the phrase.
  if field_name is specified, check only within that field."""
  features = get_future_results(get_entries_by_id_async(feature_ids))
  canon_phrase = canonicalize_string(phrase)
  result = []
  for fe in features:
    feature_strings = get_strings(fe, field_name=field_name)
    has_phrase = any(canon_phrase in canonicalize_string(fs)
                     for fs in feature_strings)
    if has_phrase:
      result.append(fe.key.integer_id())
  return result


def search_fulltext(
    textterm: str, field_name: str|None = None) -> Optional[list[int]]:
  """Return IDs of features that contain word(s) from textterm.
  if field_name is specified, check only within that field."""
  word_set, num_words = parse_words([textterm])
  if not word_set:
    logging.warning('Cannot process fulltext term: %r', textterm)
    return None  # user is searching for stop words.

  logging.info('looking for words: %r', word_set)
  query = FeatureWords.query()
  for search_word in word_set:
    query = query.filter(FeatureWords.words == search_word)
  feature_projections = query.fetch(projection=['feature_id'])
  feature_ids = [proj.feature_id for proj in feature_projections]
  if num_words > 1 or field_name:
    return post_process_phrase(textterm, feature_ids, field_name=field_name)
  else:
    return feature_ids


class ReindexAllFeatures(FlaskHandler):

  def get_template_data(self, **kwargs) -> str:
    """Updates the fulltext index for all features."""
    self.require_cron_header()

    all_feature_entries = FeatureEntry.query().fetch()
    all_feature_words = FeatureWords.query().fetch()
    updated_fw_list = batch_index_features(
        all_feature_entries, all_feature_words)
    ndb.put_multi(updated_fw_list)
    msg = f'Added or updated {len(updated_fw_list)} FeatureWords'
    logging.info(msg)
    return msg


class FindStopWords(FlaskHandler):

  JSONIFY = True

  def get_template_data(self, **kwargs) -> list[tuple[str, int]]:
    """Count occurances of all words and return the 100 most common."""
    self.require_cron_header()

    all_feature_entries = FeatureEntry.query().fetch()
    all_feature_words: list[FeatureWords] = []
    updated_fw_list = batch_index_features(
        all_feature_entries, all_feature_words)
    # Don't actually store them, we just want to report stats.

    counts: collections.Counter = collections.Counter()
    for fw in updated_fw_list:
      counts.update(fw.words)

    top_words = counts.most_common(100)
    logging.info('100 most common words')
    for word, count in top_words:
      logging.info('%6d: %s', count, word)

    return top_words
