// @ts-check
import {expect, test} from '@playwright/test';
import {
  captureConsoleMessages,
  createNewFeature,
  login,
  logout,
} from './test_utils';

const API_PREFIX = ")]}'\n";

test.beforeEach(async ({page}, testInfo) => {
  captureConsoleMessages(page);
  testInfo.setTimeout(90000);

  // Login before running each test
  await login(page);
});

test.afterEach(async ({page}) => {
  await logout(page);
});

test('Feature detail AI summary generation and review modal workflow', async ({
  page,
}) => {
  // Create a real feature on dev server and land on feature detail page
  await createNewFeature(page);

  const featureDetail = page.locator('chromedash-feature-detail');
  await expect(featureDetail).toBeVisible();

  // Extract featureId from URL
  const url = page.url();
  const featureIdMatch = url.match(/\/feature\/(\d+)/);
  const featureId = featureIdMatch ? featureIdMatch[1] : '1';

  // Mock GET and PATCH for summary suggestions for this specific feature
  await page.route(
    `**/api/v0/summary-suggestions/${featureId}`,
    async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body:
            API_PREFIX +
            JSON.stringify({
              suggestion: {
                feature_id: Number(featureId),
                status: 'PENDING',
                suggested_summary:
                  'AI proposed summary: Enhanced graphics and compute shaders on the web.',
                original_summary: 'Test summary description',
                suggested_doc_links: [],
                version_token: 1,
              },
              progress_steps: [
                {
                  step: 'READ_SPEC',
                  status: 'SUCCESS',
                  message: 'Read specification',
                },
                {
                  step: 'SEARCH_MDN',
                  status: 'SUCCESS',
                  message: 'Found MDN documentation',
                },
              ],
            }),
        });
      } else if (route.request().method() === 'PATCH') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body:
            API_PREFIX +
            JSON.stringify({
              suggestion: {
                feature_id: Number(featureId),
                status: 'APPLIED',
                suggested_summary:
                  'AI proposed summary: Enhanced graphics and compute shaders on the web.',
                version_token: 2,
              },
              progress_steps: [],
            }),
        });
      } else {
        await route.fallback();
      }
    }
  );

  // Trigger review dialog by dispatching completion event on the progress component
  const progressComp = featureDetail.locator('chromedash-ai-summary-progress');
  await expect(progressComp).toBeAttached();

  await progressComp.evaluate((el, fid) => {
    el.dispatchEvent(
      new CustomEvent('summary-generation-completed', {
        bubbles: true,
        composed: true,
        detail: {
          featureId: Number(fid),
          suggestion: {
            feature_id: Number(fid),
            status: 'PENDING',
            suggested_summary:
              'AI proposed summary: Enhanced graphics and compute shaders on the web.',
            original_summary: 'Test summary description',
            suggested_doc_links: [],
            version_token: 1,
          },
          progressSteps: [],
        },
      })
    );
  }, featureId);

  // Verify review dialog is opened
  const slDialog = featureDetail.locator(
    'chromedash-summary-review-dialog sl-dialog'
  );
  await expect(slDialog).toHaveAttribute('open', '');

  // Verify diff view contents
  const diffView = featureDetail.locator('chromedash-summary-diff-view');
  await expect(diffView).toBeVisible();
  await expect(diffView).toContainText('Test summary description');
  await expect(diffView).toContainText('AI proposed summary');

  // Click Accept & Apply in review dialog
  const applyButton = featureDetail.locator(
    'chromedash-summary-review-dialog sl-button[variant="primary"]'
  );
  await expect(applyButton).toBeVisible();
  await applyButton.click();

  // Dialog closes after applying
  await expect(slDialog).not.toHaveAttribute('open', '');
});
