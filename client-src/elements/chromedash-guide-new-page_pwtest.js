// @ts-check
import {test, expect} from '@playwright/test';

async function login(page) {
  // Attempt to login before running each test.
  // await page.goto('/');
  let loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
  expect(loginButton).toBeTruthy();
  expect(await loginButton.count()).toBe(1);
  if (loginButton && await loginButton.count() == 1) {
    await loginButton.click();
  }
  // Either way, check that we are logged in now.
  await page.waitForURL('/roadmap');
  let navContainer = page.locator('[data-testid=nav-container]');
  expect(await navContainer.count()).toBe(1);
}

async function logout(page) {
  // Attempt to sign out after running each test.
  let navContainer = page.locator('[data-testid=nav-container]');
  if (navContainer && await navContainer.count() == 1) {
    await navContainer.hover();
    const signOutLink = page.locator('[data-testid=sign-out-link]');
    expect(await signOutLink.count()).toBe(1);
    await signOutLink.click();

    navContainer = page.locator('[data-testid=nav-container]');
    expect(await navContainer.count()).toBe(0);
  }
}

// test.beforeEach(async ({page}) => {
//   // await login(page);
// });

test.afterEach(async ({page}) => {
  await logout(page);
});


test('has login button before login', async ({page}) => {
  await page.goto('/roadmap');

  // Expect the title to contain a substring.
  await expect(page).toHaveTitle(/Chrome Status/);

  // Expect a login button to be present.
  let loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
  expect(loginButton).toBeTruthy();
  expect(await loginButton.count()).toBe(1);

  // Expect a nav container to not be present.
  let navContainer = page.locator('[data-testid=nav-container]');
  expect(await navContainer.count()).toBe(0);

  // Expect a create feature button to not be present.
  const createFeatureButton = page.locator('[data-testid=create-feature]');
  expect(await createFeatureButton.count()).toBe(0);

  // Take a screenshot of the initial page.
  await expect(page).toHaveScreenshot('chrome-status.png');
});


test('has create feature button after login', async ({ page }) => {
  await page.goto('/roadmap');
  await login(page);

    // Expect a login button to not be present.
  let loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
  expect(loginButton).toBeTruthy();
  expect(await loginButton.count()).toBe(0);

  // Expect a nav container to be present.
  let navContainer = page.locator('[data-testid=nav-container]');
  expect(await navContainer.count()).toBe(1);

  // Expect a create feature button to be present.
  const createFeatureButton = page.locator('[data-testid=create-feature]');
  expect(await createFeatureButton.count()).toBe(1);

  // Take a screenshot with "Create feature" button.
  await expect(page).toHaveScreenshot('create-feature-button.png');
});

test('navigate to create feature page', async ({ page }) => {
  await page.goto('/roadmap');
  await login(page);

  // Navigate to the new feature page.
  // await page.locator('sl-button[data-testid=create-feature]').click();
  // const createFeatureButton = page.getByText(' Create feature ');
  const createFeatureButton = page.locator('[data-testid=create-feature]');
  expect(await createFeatureButton.count()).toBe(1);
  createFeatureButton.click();
  await page.waitForURL('/guide/new');

  // Take a screenshot of the content area.
  await expect(page).toHaveScreenshot('chrome-status-new-feature.png');
});


// test('new feature page content', async ({page}) => {
//   // Double check that we're logged in.
//   const navDropdownLink = page.getByText('example@chromium.org');
//   expect(await navDropdownLink.count() == 1);

//   // Navigate to the new feature page.
//   await page.goto('/guide/new');
//   await page.waitForURL('http://localhost:8080/guide/new');

//   // Take a screenshot of the content area.
//   await expect(page.locator('#content')).toHaveScreenshot();
// });
