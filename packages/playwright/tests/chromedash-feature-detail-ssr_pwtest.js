// @ts-check
import {test, expect} from '@playwright/test';
import {
  captureConsoleMessages,
  login,
  logout,
  createNewFeature,
  expectScreenshot,
} from './test_utils';

test.beforeEach(async ({page}, testInfo) => {
  captureConsoleMessages(page);
  testInfo.setTimeout(60000);

  // Login before running each test.
  await login(page);
});

test.afterEach(async ({page}) => {
  // Logout after running each test.
  await logout(page);
});

test('navigate to SSR feature detail page and take snapshot', async ({
  page,
}) => {
  // 1. Create a feature via the standard Playwright UI workflow.
  await createNewFeature(page);

  // 2. Parse the Feature ID from the resulting page URL.
  const url = page.url();
  const featureIdMatch = url.match(/\/feature\/(\d+)/);
  expect(featureIdMatch).not.toBeNull();
  const featureId = featureIdMatch[1];

  // 3. Navigate to our SSR Server-Side Rendered detail page.
  await page.goto(`/feature-ssr/${featureId}`, {timeout: 30000});

  // Wait for the SSR page container to be fully visible and rendered.
  const container = page.locator('#feature-detail-container');
  await expect(container).toBeVisible({timeout: 20000});

  // 4. Sanitize dynamic timestamps (Created / Updated / Accurate as of) to prevent snapshot flakes.
  await page.evaluate(() => {
    const dts = Array.from(document.querySelectorAll('dt'));
    for (const dt of dts) {
      const text = (dt.textContent || '').trim();
      if (
        text.includes('Created') ||
        text.includes('Updated') ||
        text.includes('Accurate as of')
      ) {
        const dd = dt.nextElementSibling;
        if (dd && dd.tagName === 'DD') {
          dd.textContent = 'Jan 1 2026 00:00:00';
        }
      }
    }
  });

  // 5. Take the snapshot baseline and compare it.
  await expectScreenshot(page, 'feature-detail-ssr');
});
