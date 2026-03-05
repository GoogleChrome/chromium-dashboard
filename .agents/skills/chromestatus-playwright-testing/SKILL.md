---
name: chromestatus-playwright-testing
description: Guidance for running, debugging, and updating Playwright end-to-end tests in chromium-dashboard.
---

# Playwright Testing Skill

This skill provides guidance on how to manage end-to-end tests using Playwright. Use these commands when frontend changes cause visual or functional regressions in the integration tests.

## Running Tests

### Run all Playwright tests
```bash
npm run pwtests
```

### Run tests in UI mode (Interactive)
Useful for debugging and seeing the browser in action.
```bash
npm run pwtests-ui
```

## Correcting Tests and Updating Snapshots

If your changes are intentional but cause visual regressions (e.g., you updated a CSS style or modified a component's layout), you may need to update the baseline snapshots.

### Update Playwright snapshots
```bash
npm run pwtests-update
```

## Debugging

### Show test report
If tests fail in CI or locally, you can view a detailed HTML report.
```bash
npm run pwtests-report
```

### Debug a specific test
```bash
npm run pwtests-debug
```

## Best Practices
1. **Verify Before Submitting**: Always run `npm run pwtests` locally if you change any files in `client-src/elements/` or `templates/`.
2. **Review Snapshots**: When running `npm run pwtests-update`, carefully review the diffs in the `__screenshots__` directories to ensure only intended changes are captured.
3. **Shutdown Environment**: If the Playwright environment stays active and consumes resources, you can manually shut it down.
```bash
npm run pwtests-shutdown
```

## Reference
- **Test Directory**: [packages/playwright/tests](file:///usr/local/google/home/suzyliu/Documents/chromium-dashboard/packages/playwright/tests)
- **Configuration**: [playwright.config.ts](file:///usr/local/google/home/suzyliu/Documents/chromium-dashboard/playwright.config.ts)
- **Scripts**: Defined in [package.json](file:///usr/local/google/home/suzyliu/Documents/chromium-dashboard/package.json)
