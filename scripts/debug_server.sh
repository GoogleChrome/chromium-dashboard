#!/bin/bash
#
# Starts the dev server and services.
#
# Copyright 2017 Eric Bidelman <ericbidelman@chromium.org>

export PYTHONPATH=cs-env/lib/python3/site-packages:$PYTHONPATH
export GOOGLE_CLOUD_PROJECT='cr-status-staging'
export SERVER_SOFTWARE='gunicorn'
export GAE_ENV='localdev'
export DATASTORE_EMULATOR_HOST=${DATASTORE_EMULATOR_HOST:-'localhost:15606'}

# Using python3 directly has a chance of picking up the wrong environment.
cs-env/bin/python3 -m debugpy --listen 0.0.0.0:5678 main.py
