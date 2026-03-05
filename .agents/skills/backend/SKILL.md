---
name: backend
description: Guidance for working on the Flask-based backend, NDB Datastore, and OpenAPI integrations in chromium-dashboard.
---

# Backend Development Skill

This skill provides context and guidelines for developing the backend of the `chromium-dashboard` project.

## Core Technologies
- **Flask**: The primary web framework for request handling and template rendering.
- **Cloud NDB**: Used for interacting with Google Cloud Datastore.
- **OpenAPI 3.0**: Used for defining APIs and generating Python data models.

## Key Directories
- `api/`: Contains Flask request handlers for various API endpoints.
- `framework/`: Core infrastructure, including `basehandlers.py` and utility functions.
- `internals/`: Business logic, search filters, and data processing.
- `pages/`: Handlers for main application pages.
- `openapi/`: OpenAPI specification file (`api.yaml`).
- `gen/py/chromestatus_openapi/`: Auto-generated Python models from OpenAPI.

## Guidelines
- **API Development**: Prefer adding new APIs via OpenAPI in `openapi/api.yaml`. Use `npm run openapi-backend` to regenerate models.
- **Handlers**: Extend `basehandlers.py` classes for consistent permission checking and response handling.
- **Datastore**: Use NDB models defined in `internals/models.py`. Ensure queries are optimized and use proper indexing (see `index.yaml`).
- **Testing**: Python unit tests are located alongside the code (e.g., `*_test.py`). Run them using `npm test`.

## Common Tasks
- **Adding a Route**: Define the route in `main.py` and map it to a handler class in `api/` or `pages/`.
- **Modifying Schema**: Update `internals/models.py` and run a backfill script if necessary.
