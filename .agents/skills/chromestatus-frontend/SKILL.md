---
name: chromestatus-frontend
description: Guidance for working on the Lit-based frontend, Shoelace widgets, and client-side routing in chromium-dashboard.
---

# Frontend Development Skill

This skill provides context and guidelines for developing the frontend of the `chromium-dashboard` project.

## Core Technologies
- **Lit**: The primary library for building web components.
- **Shoelace**: A collection of high-quality UI widgets used throughout the application.
- **page.js**: A micro client-side router for SPA navigation.
- **Rollup**: Used for bundling and code-splitting JavaScript.

## Key Directories
- `client-src/elements/`: Contains Lit web components.
- `client-src/js-src/`: General JavaScript source files, including `cs-client.js`.
- `client-src/css/`: CSS files and Lit style modules.
- `static/dist/`: Output directory for bundled assets.
- `templates/`: Jinja2 templates for the initial page load skeleton.

## Guidelines
- **Component Development**: Create new components in `client-src/elements/`. Follow the naming convention `chromedash-*.js`.
- **Icons**: Prefer Material Icons. If using Bootstrap icons via Shoelace, ensure they are copied to `static/shoelace/assets/icons`.
- **API Interaction**: Use the client wrapper in `cs-client.js` or the OpenAPI context consumer for making server requests.
- **Styling**: Use Lit's `css` tagged templates for component styles. Leverage variables from the design system where possible.
- **Legacy Code**: Do not add new code or components to the legacy `pages/` directory on the backend, even if it contains old templates. All newer frontend logic should reside in `client-src/`.

## Common Tasks
- **Adding a New Page**: Register the route in `chromedash-app.js` (within `setUpRoutes`) and create the corresponding Lit component.
- **Building assets**: Use `npm run watch` during development for live-reloading or `npm run build` for a final build.
