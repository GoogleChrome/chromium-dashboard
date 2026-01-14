// @ts-check
import { expect } from '@playwright/test';

/**
 * Checks if the current viewport is mobile width (<= 700px).
 * @param {import("@playwright/test").Page} page
 */
export function isMobile(page) {
  const size = page.viewportSize();
  return size ? size.width <= 700 : false;
}

/**
 * Captures console messages and forwards them to the Node console with timestamps.
 * Filters out common noise (SameSite warnings).
 * @param {import("@playwright/test").Page} page
 */
export function captureConsoleMessages(page) {
  page.on('console', async msg => {
    if (msg.type() === 'warning') return;

    const now = new Date();
    const time = now.toISOString().split('T')[1].slice(0, -1); // HH:mm:ss.mmm

    const args = await Promise.all(
      msg.args().map(arg => arg.jsonValue().catch(() => arg.toString()))
    );

    let logLine = args.join(' ');

    // Filter noisy SameSite cookie warnings
    if (logLine.includes('does not have a proper “SameSite” attribute value')) {
      return;
    }

    console.log(`${time}: console.${msg.type()}: ${logLine}`);
  });
}

/**
 * Basic event listeners for debugging page crashes or errors.
 * @param {import("@playwright/test").Page} page
 */
export function capturePageEvents(page) {
  page.on('pageerror', error => console.error(`pageerror: ${error}`));
  page.on('crash', () => console.error(`crash: ${page.url()}`));
}

/**
 * Auto-accepts dialogs (alert, confirm, beforeunload).
 * Note: Playwright auto-dismisses dialogs by default, so we only need this
 * if we explicitly want to 'accept' them.
 * @param {import("@playwright/test").Page} page
 */
export function acceptDialogs(page) {
  page.on('dialog', async dialog => {
    await dialog.accept();
  });
}


/**
 * fastLogin performs a robust login via the "Dev Mode" sign-in button.
 * It detects if the user is already logged in to save time.
 * @param {import("@playwright/test").Page} page
 */
export async function login(page) {
  // 1. Handle potential alerts (like "Do you want to leave?")
  acceptDialogs(page);

  // 2. Navigate to the app.
  // We use domcontentloaded to be faster than 'load', relying on locators later.
  await page.goto('/', { waitUntil: 'domcontentloaded' });

  // 3. Check authentication state efficiently.
  const accountIndicator = page.getByTestId('account-indicator');
  const loginButton = page.getByTestId('dev-mode-sign-in-button');

  // Wait for either the login button OR the account indicator to appear.
  // This avoids fixed delays or assuming one state.
  await Promise.race([
    expect(accountIndicator).toBeVisible(),
    expect(loginButton).toBeVisible()
  ]);

  if (await accountIndicator.isVisible()) {
    // Already logged in.
    return;
  }

  // 4. Perform Login
  await loginButton.click();

  // 5. Verification
  // Wait for the account indicator to confirm login success.
  await expect(accountIndicator).toBeVisible({ timeout: 10000 });
}

/**
 * Logs out via the UI.
 * Note: In standard Playwright tests, you typically don't need to logout
 * if tests run in isolated contexts.
 * @param {import("@playwright/test").Page} page
 */
export async function logout(page) {
  acceptDialogs(page); // Handle "Changes may not be saved" dialogs

  await page.goto('/');

  // Handle Mobile/Desktop menu differences
  if (isMobile(page)) {
    const menuButton = page.getByTestId('menu');
    await menuButton.click();
  } else {
    await page.getByTestId('account-indicator').click();
  }

  const signOutLink = page.getByTestId('sign-out-link');
  await signOutLink.click();

  // Verify logout state by checking for the login button
  await expect(page.getByTestId('dev-mode-sign-in-button')).toBeVisible();
}


/**
 * Navigates to the "Create Feature" form.
 * @param {import("@playwright/test").Page} page
 */
export async function gotoNewFeaturePage(page) {
  const createFeatureButton = page.getByTestId('create-feature-button');

  // If button is not visible, it might be behind the mobile menu
  if (!await createFeatureButton.isVisible() && isMobile(page)) {
    await page.getByTestId('menu').click();
  }

  await createFeatureButton.click();

  // Close menu if mobile (cleanup)
  if (isMobile(page)) {
    // Short wait to ensure menu animation doesn't block interactions,
    // or click the overlay/menu button again.
    await page.getByTestId('menu').click();
  }

  await expect(page.getByTestId('add-a-feature')).toBeVisible();
}

/**
 * Helper to handle Shoelace/Custom component input fields.
 * @param {import("@playwright/test").Page} page
 * @param {string} wrapperTestId
 * @param {string} value
 */
async function fillCustomComponent(page, wrapperTestId, value) {
  const wrapper = page.getByTestId(wrapperTestId);
  await expect(wrapper).toBeVisible();

  // Click wrapper to ensure the internal input is active/rendered
  await wrapper.click();

  const input = wrapper.locator('input');
  await expect(input).toBeEditable();
  await input.fill(value);
  // Press Enter if the component requires it to set the value
  await input.press('Enter');
}

/**
 * Creates a new feature with default test values.
 * @param {import("@playwright/test").Page} page
 */
export async function createNewFeature(page) {
  await gotoNewFeaturePage(page);

  // Use labeled locators where possible for better accessibility testing
  await page.locator('input[name="name"]').fill('Test feature name');
  await page.locator('textarea[name="summary"]').fill('Test summary description');

  // Use helper for custom components to avoid code duplication and delays
  await fillCustomComponent(page, 'blink_components_wrapper', 'blink');
  await fillCustomComponent(page, 'web_feature_wrapper', 'hwb');

  // Select feature type (Radio button)
  // We use .first() or exact locator to ensure we click the input, not the label wrapper if strict
  await page.locator('input[name="feature_type"][value="0"]').click();

  await page.locator('input[type="submit"]').click();

  // Wait for navigation to the feature details page
  await page.waitForURL(/\/feature\/\d+/); // Regex matches /feature/1234...
  await expect(page.locator('chromedash-feature-detail')).toBeVisible({ timeout: 15000 });
}
