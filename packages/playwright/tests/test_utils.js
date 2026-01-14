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
 * It waits for the async button injection and handles mobile overlays.
 * @param {import("@playwright/test").Page} page
 */
export async function login(page) {
  // 1. Expose the flag so the app knows it's being tested.
  // This enables the "Dev Mode" sign-in logic in chromedash-drawer.ts
  try {
    await page.exposeFunction('isPlaywright', () => {});
  } catch (e) {
    // Ignore if already exposed
  }

  acceptDialogs(page);

  // 2. Navigate
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await page.waitForURL('**/roadmap');

  const loginButton = page.getByTestId('dev-mode-sign-in-button');
  const accountIndicator = page.getByTestId('account-indicator');

  // 3. Wait for Auth State Resolution
  try {
    // Wait up to 10s for the button to be injected into the DOM
    await loginButton.waitFor({ state: 'visible', timeout: 10000 });
  } catch (e) {
    // If the button never shows up, check if we are possibly already logged in
    // (This handles flaky re-runs or desktop persistence)
    if (!isMobile(page) && await accountIndicator.isVisible()) {
      return;
    }
    // If we are on mobile (where avatar is hidden) or avatar is missing,
    // and the button is also missing, then something is wrong.
    console.error('Login button failed to appear.');
    throw e;
  }

  // 4. Perform Login
  // We click, then wait for the login button to detach (indicating reload/success).
  await loginButton.click({ force: true });

  // Wait for the button to disappear. This confirms the app has processed the login
  // and triggered the page reload.
  await expect(loginButton).toBeHidden({ timeout: 15000 });

  // 5. Verification
  if (!isMobile(page)) {
    // On Desktop, verify the avatar appears after the reload.
    // We increase timeout slightly to account for the full page reload.
    await expect(accountIndicator).toBeVisible({ timeout: 15000 });
  }
}

/**
 * Logs out via the UI.
 * @param {import("@playwright/test").Page} page
 */
export async function logout(page) {
  acceptDialogs(page); // Handle "Changes may not be saved" dialogs

  await page.goto('/');

  // Handle Mobile/Desktop menu differences
  if (isMobile(page)) {
    // On mobile, the sign-out link is inside the drawer menu.
    // Open the drawer first.
    const menuButton = page.getByTestId('menu');
    await menuButton.click();
    await expect(page.locator('sl-drawer')).toBeVisible();
  } else {
    // Desktop: Click avatar to see dropdown
    await page.getByTestId('account-indicator').click();
  }

  const signOutLink = page.getByTestId('sign-out-link');
  await expect(signOutLink).toBeVisible();
  await signOutLink.click();

  // Verify logout state
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
    // If mobile, open the menu to find the create button
    await page.getByTestId('menu').click();
    await expect(page.locator('sl-drawer')).toBeVisible();
  }

  await createFeatureButton.click();

  // Close menu if mobile (cleanup)
  if (isMobile(page)) {
    // Click the overlay or close button to dismiss the drawer
    await page.mouse.click(0, 0);
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

  // Use Promise.all to handle the navigation race condition.
  // The click causes a navigation, which can detach the button before click() returns,
  // causing an error. Promise.all ensures we listen for URL change while clicking.
  await Promise.all([
    page.waitForURL(/\/feature\/\d+/),
    page.locator('input[type="submit"]').click()
  ]);

  await expect(page.locator('chromedash-feature-detail')).toBeVisible({ timeout: 15000 });
}
