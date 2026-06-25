// @ts-check
import {test, expect} from '@playwright/test';
import {
  captureConsoleMessages,
  createNewFeature,
  loginAs,
  expectScreenshot,
} from './test_utils';

const API_PREFIX = ")]}'\n";

/**
 * @param {import("playwright-core").Page} page
 * @param {number} featureId
 * @param {{ toString: () => any; }} milestone
 */
async function setShippedMilestone(page, featureId, milestone) {
  console.log(
    `[E2E] Setting shipped milestone for feature ${featureId} to ${milestone}...`
  );
  await page.goto(`/guide/editall/${featureId}`);
  const milestoneInput = page.locator('input[name="shipped_milestone"]');
  await milestoneInput.scrollIntoViewIfNeeded();
  await expect(milestoneInput).toBeVisible();
  await milestoneInput.fill(milestone.toString());
  await milestoneInput.blur();

  const saveButton = page.locator('input[type="submit"]');
  await saveButton.click();
  // Wait until we are redirected back to the feature detail page
  await page.waitForURL(`**/feature/${featureId}`);
}

test.describe('AI Summary Suggestions E2E Integration Tests', () => {
  let featureId;
  /**
   * @type {any}
   */
  let stableMilestone;
  /**
   * @type {number | null}
   */
  let featureIdToDelete = null;

  test.beforeAll(async ({request}) => {
    // Fetch stable milestone dynamically from channels API
    const response = await request.get('/api/v0/channels');
    const channels = JSON.parse(
      (await response.text()).replace(API_PREFIX, '')
    );
    stableMilestone = channels.stable.version;
    console.log(
      `[E2E] Running tests against real stable milestone: ${stableMilestone}`
    );
  });

  test.beforeEach(async ({page}) => {
    captureConsoleMessages(page);
    // Block real Google Accounts GSI scripts
    await page.route('https://accounts.google.com/**', route => route.abort());
  });

  test.afterEach(async ({page}) => {
    if (featureIdToDelete) {
      console.log(
        `[E2E] Cleaning up created feature ID: ${featureIdToDelete}...`
      );
      await page.request.delete(`/api/v0/features/${featureIdToDelete}`);
      featureIdToDelete = null;
    }
    // await logout(page);
  });

  test('Feature Owner (example@chromium.org) happy path review & apply', async ({
    page,
  }) => {
    // 1. Log in as feature owner
    await loginAs(page, 'example@chromium.org');

    // 2. Create a new feature dynamically
    const featureName = `Test feature owner ${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    await createNewFeature(page, featureName);
    const url = page.url();
    const parts = url.split('/');
    featureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = featureId;
    console.log(
      `[E2E] Created new feature ID: ${featureId} with name: ${featureName}`
    );

    // Verify detail page has no suggestion banner initially
    const initBanner = page.locator('sl-alert[variant="primary"]');
    await expect(initBanner).not.toBeVisible();

    // 3. Set shipped milestone to Stable milestone to show on Releases dashboard
    await setShippedMilestone(page, featureId, stableMilestone);

    // E2E DEBUG CHECK: Fetch the feature entity directly via API to verify NDB state
    const debugRes = await page.request.get(`/api/v0/features/${featureId}`);
    const rawResponseText0 = await debugRes.text();
    const XSSIPrefix = ")]}'\n";
    if (!rawResponseText0.startsWith(XSSIPrefix)) {
      throw new Error(
        `Response does not start with XSSI prefix: ${XSSIPrefix}`
      );
    }
    const debugData = JSON.parse(rawResponseText0.substring(XSSIPrefix.length));
    console.log('[E2E DEBUG] Feature API response:', JSON.stringify(debugData));

    // 4. Navigate to Releases dashboard
    const responsePromise = page.waitForResponse(
      response =>
        response.url().includes('/api/v0/features?milestone=') &&
        response.status() === 200
    );
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const apiResponse = await responsePromise;
    const rawResponseText = await apiResponse.text();
    let apiData = {};
    if (rawResponseText.startsWith(XSSIPrefix)) {
      apiData = JSON.parse(rawResponseText.substring(XSSIPrefix.length));
    } else {
      apiData = JSON.parse(rawResponseText);
    }
    console.log(
      '[E2E DEBUG] Releases API response data:',
      JSON.stringify(apiData)
    );

    console.log(
      '[E2E DEBUG] Releases Container Text:',
      await page.locator('.releases-container').innerText()
    );

    const card = page.locator('.feature-card', {hasText: featureName});
    await expect(card).toBeVisible();

    // Verify status is "none" (shows as "Generate Summary" button)
    const generateBtn = card.getByRole('button', {name: 'Generate Summary'});
    await expect(generateBtn).toBeVisible();

    // 5. Trigger generation
    console.log('[E2E] Triggering AI generation...');
    await generateBtn.click();

    // Verify the progress element is rendered and showing details
    const progressTimeline = card.locator('chromedash-ai-summary-progress');
    await expect(progressTimeline).toBeVisible();

    const showDetailsBtn = progressTimeline.locator('.details-toggle-btn');
    await expect(showDetailsBtn).toBeVisible();
    await showDetailsBtn.click();

    // Verify DevOps console tray expands and renders logs
    const consoleTray = progressTimeline.locator('.timeline-console-tray');
    await expect(consoleTray).toBeVisible();

    // Wait until suggestion badge changes to "Draft Available"
    const suggestionBadge = card.locator('sl-tag[variant="success"]');
    await expect(suggestionBadge).toHaveText(/Draft Available/, {
      timeout: 15000,
    });

    // Capture screenshot of releases dashboard badges
    await expectScreenshot(page, 'preleases_dashboard_badges');

    // Verify "Review Suggestion" button is now visible
    const reviewBtn = card.getByRole('button', {name: 'Review Suggestion'});
    await expect(reviewBtn).toBeVisible();

    // 6. Open Review Dialog
    await reviewBtn.click();
    const dialog = page.locator('sl-dialog', {hasText: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    // Capture screenshot of review diff dialog
    await expectScreenshot(page, 'review_diff_dialog');

    // Verify content comparison
    await expect(dialog.getByTestId('original-summary')).toContainText(
      'Test summary description'
    );
    const textarea = dialog.locator('.editable-summary-textarea textarea');
    await expect(textarea).toHaveValue(/This is a mock summary suggestion/);

    // Edit summary text in dialog
    await textarea.fill('AI summary applied successfully by owner.');

    // Save and Apply (since user is owner, no bypass justification is required)
    const saveButton = dialog.getByRole('button', {name: 'Save & Apply'});
    await saveButton.click();

    // Dialog should close
    await expect(dialog).not.toBeVisible();

    // 7. Verify write-back on Feature Detail page
    await page.goto(`/feature/${featureId}`);
    const detailsContainer = page.locator('chromedash-feature-detail');
    await expect(detailsContainer.getByTestId('summary-value')).toContainText(
      'AI summary applied successfully by owner.'
    );
  });

  test('DevRel (devrel@chromium.org) bypass grace period workflow', async ({
    page,
  }) => {
    // 1. Log in as owner, create feature, set milestone, and trigger generation
    await loginAs(page, 'example@chromium.org');
    const featureName = `Test feature devrel ${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    await createNewFeature(page, featureName);
    const parts = page.url().split('/');
    const devFeatureId = parseInt(parts[parts.length - 1], 10);
    featureIdToDelete = devFeatureId;
    await setShippedMilestone(page, devFeatureId, stableMilestone);

    // Trigger generation on releases dashboard
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const card = page.locator('.feature-card', {hasText: featureName});
    await card.getByRole('button', {name: 'Generate Summary'}).click();
    await expect(card.locator('sl-tag[variant="success"]')).toHaveText(
      /Draft Available/,
      {timeout: 10000}
    );
    // 2. Log in as DevRel reviewer (direct session override to bypass UI logout flakiness)
    await loginAs(page, 'devrel@chromium.org');

    // 3. Navigate to Releases dashboard
    await page.goto(`/releases?milestone=${stableMilestone}`);
    const devrelCard = page.locator('.feature-card', {hasText: featureName});
    await devrelCard.getByRole('button', {name: 'Review Suggestion'}).click();

    const dialog = page.locator('sl-dialog', {hasText: 'Review AI Suggested'});
    await expect(dialog).toBeVisible();

    // Click save
    const saveButton = dialog.getByRole('button', {name: 'Save & Apply'});
    await saveButton.click();

    // Justification box should expand (within grace period and user is not owner)
    const justificationTextarea = dialog.locator(
      'sl-textarea[name="bypass_justification"] textarea'
    );
    await expect(justificationTextarea).toBeVisible();

    const confirmButton = dialog.getByRole('button', {name: 'Confirm Bypass'});
    await expect(confirmButton).toBeDisabled();

    // Fill justification and confirm
    await justificationTextarea.fill(
      'DevRel bypassed owner for urgent release notes.'
    );
    await expect(confirmButton).toBeEnabled();

    // Capture screenshot of bypass warning/prompt
    await expectScreenshot(page, 'bypass_justification_prompt');

    await confirmButton.click();
    await expect(dialog).not.toBeVisible();

    // 4. Verify detail page renders warning banner to owner
    // Switch back to owner (direct session override)
    await loginAs(page, 'example@chromium.org');
    await page.goto(`/feature/${devFeatureId}`);

    const banner = page.locator('sl-alert[variant="warning"]');
    await expect(banner).toBeVisible();
    await expect(banner).toContainText('AI Suggestion Applied (Bypassed)');

    // Capture screenshot of detail page banner
    await expectScreenshot(page, 'feature_detail_ai_banner');

    // 5. Owner clicks "Revert to My Original"
    const revertBtn = banner.getByRole('button', {
      name: 'Revert to My Original',
    });
    await expect(revertBtn).toBeVisible();
    await revertBtn.click();

    // Banner should disappear and text should revert to original
    await expect(banner).not.toBeVisible();
    const detailsContainer = page.locator('chromedash-feature-detail');
    await expect(detailsContainer.getByTestId('summary-value')).toContainText(
      'Test summary description'
    );
  });
});
