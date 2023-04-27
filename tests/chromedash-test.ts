import { test, expect } from '@playwright/test';

import { html } from 'lit';
// import {assert, fixture} from '@open-wc/testing';
import {ChromedashAllFeaturesPage} from './chromedash-all-features-page';
import './chromedash-toast';
import '../js-src/cs-client';
import sinon from 'sinon';

test.describe('chromedash-all-features-page', () => {
  /* window.csClient and <chromedash-toast> are initialized at spa.html
   * which are not available here, so we initialize them before each test.
   * We also stub out the API calls here so that they return test data. */
  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'getStars');
    sinon.stub(window.csClient, 'searchFeatures');
    window.csClient.getStars.returns(Promise.resolve([123456]));
  });

  afterEach(() => {
    window.csClient.getStars.restore();
    window.csClient.searchFeatures.restore();
  });

    it('render with no data', async () => {
        const invalidFeaturePromise = Promise.reject(new Error('Got error response from server'));
        window.csClient.searchFeatures.returns(invalidFeaturePromise);
        const component = await fixture(
            html`<chromedash-all-features-page></chromedash-all-features-page>`);

    });

test('has title', async ({ page }) => {
  await page.goto('https://playwright.dev/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Playwright/);
});

test('get started link', async ({ page }) => {
  await page.goto('https://playwright.dev/');

  // Click the get started link.
  await page.getByRole('link', { name: 'Get started' }).click();

  // Expects the URL to contain intro.
  await expect(page).toHaveURL(/.*intro/);
});

test('example test', async ({ page }) => {
  await page.goto('https://playwright.dev/');
  await expect(page).toHaveScreenshot();
});
