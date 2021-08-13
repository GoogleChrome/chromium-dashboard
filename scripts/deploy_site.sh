#!/bin/bash
#
# Deploys the app to App Engine.
#
# Note: This script should be used in place of using appcfg.py update directly
# to update the application on App Engine.
#
# Copyright 2015 Eric Bidelman <ericbidelman@chromium.org>


deployVersion=$1
appName=${2:-cr-status}
usage="Usage: deploy.sh `date +%Y-%m-%d`"

if [ -z "$deployVersion" ]
then
  echo "App version not specified."
  echo $usage
  exit 0
fi

# The directory in which this script resides.
readonly BASEDIR=$(dirname $BASH_SOURCE)

gulp

$BASEDIR/oauthtoken.sh deploy
gcloud app deploy \
  --project $appName \
  --version $deployVersion \
  --no-promote \
  $BASEDIR/../app-py2.yaml $BASEDIR/../notifier.yaml \
  $BASEDIR/../app-py3.yaml  \
  $BASEDIR/../dispatch.yaml $BASEDIR/../cron.yaml

# TODO(jrobbins): Add app_py3.yaml when it has some contents.
