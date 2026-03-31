# Copyright 2026 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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
"""Pytest configuration file.

This file sets up isolated test environments when running tests in parallel
using pytest-xdist. For every parallel worker thread that pytest spawns, this
script starts a dedicated, in-memory Google Cloud Datastore emulator. This
prevents race conditions and data corruption between parallel tests.
"""

import os
import subprocess
import time

import pytest
import requests


def pytest_configure(config):
    """Pytest hook that runs exactly once per worker process before any tests
    start.

    If tests are being run in parallel (via pytest-xdist), this function will:
    1. Identify which worker process this is (e.g., gw0, gw1).
    2. Assign a unique port for its Datastore emulator.
    3. Override the environment variables so Google Cloud SDK uses this local port.
    4. Boot up the gcloud datastore emulator as a background process.
    5. Block until the emulator is fully responsive.
    """
    # PYTEST_XDIST_WORKER is set by the pytest-xdist plugin (e.g., "gw0", "gw1")
    worker_id = os.environ.get('PYTEST_XDIST_WORKER')

    if worker_id is not None:
        # Calculate a unique port for this worker based on its ID
        # Base port is 15606. gw0 -> 15607, gw1 -> 15608, etc.
        port = 15606 + int(worker_id.replace('gw', '')) + 1

        # Override Google Cloud environment variables to force all Datastore
        # traffic from this worker to its dedicated local emulator.
        os.environ['DATASTORE_EMULATOR_HOST'] = f'localhost:{port}'
        os.environ['DATASTORE_EMULATOR_HOST_PATH'] = (
            f'localhost:{port}/datastore'
        )
        os.environ['DATASTORE_HOST'] = f'http://localhost:{port}'

        # Command to start the in-memory datastore emulator
        cmd = [
            'gcloud',
            'beta',
            'emulators',
            'datastore',
            'start',
            '--project=cr-status-staging',
            f'--host-port=:{port}',
            '--no-store-on-disk',  # Ensures data never writes to your actual hard drive
            '--use-firestore-in-datastore-mode',
        ]

        # Start the emulator process in the background, suppressing its logs
        proc = subprocess.Popen(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # Store the process reference in the pytest config so we can kill it later
        config.worker_emulator_proc = proc

        # Poll the emulator until it returns a 200 OK, indicating it is ready to accept traffic
        for _ in range(30):
            try:
                r = requests.get(f'http://localhost:{port}/')
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.5)


def pytest_unconfigure(config):
    """Pytest hook that runs exactly once per worker process after all tests
    finish.

    This ensures that the Java Datastore emulator processes are safely
    terminated and don't remain running as orphaned background processes.
    """
    proc = getattr(config, 'worker_emulator_proc', None)
    if proc:
        proc.terminate()
        proc.wait()


@pytest.fixture(autouse=True)
def reset_datastore_emulator():
    """A pytest fixture that automatically runs BEFORE every single test
    function.

    This guarantees strict test isolation by wiping the Datastore emulator clean
    before a test executes. It prevents residual data from previous tests from
    causing false positives or failures.
    """
    worker_id = os.environ.get('PYTEST_XDIST_WORKER')

    if worker_id is not None:
        # We are running in parallel, wipe the worker-specific emulator
        port = 15606 + int(worker_id.replace('gw', '')) + 1
        try:
            requests.post(f'http://localhost:{port}/reset', timeout=2)
        except Exception:
            pass
    else:
        # We are running sequentially (single process mode), wipe the default emulator
        host = os.environ.get('DATASTORE_EMULATOR_HOST', 'localhost:15606')
        try:
            requests.post(f'http://{host}/reset', timeout=2)
        except Exception:
            pass
