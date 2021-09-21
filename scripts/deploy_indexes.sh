#!/bin/bash
#
# Deploys the datastore indexes to App Engine.
#
# Note: This script should be used in place of using appcfg.py update directly
# to update the application on App Engine.


appName=${1:-cr-status}
usage="Usage: deploy_indexes.sh cr-status-staging"

# The directory in which this script resides.
readonly BASEDIR=$(dirname $BASH_SOURCE)

gcloud app deploy \
  --project $appName \
  $BASEDIR/../index.yaml
