Chrome Platform Status
==================

[chromestatus.com](http://chromestatus.com/)

### Get the code

    git clone --recursive https://github.com/GoogleChrome/chromium-dashboard

### Installation

First, install the [Google App Engine SDK for Python](https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python).

Then run:

    npm install

This will also pull down bower_components and run `grunt` to build the site.

### Run the local test server

Start the local test server in the root project directory using the Google App
Engine Python SDK:

    dev_appserver.py .

### LICENSE

Copyright (c) 2013-2015 The Chromium Authors. All rights reserved.

[BSD License](http://src.chromium.org/viewvc/chrome/trunk/src/LICENSE)


[![Analytics](https://ga-beacon.appspot.com/UA-39048143-2/GoogleChrome/chromium-dashboard/README)](https://github.com/igrigorik/ga-beacon)
