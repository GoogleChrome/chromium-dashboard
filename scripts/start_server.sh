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
  $BASEDIR/../dev-default.yaml \
  $BASEDIR/../app-py3.yaml

# Note: When running locally, the default service is dev-default.yaml
# which is a py3 service which does nothing.  That avoids needing py2
# on the developer's workstation.
# On GAE, the default service is py2/app-py2.yaml which uses the GAE
# py2 runtime.
