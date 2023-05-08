import { test, expect } from '@playwright/test';

test('myfeatures page test', async ({ page }) => {
  await page.goto('http://localhost:8080/myfeatures');
  await expect(page).toHaveScreenshot();
});
