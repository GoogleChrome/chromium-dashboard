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
- **Component Development**: Create new components in `client-src/elements/`. Follow the naming convention `chromedash-*.ts` or `chromedash-*.js`.
- **Icons**: Prefer Material Icons. If using Bootstrap icons via Shoelace, ensure they are copied to `static/shoelace/assets/icons`.
- **API Interaction**: Use the client wrapper in `cs-client.js` or the OpenAPI context consumer for making server requests.
- **Styling & CSS Hygiene**:
  - **Design Tokens**: Use Lit's `css` tagged templates for component styles and leverage design tokens defined in `client-src/css/_vars-css.js` and `client-src/css/shared-css.js` (e.g., `var(--max-content-width)`, `var(--card-background)`, `var(--content-padding)`).
  - **Global CSS Inheritance**: In SSR templates (`templates/*.html`), rely on global style inheritance from `static/css/main.css`. Do not redundantly override base typography (`h1`, `h2`, `h3`), link styling (`a`, `a:hover`), or standard button rules.
  - **Layout Containment**: `templates/_base.html` automatically wraps page content in `#content-component-wrapper`, handling horizontal centering and maximum width containment via `var(--max-content-width)`. Avoid defining redundant width caps or outer centering wrappers in individual template views.
  - **Anchor & Hash Navigation**: When implementing in-page anchor targets, section headings, or deep-linkable cards, apply `scroll-margin-top` to account for the sticky top toolbar and header (`<chromedash-header>`) to prevent content occlusion upon navigation.
- **Legacy Code**: Do not add new code or components to the legacy `pages/` directory on the backend, even if it contains old templates. All newer frontend logic should reside in `client-src/`.

## Common Tasks
- **Adding a New Page**: Register the route in `chromedash-app.ts` (within `setUpRoutes`) and create the corresponding Lit component.
- **Building assets**: Use `make watch` during development for live-reloading or `make build` for a final build.
