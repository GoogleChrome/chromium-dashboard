#!/bin/bash
#
# Starts the dev server and services.
#
# Copyright 2017 Eric Bidelman <ericbidelman@chromium.org>

# The directory in which this script resides.
readonly BASEDIR=$(dirname $BASH_SOURCE)

dev_appserver.py -A cr-status \
  $BASEDIR/../app.yaml $BASEDIR/../notifier.yaml
