#!/bin/bash
#
# Deploys the app to App Engine.
# 
# Note: This script should be used in place of using appcfg.py update directly
# to update the application on App Engine.
#
# Copyright 2013 Eric Bidelman <ericbidelman@chromium.org>


# The directory in which this script resides.
readonly BASEDIR=$(dirname $BASH_SOURCE)

$BASEDIR/oauthtoken.sh deploy
appcfg.py update $BASEDIR/../
