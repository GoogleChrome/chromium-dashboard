// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
// require('dotenv').config();

/**
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  // Directory where the tests are located. "." for top-level directory.
  testDir: '.',
  // Glob patterns or regular expressions that match test files.
  testMatch: '*/*_pwtest.js',
  snapshotPathTemplate: '{testDir}/{testFileDir}/__screenshots__/{testFileName}/{testName}/{arg}-{projectName}-{platform}{ext}',

  /* Run tests in files in parallel */
  fullyParallel: false,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retries should only be needed for flakey tests, which we should avoid. */
  retries: 0, // process.env.CI ? 2 : 0,
  /* Opt out of parallel tests, since we cannot avoid shared sessions ATM. */
  workers: 1, // was: process.env.CI ? 1 : undefined,
  /* Use pwtests-report instead of reporter: 'html'.  Not for CI. See https://playwright.dev/docs/test-reporters */
  reporter: 'line', /* was: process.env.CI ? [ ['html', { open: 'never'}] ] : [ ['html', { open: 'always'}] ], */
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:8080',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',

    // See https://playwright.dev/docs/test-use-options#recording-options.
    screenshot: 'only-on-failure',
  },
  preserveOutput: 'always',

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'chromium-mobile',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 600, height: 1000 },
      }
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'firefox-mobile',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 600, height: 1000 },
      }
    },

    // Dependencies for webkit are not working yet.
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },

    /* Test against mobile viewports. */
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },

    /* Test against branded browsers. */
    // {
    //   name: 'Microsoft Edge',
    //   use: { ...devices['Desktop Edge'], channel: 'msedge' },
    // },
    // {
    //   name: 'Google Chrome',
    //   use: { ..devices['Desktop Chrome'], channel: 'chrome' },
    // },
  ],

  /* Run your local dev server before starting the tests */
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:8080',
    reuseExistingServer: true,
  },
});
