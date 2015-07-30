#!/bin/bash
#
# Deploys the app to App Engine.
#
# Note: This script should be used in place of using appcfg.py update directly
# to update the application on App Engine.
#
# Copyright 2015 Eric Bidelman <ericbidelman@chromium.org>


# The directory in which this script resides.
readonly BASEDIR=$(dirname $BASH_SOURCE)

# vulcanize $BASEDIR/../static/elements/elements.html -o $BASEDIR/../static/elements/elements.vulcanized.html --config vulcanize_config.json

compass compile
grunt

$BASEDIR/oauthtoken.sh deploy
appcfg.py update --oauth2 $BASEDIR/../
