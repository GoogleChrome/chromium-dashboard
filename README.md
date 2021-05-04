Chrome Platform Status
==================

[![Lighthouse score: 100/100](https://lighthouse-badge.appspot.com/?score=100&category=PWA)](https://github.com/ebidel/lighthouse-badge)

[chromestatus.com](http://chromestatus.com/)

### Get the code

    git clone --recursive https://github.com/GoogleChrome/chromium-dashboard

### Installation

1. Install global CLIs
    1. [Google App Engine SDK for Python](https://developers.google.com/appengine/downloads#Google_App_Engine_SDK_for_Python).
    1. pip, node, npm.
    1. Gulp `npm install -g gulp`
1. Install npm dependencies `npm ci`
1. Install other dependencies `npm run deps` and `npm run dev-deps`

##### Add env_vars.yaml

Create a file named `env_vars.yaml` in the root directory and fill it with:

```yaml
env_variables:
  DJANGO_SETTINGS_MODULE: 'settings'
  DJANGO_SECRET: 'this-is-a-secret'
```

### Developing

To start the main server and the notifier backend, run:

```bash
npm start
```
Then visit `http://localhost:8080/`.

To start front end code watching (sass, js lint check, babel, minify files), run

```bash
npm run watch
```

To run lint & lit-analyzer:

```bash
npm run lint
```

To run unit tests:

```bash
npm run test
```

Note: featurelist is temporarily excluded because lit-analyzer throws `Maximum call stack size exceeded`.

There are some developing information in developer-documentation.md.


**Notes**

- If you get an error saying `No module named protobuf`, try installing it locally with `python -m pip install protobuf`.

- When installing the GAE SDK, make sure to get the version for python 2.7.  It is no longer the default version.

- When running `npm start` you may get an ImportError for jinja2.tests.  This was caused by an over-general line in skip_files.yaml.  Pulling the latest source code should resolve the problem.

#### Blink components

Chromestatus gets the list of Blink components from a separate [app running on Firebase](https://blinkcomponents-b48b5.firebaseapp.com/blinkcomponents). See [source](https://github.com/ebidel/blink-components).

#### Seed the blink component owners

Visit http://localhost:8080/admin/blink/populate_blink to see the list of Blink component owners.

#### Debugging / settings

[`settings.py`](https://github.com/GoogleChrome/chromium-dashboard/blob/master/settings.py) contains a list
of globals for debugging and running the site locally.

### Deploying

If you have uncommited local changes, the appengine version name will end with `-tainted`.
It is OK to test on staging with tainted versions, but everything should be committed
(and thus not tainted) before staging a version that can later be pushed to prod.

**Note** you need to have admin privileges on the `cr-status-staging` and `cr-status`
cloud projects to be able to deploy the site.

Run the npm target:

    npm run staging

Open the [Google Developer
Console for the staging site](https://console.cloud.google.com/appengine/versions?project=cr-status-staging)
and flip to the new version by selecting from the list and clicking *MIGRATE TRAFFIC*. Make sure to do this for both the 'default' service as well as for the 'notifier' service.

If manual testing on the staging server looks good, then repeat the same steps to deploy to prod:

    npm run deploy

Open the [Google Developer
Console for the production site](https://console.cloud.google.com/appengine/versions?project=cr-status)

The production site should only have versions that match versions on staging.

### LICENSE

Copyright (c) 2013-2016 Google Inc. All rights reserved.

Apache2 License.


[![Analytics](https://ga-beacon.appspot.com/UA-39048143-2/GoogleChrome/chromium-dashboard/README)](https://github.com/igrigorik/ga-beacon)
