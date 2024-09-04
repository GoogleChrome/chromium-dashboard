// @ts-check
import { expect } from '@playwright/test';
import { Page } from "playwright-core";


/**
 * @param {number | undefined} ms
 */
export async function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}


/**
 * Call this, say in your test.beforeEach() method, to capture all
 * console messages and copy them to the playwright console.
 * @param {Page} page
 */
export function captureConsoleMessages(page) {
  page.on('console', async msg => {
    // ignore warnings for now.  There are tons of them.
    if (msg.type() === 'warn') {
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
      } catch (e) {
        argString = arg.toString();
      }
      // Simplify tons of "SameSite" warnings.
      if (argString.match(/does not have a proper “SameSite” attribute value/)) {
        argString = argString.replace('JavaScript Warning: ', 'SameSite ')
          .replace('does not have a proper “SameSite” attribute value. Soon, cookies without the “SameSite” attribute or with an invalid value will be treated as “Lax”. This means that the cookie will no longer be sent in third-party contexts. If your application depends on this cookie being available in such contexts, please add the “SameSite=None“ attribute to it. To know more about the “SameSite“ attribute, read https://developer.mozilla.org/docs/Web/HTTP/Headers/Set-Cookie/SameSite', '');
      }
      values.push(argString);
    }
    const valuesString = values.join(' ');
    console.log(`${time}: console.${msg.type()}: ${valuesString}`);
  });
}

/**
 * @param {Page} page
 */
export function capturePageEvents(page) {
  // page.on('open', async () => {
  //   console.log(`open: ${page.url()}`);
  // });
  page.on('close', async () => {
    console.log(`close: ${page.url()}`);
  });
  // page.on('requestfailed', request => {
  //   console.log(`requestfailed: ${request.url()} with: ${request.failure().errorText}`);
  // });
  page.on('pageerror', async (/** @type {Error} */ error) => {
    console.log(`pageerror: ${error}`);
  });
  page.on('crash', async () => {
    console.log(`crash: ${page.url()}`);
  });
  page.on('domcontentloaded', async () => {
    console.log(`domcontentloaded: ${page.url()}`);
  });
  // The following are often not useful, since there are so many
  // requests and responses.  But you can look for particular urls.
  // page.on('request', async (/** @type {Request} */ request) => {
  //   console.log(`request: ${request.url()}`);
  // });
  // page.on('response', async (/** @type {Response} */ response) => {
  //   console.log(`response: ${response.url()}`);
  // });
  // page.on('requestfinished', request => {
  //   console.log(`requestfinished: ${request.url()}`);
  // });
}

/**
 * @param {Page} page
 */
export async function decodeCookies(page) {
  const cookies = await page.context().cookies();
  cookies.forEach((cookie) => {
    console.log('Decoded Cookie:', cookie);
  });
}

/**
 * @param {Page} page
 */
export async function isMobile(page) {
  const viewportSize = page.viewportSize();
  return (viewportSize && viewportSize.width <= 700)
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


// Timeout for logging in, in milliseconds.
// Initially set to longer timeout, in case server needs to warm up and
// respond to the login.  Changed to shorter timeout after login is successful.
// Not sure we need this yet.
let loginTimeout = 20000;

/**
 * @param {Page} page
 */
export async function login(page) {

  page.exposeFunction('isPlaywright', () => {});

  // Always reset to the roadmap page.
  // But first accept alert dialogs, which
  // can occur in Chrome when not logged in.
  acceptAlertDialogs(page);

  await page.pause();
  // console.log('login: goto /');
  await page.goto('/', {timeout: 20000});
  await page.waitForURL('**/roadmap', {timeout: 20000});

  await delay(1000);
  await expect(page).toHaveTitle(/Chrome Status/);
  page.mouse.move(0, 0); // Move away from content on page.
  await delay(1000);

  // Check whether we are already or still logged in.
  let accountIndicator = page.getByTestId('account-indicator');
  while (await accountIndicator.isVisible()) {
    // console.log('Already (still) logged in. Need to logout.');
    await accountIndicator.hover({timeout: 5000});
    const signOutLink = page.getByTestId('sign-out-link');
    await expect(signOutLink).toBeVisible();

    await signOutLink.hover({timeout: 5000});
    await signOutLink.click({timeout: 5000});

    await delay(1000);
    await page.waitForURL('**/roadmap');
    await expect(page).toHaveTitle(/Chrome Status/);
    page.mouse.move(0, 0); // Move away from content on page.
    await delay(1000);

    accountIndicator = page.getByTestId('account-indicator');
  }
  await delay(1000);

  // Expect login button to be present.
  // console.info('expect login button to be present and visible');
  const loginButton = page.getByTestId('dev-mode-sign-in-button');
  await expect(loginButton).toBeVisible({timeout: loginTimeout});

  await loginButton.click({timeout: 5000, delay: 1000});
  await delay(loginTimeout / 3); // longer delay here, to allow for initial login.

  // Expect the title to contain a substring.
  await expect(page).toHaveTitle(/Chrome Status/);
  page.mouse.move(0, 0); // Move away from content on page.
  await delay(1000);

  // After first login, reduce timeout/delay.
  loginTimeout = 5000;
  // console.log('login: done');
}

/**
 * @param {Page} page
 */
export async function logout(page) {
  // Attempt to sign out after running each test.
  // First reset to the roadmap page, so that we avoid the alert
  // when signed out on other pages.
  // But in case the current page has unsaved changes we need to
  // accept leaving them unsaved.
  acceptBeforeUnloadDialogs(page);

  // console.log('logout: goto /');
  await page.goto('/');
  await page.waitForURL('**/roadmap');
  await delay(1000);
  await expect(page).toHaveTitle(/Chrome Status/);

  page.mouse.move(0, 0); // Move away from content on page.
  await delay(1000);

  if (await isMobile(page)) {
    const menuButton = page.locator('[data-testid=menu]');
    await expect(menuButton).toBeVisible();
    await menuButton.click();
  } else {
    const accountIndicator = page.getByTestId('account-indicator');
    await expect(accountIndicator).toBeVisible({ timeout: 20000 });
    await accountIndicator.hover({timeout: 5000});
  }
  await delay(1000);

  // Need to hover to see the sign-out-link
  const signOutLink = page.getByTestId('sign-out-link');
  await expect(signOutLink).toBeVisible();
  await signOutLink.click({ timeout: 5000 });
  await delay(500);

  await page.waitForURL('**/roadmap');
  await expect(page).toHaveTitle(/Chrome Status/);

  // Redundant? Go to roadmap page.
  await page.goto('/');
  await page.waitForURL('**/roadmap');
  await delay(500);

  // console.log('logout: done');
}


/**
 * From top-level page, after logging in, go to the New Feature page.
 * @param {Page} page
 */
export async function gotoNewFeaturePage(page) {
  // console.log('navigate to create feature page');
  const mobile = await isMobile(page);
  const createFeatureButton = page.getByTestId('create-feature-button');
  const menuButton = page.locator('[data-testid=menu]');

  // Navigate to the new feature page.
  await expect(menuButton).toBeVisible();
  if (mobile) {
    await menuButton.click();  // To show menu.
  }
  await createFeatureButton.click();
  if (mobile) {
    await menuButton.click();  // To hide menu
    await delay(500);
  }

  // Expect "Add a feature" header to be present.
  const addAFeatureHeader = page.getByTestId('add-a-feature');
  await expect(addAFeatureHeader).toBeVisible({ timeout: 10000 });
  // console.log('navigate to create feature page done');
  await delay(500);
}


/**
 * Enters a blink component on the page.
 *
 * @param {Page} page - The page object representing the web page.
 * @return {Promise<void>} A promise that resolves once the blink component is entered.
 */
export async function enterBlinkComponent(page) {
  const blinkComponentsInputWrapper = page.locator('div.datalist-input-wrapper');
  await expect(blinkComponentsInputWrapper).toBeVisible();

  // Trying to show options, doesn't work yet.
  await blinkComponentsInputWrapper.focus();
  await delay(500);

  const blinkComponentsInput = blinkComponentsInputWrapper.locator('input');
  await blinkComponentsInput.fill('blink');
  await delay(500);
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
  await delay(500);

  // Enter summary description
  const summaryInput = page.locator('textarea[name="summary"]');
  await summaryInput.fill('Test summary description');
  await delay(500);

  await enterBlinkComponent(page);

  // Select feature type.
  const featureTypeRadioNew = page.locator('input[name="feature_type"][value="0"]');
  await featureTypeRadioNew.click();
  await delay(500);

  // Submit the form.
  const submitButton = page.locator('input[type="submit"]');
  await submitButton.click();
  await delay(500);

  // Wait until we are on the Feature page.
  await page.waitForURL('**/feature/*');
  await delay(500);
}

export async function gotoNewFeatureList(page) {
  await page.goto('/newfeatures');
  await page.locator('chromedash-feature-pagination');
  await delay(500);
}
