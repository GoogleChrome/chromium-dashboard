# Gemini Code Assist Configuration for chromium-dashboard

<!-- Last analyzed commit: 598417df62c75ccaecbed268f4b2429a8c86911c -->

This document provides context to Gemini Code Assist to help it generate more accurate and project-specific code suggestions for the `chromium-dashboard` project.

## 1. Project Overview

`chromium-dashboard` (chromestatus.com) is the official tool for tracking feature launches in Blink. It guides feature owners through the launch process and serves as a primary source of developer information.

The architecture consists of:
- **Backend**: A Flask-based application running on Google App Engine, using Cloud NDB for Datastore interactions.
- **Frontend**: A Lit-based single-page application (SPA) using Shoelace widgets and `page.js` for routing.
- **API**: Uses OpenAPI 3.0 for specification and code generation.
- **AI Features**: Includes an AI-powered WPT coverage evaluation pipeline using Gemini.

## 2. Local Development Workflow

- **Setup**: `make setup` initializes the environment (Node.js and Python venv).
- **Starting**: `npm start` runs the Datastore emulator and the Flask server.
- **Testing**:
    - `npm test`: Runs Python unit tests with the Datastore emulator.
    - `make webtest`: Runs Lit component tests using Playwright.
    - `make pwtests`: Runs end-to-end Playwright visual tests.
- **Linting**: `make lint` runs Prettier, ESLint, and Lit-analyzer.
- **OpenAPI**: `make openapi` generates frontend and backend code from `openapi/api.yaml`.

## 3. Project Rules

- **Legacy Code**: Do not add new features or logic to the legacy `pages/` directory. This directory is deprecated and only maintained for existing functionality. Use `api/` for new backend endpoints and `client-src/elements/` for new frontend components.

## 4. Specialized Skills

Detailed architectural guidance and "how-to" guides for specific domains are available as **Gemini Skills**:

- `chromestatus-adding-a-field`: How to add a new field to a feature across the entire stack (Data, API, and Frontend).
- `chromestatus-backend`: Flask handlers, NDB interactions, and OpenAPI integration.
- `chromestatus-frontend`: Lit web components, Shoelace widgets, and routing.
- `chromestatus-ci-verification`: Local commands for linting, type checking, and testing to match CI.
- `chromestatus-playwright-testing`: Guidance for running and updating Playwright end-to-end tests.

## 4. Updating the Knowledge Base

To keep these skills and this document up-to-date, you can ask Gemini to analyze the latest commits. Use the hidden marker at the top of this file to find commits made since the last analysis.

### 4.1. Prompt for Updating

> Please update your knowledge base by analyzing the commits since the last analyzed commit stored in `GEMINI.md`.

### 4.2. Process

When given this prompt, Gemini will:
1. Read `GEMINI.md` to find the last analyzed commit SHA.
2. Use `git log` to identify new commits since that SHA.
3. Analyze the changes, consulting sources of truth like `openapi/api.yaml` or `internals/models.py`.
4. Update the relevant skill files in `.agents/skills/`.
5. Update the last analyzed commit SHA in `GEMINI.md`.
