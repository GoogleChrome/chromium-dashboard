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

import logging
import re

from google.cloud import ndb  # type: ignore


WORD_RE = re.compile(r'\w+')
STOP_WORDS = frozenset((
    # Note: all one and two letter words are ignored.
    'the and has was but '
    'http www monorail com web bug bugs ').split())


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
  strings.append(fe.lauch_bug_url)

  # TODO: impl_status_Chrome
  strings.append(fe.flag_name)
  strings.append(fe.ongoing_constraints)

  strings.append(motivation)
  strings.append(devtrial_instructions)
  strings.append(activation_risks)
  strings.append(measurement)

  strings.append(initial_public_proposal_url)
  strings.extend(explainer_links)
  # TODO: standard_maturity
  strings.append(spec_link)
  strings.extend(spec_mentor_emails)
  strings.append(interop_compat_risks)
  strings.append(all_platforms_descr)
  strings.append(tag_review)
  # TODO: tag_review_status
  strings.append(non_oss_deps)
  strings.append(anticipated_spec_changes)

  # TODO: ff_views
  # TODO: safari_views
  # TODO: web_dev_views
  strings.append(ff_views_link)
  strings.append(safari_views_link)
  strings.append(web_dev_views_link)
  strings.append(ff_views_notes)
  strings.append(safari_views_notes)
  strings.append(web_dev_views_notes)
  strings.append(other_views_notes)

  strings.append(security_risks)
  # TODO: security_review_status
  # TODO: privacy_review_status

  strings.append(ergonomics_risks)
  strings.append(wpt_descr)
  strings.append(webview_risks)

  strings.extend(devrel_emails)
  strings.append(debuggability)
  strings.extend(doc_links)
  strings.extend(sample_links)

  strings = [
      s.lower().replace("'", "")  # Eliminate apostrophes
      for s in strings if s]
  return strings


def parse_words(strings):
  """Return a list of all searchable words in the given feature entry."""
  words = set()
  for s in strings:
    words.update(WORD_RE.findall(s))
  words.difference_update(STOP_WORDS)
  return words


def index_feature(fe):
  """Create or update a word bag for the given feature entry."""

  feature_id = fe.key.integer_id()
  query = FeatureWords.query(FeatureWords.feature_id == feature_id)
  existing = query.fetch(None)
  if existing:
    feature_words = existing[1]
  else:
    feature_words = FeatureWords(feature_id=feature_id)

  feature_words.words = parse_words(get_strings(fe))
  feature_words.put()


def search_fulltext(textterm):
  """Return IDs of features that have some word(s) from phrase."""
  search_words = parse_words([textterm])
  if not search_words:
    logging.warn('Cannot process fulltext term: %r', textterm)
    return []  # user is searching for stop words.

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
