// @ts-check
import {test, expect} from '@playwright/test';

test.beforeEach(async ({page}) => {
  // Attempt to login before running each test.
  let loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
  if (loginButton && await loginButton.count() == 1) {
    await loginButton.click();
    await page.waitForURL('/roadmap');
    loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
    expect(await loginButton.count()).toBe(0);
  }
  // Either way, we should be logged in now.
  const navDropdownLink = page.getByText('example@chromium.org');
  expect(await navDropdownLink.count() == 1);
});

test.afterEach(async ({page}) => {
  // Attempt to sign out after running each test.
  let navDropdownLink = page.getByText('example@chromium.org');
  if (navDropdownLink && await navDropdownLink.count() == 1) {
    await navDropdownLink.hover();
    const signOutLink = page.getByText('Sign out');
    expect(await signOutLink.count()).toBe(1);
    await signOutLink.click();
    navDropdownLink = page.getByText('example@chromium.org');
    expect(await navDropdownLink.count()).toBe(0);
  }
});


// test('has title', async ({page}) => {
//   await page.goto('http://localhost:8080/guide/new');

//   // Expect a title "to contain" a substring.
//   await expect(page).toHaveTitle(/Chrome Status/);
// });

test('navigate to create feature page', async ({page}) => {
  page.goto('http://localhost:8080/');
  await page.waitForURL('http://localhost:8080/');

  // Attempt to login before running each test.
  // let loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
  let loginButton = page.getByTestId('dev-mode-sign-in-button');
  if (loginButton && await loginButton.count() == 1) {
    await loginButton.click();
    await page.waitForURL('/roadmap');
    loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
    expect(await loginButton.count()).toBe(0);
  }
  // Either way, we should be logged in now.
  const navDropdownLink = page.getByText('example@chromium.org');
  expect(await navDropdownLink.count() == 1);

  const maintabs = page.locator('div');
  expect(await maintabs.count()).toBe(1);

  // Navigate to the new feature page.
  // await page.locator('sl-button[data-testid=create-feature]').click();
  // const createFeatureButton = page.getByText(' Create feature ');
  const createFeatureButton = page.getByTestId('create-feature');
  expect(await createFeatureButton.count()).toBe(1);
  createFeatureButton.click();
  await page.waitForURL('/guide/new');
});


// test('new feature page content', async ({page}) => {
//   // Double check that we're logged in.
//   const navDropdownLink = page.getByText('example@chromium.org');
//   expect(await navDropdownLink.count() == 1);

//   // Navigate to the new feature page.
//   page.goto('/guide/new');
//   await page.waitForURL('http://localhost:8080/guide/new');

//   // Take a screenshot of the content area.
//   await expect(page.locator('#content')).toHaveScreenshot();
// });
