#!/bin/bash
set -e

# Auto-Deploy Pull Request

# If this isn't a pull request, abort.
if [ "${TRAVIS_EVENT_TYPE}" != "pull_request" ]; then
  echo "This only runs on pull_request events. Event was $TRAVIS_EVENT_TYPE."
  exit
fi

# If there were build failures, abort
if [ "${TRAVIS_TEST_RESULT}" = "1" ]; then
  echo "Deploy aborted, there were build/test failures."
  exit
fi

./travis/install_google_cloud_sdk.sh

# Set the AppEngine version for staging
# VERSION=pr-$TRAVIS_PULL_REQUEST
VERSION=lighthouse-ci-staging

# Determine staging URL based on PR.
export LH_TEST_URL=https://$VERSION-dot-$GAE_APP_ID.appspot.com/features
echo "Pull Request: $TRAVIS_PULL_REQUEST will be staged at $LH_TEST_URL"

# Deploy to AppEngine
$HOME/google-cloud-sdk/bin/gcloud app deploy app.yaml -q --no-promote --version $VERSION

# Make sure an AppEngine instance has started.
curl $LH_TEST_URL
