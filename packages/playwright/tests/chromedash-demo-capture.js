// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages,
  createNewFeature,
  loginAs,
} from './test_utils';

const API_PREFIX = ")]}'\n";

/**
 * Helper to set shipped milestone on the editall page
 * @param {import("playwright-core").Page} page
 * @param {number} featureId
 * @param {number} milestone
 */
async function setShippedMilestone(page, featureId, milestone) {
  console.log(`[DEMO] Setting shipped milestone for feature ${featureId} to ${milestone}...`);
  await page.goto(`/guide/editall/${featureId}`);
  await page.waitForTimeout(1000); // Gentle delay for visual clarity

  const milestoneInput = page.locator('input[name="shipped_milestone"]');
  await milestoneInput.scrollIntoViewIfNeeded();
  await expect(milestoneInput).toBeVisible();
  await milestoneInput.fill(milestone.toString());
  await milestoneInput.blur();
  await page.waitForTimeout(1000);

  const saveButton = page.locator('input[type="submit"]');
  await saveButton.click();
  await page.waitForURL(`**/feature/${featureId}`);
  await page.waitForTimeout(1500);
}

test.describe('AI-Assisted Release Notes Demo Capture', () => {
  let featureId;
  let stableMilestone;
  let featureIdToDelete = null;

  test.beforeAll(async ({ request }) => {
    // Seed Blink components
    console.log('[DEMO] Seeding Blink components...');
    await request.get('/cron/update_blink_components');

    // Retrieve the active Stable milestone version
    const response = await request.get('/api/v0/channels');
    const channels = JSON.parse((await response.text()).replace(API_PREFIX, ''));
    stableMilestone = channels.stable.version;
    console.log(`[DEMO] Target Stable Milestone determined as: M${stableMilestone}`);
  });

  test.beforeEach(async ({ page }) => {
    captureConsoleMessages(page);
    await page.route('https://accounts.google.com/**', route => route.abort());
  });

  test.afterEach(async ({ page }) => {
    if (featureIdToDelete) {
      console.log(`[DEMO CLEANUP] Removing temporary feature ID: ${featureIdToDelete}...`);
      const xsrfToken = await page.evaluate(() => {
        // @ts-ignore
        return window.csClient ? window.csClient.token : '';
      });
      await page.request.delete(`/api/v0/features/${featureIdToDelete}`, {
        headers: { 'X-Xsrf-Token': xsrfToken }
      });
    }
  });

  test('Walkthrough: Create, Generate, Review, and Apply Release Notes', async ({ page }) => {
    // 1. Log in as a Feature Owner
    console.log('\n>>> STEP 1: LOGGING IN AS FEATURE OWNER <<<');
    await loginAs(page, 'example@chromium.org');
    await page.waitForTimeout(2000);

    // 2. Create a new feature
    console.log('\n>>> STEP 2: CREATING A NEW FEATURE ENTRY <<<');
    const uniqueFeatureName = `📦 AI release notes demo - ${Date.now()}`;
    await createNewFeature(page, uniqueFeatureName);
    
    const currentUrl = page.url();
    const urlParts = currentUrl.split('/');
    featureId = parseInt(urlParts[urlParts.length - 1], 10);
    featureIdToDelete = featureId;
    console.log(`[DEMO] Feature created successfully. ID: ${featureId}`);
    await page.waitForTimeout(2000);

    // 3. Set Shipped Milestone to stable
    console.log('\n>>> STEP 3: ASSIGNING SHIPPED MILESTONE <<<');
    await setShippedMilestone(page, featureId, stableMilestone);

    // 4. Navigate to the Releases page
    console.log('\n>>> STEP 4: NAVIGATING TO RELEASES PAGE <<<');
    await page.goto(`/releases?milestone=${stableMilestone}`);
    await page.waitForTimeout(3000); // Visual pause to absorb the page layout

    const card = page.getByTestId(`feature-card-${featureId}`);
    await expect(card).toBeVisible();
    await card.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1500);

    // Verify "Generate Summary" button is visible
    const generateBtn = card.getByRole('button', { name: 'Generate Summary' });
    await expect(generateBtn).toBeVisible();

    // 5. Trigger AI Summary generation
    console.log('\n>>> STEP 5: TRIGGERING AI SUMMARY GENERATION <<<');
    await generateBtn.click();
    console.log('[DEMO] Generation triggered. Waiting for Gemini draft to complete...');

    // Wait for the status badge to change to "Draft Available"
    const draftBadge = card.locator('sl-tag[variant="success"]');
    await expect(draftBadge).toHaveText(/Draft Available/, { timeout: 15000 });
    await page.waitForTimeout(2000); // Visual pause

    // 6. Open the side-by-side Review Dialog
    console.log('\n>>> STEP 6: OPENING INTERACTIVE REVIEW WORKSPACE <<<');
    const reviewBtn = card.getByRole('button', { name: /Review.*suggestion/i });
    await expect(reviewBtn).toBeVisible();
    await reviewBtn.click();

    const dialog = page.getByRole('dialog', { name: 'Review AI Suggested' });
    await expect(dialog).toBeVisible();
    await page.waitForTimeout(3000); // Visual pause to highlight the side-by-side layout

    // Verify dialog elements
    const originalSummary = page.getByTestId('original-summary');
    await expect(originalSummary).toContainText('Test summary description');
    
    const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
    await expect(textarea).toHaveValue(/This is a mock summary suggestion/);

    // 7. Toggle tabs to show Markdown Preview
    console.log('\n>>> STEP 7: DEMONSTRATING WRITE & PREVIEW TABS <<<');
    const previewTab = page.getByRole('tab', { name: 'Preview' });
    await previewTab.click();
    await page.waitForTimeout(2000); // Pause on Preview mode

    const writeTab = page.getByRole('tab', { name: 'Write' });
    await writeTab.click();
    await page.waitForTimeout(1000);

    // 8. Edit the AI-suggested release notes
    console.log('\n>>> STEP 8: POLISHING THE DRAFT SUMMARY <<<');
    await textarea.clear();
    await page.waitForTimeout(500);
    
    const polishedSummary = 'This is a **hand-polished, highly professional** release note summary. It describes how developers can leverage our new capabilities immediately!';
    // Type out slowly for human-like demonstration effect
    for (const char of polishedSummary) {
      await textarea.type(char);
      await page.waitForTimeout(20); // typing cadence
    }
    await page.waitForTimeout(1500);

    // Show Markdown Preview again with updated text
    await previewTab.click();
    console.log('[DEMO] Verifying rendered HTML in Preview mode...');
    const previewContainer = page.getByTestId('summary-preview-container');
    await expect(previewContainer.locator('strong')).toHaveText('hand-polished, highly professional');
    await page.waitForTimeout(2500); // Visual pause on rendered markdown

    // Back to Write tab
    await writeTab.click();
    await page.waitForTimeout(1000);

    // 9. Save and Apply the release notes
    console.log('\n>>> STEP 9: APPLYING FINALIZED RELEASE NOTES <<<');
    const saveButton = page.getByRole('button', { name: 'Save & Apply' });
    const patchPromise = page.waitForResponse(
      r => r.url().includes('/summary_suggestion') && r.request().method() === 'PATCH' && r.status() === 200
    );
    await saveButton.click({ force: true });
    await patchPromise;

    // Verify dialog closes
    await expect(dialog).not.toBeVisible();
    console.log('[DEMO] Suggestion successfully applied.');
    await page.waitForTimeout(2000);

    // 10. Visit the final Feature Detail page to show the applied state
    console.log('\n>>> STEP 10: VERIFYING APPLIED STATE ON DETAIL PAGE <<<');
    await page.goto(`/feature/${featureId}`);
    await page.waitForTimeout(2000);

    // Expand metadata if needed
    const metadataBtn = page.getByRole('button', { name: 'Metadata' });
    if (await metadataBtn.isVisible()) {
      await metadataBtn.click();
      await page.waitForTimeout(1000);
    }

    const summaryValue = page.getByTestId('summary-value');
    await expect(summaryValue).toContainText('hand-polished, highly professional');
    console.log('[DEMO] Confirmed: Polished release notes are successfully saved to the feature entry!');
    await page.waitForTimeout(3000); // Final triumph pause
  });
});
