Chrome Platform Status
==================

[![Lighthouse score: 100/100](https://lighthouse-badge.appspot.com/?score=100&category=PWA)](https://github.com/ebidel/lighthouse-badge)

[chromestatus.com](http://chromestatus.com/)

### Get the code

    git clone https://github.com/GoogleChrome/chromium-dashboard

### Installation
1. Before you begin, make sure that you have a java JRE (version 8 or greater) installed. JRE is required to use the DataStore Emulator. 
1. Install global CLIs
    1. [Google App Engine SDK for Python](https://cloud.google.com/appengine/docs/standard/python/setting-up-environment). Make sure to select Python 2.7.
    1. pip, node, npm.
    1. Gulp `npm install --global gulp-cli`
1. Install npm dependencies `npm ci`
1. Install other dependencies `npm run deps` and `npm run dev-deps`

If you face any error during the installation process, the section **Notes** (later in this README.md) may help. 

##### Add env_vars.yaml

Create a file named `env_vars.yaml` in the root directory and fill it with:

```yaml
env_variables:
  DJANGO_SETTINGS_MODULE: 'settings'
  DJANGO_SECRET: 'this-is-a-secret'
  DATASTORE_EMULATOR_HOST: 'localhost:15606'
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
npm run start-emulator      # Start the emulator
npm run test                # Reset the datastore emulator and start testing
npm run stop-emulator       # Stop the emulator. You do not have to stop the emulator between consecutive tests
```

Note: featurelist is temporarily excluded because lit-analyzer throws `Maximum call stack size exceeded`.

There are some developing information in developer-documentation.md.


**Notes**

- If you get an error saying `No module named protobuf` or `No module named six` or `No module named enum` , try installing them locally with `pip install six enum34 protobuf`.

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

Each deployment also uploads the same code to a version named `rc` for "Release candidate".  This is the only version that you can test using Google Sign-In at `https://rc-dot-cr-status-staging.appspot.com`.

If manual testing on the staging server looks good, then repeat the same steps to deploy to prod:

    npm run deploy

Open the [Google Developer
Console for the production site](https://console.cloud.google.com/appengine/versions?project=cr-status)

The production site should only have versions that match versions on staging.

### LICENSE

Copyright (c) 2013-2016 Google Inc. All rights reserved.

Apache2 License.


[![Analytics](https://ga-beacon.appspot.com/UA-39048143-2/GoogleChrome/chromium-dashboard/README)](https://github.com/igrigorik/ga-beacon)
