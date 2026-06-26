// @ts-check
import { test, expect } from '@playwright/test';
import {
  captureConsoleMessages,
  createNewFeature,
  loginAs,
} from './test_utils';
import { demoFeatures } from './demo_features';

const API_PREFIX = ")]}'\n";

async function setFeatureCurationDetails(page, featureId, milestone, explainer, spec) {
  console.log(`[Demo 3] Setting curation details (Milestone: ${milestone}, Explainer: ${explainer}, Spec: ${spec})...`);
  await page.goto(`/guide/editall/${featureId}`);
  await page.waitForTimeout(1500); // Visual pause for pacing

  const milestoneInput = page.locator('input[name="shipped_milestone"]');
  await milestoneInput.scrollIntoViewIfNeeded();
  await expect(milestoneInput).toBeVisible();
  await milestoneInput.fill(milestone.toString());
  await page.waitForTimeout(500);

  const explainerInput = page.locator('textarea[name="explainer_links"]');
  await explainerInput.scrollIntoViewIfNeeded();
  await expect(explainerInput).toBeVisible();
  await explainerInput.fill(explainer);
  await page.waitForTimeout(500);

  const specInput = page.locator('input[name="spec_link"]');
  await specInput.scrollIntoViewIfNeeded();
  await expect(specInput).toBeVisible();
  await specInput.fill(spec);
  await page.waitForTimeout(800);

  const saveButton = page.locator('input[type="submit"]');
  await saveButton.click();
  await page.waitForURL(`**/feature/${featureId}`);
  await page.waitForTimeout(2000); // Visual pause after save
}

test('Demo 3: Optimistic Concurrency Conflict Resolution', async ({ page, request }) => {
  // Guard to skip this demo script during standard automated E2E test runs
  if (!process.env.RUN_DEMO) {
    test.skip();
  }
  test.setTimeout(120000); // Give a generous 120s runway for live LLM generation and conflict resolution UI!

  captureConsoleMessages(page);
  await page.route('https://accounts.google.com/**', route => route.abort());

  const response = await request.get('/api/v0/channels');
  const channels = JSON.parse((await response.text()).replace(API_PREFIX, ''));
  const stableMilestone = channels.stable.version;

  console.log('[Demo 3] Step 1: Logging in as Feature Owner');
  await loginAs(page, 'example@chromium.org');
  await page.waitForTimeout(2000);

  console.log('[Demo 3] Step 2: Creating a new real-world feature');
  const targetFeature = demoFeatures.anchorPositioning;
  const uniqueFeatureName = `${targetFeature.name} (Conflict) - ${Date.now()}`;
  await createNewFeature(page, uniqueFeatureName, targetFeature.summary);
  
  const parts = page.url().split('/');
  const featureId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(2000);

  console.log('[Demo 3] Step 3: Setting Shipped Milestone, Explainer, and Spec Links');
  await setFeatureCurationDetails(page, featureId, stableMilestone, targetFeature.explainer, targetFeature.spec);

  console.log('[Demo 3] Step 4: Navigating to Releases Page & Triggering AI Generation');
  await page.goto(`/releases?milestone=${stableMilestone}`);
  const card = page.getByTestId(`feature-card-${featureId}`);
  await expect(card).toBeVisible();
  await card.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1500);

  const generateBtn = card.getByRole('button', { name: 'Generate Summary' });
  await generateBtn.click();

  // Wait for the status badge to change to "Draft Available"
  const suggestionBadge = card.locator('sl-tag[variant="success"]');
  await expect(suggestionBadge).toHaveText(/Draft Available/, { timeout: 75000 });
  await page.waitForTimeout(2000); // Visual pause

  // Set up the mock interceptor to return 409 on first PATCH, 200 on second PATCH
  let patchCount = 0;
  await page.route(`**/api/v0/features/${featureId}/summary_suggestion`, async (route, request) => {
    if (request.method() === 'PATCH') {
      patchCount++;
      if (patchCount === 1) {
        console.log('[Demo 3] Mocking 409 Conflict response from server...');
        await route.fulfill({
          status: 409,
          contentType: 'application/json',
          body: API_PREFIX + JSON.stringify({
            error: 'Conflict: The suggestion has been modified by another request.'
          })
        });
      } else {
        console.log('[Demo 3] Mocking 200 OK response from server...');
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: API_PREFIX + JSON.stringify({
            message: 'AI suggestion status updated successfully.'
          })
        });
      }
    } else {
      await route.continue();
    }
  });

  console.log('[Demo 3] Step 5: Opening the Review Dialog');
  const reviewBtn = card.getByRole('button', { name: /Review.*suggestion/i });
  await reviewBtn.hover();
  await page.waitForTimeout(800);
  await reviewBtn.click();

  const dialog = page.getByRole('dialog', { name: 'Review AI Suggested' });
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(2000); // Symmetrical layout visibility pause

  console.log('[Demo 3] Step 6: Making local edits to the summary');
  const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
  await textarea.click();
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(600);
  
  const conflictingEdit = 'This is a custom edit to the CSS Anchor Positioning summary that will trigger a concurrency conflict on save!';
  await textarea.focus();
  for (const char of conflictingEdit) {
    await page.keyboard.type(char);
    await page.waitForTimeout(30);
  }
  await page.waitForTimeout(1500);

  console.log('[Demo 3] Step 7: Clicking Save & Apply (triggers conflict)');
  const saveBtn = page.getByRole('button', { name: 'Save & Apply' });
  await saveBtn.hover();
  await page.waitForTimeout(800);
  await saveBtn.click({ force: true });

  console.log('[Demo 3] Step 8: Inspecting Conflict Resolution UI');
  // Wait for conflict banner to render
  const conflictBanner = page.locator('.conflict-banner');
  await expect(conflictBanner).toBeVisible();
  await page.waitForTimeout(1500);

  // Verify split panes
  const serverRef = page.getByTestId('server-summary-reference');
  const localRef = page.getByTestId('local-summary-draft-reference');
  await expect(serverRef).toBeVisible();
  await expect(localRef).toBeVisible();
  
  // Highlight the conflict sections by scrolling to them slowly
  await serverRef.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);
  await localRef.scrollIntoViewIfNeeded();
  await page.waitForTimeout(2500); // Allow viewer to inspect the split pane comparison

  console.log('[Demo 3] Step 9: Resolving conflict via "Force Overwrite Server"');
  const forceBtn = page.getByRole('button', { name: 'Force Overwrite Server' });
  await forceBtn.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);
  await forceBtn.hover();
  await page.waitForTimeout(800);
  await forceBtn.click({ force: true });

  // Dialog should close, indicating successful resolution
  await expect(dialog).not.toBeVisible();
  console.log('[Demo 3] Conflict successfully resolved!');
  await page.waitForTimeout(3000); // Hold final screen
});
