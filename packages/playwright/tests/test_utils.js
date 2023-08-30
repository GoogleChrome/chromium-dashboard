// @ts-check
import '@playwright/test';

export const delay = (/** @type {number | undefined} */ ms) =>
  new Promise((resolve) => setTimeout(resolve, ms));


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
  page.on('open', async () => {
    console.log(`open: ${page.url()}`);
  });
  page.on('close', async () => {
    console.log(`close: ${page.url()}`);
  });
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
