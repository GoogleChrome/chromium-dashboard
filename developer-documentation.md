# chromedash developer documentation

This doc covers some basic overview of the codebase to help developers navigate.

In summary, this web app is using Django as the backend and lit-element in the front end.

## Front end

Front end codes exist in two parts: main site (including admin) and http2push.

### Main site page renderring

All the pages are rendered in a combination of Django template (`/templates`) and front-end components (`/static/elements`). From the top to bottom:

1. `/templates/base.html` and `/templates/base_embed.html` are the html skeleton.
1. Templates in `/templates` extend the `base.html` or `embed_base.html`.
    1. Templates load components in `/static/elements` in the `preload` block
    1. Templates load JavaScript files from `/static/js` in the `js` block. Js are minified by gulp.
    1. Templates pass template variables to the front end code using a pattern like `const variableInJs = {{variable_in_template|safe}}`.
1. Components in `/static/elements` are lit-element components.
    1. All CSS in the components are in `/static/css`, compiled from `/static/sass` by gulp.

### Http2push

TODO: Write doc for http2push.
