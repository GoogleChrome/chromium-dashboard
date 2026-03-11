---
name: chromestatus-ci-verification
description: Guidance for local verification of changes to ensure they pass CI checks (linting, type checking, testing, and building).
---

# CI Verification Skill

This skill provides the necessary commands and context to verify your changes locally, matching the checks performed by the GitHub Actions CI pipeline in [.github/workflows/ci.yml](file:///usr/local/google/home/suzyliu/Documents/chromium-dashboard/.github/workflows/ci.yml).

## Verification Pipeline

Before submitting a pull request, ensure all the following checks pass.

### 1. Setup Environment
Ensure your local environment is correctly set up.
```bash
make setup
```

### 2. Linting
Runs Prettier, ESLint, and Lit-analyzer to check code style and common issues.
```bash
make lint
```

### 3. Type Checking (Python)
Runs `mypy` for static type analysis of Python code.
```bash
make mypy
```

### 4. Backend Tests (Python)
Runs Python unit tests using the Datastore emulator.
```bash
npm test
```

### 5. Frontend Tests (Lit/Playwright)
Runs web component tests using Playwright.
```bash
make webtest
```

### 6. Build Assets
Verifies that all assets (JS, CSS, etc.) build correctly.
```bash
make build
```

## Summary Command
To run the most critical local checks (test, webtest, lint, mypy) in one go:
```bash
make presubmit
```

## Reference
- **Build Targets**: @Makefile
- **Task Scripts**: Defined in @package.json.
