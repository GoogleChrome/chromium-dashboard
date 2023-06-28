// @ts-check
import {test, expect} from '@playwright/test';

test('has title', async ({page}) => {
  await page.goto('http://localhost:8080/guide/new');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Chrome Status/);
});

test('get started link', async ({page}) => {
  await page.goto('https://playwright.dev/');

  // Click the get started link.
  await page.getByRole('link', {name: 'Get started'}).click();

  // Expects the URL to contain intro.
  await expect(page).toHaveURL(/.*intro/);
});

test('new feature page content', async ({page}) => {
  await page.goto('http://localhost:8080/guide/new');
  await expect(page.locator('#content')).toHaveScreenshot(); // 'new-feature-page-content');
  // await expect(page).toHaveScreenshot();
});
