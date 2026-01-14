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
 * @param {import("@playwright/test").Page} page
 */
export async function login(page) {
  // 1. Setup: Expose the helper function needed by the component
  try {
    await page.exposeFunction('isPlaywright', () => {});
  } catch (e) {
    // Function already exposed, ignore
  }

  // Handle dialogs (Fixed name to match exported function)
  acceptDialogs(page);

  // 2. Navigation: Go to the homepage
  await page.goto('/');

  // Define locators
  const accountIndicator = page.getByTestId('account-indicator');
  const loginButton = page.getByTestId('dev-mode-sign-in-button');
  const signOutLink = page.getByTestId('sign-out-link');

  // 3. Check specific "Already Logged In" state
  if (await accountIndicator.isVisible()) {
    // Handle mobile/desktop menu interaction differences for logging out
    if (isMobile(page)) {
      const menuButton = page.getByTestId('menu');
      if (await menuButton.isVisible()) {
        await menuButton.click();
      }
    } else {
      // On Desktop, hover/click the avatar to reveal the sign out link
      await accountIndicator.click();
    }

    // Ensure sign out link is ready before clicking
    await expect(signOutLink).toBeVisible();
    await signOutLink.click();

    // Wait for the login button to appear to confirm we are logged out
    await expect(loginButton).toBeVisible();
  }

  // 4. Perform Login
  // We explicitly wait for the login button to be ready/clickable
  await expect(loginButton).toBeVisible();

  // The component uses a setTimeout(..., 1000) followed by a
  // window.location.reload(). We must wait for this specific navigation event,
  // otherwise Playwright checks for the account indicator on the *old* page
  // before the reload happens.
  await Promise.all([
    // Wait for the navigation (reload) to complete.
    // We expect the URL to effectively remain the same (or match the base),
    // but the 'load' event ensures the reload finished.
    page.waitForLoadState('domcontentloaded'),
    loginButton.click()
  ]);

  // 5. Verify Success
  // Now that the page has reloaded, the account indicator should appear.
  await expect(accountIndicator).toBeVisible({ timeout: 20000 });
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
