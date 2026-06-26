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
  console.log(`[Demo 4] Setting curation details (Milestone: ${milestone}, Explainer: ${explainer}, Spec: ${spec})...`);
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

test('Demo 4: DevRel Grace Period Bypass & Owner Revert Banner', async ({ page, request }) => {
  captureConsoleMessages(page);
  await page.route('https://accounts.google.com/**', route => route.abort());

  const response = await request.get('/api/v0/channels');
  const channels = JSON.parse((await response.text()).replace(API_PREFIX, ''));
  const stableMilestone = channels.stable.version;

  // Setup: Create feature and draft suggestion as Owner
  console.log('[Demo 4] Setup: Creating real-world feature as Owner');
  await loginAs(page, 'example@chromium.org');
  
  const targetFeature = demoFeatures.anchorPositioning;
  const uniqueFeatureName = `${targetFeature.name} (Bypass) - ${Date.now()}`;
  await createNewFeature(page, uniqueFeatureName, targetFeature.summary);
  
  const parts = page.url().split('/');
  const featureId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(2000);

  console.log('[Demo 4] Setup: Setting Shipped Milestone, Explainer, and Spec Links');
  await setFeatureCurationDetails(page, featureId, stableMilestone, targetFeature.explainer, targetFeature.spec);

  // Navigate to Releases page and generate suggestion
  await page.goto(`/releases?milestone=${stableMilestone}`);
  const card = page.getByTestId(`feature-card-${featureId}`);
  await expect(card).toBeVisible();
  await card.getByRole('button', { name: 'Generate Summary' }).click();
  await expect(card.locator('sl-tag[variant="success"]')).toHaveText(/Draft Available/, { timeout: 25000 });
  await page.waitForTimeout(2000);

  // Step 1: Log in as DevRel reviewer
  console.log('[Demo 4] Step 1: Logging in as DevRel Reviewer');
  await loginAs(page, 'devrel@chromium.org');
  await page.waitForTimeout(1500);

  // Step 2: Navigate to Releases page and open review dialog
  console.log('[Demo 4] Step 2: Opening Review Dialog as DevRel');
  await page.goto(`/releases?milestone=${stableMilestone}`);
  const devrelCard = page.getByTestId(`feature-card-${featureId}`);
  await expect(devrelCard).toBeVisible();
  await devrelCard.getByRole('button', { name: /Review.*suggestion/i }).click();

  const dialog = page.getByRole('dialog', { name: 'Review AI Suggested' });
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(2000); // Symmetrical layout pause

  // Step 3: Triggering Bypass Workflow with a custom summary edit
  console.log('[Demo 4] Step 3: Triggering Bypass by clicking Save & Apply');
  const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
  await textarea.click();
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(500);
  
  const bypassEdit = 'Urgent DevRel release notes summary edit for the CSS Anchor Positioning feature description.';
  await page.keyboard.type(bypassEdit);
  await page.waitForTimeout(1000);

  const saveBtn = page.getByRole('button', { name: 'Save & Apply' });
  await saveBtn.click({ force: true });
  await page.waitForTimeout(1500); // Wait for bypass justification dialog to slide in

  console.log('[Demo 4] Step 4: Entering bypass justification');
  const justificationTextarea = page.locator('sl-textarea[name="bypass_justification"]').locator('textarea');
  await expect(justificationTextarea).toBeVisible();
  await justificationTextarea.focus();
  await page.waitForTimeout(500);
  
  const justification = 'Milestone release is tomorrow; owner is currently OOO and we need to correct positioning terminology.';
  for (const char of justification) {
    await page.keyboard.type(char);
    await page.waitForTimeout(30);
  }
  await page.waitForTimeout(1500);

  // Confirm bypass
  const confirmBtn = page.getByRole('button', { name: 'Confirm Apply Bypass' });
  await expect(confirmBtn).toBeEnabled();
  await confirmBtn.hover();
  await page.waitForTimeout(800);
  await confirmBtn.click({ force: true });

  // Dialog closes
  await expect(dialog).not.toBeVisible();
  await page.waitForTimeout(2000);

  // Step 5: Log back in as Owner to see the warning banner
  console.log('[Demo 4] Step 5: Logging back in as Owner');
  await loginAs(page, 'example@chromium.org');
  await page.waitForTimeout(1500);

  console.log('[Demo 4] Step 6: Viewing owner warning banner on feature detail page');
  await page.goto(`/feature/${featureId}`);
  await page.waitForTimeout(2500); // Allow detail page to load and alert to slide in

  const alertBanner = page.locator('sl-alert[variant="warning"]');
  await expect(alertBanner).toBeVisible();
  await expect(alertBanner).toContainText('AI Suggestion Applied (Bypassed)');
  await page.waitForTimeout(3000); // Pause for recording the warning banner

  console.log('[Demo 4] Step 7: Owner clicks Revert to My Original');
  const revertBtn = alertBanner.getByRole('button', { name: 'Revert to My Original' });
  await revertBtn.hover();
  await page.waitForTimeout(800);
  await revertBtn.click();

  // Banner should disappear
  await expect(alertBanner).not.toBeVisible();
  console.log('[Demo 4] Revert successful and banner dismissed!');
  await page.waitForTimeout(3000); // Hold final screen showing restored original summary
});
