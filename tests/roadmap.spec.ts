import { test, expect } from '@playwright/test';

test('roadmap page test', async ({ page }) => {
  await page.goto('http://localhost:8080/roadmap');
  await expect(page).toHaveScreenshot();
});
