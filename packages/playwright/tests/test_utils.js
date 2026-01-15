// @ts-check
import { expect } from '@playwright/test';

/**
 * Call this, say in your test.beforeEach() method, to capture all
 * console messages and copy them to the playwright console.
 * @param {import("playwright-core").Page} page
 */
export function captureConsoleMessages(page) {
  page.on('console', async msg => {
    // ignore warnings for now.  There are tons of them.
    if (msg.type() === 'warning') {
      return;
    }

    // Get time before await on arg values.
    const now = new Date();
    const minutes = now.getUTCMinutes().toString().padStart(2, '0');
    const seconds = now.getUTCSeconds().toString().padStart(2, '0');
    const millis = now.getUTCMilliseconds().toString().padStart(3, '0');
    const time = `${minutes}:${seconds}:${millis}`;

    const values = [];
    for (const arg of msg.args()) {
      let argString = '';
      try {
        // Sometimes this fails with something like:
        //  "Protocol error (Runtime.callFunctionOn): Target closed."
        argString = (await arg.jsonValue()).toString();
      } catch {
        argString = arg.toString();
      }
      // Simplify tons of "SameSite" warnings.
      if (
        argString.match(/does not have a proper “SameSite” attribute value/)
      ) {
        argString = argString
          .replace('JavaScript Warning: ', 'SameSite ')
          .replace(
            'does not have a proper “SameSite” attribute value. Soon, cookies without the “SameSite” attribute or with an invalid value will be treated as “Lax”. This means that the cookie will no longer be sent in third-party contexts. If your application depends on this cookie being available in such contexts, please add the “SameSite=None“ attribute to it. To know more about the “SameSite“ attribute, read https://developer.mozilla.org/docs/Web/HTTP/Headers/Set-Cookie/SameSite',
            ''
          );
      }
      values.push(argString);
    }
    const valuesString = values.join(' ');
    console.log(`${time}: console.${msg.type()}: ${valuesString}`);
  });
}

/**
 * @param {import("playwright-core").Page} page
 */
export function capturePageEvents(page) {
  page.on('close', async () => {
    console.log(`close: ${page.url()}`);
  });
  page.on('pageerror', async (/** @type {Error} */ error) => {
    console.log(`pageerror: ${error}`);
  });
  page.on('crash', async () => {
    console.log(`crash: ${page.url()}`);
  });
  page.on('domcontentloaded', async () => {
    console.log(`domcontentloaded: ${page.url()}`);
  });
}

/**
 * @param {import("playwright-core").Page} page
 */
export async function decodeCookies(page) {
  const cookies = await page.context().cookies();
  cookies.forEach(cookie => {
    console.log('Decoded Cookie:', cookie);
  });
}

/**
 * @param {import("playwright-core").Page} page
 */
export async function isMobile(page) {
  const viewportSize = page.viewportSize();
  return (viewportSize && viewportSize.width <= 700);
}

/**
 * Handle beforeunload by accepting it.
 * @param {import('@playwright/test').Page} page
 */
export function acceptBeforeUnloadDialogs(page) {
  page.on('dialog', async dialog => {
    if (dialog.type() === 'beforeunload') {
      await dialog.accept();
    }
  });
}

/**
 * Handle confirm dialog by accepting it.
 * @param {import('@playwright/test').Page} page
 */
export function acceptConfirmDialogs(page) {
  // Setup handler for confirm dialog
  page.on('dialog', async dialog => {
    if (dialog.type() === 'confirm') {
      await dialog.accept();
    }
  });
}

/**
 * Handle alert dialog by accepting it.
 * @param {import('@playwright/test').Page} page
 */
export function acceptAlertDialogs(page) {
  // Setup handler for confirm dialog
  page.on('dialog', async dialog => {
    if (dialog.type() === 'alert') {
      await dialog.accept();
    }
  });
}

/**
 * @param {import("playwright-core").Page} page
 */
export async function login(page) {
  page.exposeFunction('isPlaywright', () => {});

  // Always reset to the roadmap page.
  // But first accept alert dialogs, which
  // can occur in Chrome when not logged in.
  acceptAlertDialogs(page);

  await page.goto('/', { timeout: 20000 });
  await page.waitForURL('**/roadmap', { timeout: 20000 });

  await expect(page).toHaveTitle(/Chrome Status/);

  // Check whether we are already or still logged in.
  // We use the presence of the 'dev-mode-sign-in-button' as the definitive
  // indicator of "Not Logged In" because the Account Indicator layout varies.
  const loginButton = page.getByTestId('dev-mode-sign-in-button');

  if (await loginButton.isHidden()) {
    // If the login button is hidden, we assume we are logged in.
    return;
  }

  // Expect login button to be present now.
  await expect(loginButton).toBeVisible();

  // Click login and wait for the page reload that the button triggers.
  // We cannot use waitForURL because the URL might be the same.
  // Waiting for 'domcontentloaded' ensures the reload has actually happened.
  await Promise.all([
    page.waitForEvent('domcontentloaded'),
    loginButton.click()
  ]);

  // Validate successful login.
  await expect(page).toHaveTitle(/Chrome Status/);

  if (await isMobile(page)) {
    // On mobile, the account indicator is hidden inside the drawer.
    // Verifying that the login button is GONE is sufficient proof of login.
    await expect(loginButton).not.toBeVisible();
  } else {
    // On desktop, we can verify the account indicator is visible in the header.
    const accountIndicator = page.getByTestId('account-indicator');
    await expect(accountIndicator).toBeVisible();
  }
}

/**
 * @param {import("playwright-core").Page} page
 */
export async function logout(page) {
  // Attempt to sign out after running each test.
  // First reset to the roadmap page, so that we avoid the alert
  // when signed out on other pages.
  // But in case the current page has unsaved changes we need to
  // accept leaving them unsaved.
  acceptBeforeUnloadDialogs(page);

  await page.goto('/');
  await page.waitForURL('**/roadmap');
  await expect(page).toHaveTitle(/Chrome Status/);

  if (await isMobile(page)) {
    const menuButton = page.getByTestId('menu');
    // If menu isn't visible, we might not be logged in or page is broken,
    // but we check anyway.
    if (await menuButton.isVisible()) {
      await menuButton.click();

      const signOutLink = page.getByTestId('sign-out-link');
      if (await signOutLink.isVisible()) {
        await signOutLink.click();
        await page.waitForURL('**/roadmap');
        // The sign in button should be visible again if we are logged out.
        const loginButton = page.getByTestId('dev-mode-sign-in-button');
        await expect(loginButton).toBeVisible();
      }
    }
  } else {
    const accountIndicator = page.getByTestId('account-indicator');

    // Only attempt to logout if the account indicator is actually visible.
    // This prevents test failures in teardown if the test failed before login.
    if (await accountIndicator.isVisible()) {
      // Click account indicator to open the menu
      await accountIndicator.click();

      // Need to wait for the sign-out-link to be visible
      const signOutLink = page.getByTestId('sign-out-link');
      await expect(signOutLink).toBeVisible();
      await signOutLink.click();

      // Confirm we are back on roadmap and signed out
      await page.waitForURL('**/roadmap');
      await expect(page).toHaveTitle(/Chrome Status/);
    }
  }
}

/**
 * From top-level page, after logging in, go to the New Feature page.
 * @param {import('@playwright/test').Page} page
 */
export async function gotoNewFeaturePage(page) {
  const mobile = await isMobile(page);
  const createFeatureButton = page.getByTestId('create-feature-button');
  const menuButton = page.getByTestId('menu');

  // Navigate to the new feature page.
  await expect(menuButton).toBeVisible();
  if (mobile) {
    await menuButton.click();
  }

  await expect(createFeatureButton).toBeVisible();
  await createFeatureButton.click();

  if (mobile) {
    // To hide menu (Close Drawer).
    await menuButton.click();
  }

  // Expect "Add a feature" header to be present.
  const addAFeatureHeader = page.getByTestId('add-a-feature');
  await expect(addAFeatureHeader).toBeVisible({ timeout: 10000 });
}

/**
 * Enters a blink component on the page.
 *
 * @param {import("playwright-core").Page} page - The page object representing the web page.
 * @return {Promise<void>} A promise that resolves once the blink component is entered.
 */
export async function enterBlinkComponent(page) {
  const blinkComponentsInputWrapper = page.getByTestId(
    'blink_components_wrapper'
  );
  await expect(blinkComponentsInputWrapper).toBeVisible();

  const blinkComponentsInput = blinkComponentsInputWrapper.locator('input');
  await blinkComponentsInput.fill('blink');

  // If you need to verify the value "stuck"
  await expect(blinkComponentsInput).toHaveValue('blink');
}

/**
 * Enters a web feature id on the page.
 *
 * @param {import("playwright-core").Page} page - The page object representing the web page.
 * @return {Promise<void>} A promise that resolves once the web feature id is entered.
 */
export async function enterWebFeatureId(page) {
  const webFeatureIdInputWrapper = page.getByTestId('web_feature_wrapper');
  await expect(webFeatureIdInputWrapper).toBeVisible();

  const webFeatureIdInput = webFeatureIdInputWrapper.locator('input');
  await webFeatureIdInput.fill('hwb');

  // Verify the value
  await expect(webFeatureIdInput).toHaveValue('hwb');

  // TODO(kyleju): assert that the link to webstatus.dev is present.
  // It is missing in the current test setup.
}

/**
 * Create a new feature, starting from top-level page, ending up on feature page.
 * @param {import('@playwright/test').Page} page
 */
export async function createNewFeature(page) {
  await gotoNewFeaturePage(page);
  // Enter feature name
  const featureNameInput = page.locator('input[name="name"]');
  await featureNameInput.fill('Test feature name');

  // Enter summary description
  const summaryInput = page.locator('textarea[name="summary"]');
  await summaryInput.fill('Test summary description');

  await enterBlinkComponent(page);
  await enterWebFeatureId(page);

  // Select feature type.
  const featureTypeRadioNew = page.locator(
    'input[name="feature_type"][value="0"]'
  );
  await featureTypeRadioNew.click();

  // Submit the form.
  const submitButton = page.locator('input[type="submit"]');
  await submitButton.click();

  // Wait until we are on the Feature page.
  await page.waitForURL('**/feature/*');
  const detail = page.locator('chromedash-feature-detail');
  await expect(detail).toBeVisible({timeout: 30000});
}

/**
 * Navigates to new features list page.
 * @param {import("playwright-core").Page} page
 */
export async function gotoNewFeatureList(page) {
  await page.goto('/features');
  const pagiation = page.locator('chromedash-feature-pagination');
  await expect(pagiation).toBeVisible();
}
