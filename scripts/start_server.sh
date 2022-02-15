#!/bin/bash
#
# Starts the dev server and services.
#
# Copyright 2017 Eric Bidelman <ericbidelman@chromium.org>

export PYTHONPATH=cs-env/lib/python3.9/site-packages:$PYTHONPATH
export GOOGLE_CLOUD_PROJECT='cr-status-staging'
export SERVER_SOFTWARE='gunicorn'
export GAE_ENV='localdev'
export DJANGO_SETTINGS_MODULE='settings'
export DJANGO_SECRET='this-is-a-secret'
export DATASTORE_EMULATOR_HOST='localhost:15606'


gunicorn --bind :8080 --workers 4 main:app


# TODO(jrobbins): Consider switching back to dev_appserver when
# it no longer requires python2.
#
# The directory in which this script resides.
#readonly BASEDIR=$(dirname $BASH_SOURCE)
#
#dev_appserver.py -A cr-status --enable_console=1 \
#  --support_datastore_emulator=1 --datastore_emulator_port=15606 \
#  --env_var DATASTORE_EMULATOR_HOST='localhost:15606' \
#  $BASEDIR/../dispatch.yaml \
#  $BASEDIR/../notifier.yaml \
#  $BASEDIR/../dev-default.yaml \
#  $BASEDIR/../app-py3.yaml

# Note: When running locally, the default service is dev-default.yaml
# which is a py3 service which does nothing.  That avoids needing py2
# on the developer's workstation.
# On GAE, the default service is py2/app-py2.yaml which uses the GAE
# py2 runtime.
