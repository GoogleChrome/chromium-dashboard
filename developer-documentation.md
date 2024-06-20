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
1. All Lit components are in `/client-src/elements`, and other Javascript files are in `/client-src/js-src/`.
1. JavaScript is processed and code-split by Rollup, then output to `/static/dist/` and included in templates.
2. All `*-css.js` files used in client-side components are in `/client-src/css/`.  The remaining css files still being included in templates are in `/static/css/`.

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

## Adding a new API

This section outlines the steps to consider when adding a new API.

Note: For all new APIs, please consider using [OpenAPI](https://www.openapis.org/).
With OpenAPI, developers can write a specification for their API and have code
generated for them on both the frontend and backend. This helps remove the
burden of manually writing data models and data encoding and decoding for both sides.
There is a tool installed as a devDependency called
[openapi-generator-cli](https://github.com/OpenAPITools/openapi-generator-cli)
to do the generation of the code.

The specification follows OpenAPI version 3 and is located at [openapi/api.yaml](./openapi/api.yaml).

Below are steps to help guide a developer along with a relatable example that follows the same steps.

### Step 0: Additional Tools To Help

If using Visual Studio Code, install the following extensions. (These are pre-installed if using the devcontainer)
- [OpenAPI (Swagger) Editor](https://marketplace.visualstudio.com/items?itemName=42Crunch.vscode-openapi)

### Step 1: Add the path to openapi/api.yaml

*Before completing this step, read the [Paths and Operations](https://swagger.io/docs/specification/paths-and-operations/) and [Describing Parameters](https://swagger.io/docs/specification/describing-parameters/) OpenAPI docs*

- Under paths, add the path. You'll add operations named after HTTP methods under this.

<details>
  <summary>Example (click to expand)</summary>

  #### openapi/api.yaml
  ```yaml
  paths:
    /features/{feature_id}:
      ...
  ```
</details>

### Step 2: Add the operations

Operations = HTTP verbs. (e.g. GET, POST, PUT, etc)

- Add the operation(s) under the path.
- Ensure each operation has a `summary`, `description` and `operationId`
- If your path has path parameters, describe the parameters now too.
  - Mark required parameters with `required: true`.

<details>
  <summary>Example (click to expand)</summary>

  #### openapi/api.yaml
  ```yaml
  paths:
    ...
    /features/{feature_id}:
      get:
        summary: Get a feature by ID.
        description: |
          Get a feature by ID. More details about this here.
          Also, can do more comments
        operationId: getFeatureById
        parameters:
          - name: feature_id
            in: path
            description: Feature ID
            required: true
            schema:
              type: integer
      post:
        summary: Update a feature by ID.
        description: |
          Update a feature with the given ID.
          More details about this here.
        operationId: updateFeatureById
        parameters:
          - name: feature_id
            in: path
            description: Feature ID
            required: true
            schema:
              type: integer
  ```
</details>


### Step 3: Describe the request body

*Before completing this step, read the [Describing Request Body](https://swagger.io/docs/specification/describing-request-body/) OpenAPI doc*

*Skip this step if there is no request body*

- Inside the operation (`post` in this example), add a `requestBody.content.application/json.schema` object.
- Use a JSON Schema to define the request body.
- You can re-use parts or all of the schema by writing `$ref: '#/components/schemas/WellNamedObject'`
  and defining the `WellNamedObject` under the top-level `components.schemas` object.

<details>
  <summary>Example (click to expand)</summary>

  #### openapi/api.yaml
  ```yaml
  paths:
    ...
    /features/{feature_id}:
      post:
        summary: Update a feature by ID.
        description: |
          Update a feature with the given ID.
          More details about this here.
        operationId: updateFeatureById
        parameters:
          - name: feature_id
            in: path
            description: Feature ID
            required: true
            schema:
              type: integer
        requestBody:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Feature'
  components:
    schemas:
      Feature:
        description: A feature
        type: object
        properties:
          id:
            type: integer
          name:
            type: string
          live:
            type: boolean
            description: Some optional field
        required:
          - id
          - name
  ```
</details>

*For this example, only needed to describe a request body for the `post` operation.*

### Step 4: Describe the Responses

*Before completing this step, read the [Describing Responses](https://swagger.io/docs/specification/describing-request-body/) OpenAPI doc*

*Skip this step if there is no response body*

- Add the appropriate response code(s)
  - Don't worry about describing global errors like unauthorized calls right now.
- For each response code, describe the response object. As with the request body, you can refer to
  schemas defined in the `components.schemas` top-level object with `$ref:
  '#/components/schemas/WellNamedObject'`.

<details>
  <summary>Example (click to expand)</summary>

  #### openapi/api.yaml
  ```yaml
  paths:
    ...
    /features/{feature_id}:
      post:
        summary: Update a feature by ID.
        description: |
          Update a feature with the given ID.
          More details about this here.
        operationId: updateFeatureById
        parameters:
          - name: feature_id
            in: path
            description: Feature ID
            required: true
            schema:
              type: integer
        requestBody:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Feature'
        responses:
          '200':
            description: An updated feature
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Feature'
  components:
    schemas:
      Feature:
        description: A feature
        type: object
        ...
  ```
</details>

### Step 5: Generate the Code

Validate that the linked schema objects are valid. There should be zero errors and zero warnings:
- `npm run openapi-validate`

Generate the code:
- `npm run openapi`


### Step 6: Incorporate Into Backend

Currently, the repository is configured to use the generated Python data models for the backend. *Once all routes are generated by OpenAPI, it would be wise to revisit using the controllers as well*

- Open `main.py`
- Locate the `api_routes` variable.
- Add a route.
  - In this example, it would be `Route(f'{API_BASE}/features/<int:feature_id>', features_api.FeaturesAPI)`.
- In the handler, the generated model classes can be imported from `chromestatus_openapi.models`.
- Since we do not use the controllers, you will need to return a dictionary of the model class. Then, Flask can convert it appropriately to json. Each generated class has a `to_dict()` method to accomplish this.

### Step 7: Incorporate Into Frontend

The frontend use @lit-labs/context to pass the client around. The benefits of it can be seen [here](https://lit.dev/docs/data/context/) and the advertised use cases [here](https://lit.dev/docs/data/context/#example-use-cases).

Your element needs to use a context consumer to retrieve the client that is provided by `chromedash-app`. Once you have the client, you can make an API call like normal.

```js
import {ContextConsumer} from '@lit-labs/context';
import {chromestatusOpenApiContext} from '../contexts/openapi-context';
export class SomeElement extends LitElement {
  // Nice to have type hinting so that the IDE can auto complete the client and its functions.
  /** @type {ContextConsumer<import("../contexts/openapi-context").chromestatusOpenApiContext>} */
  _clientConsumer;

  constructor() {
    super();
    this._clientConsumer = new ContextConsumer(this, chromestatusOpenApiContext, undefined, true);
  }

  fetchData() {
    // Important to call .value to get the client from the context.
    this.clientConsumer.value.getFeature();
  }
  // other element stuff
}
```

## Miscellaneous

### Feature Links

Feature links provide users with easy access to additional information about URLs in the feature, without the need to navigate away from the site.

You can view all existing feature links and their associated statistics on [admin page](https://chromestatus.com/admin/feature_links).

#### How to add a new type of feature link (or updating an existing one)

1. Modify `internals/link_helpers.py` and `internals/link_helpers_test.py` to include support for parsing the new type of feature link.
2. Update `client-src/elements/feature-link.js` to render the new type of feature link.
3. Wait for the next cron job (which runs every Tuesday) to update the corresponding feature links, or trigger the job immediately by running `/cron/update_all_feature_links`

#### How to backfill feature links to the database

Feature links are automatically updated when a feature is created or edited. However, if you’ve performed a database cleanup, you can use a script to backfill the feature links.

1. Run `/scripts/backfill_feature_links` to backfill the feature links without extracting information into the database. After running the script, you can verify the results by visiting [admin page](https://chromestatus.com/admin/feature_links).
2. Run `/cron/update_all_feature_links?no_filter=true` to update all existing feature links with latest information.
