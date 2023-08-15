// @ts-check
import {test, expect} from '@playwright/test';

// import playwright from "playwright";

// (async () => {
//   // Capture console messages at top level.  No idea if we need this.
//   const browser = await playwright.chromium.launch();
//   const context = await browser.newContext();
//   const page = await context.newPage();
//   let consoleMsgs = []
//   page.on("console", (message) => {
//     // if (message.type() === "error") {
//     // consoleMsgs.push([message.type(), message.text()])
//     // }
//     console.log(message.type(), message.text());
//   });
//   await page.evaluate(() => {
//     console.log("hello from the browser console.log");
//     // console.info("hello from the browser console.info");
//     // console.error("hello from the browser console.error");
//   });
//   if (consoleMsgs.length > 0) {
//     console.log('console messages: ', consoleMsgs);
//     consoleMsgs = [];
//   }
//   await browser.close();
//   // if (consoleMsgs.length > 0) {
//   //   console.log('After browser.close(); console messages: ', consoleMsgs);
//   //   consoleMsgs = [];
//   // }

//     // // Wait for all messages to be received.
//     // await page.waitForNavigation();

//     // // Close the browser instance.
//     // await browser.close();
//  })();

const delay = (/** @type {number | undefined} */ ms) =>
  new Promise((resolve) => setTimeout(resolve, ms));


function captureConsoleMessages(page) {
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

function capturePageEvents(page) {
  page.on('open', async () => {
    console.log(`open: ${page.url()}`);
  });
  page.on('close', async () => {
    console.log(`close: ${page.url()}`);
  });
  // page.on('request', async (/** @type {Request} */ request) => {
  //   console.log(`request: ${request.url()}`);
  // });
  // page.on('response', async (/** @type {Response} */ response) => {
  //   console.log(`response: ${response.url()}`);
  // });
  // page.on('requestfinished', request => {
  //   console.log(`requestfinished: ${request.url()}`);
  // });
  page.on('requestfailed', request => {
    console.log(`requestfailed: ${request.url()} with: ${request.failure().errorText}`);
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

// Timeout for logging in, in milliseconds.
// Initially set to longer timeout, in case server needs to warm up and
// respond to the login.  Changed to shorter timeout after login is successful.
// Not sure we need this yet.
let loginTimeout = 30000;

async function login(page) {
  // await expect(page).toHaveScreenshot('roadmap.png');
  // Always reset to the roadmap page.
  console.log('login: goto /');
  await page.goto('/', {timeout: 20000});
  await page.waitForURL('**/roadmap', {timeout: 20000});

  await delay(1000);
  await expect(page).toHaveTitle(/Chrome Status/);
  page.mouse.move(0, 0); // Move away from content on page.

  await delay(1000);
  // Check whether we are already or still logged in.
  let navContainer = page.locator('[data-testid=nav-container]');
  while (await navContainer.isVisible()) {
    console.log('Already (still) logged in. Need to logout.');
    await navContainer.hover({timeout: 5000});
    const signOutLink = page.locator('[data-testid=sign-out-link]');
    await expect(signOutLink).toBeVisible();

    await signOutLink.hover({timeout: 5000});
    await signOutLink.click({timeout: 5000});

    await delay(1000);
    await page.waitForURL('**/roadmap');
    await expect(page).toHaveTitle(/Chrome Status/);
    page.mouse.move(0, 0); // Move away from content on page.
    console.log('Should be logged out ow.');

    await delay(1000);
    navContainer = page.locator('[data-testid=nav-container]');
  }

  // Expect login button to be present.
  console.info('expect login button to be present and visible');
  const loginButton = page.locator('button[data-testid=dev-mode-sign-in-button]');
  await expect(loginButton).toBeVisible({timeout: loginTimeout});

  await delay(1000);

  // // Expect nav container to not be present.
  // const navContainer = page.locator('[data-testid=nav-container]');
  // await expect(navContainer).toHaveCount(0);

  // // Take a screenshot of the initial page before login.
  // if (!loginScreenshots) {
  //   await expect(page).toHaveScreenshot('before-login.png');
  // }

  // Need to wait for the google signin button to be ready, to avoid
  // loginButton.waitFor('visible');
  await loginButton.click({timeout: 1000, delay: 100, noWaitAfter: true});
  await delay(1000);

  // await page.goto('/', {timeout: 30000});
  // await page.waitForURL('**/roadmap', {timeout: 20000});

  // Expect the title to contain a substring.
  await expect(page).toHaveTitle(/Chrome Status/);
  page.mouse.move(0, 0); // Move away from content on page.
  await delay(loginTimeout / 3); // longer delay here, to allow for initial login.

  // Take a screenshot of header that should have "Create feature" button.
  await expect(page.locator('[data-testid=header]')).toHaveScreenshot('after-login-click.png');
  // was; await expect(page).toHaveScreenshot('after-login-click.png');

  // Check that we are logged in now.
  // Expect a nav container to be present.
  // This sometimes fails, even though the screenshot seems correct.
  navContainer = page.locator('[data-testid=nav-container]');
  await expect(navContainer).toBeVisible({timeout: loginTimeout});
  loginTimeout = 10000; // After first login, reduce timeout.

  // if (!loginScreenshots) {
  //   // Take a screenshot of the page after login.
  //   await expect(page).toHaveScreenshot('after-login.png', {timeout: 10000});
  //   loginScreenshots = true;
  // }
  console.log('login: done');
}

// let logoutScreenshots = false;

async function logout(page) {
  // Attempt to sign out after running each test.
  // First reset to the roadmap page.
  console.log('logout: goto /');
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
  // if (!logoutScreenshots) {
  //   await expect(page).toHaveScreenshot('sign-out-link.png');
  // }
  await signOutLink.click({timeout: 5000});

  await page.waitForURL('**/roadmap');
  // await page.goto('/');
  // await page.waitForURL('**/roadmap');
  await expect(page).toHaveTitle(/Chrome Status/);
  // page.mouse.move(0, 0); // Move away from content on page.

  // await page.goto('/');
  // await page.waitForURL('**/roadmap');
  // page.mouse.move(0, 0); // Move away from content on page.

  // if (!logoutScreenshots) {
  //   await expect(page).toHaveScreenshot('after-sign-out.png', { timeout: 10000 });
  //   logoutScreenshots = true;
  // }

  // Wait for sign in button to appear.
  // This sometimes fails, even though the screenshot seems correct.
  // const loginButton = page.locator('[data-testid=dev-mode-sign-in-button]');
  // await loginButton.waitFor('visible', {timeout: 10000});
  // await expect(loginButton).toBeVisible({timeout: 10000});
  console.log('logout: done');
}


test.beforeEach(async ({page}) => {
  captureConsoleMessages(page);
  capturePageEvents(page);
  test.setTimeout(60000 + loginTimeout);
  // Attempt to login before running each test.
  await login(page);
});

test.afterEach(async ({page}) => {
  test.setTimeout(60000 + loginTimeout);
  await logout(page);
});


test('navigate to create feature page', async ({page}) => {
  console.log('navigate to create feature page');
  // await page.goto('/');
  // await page.waitForURL('**/roadmap');

  // Take a screenshot of header with "Create feature" button.
  // await expect(page.locator('header')).toHaveScreenshot('create-feature-button-check.png');

  // Expect create feature button to be present.
  const createFeatureButton = page.locator('[data-testid=create-feature-button]');
  await expect(createFeatureButton).toBeVisible({timeout: 30000});

  // Take a screenshot of header with "Create feature" button.
  await expect(page.locator('[data-testid=header]')).toHaveScreenshot('create-feature-button.png');

  // Navigate to the new feature page by clicking.
  createFeatureButton.click();
  // await page.waitForURL('**/guide/new', {timeout: 20000});

  // Expect "Add a feature" header to be present.
  const addAFeatureHeader = page.locator('[data-testid=add-a-feature]');
  await expect(addAFeatureHeader).toBeVisible();

  // Take a screenshot of the content area.
  await expect(page).toHaveScreenshot('new-feature-page.png');
  console.log('navigate to create feature page done');
});

// test('new feature page content', async ({page}) => {
//   // Navigate to the new feature page.
//   await page.goto('/guide/new', {timeout: 20000});
//   // await page.waitForURL('**/guide/new', {timeout: 30000});

//   // Expect "Add a feature" header to be present.
//   const addAFeatureHeader = page.locator('[data-testid=add-a-feature]');
//   await expect(addAFeatureHeader).toBeVisible({timeout: 30000});

//   // Take a screenshot
//   await expect(page.locator('chromedash-guide-new-page'))
//     .toHaveScreenshot('new-feature-page-content.png');
// });

test('enter feature name', async ({page}) => {
  console.log('enter feature name');
  test.setTimeout(90000);

  // Navigate to the new feature page.
  const createFeatureButton = page.locator('[data-testid=create-feature-button]');
  createFeatureButton.click({timeout: 10000});

  const featureNameInput = page.locator('input[name="name"]');
  await expect(featureNameInput).toBeVisible({timeout: 60000});

  // Expand the extra help.
  const extraHelpButton = page.locator('chromedash-form-field[name="name"] sl-icon-button');
  await expect(extraHelpButton).toBeVisible();
  extraHelpButton.click();

  // Enter a feature name.
  featureNameInput.fill('Test feature name');

  await expect(page).toHaveScreenshot('feature-name.png');
  console.log('enter feature name done');
});
