Chrome Platform Status
==================

[chromestatus.com](http://chromestatus.com/)

### Get the code

    git clone --recursive https://github.com/GoogleChrome/chromium-dashboard

### Installation

First, install the [Google App Engine SDK for Python](https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python).

You'll also need pip, node, and npm. Next, install `bower` and the deps:

    npm install -g bower
    npm install
    pip install -t lib -r requirements.txt

This will also pull down bower_components and run `gulp` to build the site.

### Developing

Note: I've had issues with Django errors just running `grunt serve` or using the `dev_appserver.py` but others haven't.

Download the [Google App Engine Python SDK launcher](https://cloud.google.com/appengine/downloads) (Mac) and use that. Open the launcher and run the app in the main repo directory.

Locally, the `/feature` list pulls from prod (https://www.chromestatus.com/features.json). Opening one of the features will 404 because the entry is not actually in the local db. If you want to test local entries, modify [`templates/features.html`](https://github.com/GoogleChrome/chromium-dashboard/blob/0b3e3eb444f1e6b6751140f9524a2f60cdc2ca5d/templates/features.html#L181-L182) to pull locally and add some db entries by signing in to the app (bottom link). Make sure to check the "sign in as admin" box when doing so. Note that you can also simply go to `http://127.0.0.1:8080/` instead of `localhost` to pull locally.

#### Seed the blink component owners

Visit http://localhost:8080/admin/blink/populate_blink to see the list of Blink component owners

#### Debugging / settings

[`settings.py`](https://github.com/GoogleChrome/chromium-dashboard/blob/master/settings.py) contains a list
of globals for debugging and running the site locally.

`VULCANIZE` - `False` will run the site without vulcanizing the Polymer elements.

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

Copyright (c) 2013-2016 Google Inc. All rights reserved.

Apache2 License.


[![Analytics](https://ga-beacon.appspot.com/UA-39048143-2/GoogleChrome/chromium-dashboard/README)](https://github.com/igrigorik/ga-beacon)
