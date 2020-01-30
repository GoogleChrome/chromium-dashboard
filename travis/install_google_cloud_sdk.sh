#!/bin/bash
set -e

# Note: We now install and update the Google Cloud SDK in .travis.yml.
# The rest of this file does configuraton and authorization steps.

# Decrypt the Service Account Key
openssl aes-256-cbc -K $encrypted_aee7e38c959c_key -iv $encrypted_aee7e38c959c_iv \
    -in gcloud-client-secret.json.enc -out gcloud-client-secret.json -d

# Set the AppEngine App ID to $GAE_APP_ID
$HOME/google-cloud-sdk/bin/gcloud config set project $GAE_APP_ID

# Authenticate to AppEngine using the service account
$HOME/google-cloud-sdk/bin/gcloud auth activate-service-account \
    --key-file gcloud-client-secret.json
