import { test, expect } from '@playwright/test';
import '../js-src/cs-client';
import sinon from 'sinon';

/* window.csClient and <chromedash-toast> are initialized at spa.html
 * which are not available here, so we initialize them before each test.
 * We also stub out the API calls here so that they return test data. */
test.beforeEach(async () => {
  await fixture(html`<chromedash-toast></chromedash-toast>`);
  window.csClient = new ChromeStatusClient('fake_token', 1);
  sinon.stub(window.csClient, 'getStars');
  sinon.stub(window.csClient, 'searchFeatures');
  window.csClient.getStars.returns(Promise.resolve([123456]));
});

test.afterEach(() => {
  window.csClient.getStars.restore();
  window.csClient.searchFeatures.restore();
});

test('features page test', async ({ page }) => {
  await page.goto('http://localhost:8080/features');
  await expect(page).toHaveScreenshot();
});
