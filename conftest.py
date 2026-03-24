import os
import subprocess
import time
import pytest
import requests

def pytest_configure(config):
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id is not None:
        port = 15606 + int(worker_id.replace("gw", "")) + 1
        os.environ['DATASTORE_EMULATOR_HOST'] = f'localhost:{port}'
        os.environ['DATASTORE_EMULATOR_HOST_PATH'] = f'localhost:{port}/datastore'
        os.environ['DATASTORE_HOST'] = f'http://localhost:{port}'
        
        cmd = [
            "gcloud", "beta", "emulators", "datastore", "start",
            "--project=cr-status-staging",
            f"--host-port=:{port}",
            "--no-store-on-disk",
            "--use-firestore-in-datastore-mode"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        config.worker_emulator_proc = proc
        
        for _ in range(30):
            try:
                r = requests.get(f'http://localhost:{port}/')
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.5)

def pytest_unconfigure(config):
    proc = getattr(config, 'worker_emulator_proc', None)
    if proc:
        proc.terminate()
        proc.wait()

@pytest.fixture(autouse=True)
def reset_datastore_emulator():
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id is not None:
        port = 15606 + int(worker_id.replace("gw", "")) + 1
        try:
            requests.post(f'http://localhost:{port}/reset', timeout=2)
        except Exception:
            pass
    else:
        # For single process mode
        host = os.environ.get("DATASTORE_EMULATOR_HOST", "localhost:15606")
        try:
            requests.post(f'http://{host}/reset', timeout=2)
        except Exception:
            pass
