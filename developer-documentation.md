# chromedash developer documentation

This doc covers some basic overview of the codebase to help developers navigate.

In summary, this web app is using Flask as the backend and uses Lit webcomponents in the front end.
It uses [Sign in with Google](https://developers.google.com/identity/gsi/web) for authentication.
**Google Cloud Datastore** is used as database.

## Back end

In the Backend,

- **Flask** is being used for:
  - All the request handlers (see `basehandlers.py` and all the code under `api/` and `pages/`).
  - HTML templates (see `FlaskHandler.render()` in `framework/basehandlers.py`).

HISTORY:-

- The app used to use a combination of Django plus Webapp2. However, now it uses Flask as mentioned above.
- The app used to use _DB Client Library_ for interacting with Google Cloud DataStore. It was later replaced by _NDB Client Library_. Now, it uses the _Cloud NDB Library_

## Front end

- Our client side is implemented in [Lit](https://lit.dev).
- It is largely a SPA (single-page application) with routing done via `page.js` (see [visionmedia/page.js: Micro client-side router inspired by the Express router](http://github.copm/visionmedia/page.js)), configured in `setUpRoutes` of `chromedash-app.js`.
- It communicates with the server via code in `cs-client.js`.
- We use [Shoelace widgets](https://shoelace.style).


### Main site page rendering

All the pages are rendered in a combination of Jinja2 template (`/templates`) and front-end components (`/client-src/elements`).

1. `/templates/base.html` and `/templates/base_embed.html` are the html skeleton.
1. Templates in `/templates` (extend the `_base.html` or `_embed_base.html`) are the Jinja2 templates for each page.
   - The folder organization and template file names matches the router. (See `template_path=os.path.join(path + '.html')` in `server.py`)
   - lit-element components, css, js files are all imported/included in those templates.
   - We pass backend variables to js like this: `const variableInJs = {{variable_in_template|safe}}`.
1. All Lit components are in `/client-src/elements`.
1. All JavaScript files are in `/client-src/js-src/` and processed by gulp, then output to `/static/js/` and get included in templates.
1. All CSS files are in `/client-src/sass/` and processed by gulp, then output to `/static/css/` and get included in templates.

### Adding an icon

Shoelace comes bundled with [Bootstrap Icons](https://icons.getbootstrap.com), but we prefer to use [Material Icons](https://fonts.google.com/icons?icon.set=Material+Icons) in most cases.

To add a new Bootstrap icon:
1. Copy it from node_modules/@shoelace-style/shoelace/dist/assets/icons to static/shoelace/assets/icons.
1. Reference it like `<sl-icon name="icon-name">`.

To add a new Material icon:
1. Download the 24pt SVG file from https://fonts.google.com/icons?icon.set=Material+Icons
1. Rename it to the icon name with underscores, and place it in static/shoelace/assets/material-icons.
1. Reference it like `<sl-icon library="material" name="icon_name">`.


## Creating a user with admin privileges

Creating or editing features normally requires a `@google.com` or `@chromium.org` account.
To work around this when running locally, you can make a temporary change to the file `framework/permissions.py` to
make function `can_admin_site()` return `True`.
Once you restart the server and log in using any account, you will be able create or edit features.

To avoid needing to make this temporary change more than once, you can sign in
and visit `/admin/users/new` to create a new registered account using the email
address of any Google account that you own, such as an `@gmail.com` account.

## Generating Diffs for sending emails to subscribers of a feature

- When someone edits a feature, everyone who have subscribed to that feature will receive a email stating what fields were edited, the old values and the new values.
- The body of this email (diffs) can be seen in the console logs. To see the logs, follow these steps:-
  1. Create a feature using one account.
  1. Now, signout and login with another account.
  1. Click on the star present in the feature box in the all features page.
  1. Now login again using the first account and edit a feature.
  1. On pressing submit after editing the feature, you will be able to see the diff in the console logs.

## Local Development

- When run locally, Datastore Emulator is used for storing all the entries. To reset local database, remove the local directory for storing data/config for the emulator. The default directory is `<USER_CONFIG_DIR>/emulators/datastore`. The value of `<USER_CONFIG_DIR>` can be found by running: `$ gcloud info --format='get(config.paths.global_config_dir)'` in the terminal. To learn more about using the Datastore Emulator CLI, execute `$ gcloud beta emulators datastore --help`.
- Executing `npm start` or `npm test` automatically starts the Datastore Emulator and shuts it down afterwards.
