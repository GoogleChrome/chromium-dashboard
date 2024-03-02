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

import testing_config  # Must be imported before the module under test.

from unittest import mock

import flask

from internals import core_enums
from internals import core_models
from internals import search_fulltext
import settings


test_app = flask.Flask(__name__,
  template_folder=settings.get_flask_template_path())


class SearchFulltextRegexTest(testing_config.CustomTestCase):

  def test_WORD_RE(self):
    """Our RE finds words of three letters or more."""
    actual = search_fulltext.WORD_RE.findall('')
    self.assertEqual([], actual)

    actual = search_fulltext.WORD_RE.findall(
        'four_score & 7 years ago, our 4fathers brought 4th '
        'on this contenent a    new nation')
    self.assertEqual(
        ['four_score', 'years', 'ago', 'our', '4fathers', 'brought',
         '4th', 'this', 'contenent', 'new', 'nation'],
        actual)


class SearchFulltextFunctionsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.fe = core_models.FeatureEntry(
        id=123,
        creator_email='creator@example.com',
        updater_email='updater@example.com',
        owner_emails=['owner1@example.com', 'owner2@example.com'],
        name='feature name',
        summary='sum',
        category=core_enums.NETWORKING,
        flag_name='flag_name',
        sample_links=[])

  def test_get_strings(self):
    """We can extract a list of strings from a FeatureEntry."""
    actual = search_fulltext.get_strings(self.fe)
    self.assertEqual(
        ['creator@example.com',
         'updater@example.com',
         'owner1@example.com', 'owner2@example.com',
         'feature name',
         'sum',
         'Blink',  # A default value
         'flag_name'],
        actual)

  def test_parse_words__empty(self):
    """We can cope with empty strings and lists."""
    self.assertEqual(
        set(), search_fulltext.parse_words([]))
    self.assertEqual(
        set(), search_fulltext.parse_words(['']))
    self.assertEqual(
        set(), search_fulltext.parse_words(['', '']))

  def test_parse_words__normal(self):
    """We parse strings into sets of words, without stopwords."""
    actual = search_fulltext.parse_words([
        'one, two, buckle my shoe',
        'three, four, close the door.'])
    self.assertEqual(
        set(['one', 'two', 'buckle', 'shoe',
             'three', 'four', 'close', 'door']),
        actual)

  def test_batch_index_features__empty(self):
    """We can cope with a no-op."""
    actual = search_fulltext.batch_index_features([], [])
    self.assertEqual([], actual)

  def test_batch_index_features__first_time(self):
    """When indexing a FeatureEntry for the first time, create FW."""
    actual = search_fulltext.batch_index_features([self.fe], [])
    self.assertEqual(1, len(actual))
    self.assertEqual(123, actual[0].feature_id)
    self.assertCountEqual(
        ['creator', 'example', 'updater', 'owner1', 'owner2',
         'feature', 'name', 'sum', 'flag_name'],
        actual[0].words)

  def test_batch_index_features__update_words(self):
    """When reindexing a FeatureEntry, FW is updated."""
    fw = search_fulltext.FeatureWords(feature_id=123, words=['old'])
    actual = search_fulltext.batch_index_features([self.fe], [fw])
    self.assertEqual(1, len(actual))
    self.assertEqual(fw, actual[0])
    self.assertCountEqual(
        ['creator', 'example', 'updater', 'owner1', 'owner2',
         'feature', 'name', 'sum', 'flag_name'],
        actual[0].words)

  # TODO(jrobbins): Unit test for index_feature.

  # TODO(jrobbins): Unit test for search_fulltext.

  # TODO(jrobbins): Unit test for ReindexAllFeatures.


class FindStopWordsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.fe_1 = core_models.FeatureEntry(
        creator_email='creator@example.com',
        updater_email='updater@example.com',
        owner_emails=['owner1@example.com', 'owner2@example.com'],
        name='feature name',
        summary='sum',
        category=core_enums.NETWORKING,
        flag_name='flag_name',
        sample_links=[])
    self.fe_1.put()

    self.fe_2 = core_models.FeatureEntry(
        creator_email='someone@example.com',
        updater_email='other@example.com',
        owner_emails=['someone@example.com'],
        name='awesome',
        summary='sum',
        category=core_enums.NETWORKING)
    self.fe_2.put()

    self.handler = search_fulltext.FindStopWords()
    self.request_path = '/admin/find_stop_words'

  def tearDown(self):
    self.fe_1.key.delete()
    self.fe_2.key.delete()

  def test_get_template_date(self):
    with test_app.test_request_context(self.request_path):
      actual = self.handler.get_template_data()

    expected = [
        ('example', 2),  # Two features use these words
        ('sum', 2),
        ('awesome', 1), # Only one feature uses each of these words
        ('creator', 1),
        ('feature', 1),
        ('flag_name', 1),
        ('name', 1),
        ('other', 1),
        ('owner1', 1),
        ('owner2', 1),
        ('someone', 1),
        ('updater', 1),
        ]
    # We don't care about the exact order of the ones that have the same count.
    self.assertCountEqual(expected, actual)
