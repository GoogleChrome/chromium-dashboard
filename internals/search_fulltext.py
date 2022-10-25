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

from google.cloud import ndb  # type: ignore

from framework.basehandlers import FlaskHandler
from internals.core_models import FeatureEntry


# We consider all words that have three or more letters.
# That includes underscores (_) and digits.
WORD_RE = re.compile(r'\w\w\w+')

# We ignore stop words because they return too many results to be useful.
STOP_WORDS = frozenset((
    'the and has was but was will are were with can this that have than then '
    'for not now some '
    'new add adds '
    'http https www monorail com net org web bug bugs blink '
    'gmail google chromium chrome github ').split())


class FeatureWords(ndb.Model):
  """A bag of words that occur in the fulltext of the feature."""

  feature_id = ndb.IntegerProperty(required=True)
  words = ndb.StringProperty(repeated=True)


def get_strings(fe):
  """Return a list of separate string values in the given feature entry."""
  strings = []
  strings.append(fe.creator_email)
  strings.append(fe.updater_email)
  strings.extend(fe.owner_emails)
  strings.extend(fe.editor_emails)
  strings.extend(fe.cc_emails)

  strings.append(fe.name)
  strings.append(fe.summary)
  # TODO: category
  strings.extend(fe.blink_components)
  strings.extend(fe.search_tags)
  strings.append(fe.feature_notes)

  strings.append(fe.bug_url)
  strings.append(fe.launch_bug_url)

  # TODO: impl_status_Chrome
  strings.append(fe.flag_name)
  strings.append(fe.ongoing_constraints)

  strings.append(fe.motivation)
  strings.append(fe.devtrial_instructions)
  strings.append(fe.activation_risks)
  strings.append(fe.measurement)

  strings.append(fe.initial_public_proposal_url)
  strings.extend(fe.explainer_links)
  # TODO: standard_maturity
  strings.append(fe.spec_link)
  strings.extend(fe.spec_mentor_emails)
  strings.append(fe.interop_compat_risks)
  strings.append(fe.all_platforms_descr)
  strings.append(fe.tag_review)
  # TODO: tag_review_status
  strings.append(fe.non_oss_deps)
  strings.append(fe.anticipated_spec_changes)

  # TODO: ff_views
  # TODO: safari_views
  # TODO: web_dev_views
  strings.append(fe.ff_views_link)
  strings.append(fe.safari_views_link)
  strings.append(fe.web_dev_views_link)
  strings.append(fe.ff_views_notes)
  strings.append(fe.safari_views_notes)
  strings.append(fe.web_dev_views_notes)
  strings.append(fe.other_views_notes)

  strings.append(fe.security_risks)
  # TODO: security_review_status
  # TODO: privacy_review_status

  strings.append(fe.ergonomics_risks)
  strings.append(fe.wpt_descr)
  strings.append(fe.webview_risks)

  strings.extend(fe.devrel_emails)
  strings.append(fe.debuggability)
  strings.extend(fe.doc_links)
  strings.extend(fe.sample_links)

  # Skip missing fields.
  non_empty_strings = [s for s in strings if s]
  return non_empty_strings


def parse_words(strings):
  """Return a set of all searchable words in the given feature entry."""
  words = set()
  for s in strings:
    # eliminate apostrophes
    s = s.lower().replace("'", "")
    words.update(WORD_RE.findall(s))

  words.difference_update(STOP_WORDS)
  return words


def batch_index_features(fe_list, existing_fw_list):
  """Process FeatureEntries to make word bags, but don't save to NDB."""
  existing_fw_dict = {
      fw.feature_id: fw
      for fw in existing_fw_list}
  updated_fw_list = []

  for fe in fe_list:
    feature_id = fe.key.integer_id()
    feature_words = (existing_fw_dict.get(feature_id) or
                     FeatureWords(feature_id=feature_id))

    words = sorted(parse_words(get_strings(fe)))
    logging.info('feature %r has words %r', feature_id, words)
    feature_words.words = words
    updated_fw_list.append(feature_words)

  return updated_fw_list


def index_feature(fe):
  """Create or update a word bag for the given feature entry."""
  feature_id = fe.key.integer_id()
  query = FeatureWords.query(FeatureWords.feature_id == feature_id)
  existing_fw_list = query.fetch(None)
  updated_fw_list = batch_index_features([fe], existing_fw_list)
  updated_fw_list[0].put()


def search_fulltext(textterm):
  """Return IDs of features that have some word(s) from phrase."""
  search_words = parse_words([textterm])
  if not search_words:
    logging.warn('Cannot process fulltext term: %r', textterm)
    return []  # user is searching for stop words.

  logging.info('looking for words: %r', search_words)
  query = FeatureWords.query(FeatureWords.words.IN(search_words))
  feature_projections = query.fetch(projection=['feature_id'])
  feature_ids = [proj.feature_id for proj in feature_projections]
  return feature_ids


# TODO(jrobbins): Implement phrase search as post-procesing.  I.e.,
# searching for phrase "build useful stuff" would first be handled as
# a search for any combination of those words.  Then, after all search
# conditions have been applied, a post-processing step would load all
# potentially matching features and keep only the ones that contain
# the entire phrase in one string.

# TODO(jrobbins): Likewise, searching for a word or phrase in a
# specific field of a feature entry can be done with post-processing.


class ReindexAllFeatures(FlaskHandler):

  def get_template_data(self, **kwargs):
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

  def get_template_data(self, **kwargs):
    """Count occurances of all words and return the 100 most common."""
    self.require_cron_header()

    all_feature_entries = FeatureEntry.query().fetch()
    all_feature_words = []
    updated_fw_list = batch_index_features(
        all_feature_entries, all_feature_words)
    # Don't actually store them, we just want to report stats.

    counts = collections.Counter()
    for fw in updated_fw_list:
      counts.update(fw.words)

    logging.info('100 most common words')
    for word, count in counts.most_common(100):
      logging.info('%6d: %s', count, word)

    return 'OK'
