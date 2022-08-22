# chromedash developer documentation

This doc covers some basic overview of the codebase to help developers navigate.

In summary, this web app is using a combination of Django & Flask as the backend and uses Lit webcomponents in the front end.
It uses [Sign in with Google](https://developers.google.com/identity/gsi/web) for authentication.
**Google Cloud Datastore** is used as database.

## Back end

In the Backend,
* **Django** is used just for HTML templates and forms (see `FlaskHandler.render()` in `Framework/basehandlers.py` and `pages/guideforms.py`).
* **Flask** is being used for all the request handlers (see `basehandlers.py` and all the code under `api/` and `pages/`).

HISTORY:-
* The app used to use a combination of Django plus Webapp2. However, now it uses Django plus Flask as mentioned above.
* The app used to use *DB Client Library* for interacting with Google Cloud DataStore. It was later replaced by *NDB Client Library*. Now, it uses the *Cloud NDB Library*

## Front end

Front end codes exist in two parts: main site (including admin) and http2push.

### Main site page renderring

All the pages are rendered in a combination of Django template (`/templates`) and front-end components (`/static/elements`).

1. `/templates/base.html` and `/templates/base_embed.html` are the html skeleton.
1. Templates in `/templates` (extend the `_base.html` or `_embed_base.html`) are the Django templates for each page.
    - The folder organization and template file names matches the router. (See `template_path=os.path.join(path + '.html')` in `server.py`)
    - lit-element components, css, js files are all imported/included in those templates.
    - We pass backend variables to js like this: `const variableInJs = {{variable_in_template|safe}}`.
1. All Lit components are in `/static/elements`.
1. All JavaScript files are in `/static/js-src/` and processed by gulp, then output to '/static/js/' and get included in templates.
1. All CSS files are in `/static/sass/` and processed by gulp, then output to `/static/css/` and get included in templates.


## Creating a user with admin privileges

Creating or editing features normally requires a `@google.com` or `@chromium.org` account.
To work around this when running locally, you can make a temporary change to the file `framework/permissions.py` to
make function `can_admin_site()` return `True`.
Once you restart the server and log in using any account, you will be able create or edit features.

To avoid needing to make this temporary change more than once, you can sign in
and visit `/admin/users/new` to create a new registered account using the email
address of any Google account that you own, such as an `@gmail.com` account.


## Generating Diffs for sending emails to subscribers of a feature
* When someone edits a feature, everyone who have subscribed to that feature will receive a email stating what fields were edited, the old values and the new values.
* The body of this email (diffs) can be seen in the console logs. To see the logs, follow these steps:-
  1. Create a feature using one account.
  1. Now, signout and login with another account.
  1. Click on the star present in the feature box in the all features page.
  1. Now login again using the first account and edit a feature.
  1. On pressing submit after editing the feature, you will be able to see the diff in the console logs.

## Local Development
* When run locally, Datastore Emulator is used for storing all the entries.
* Executing `npm start` or `npm test` automatically starts the Datastore Emulator and shuts it down afterwards.
