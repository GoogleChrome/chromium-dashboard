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

from internals import core_enums
from internals import core_models
from internals import search_fulltext


class SearchFulltextRegexTest(testing_config.CustomTestCase):

  def test_WORD_RE(self):
    """Our RE finds words of three letters or more."""
    expected = search_fulltext.WORD_RE.findall('')
    self.assertEqual([], expected)

    expected = search_fulltext.WORD_RE.findall(
        'four_score & 7 years ago, our 4fathers brought 4th '
        'on this contenent a    new nation')
    self.assertEqual(
        ['four_score', 'years', 'ago', 'our', '4fathers', 'brought',
         '4th', 'this', 'contenent', 'new', 'nation'],
        expected)


class SearchFulltextFunctionsTest(testing_config.CustomTestCase):

  def setUp(self):
    self.fe = core_models.FeatureEntry(
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
    expected = search_fulltext.get_strings(self.fe)
    self.assertEqual(
        ['creator@example.com',
         'updater@example.com',
         'owner1@example.com', 'owner2@example.com',
         'feature name',
         'sum',
         'Blink',  # A default value
         'flag_name'],
        expected)

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
    expected = search_fulltext.parse_words([
        'one, two, buckle my shoe',
        'three, four, close the door.'])
    self.assertEqual(
        set(['one', 'two', 'buckle', 'shoe',
             'three', 'four', 'close', 'door']),
        expected)

  def test_batch_index_features__empty(self):
    """We can cope with a no-op."""
    expected = search_fulltext.batch_index_features([], [])
    self.assertEqual([], expected)
