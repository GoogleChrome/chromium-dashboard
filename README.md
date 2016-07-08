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

I've had issues with Django errors just runnning `grunt serve` or using the `dev_appserver.py`. Download the [Google App Engine Python SDK launcher](https://cloud.google.com/appengine/downloads) (Mac) and use that. Open the launcher and run the app in the main repo directory.

**Notes**

- Locally, the /feature list pulls from prod (https://www.chromestatus.com/features.json). Opening one of the features will 404 because the entry is not actually in the local db. If you want to test local entries, [`templates/features.html`](https://github.com/GoogleChrome/chromium-dashboard/blob/master/templates/features.html#L138-L139) to pull locally and add some db entries by signing in to the app (bottom link). Make sure to check the "sign in as admin" box when doing so.

### Deploying

**Note** you need to have admin privileges on the `cr-status` cloud project to be
able to deploy the site.

First, update the version field in `app.yaml`. That will ensure the app deploys
to a versioned URL and helps for rolling back later. Then, run the helper script:

    ./scripts/deploy_site.sh

This will build the site and deploy it to GAE.

Lastly, open the [Google Developer Console](https://console.cloud.google.com/appengine/versions?project=cr-status&organizationId=433637338589&moduleId=default) and flip
to the new version.

### LICENSE

Copyright (c) 2013-2016 The Chromium Authors. All rights reserved.

[BSD License](http://src.chromium.org/viewvc/chrome/trunk/src/LICENSE)


[![Analytics](https://ga-beacon.appspot.com/UA-39048143-2/GoogleChrome/chromium-dashboard/README)](https://github.com/igrigorik/ga-beacon)
