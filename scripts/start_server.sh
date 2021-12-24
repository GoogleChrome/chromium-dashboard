#!/bin/bash
#
# Starts the dev server and services.
#
# Copyright 2017 Eric Bidelman <ericbidelman@chromium.org>

# The directory in which this script resides.
readonly BASEDIR=$(dirname $BASH_SOURCE)


dev_appserver.py -A cr-status --enable_console=1 \
  --support_datastore_emulator=1 --datastore_emulator_port=15606 \
  --env_var DATASTORE_EMULATOR_HOST='localhost:15606' \
  $BASEDIR/../dispatch.yaml \
  $BASEDIR/../notifier.yaml \
  $BASEDIR/../py2/app-py2.yaml \
  $BASEDIR/../app-py3.yaml

# Note: We don't create tasks in dev mode, so the app-py2 service is
# normally idle.  You can hit the URL http://localhost:8080/py2
# to see if the app-py2 service is responding at all.
