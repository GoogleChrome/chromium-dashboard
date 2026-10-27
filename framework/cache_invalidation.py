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

"""Batching of rediscache invalidations.

Model write hooks call `invalidate()` to say which cache keys and key
prefixes became stale. Inside a `batch()` (every web request runs inside one,
see `wsgi_middleware()`), invalidations are collected, de-duplicated, and
flushed once when the batch ends, after all of the request's writes. Outside
of a batch (e.g., unit tests that call handler methods directly, or scripts),
invalidations are flushed immediately.

Flushing never raises: failures are logged, and the cache TTL bounds any
resulting staleness.
"""

import contextlib
import contextvars
import dataclasses
import logging
import time
from collections.abc import Iterable, Iterator

from framework import rediscache

# Maximum number of keys passed to a single delete command.
_DELETE_BATCH_SIZE = 1000


@dataclasses.dataclass
class _PendingInvalidations:
    """Cache keys and key prefixes to delete when the batch ends."""

    keys: set[str] = dataclasses.field(default_factory=set)
    prefixes: set[str] = dataclasses.field(default_factory=set)


_pending: contextvars.ContextVar[_PendingInvalidations | None] = (
    contextvars.ContextVar('pending_cache_invalidations', default=None)
)


def invalidate(keys: Iterable[str] = (), prefixes: Iterable[str] = ()) -> None:
    """Delete cache keys and all keys under the given prefixes.

    Inside a batch, the deletion is deferred until the batch ends.
    """
    pending = _pending.get()
    if pending is None:
        _flush(set(keys), set(prefixes), log=False)
    else:
        pending.keys.update(keys)
        pending.prefixes.update(prefixes)


@contextlib.contextmanager
def batch() -> Iterator[None]:
    """Collect invalidations and flush them once when the block exits.

    Nested batches join the outermost batch, which does the flush. The flush
    also happens if the block raises, because some writes may have been
    committed before the error.
    """
    if _pending.get() is not None:
        yield
        return

    pending = _PendingInvalidations()
    token = _pending.set(pending)
    try:
        yield
    finally:
        _pending.reset(token)
        _flush(pending.keys, pending.prefixes, log=True)


def wsgi_middleware(wsgi_app):
    """Run each request inside a batch so that it flushes at most once."""

    def middleware(environ, start_response):
        with batch():
            return wsgi_app(environ, start_response)

    return middleware


def _flush(keys: set[str], prefixes: set[str], log: bool) -> None:
    """Delete the given keys and prefixes, logging instead of raising."""
    if not keys and not prefixes:
        return

    start = time.monotonic()
    prefix_keys_deleted = 0
    try:
        sorted_keys = sorted(keys)
        for i in range(0, len(sorted_keys), _DELETE_BATCH_SIZE):
            rediscache.delete_multi(sorted_keys[i : i + _DELETE_BATCH_SIZE])
        for prefix in sorted(prefixes):
            prefix_keys_deleted += rediscache.delete_keys_with_prefix(prefix)
    except Exception:
        logging.exception(
            'cache_invalidation: flush failed: keys=%d prefixes=%s',
            len(keys),
            sorted(prefixes),
        )
        return

    if log:
        logging.info(
            'cache_invalidation: keys=%d prefixes=%s prefix_keys_deleted=%d '
            'elapsed_ms=%d',
            len(keys),
            sorted(prefixes),
            prefix_keys_deleted,
            (time.monotonic() - start) * 1000,
        )
