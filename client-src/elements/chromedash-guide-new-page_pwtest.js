// @ts-check
import {test, expect} from '@playwright/test';

// Record whether we captured images of the page before and after login
let loginScreenshots = false;

async function login(page) {
  // await expect(page).toHaveScreenshot('roadmap.png');
  // Always reset to the roadmap page.
  await page.goto('/');
  await page.waitForURL('**/roadmap');
  page.mouse.move(0, 0); // Move away from content on page.

  // Expect login button to be present.
  const loginButton = page.locator('button[data-testid=dev-mode-sign-in-button]');
  await expect(loginButton).toBeVisible();

  // Expect nav container to not be present.
  let navContainer = page.locator('[data-testid=nav-container]');
  await expect(navContainer).toHaveCount(0);

  // Take a screenshot of the initial page before login.
  if (!loginScreenshots) {
    await expect(page).toHaveScreenshot('before-login.png');
  }

  // Need to wait for the google signin button to be ready, to avoid
  loginButton.waitFor('visible');
  await page.click('[data-testid=dev-mode-sign-in-button]');

  // Check that we are logged in now.
  await page.waitForURL('**/roadmap');
  page.mouse.move(0, 0); // Move away from content on page.

  // Expect the title to contain a substring.
  await expect(page).toHaveTitle(/Chrome Status/);

  await expect(page).toHaveScreenshot('after-login-click.png');

  // Expect a nav container to be present.
  // This sometimes fails, even though the screenshot seems correct.
  navContainer = page.locator('[data-testid=nav-container]');
  await expect(navContainer).toBeVisible({timeout: 20000});

  if (!loginScreenshots) {
    // Take a screenshot of the page after login.
    await expect(page).toHaveScreenshot('after-login.png', {timeout: 10000});
    loginScreenshots = true;
  }
}

test.beforeEach(async ({ page }) => {
  test.setTimeout(60000);
  // Attempt to login before running each test.
  await login(page);
});

let logoutScreenshots = false;

async function logout(page) {
  // Attempt to sign out after running each test.
  // First reset to the roadmap page.
  await page.goto('/');
  await page.waitForURL('**/roadmap');

  const navContainer = page.locator('[data-testid=nav-container]');
  if (navContainer && await navContainer.count() == 1) {
    await navContainer.hover({timeout: 1000});
    const signOutLink = page.locator('[data-testid=sign-out-link]');
    await expect(signOutLink).toBeVisible();

    await signOutLink.hover({ timeout: 1000 });
    if (!logoutScreenshots) {
      await expect(page).toHaveScreenshot('sign-out-link.png');
    }
    await signOutLink.click({timeout: 5000});

    // await page.goto('/');
    await page.waitForURL('**/roadmap');
    // page.mouse.move(0, 0); // Move away from content on page.

    if (!logoutScreenshots) {
      await expect(page).toHaveScreenshot('after-sign-out.png', { timeout: 10000 });
      logoutScreenshots = true;
    }

    // Wait for sign in button to appear.
    // This sometimes fails, even though the screenshot seems correct.
    const loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
    await loginButton.waitFor('visible', {timeout: 10000});
    await expect(loginButton).toBeVisible({timeout: 10000});
  }
}

test.afterEach(async ({ page }) => {
  test.setTimeout(60000);
  await logout(page);
});


test('navigate to create feature page', async ({page}) => {
  await page.goto('/');
  await page.waitForURL('**/roadmap');

  // Take a screenshot with "Create feature" button.
  await expect(page).toHaveScreenshot('create-feature-button-check.png');

  // Expect create feature button to be present.
  const createFeatureButton = page.locator('[data-testid=create-feature-button]');
  await expect(createFeatureButton).toBeVisible({timeout: 15000});

  // Take a screenshot with "Create feature" button.
  await expect(page).toHaveScreenshot('create-feature-button.png');

  // Navigate to the new feature page by clicking.
  createFeatureButton.click();
  await page.waitForURL('**/guide/new');

  // Expect "Add a feature" button to be present.
  const addAFeatureHeader = page.locator('[data-testid=add-a-feature]');
  await expect(addAFeatureHeader).toBeVisible();

  // Take a screenshot of the content area.
  await expect(page).toHaveScreenshot('new-feature.png');
});


test('new feature page content', async ({page}) => {
  // Navigate to the new feature page.
  await page.goto('/guide/new');
  await page.waitForURL('**/guide/new');

  // Expect "Add a feature" button to be present.
  const addAFeatureHeader = page.locator('[data-testid=add-a-feature]');
  await expect(addAFeatureHeader).toBeVisible({timeout: 5000});

  // Take a screenshot
  await expect(page.locator('chromedash-guide-new-page')).toHaveScreenshot('new-feature-page.png');
});
