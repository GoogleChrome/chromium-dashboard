# Copyright 2026 Google LLC
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

"""Unit tests for the cache_invalidation module."""

from unittest import mock

import flask

import testing_config  # Must be imported before the module under test.
from framework import basehandlers, cache_invalidation, rediscache


class CacheInvalidationTest(testing_config.CustomTestCase):
    """Tests for immediate and batched cache invalidation."""

    def setUp(self):
        """Populate some cache entries."""
        rediscache.set('entry|1', 'one')
        rediscache.set('entry|2', 'two')
        rediscache.set('search|q1', 'results 1')
        rediscache.set('search|q2', 'results 2')
        rediscache.set('other|1', 'other')

    def tearDown(self):
        """Clear the cache."""
        rediscache.flushall()

    def test_invalidate__immediate_outside_batch(self):
        """Outside of a batch, keys and prefixes are deleted right away."""
        cache_invalidation.invalidate(keys=['entry|1'], prefixes=['search'])

        self.assertIsNone(rediscache.get('entry|1'))
        self.assertIsNone(rediscache.get('search|q1'))
        self.assertIsNone(rediscache.get('search|q2'))
        self.assertEqual('two', rediscache.get('entry|2'))
        self.assertEqual('other', rediscache.get('other|1'))

    def test_batch__deferred_until_exit(self):
        """Inside a batch, nothing is deleted until the batch exits."""
        with cache_invalidation.batch():
            cache_invalidation.invalidate(keys=['entry|1'], prefixes=['search'])
            self.assertEqual('one', rediscache.get('entry|1'))
            self.assertEqual('results 1', rediscache.get('search|q1'))

        self.assertIsNone(rediscache.get('entry|1'))
        self.assertIsNone(rediscache.get('search|q1'))
        self.assertEqual('two', rediscache.get('entry|2'))
        self.assertEqual('other', rediscache.get('other|1'))

    @mock.patch('framework.rediscache.delete_keys_with_prefix')
    @mock.patch('framework.rediscache.delete_multi')
    def test_batch__deduplicates(self, mock_delete_multi, mock_dkwp):
        """Many invalidations in a batch result in one flush per prefix."""
        mock_dkwp.return_value = 0
        with cache_invalidation.batch():
            for _ in range(10):
                cache_invalidation.invalidate(
                    keys=['entry|1', 'entry|2'], prefixes=['search']
                )
            cache_invalidation.invalidate(prefixes=['search'])

        mock_dkwp.assert_called_once_with('search')
        mock_delete_multi.assert_called_once_with(['entry|1', 'entry|2'])

    @mock.patch('framework.rediscache.delete_keys_with_prefix')
    def test_batch__nested_batches_flush_once(self, mock_dkwp):
        """A nested batch joins the outer batch, which does the flush."""
        mock_dkwp.return_value = 0
        with cache_invalidation.batch():
            with cache_invalidation.batch():
                cache_invalidation.invalidate(prefixes=['search'])
            mock_dkwp.assert_not_called()
            cache_invalidation.invalidate(prefixes=['search'])

        mock_dkwp.assert_called_once_with('search')

    @mock.patch('framework.rediscache.delete_keys_with_prefix')
    def test_batch__empty_batch_does_nothing(self, mock_dkwp):
        """A batch with no invalidations does not touch Redis."""
        with cache_invalidation.batch():
            pass
        mock_dkwp.assert_not_called()

    def test_batch__flushes_when_body_raises(self):
        """Invalidations are flushed even if the block raises."""
        with self.assertRaises(ValueError):
            with cache_invalidation.batch():
                cache_invalidation.invalidate(keys=['entry|1'])
                raise ValueError('boom')

        self.assertIsNone(rediscache.get('entry|1'))
        # A later invalidation is no longer batched.
        cache_invalidation.invalidate(keys=['entry|2'])
        self.assertIsNone(rediscache.get('entry|2'))

    @mock.patch('logging.exception')
    @mock.patch('framework.rediscache.delete_keys_with_prefix')
    def test_flush_failure_is_logged_not_raised(self, mock_dkwp, mock_log):
        """A Redis error during the flush is logged instead of raised."""
        mock_dkwp.side_effect = ConnectionError('redis is down')

        with cache_invalidation.batch():
            cache_invalidation.invalidate(prefixes=['search'])
        cache_invalidation.invalidate(prefixes=['search'])

        self.assertEqual(2, mock_log.call_count)

    @mock.patch('framework.rediscache.delete_multi')
    def test_flush__large_key_sets_are_chunked(self, mock_delete_multi):
        """Very large sets of keys are deleted in bounded chunks."""
        keys = [f'entry|{i}' for i in range(2500)]
        with cache_invalidation.batch():
            cache_invalidation.invalidate(keys=keys)

        self.assertEqual(3, mock_delete_multi.call_count)
        deleted = [
            k for c in mock_delete_multi.call_args_list for k in c.args[0]
        ]
        self.assertCountEqual(keys, deleted)


class WsgiMiddlewareTest(testing_config.CustomTestCase):
    """Tests that each request flushes its invalidations once, at the end."""

    def setUp(self):
        """Create an app whose route invalidates the same caches 3 times."""
        self.app = flask.Flask(__name__)

        @self.app.route('/write', methods=['POST'])
        def write():
            for _ in range(3):
                cache_invalidation.invalidate(
                    keys=['entry|1'], prefixes=['search']
                )
            # Nothing is flushed until the request is done.
            return {'entry_cached': rediscache.get('entry|1') is not None}

        self.app.wsgi_app = cache_invalidation.wsgi_middleware(
            self.app.wsgi_app
        )
        rediscache.set('entry|1', 'one')
        rediscache.set('search|q1', 'results 1')

    def tearDown(self):
        """Clear the cache."""
        rediscache.flushall()

    def test_request_flushes_once_after_handler(self):
        """A request's invalidations are flushed once, after the handler."""
        with mock.patch(
            'framework.rediscache.delete_keys_with_prefix',
            wraps=rediscache.delete_keys_with_prefix,
        ) as spy:
            response = self.app.test_client().post('/write')

        self.assertEqual(200, response.status_code)
        # During the handler, the entry had not been deleted yet.
        self.assertEqual({'entry_cached': True}, response.get_json())
        # The flush happened once, after the handler finished.
        spy.assert_called_once_with('search')
        self.assertIsNone(rediscache.get('entry|1'))
        self.assertIsNone(rediscache.get('search|q1'))

    def test_flask_application_installs_middleware(self):
        """Every app built by FlaskApplication batches invalidations."""
        with mock.patch(
            'framework.cache_invalidation.wsgi_middleware',
            wraps=cache_invalidation.wsgi_middleware,
        ) as spy:
            basehandlers.FlaskApplication(__name__, [])
        spy.assert_called_once()
