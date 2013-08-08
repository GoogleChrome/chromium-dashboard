#!/bin/bash

# A bootstrap for obtaining an OAuth2 access token for querying the BigStore
# REST API from AppEngine. Run this script before testing from the dev server.
# It is only necessary for local development.
#
# Note: the token needs to be acquired for an @google.com account.
#
# Author: Eric Bidelman <ericbidelman@chromium.org>

set -e

# The directory in which this script resides.
readonly BASEDIR=$(dirname $BASH_SOURCE)

# The filename for the OAuth2 token.  Should be within the app directory.
readonly OAUTH2_CREDENTIALS_FILENAME="$BASEDIR"'/oauth2.data'

# If deploying to production, delete the OAuth2 access token (if it exists).
# Otherwise, refresh the OAuth2 access token for fetching data from BigStore.
if [ "$1" == "deploy" ]; then
  if [ -a "$OAUTH2_CREDENTIALS_FILENAME" ]; then
    rm "$OAUTH2_CREDENTIALS_FILENAME"
  fi
else
  $BASEDIR/fetch_oauth_credentials.py --credentials_file="$OAUTH2_CREDENTIALS_FILENAME" \
                                      --client_secrets_file=client_secrets.json
fi
