#!/bin/bash
#
# Starts the dev server and services.
#
# Copyright 2017 Eric Bidelman <ericbidelman@chromium.org>

# The directory in which this script resides.
readonly BASEDIR=$(dirname $BASH_SOURCE)

dev_appserver.py -A cr-status --enable_console=1 \
  --support_datastore_emulator=1 --datastore_emulator_port=15606 \
  $BASEDIR/../app.yaml $BASEDIR/../notifier.yaml
