// @ts-check
import { expect } from '@playwright/test';

/**
 * @deprecated Avoid using hard delays. Use web-first assertions or page.waitForTimeout() if absolutely necessary.
 * @param {number} ms
 */
export async function delay(ms) {
  // eslint-disable-next-line no-restricted-syntax
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Capture console messages.
 * Optimized to handle argument parsing safely without blocking.
 * @param {import("playwright-core").Page} page
 */
export function captureConsoleMessages(page) {
  page.on('console', async msg => {
    if (msg.type() === 'warning') return;

    const now = new Date();
    const time = now.toISOString().split('T')[1].slice(0, -1); // HH:mm:ss.sss

    const args = [];
    for (const arg of msg.args()) {
      let argValue;
      try {
        // jsonValue() is safer than generic toString on handles
        argValue = await arg.jsonValue();
      } catch (e) {
        argValue = msg.text();
      }

      let argString = String(argValue);

      // SameSite warning filter
      if (argString.includes('does not have a proper “SameSite” attribute value')) {
        argString = argString.replace('JavaScript Warning: ', 'SameSite ')
          .split('Soon, cookies without')[0]
          .trim();
      }
      args.push(argString);
    }
    console.log(`${time}: console.${msg.type()}: ${args.join(' ')}`);
  });
}

/**
 * @param {import("playwright-core").Page} page
 */
export function capturePageEvents(page) {
  // Only keeping the active ones from original code to reduce noise
  page.on('close', () => console.log(`close: ${page.url()}`));
  page.on('pageerror', (error) => console.log(`pageerror: ${error.message}`));
  page.on('crash', () => console.log(`crash: ${page.url()}`));
  page.on('domcontentloaded', () => console.log(`domcontentloaded: ${page.url()}`));
}

/**
 * @param {import("playwright-core").Page} page
 */
export async function decodeCookies(page) {
  const cookies = await page.context().cookies();
  for (const cookie of cookies) {
    console.log('Decoded Cookie:', cookie);
  }
}

/**
 * @param {import("playwright-core").Page} page
 */
export async function isMobile(page) {
  const viewportSize = page.viewportSize();
  return (viewportSize?.width || 1024) <= 700;
}

/**
 * consolidated dialog handler.
 * @param {import('@playwright/test').Page} page
 */
export function acceptDialogs(page) {
  page.on('dialog', async dialog => {
    await dialog.accept();
  });
}

// Re-export specific ones if existing tests rely on strict naming
export const acceptBeforeUnloadDialogs = acceptDialogs;
export const acceptConfirmDialogs = acceptDialogs;
export const acceptAlertDialogs = acceptDialogs;

/**
 * @param {import("playwright-core").Page} page
 */
export async function login(page) {
  await page.exposeFunction('isPlaywright', () => {});

  acceptDialogs(page);

  // Navigate and wait for load
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.waitForURL('**/roadmap');
  await expect(page).toHaveTitle(/Chrome Status/);

  // 1. Check if we need to logout first
  const accountIndicator = page.getByTestId('account-indicator');

  // isVisible() does not wait, it returns immediate status.
  // We use a short wait here to account for hydration.
  try {
    await accountIndicator.waitFor({ state: 'visible', timeout: 2000 });
    // If we are here, we are logged in. Logout.
    await performLogout(page);
  } catch (e) {
    // If timeout, we are not logged in, proceed.
  }

  // 2. Perform Login
  const loginButton = page.getByTestId('dev-mode-sign-in-button');
  await expect(loginButton).toBeVisible(); // Default 30s timeout is safer than custom vars
  await loginButton.click();

  // 3. Verify Login Success
  // Waiting for the account indicator is the best proof of login
  await expect(accountIndicator).toBeVisible({ timeout: 10000 });
}

/**
 * Helper function to handle the actual clicking for logout
 * @param {import("playwright-core").Page} page
 */
async function performLogout(page) {
  // Handle mobile menu interaction
  if (await isMobile(page)) {
    const menuButton = page.getByTestId('menu');
    await expect(menuButton).toBeVisible();
    await menuButton.click();
  } else {
    const accountIndicator = page.getByTestId('account-indicator');
    await accountIndicator.click();
  }

  const signOutLink = page.getByTestId('sign-out-link');
  await expect(signOutLink).toBeVisible();
  await signOutLink.click();

  // Wait for the login button to reappear to confirm logout
  await expect(page.getByTestId('dev-mode-sign-in-button')).toBeVisible();
}

/**
 * @param {import("playwright-core").Page} page
 */
export async function logout(page) {
  acceptDialogs(page);

  // Go home first
  await page.goto('/');
  await page.waitForURL('**/roadmap');

  // Check if we are actually logged in before trying to log out
  const loginButton = page.getByTestId('dev-mode-sign-in-button');
  if (await loginButton.isVisible()) {
    // Already logged out
    return;
  }

  await performLogout(page);

  // Verify clean state
  await expect(page).toHaveTitle(/Chrome Status/);
}

/**
 * From top-level page, after logging in, go to the New Feature page.
 * @param {import('@playwright/test').Page} page
 */
export async function gotoNewFeaturePage(page) {
  const mobile = await isMobile(page);
  const createFeatureButton = page.getByTestId('create-feature-button');
  const menuButton = page.getByTestId('menu');

  if (mobile) {
    await expect(menuButton).toBeVisible();
    await menuButton.click();
  }

  // Ensure button is actionable before clicking
  await expect(createFeatureButton).toBeVisible();
  await createFeatureButton.click();

  if (mobile) {
    // If the menu overlaps content, close it.
    // If navigation happened, the menu might auto-close.
    // Checking visibility before clicking is safer.
    if (await menuButton.isVisible()) {
      await menuButton.click();
    }
  }

  // Assertion: Page Transition occurred
  const addAFeatureHeader = page.getByTestId('add-a-feature');
  await expect(addAFeatureHeader).toBeVisible();
}

/**
 * Enters a blink component on the page.
 * @param {import("playwright-core").Page} page
 */
export async function enterBlinkComponent(page) {
  const wrapper = page.getByTestId('blink_components_wrapper');
  await expect(wrapper).toBeVisible();

  // Scoped locator: Find the input *inside* the wrapper
  const input = wrapper.locator('input');

  // Fill automatically waits for visibility, checks actionability, and focuses.
  await input.fill('blink');

  // If the UI requires selecting from a dropdown that appears after typing:
  // await page.keyboard.press('Enter'); // Uncomment if a selection is required
}

/**
 * Enters a web feature id on the page.
 * @param {import("playwright-core").Page} page
 */
export async function enterWebFeatureId(page) {
  const wrapper = page.getByTestId('web_feature_wrapper');
  await expect(wrapper).toBeVisible();

  const input = wrapper.locator('input');
  await input.fill('hwb');
}

/**
 * Create a new feature, starting from top-level page, ending up on feature page.
 * @param {import('@playwright/test').Page} page
 */
export async function createNewFeature(page) {
  await gotoNewFeaturePage(page);

  // Using specific locators.
  // 'fill' is robust; it will retry if the element is being hydrated.
  await page.locator('input[name="name"]').fill('Test feature name');
  await page.locator('textarea[name="summary"]').fill('Test summary description');

  await enterBlinkComponent(page);
  await enterWebFeatureId(page);

  // Select feature type
  await page.locator('input[name="feature_type"][value="0"]').click();

  // Submit and wait for navigation
  const submitButton = page.locator('input[type="submit"]');
  await submitButton.click();

  // Verification: Wait for URL change first (fastest check)
  await page.waitForURL('**/feature/*');

  // Verification: Wait for content
  const detail = page.locator('chromedash-feature-detail');
  await expect(detail).toBeVisible({ timeout: 15000 });
}

/**
 * Navigates to new features list page.
 * @param {import("playwright-core").Page} page
 */
export async function gotoNewFeatureList(page) {
  await page.goto('/newfeatures');
  const pagination = page.locator('chromedash-feature-pagination');
  await expect(pagination).toBeVisible();
}
