#!/bin/bash
set -e

# Installs the Google Cloud SDK

# Decrypt the Service Account Key
openssl aes-256-cbc -K $encrypted_aee7e38c959c_key -iv $encrypted_aee7e38c959c_iv \
    -in gcloud-client-secret.json.enc -out gcloud-client-secret.json -d

# Download & install the Google Cloud SDK
curl https://sdk.cloud.google.com | bash

# Update any necessary components
$HOME/google-cloud-sdk/bin/gcloud components update -q
$HOME/google-cloud-sdk/bin/gcloud components install app-engine-python

# Set the AppEngine App ID to $GAE_APP_ID
$HOME/google-cloud-sdk/bin/gcloud config set project $GAE_APP_ID

# Authenticate to AppEngine using the service account
$HOME/google-cloud-sdk/bin/gcloud auth activate-service-account \
    --key-file gcloud-client-secret.json
