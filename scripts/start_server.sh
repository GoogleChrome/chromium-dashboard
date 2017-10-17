#!/bin/bash
#
# Starts the dev server and services.
#
# Copyright 2017 Eric Bidelman <ericbidelman@chromium.org>

# The directory in which this script resides.
readonly BASEDIR=$(dirname $BASH_SOURCE)
readonly FIREBASE_SERVER_KEY=`cat .fcm_server_key`

dev_appserver.py -A cr-status \
  $BASEDIR/../app.yaml $BASEDIR/../notifier.yaml
