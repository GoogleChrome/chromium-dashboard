# chromedash developer documentation

This doc covers some basic overview of the codebase to help developers navigate.

In summary, this web app is using Django as the backend and lit-element in the front end.

## Front end

Front end codes exist in two parts: main site (including admin) and http2push.

### Main site page renderring

All the pages are rendered in a combination of Django template (`/templates`) and front-end components (`/static/elements`).

1. `/templates/base.html` and `/templates/base_embed.html` are the html skeleton.
1. Templates in `/templates` (extend the `base.html` or `embed_base.html`) are the Django templates for each page.
    - lit-element components, css, js files are all imported/included in those templates.
    - We pass backend variables to js like this: `const variableInJs = {{variable_in_template|safe}}`.
1. All lit-element components are in `/static/elements`.
1. All JavaScript files are in `/static/js-src/` and processed by gulp, then output to '/static/js/' and get included in templates.
1. All CSS files are in `/static/sass/` and processed by gulp, them output to `/static/css/` and get included in templates.
1. A service worker is created by gulp too. Output in `/static/dist/service-worker.js`.
