// @ts-check
import { expect } from '@playwright/test';

/**
 * @param {number | undefined} ms
 */
export async function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}


/**
 * @param {import("playwright-core").Page} page
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
 * @param {import("playwright-core").Page} page
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
 * @param {import("playwright-core").Page} page
 */
export async function decodeCookies(page) {
  const cookies = await page.context().cookies();
  cookies.forEach((cookie) => {
    console.log('Decoded Cookie:', cookie);
  });
}



// Timeout for logging in, in milliseconds.
// Initially set to longer timeout, in case server needs to warm up and
// respond to the login.  Changed to shorter timeout after login is successful.
// Not sure we need this yet.
let loginTimeout = 20000;

/**
 * @param {import("playwright-core").Page} page
 */
export async function login(page) {

  page.exposeFunction('isPlaywright');

  // Always reset to the roadmap page.
  await page.pause();
  // console.log('login: goto /');
  await page.goto('/', {timeout: 20000});
  await page.waitForURL('**/roadmap', {timeout: 20000});

  await delay(1000);
  await expect(page).toHaveTitle(/Chrome Status/);
  page.mouse.move(0, 0); // Move away from content on page.
  await delay(1000);

  // Check whether we are already or still logged in.
  let navContainer = page.locator('[data-testid=nav-container]');
  while (await navContainer.isVisible()) {
    // console.log('Already (still) logged in. Need to logout.');
    await navContainer.hover({timeout: 5000});
    const signOutLink = page.locator('[data-testid=sign-out-link]');
    await expect(signOutLink).toBeVisible();

    await signOutLink.hover({timeout: 5000});
    await signOutLink.click({timeout: 5000});

    await delay(1000);
    await page.waitForURL('**/roadmap');
    await expect(page).toHaveTitle(/Chrome Status/);
    page.mouse.move(0, 0); // Move away from content on page.
    // console.log('Should be logged out ow.');
    await delay(1000);

    navContainer = page.locator('[data-testid=nav-container]');
  }
  await delay(1000);

  // Expect login button to be present.
  // console.info('expect login button to be present and visible');
  const loginButton = page.locator('button[data-testid=dev-mode-sign-in-button]');
  await expect(loginButton).toBeVisible({timeout: loginTimeout});

  await loginButton.click({timeout: 1000, delay: 100});
  await delay(loginTimeout / 3); // longer delay here, to allow for initial login.

  // Expect the title to contain a substring.
  await expect(page).toHaveTitle(/Chrome Status/);
  page.mouse.move(0, 0); // Move away from content on page.
  await delay(6000);

  // Take a screenshot of header that should have "Create feature" button.
  // console.log('take a screenshot of header that should have "Create feature" button');
  await expect(page.locator('[data-testid=header]')).toHaveScreenshot('after-login-click.png');

  // Check that we are logged in now.
  // Expect a nav container to be present.
  // This sometimes fails, even though the screenshot seems correct.
  navContainer = page.locator('[data-testid=nav-container]');
  await expect(navContainer).toBeVisible({timeout: loginTimeout});
  loginTimeout = 5000; // After first login, reduce timeout/delay.

  // console.log('login: done');
}

/**
 * @param {import("playwright-core").Page} page
 */
export async function logout(page) {
  // Attempt to sign out after running each test.
  // First reset to the roadmap page.
  // console.log('logout: goto /');
  await page.goto('/');
  await page.waitForURL('**/roadmap');
  await delay(1000);

  await expect(page).toHaveTitle(/Chrome Status/);
  page.mouse.move(0, 0); // Move away from content on page.
  await delay(1000);

  const navContainer = page.locator('[data-testid=nav-container]');
  await expect(navContainer).toBeVisible({timeout: 20000});
  await delay(1000);

  await navContainer.hover({timeout: 5000});
  const signOutLink = page.locator('[data-testid=sign-out-link]');
  await expect(signOutLink).toBeVisible();

  await signOutLink.hover({timeout: 5000});
  await signOutLink.click({timeout: 5000});

  await page.waitForURL('**/roadmap');
  await expect(page).toHaveTitle(/Chrome Status/);

  // console.log('logout: done');
}
