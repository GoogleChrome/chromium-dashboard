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
  $BASEDIR/../app-py2.yaml $BASEDIR/../notifier.yaml \
  $BASEDIR/../app-py3.yaml

# TODO(jrobbins): Add app-py3.yaml when it has some contents.  At some point in
# the future when we cannot run the app-py2 service locally, tasks for
# outbound-email would simply queue up forever.  However, we don't even create
# those tasks in dev mode.
