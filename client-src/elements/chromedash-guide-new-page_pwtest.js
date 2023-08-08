// @ts-check
import {test, expect} from '@playwright/test';

// Record whether we are logged in or not,
// so we can avoid logging in more than once.
let loggedIn = false;

async function login(page) {
  // Reset to the roadmap page.
  await page.goto('/');
  await page.waitForURL('**/roadmap');

  if (loggedIn) return;

  // Expect a login button to be present.
  const loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
  expect(loginButton).toBeTruthy();
  expect(await loginButton.count()).toBe(1);

  // Expect a nav container to not be present.
  let navContainer = page.locator('[data-testid=nav-container]');
  expect(await navContainer.count()).toBe(0);

  // Take a screenshot of the initial page before login.
  await expect(page).toHaveScreenshot('before-login.png');

  // Attempt to login before running each test.
  // if (loginButton && await loginButton.count() == 1) {
  // Need to wait for the google signin button to be ready, to avoid
  // accidentally clicking on it when the layout shifts.
  // const googleSigninButton = page.locator('[data-testid=google-signin-button]');
  // expect(googleSigninButton).toBeTruthy();
  // expect(await googleSigninButton.count()).toBe(1);
  // await googleSigninButton.elementHandle().waitForElementState('stable');
  // Now we can safely click on the login button.
  loginButton.waitFor('visible');
  await page.click('[data-testid=dev-mode-sign-in-button]');
  // await loginButton.elementHandle().click();
  // }

  loggedIn = true;

  // Either way, check that we are logged in now.

  // await page.goto('/roadmap');
  // await page.waitForURL('**/roadmap');
  // await page.waitForSelector('[data-testid=nav-container]');
  // const navContainer = page.locator('[data-testid=nav-container]');
  // expect(navContainer).toBeTruthy();
  // expect(await navContainer.count()).toBe(1);

  // await page.goto('/roadmap');
  // await page.goto('/');
  // await page.reload(); // Doesn't reload? SPA?

  await page.waitForURL('**/roadmap');

  // Expect the title to contain a substring.
  await expect(page).toHaveTitle(/Chrome Status/);

  // The following fails inconsistently, and differently on Chrome vs Firefox.
  // // Expect a login button to not be present.
  // loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
  // expect(loginButton).toBeTruthy();
  // expect(await loginButton.count()).toBe(0);

  // Expect a nav container to be present.
  // navContainer = page.locator('[data-testid=nav-container]');
  navContainer = page.getByText('example@chromium.org', { exact: true });
  expect(navContainer).toBeTruthy();
  await expect(navContainer).toBeVisible();

  // Take a screenshot of the page after login.
  await expect(page).toHaveScreenshot('after-login.png');
}

// async function logout(page) {
//   // Attempt to sign out after running each test.
//   // First reset to the roadmap page.
//   await page.goto('/');
//   await page.waitForURL('**/roadmap');

//   const navContainer = page.locator('[data-testid=nav-container]');
//   if (navContainer && await navContainer.count() == 1) {
//     await navContainer.hover({timeout: 1000});
//     const signOutLink = page.locator('[data-testid=sign-out-link]');
//     expect(await signOutLink.count()).toBe(1);
//     await page.click('[data-testid=sign-out-link]');
//     // await signOutLink.click();

//     // await page.goto('/');
//     await page.waitForURL('**/roadmap');

//     // Wait for sign in button to appear.
//     const loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
//     loginButton.waitFor('visible');
//     expect(await loginButton.count()).toBe(1);
//   }
// }

test.beforeEach(async ({page}) => {
  await login(page);
});

// test.afterEach(async ({page}) => {
//   // await logout(page);
// });


test('navigate to create feature page', async ({page}) => {
  // await page.goto('/roadmap');
  // await login(page);


  // Expect create feature button to be present.
  const createFeatureButton = page.getByText('Create feature');
  expect(await createFeatureButton.count()).toBe(1);

  // Take a screenshot with "Create feature" button.
  await expect(page).toHaveScreenshot('create-feature-button.png');

  // Navigate to the new feature page.
  // await page.locator('sl-button[data-testid=create-feature]').click();
  // const createFeatureButton = page.getByText(' Create feature ');

  createFeatureButton.click();
  await page.waitForURL('/guide/new');

  // Expect "Add a feature" to be present.
  const addAFeatureHeader = page.getByText('Add a feature');
  expect(await addAFeatureHeader.count()).toBe(1);

  // Take a screenshot of the content area.
  await expect(page).toHaveScreenshot('new-feature.png');
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
