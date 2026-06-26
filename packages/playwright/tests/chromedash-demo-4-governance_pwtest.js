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
  await page.waitForTimeout(1500); // Visual pacing

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
  await page.waitForTimeout(2000);
}

test('Demo 4: Milestone Governance, Locks & Frictionless Reversion', async ({ page, request }) => {
  // Guard to skip this demo script during standard automated E2E test runs
  if (!process.env.RUN_DEMO) {
    test.skip();
  }
  test.setTimeout(200000); // Generous runway for extensive multi-role governance flow!

  captureConsoleMessages(page);
  await page.route('https://accounts.google.com/**', route => route.abort());

  const response = await request.get('/api/v0/channels');
  const channels = JSON.parse((await response.text()).replace(API_PREFIX, ''));
  const stableMilestone = channels.stable.version;

  // Setup: Create feature and apply suggestion
  console.log('[Demo 4] Setup: Creating real-world feature as Owner');
  await loginAs(page, 'example@chromium.org');
  
  const targetFeature = demoFeatures.anchorPositioning;
  const uniqueFeatureName = `${targetFeature.name} (Gov) - ${Date.now()}`;
  await createNewFeature(page, uniqueFeatureName, targetFeature.summary);
  
  const parts = page.url().split('/');
  const featureId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(2000);

  console.log('[Demo 4] Setup: Setting Shipped Milestone, Explainer, and Spec Links');
  await setFeatureCurationDetails(page, featureId, stableMilestone, targetFeature.explainer, targetFeature.spec);

  // Navigate to Release Notes and generate suggestion
  await page.goto(`/release-notes?milestone=${stableMilestone}`);
  const card = page.getByTestId(`feature-card-${featureId}`);
  await expect(card).toBeVisible();
  await card.getByRole('button', { name: 'Generate Summary' }).click();
  await expect(card.locator('sl-tag[variant="success"]')).toHaveText(/Draft Available/, { timeout: 90000 });
  await page.waitForTimeout(2000);

  // Log in as DevRel and apply curation
  console.log('[Demo 4] Setup: Logging in as DevRel to Apply Curation');
  await loginAs(page, 'devrel@chromium.org');
  await page.waitForTimeout(1500);
  await page.goto(`/release-notes?milestone=${stableMilestone}`);
  const devrelCard = page.getByTestId(`feature-card-${featureId}`);
  await expect(devrelCard).toBeVisible();
  await devrelCard.getByRole('button', { name: /Review.*suggestion/i }).click();

  const dialog = page.getByRole('dialog', { name: 'Review AI Suggested' });
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(1500);

  const saveBtn = page.getByRole('button', { name: 'Save & Apply' });
  await saveBtn.click({ force: true });
  await expect(dialog).not.toBeVisible();
  await page.waitForTimeout(2000);

  // Step 1: Log in as Release Coordinator and finalize milestone
  console.log('[Demo 4] Step 1: Milestone Finalization (Release Coordinator locks milestone)');
  // We perform this via a programmatic PATCH fetch inside the page context
  await page.evaluate(async (m) => {
    await window.csClient.ensureTokenIsValid();
    const token = window.csClient.token;
    const resp = await fetch(`/api/v0/milestones/${m}/curation`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'X-Xsrf-Token': token,
      },
      body: JSON.stringify({ status: 'finalized' }),
    });
    if (!resp.ok) {
      throw new Error(`Failed to finalize milestone: ${resp.statusText}`);
    }
  }, stableMilestone);
  console.log('[Demo 4] Milestone finalized successfully!');
  await page.waitForTimeout(2000);

  // Step 2: Log back in as Owner to observe the governance lock
  console.log('[Demo 4] Step 2: Logging in as Feature Owner to observe lock');
  await loginAs(page, 'example@chromium.org');
  await page.waitForTimeout(1500);

  await page.goto(`/release-notes?milestone=${stableMilestone}`);
  const ownerCard = page.getByTestId(`feature-card-${featureId}`);
  await expect(ownerCard).toBeVisible();
  await ownerCard.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1500);

  // Verify grey "Finalized" badge is visible
  const finalizedBadge = ownerCard.locator('sl-tag[variant="neutral"]');
  await expect(finalizedBadge).toHaveText(/Finalized/);
  await page.waitForTimeout(2000);

  // Click "View applied summary"
  const viewAppliedBtn = ownerCard.getByRole('button', { name: 'View applied summary' });
  await expect(viewAppliedBtn).toBeVisible();
  await viewAppliedBtn.hover();
  await page.waitForTimeout(800);
  await viewAppliedBtn.click();

  // Dialog opens in read-only locked state
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(2000);

  console.log('[Demo 4] Step 3: Verifying Governance Lock is active in dialog');
  const finalizedBanner = dialog.locator('.conflict-banner');
  await expect(finalizedBanner).toBeVisible();
  await expect(finalizedBanner).toContainText('Milestone is finalized. Curation is locked.');

  // Verify textarea and other inputs are disabled
  const disabledTextarea = dialog.locator('sl-textarea.editable-summary-textarea');
  await expect(disabledTextarea).toHaveAttribute('disabled', '');
  
  // Verify Save & Apply button is NOT rendered
  const dialogSaveBtn = dialog.getByRole('button', { name: 'Save & Apply' });
  await expect(dialogSaveBtn).not.toBeVisible();
  await page.waitForTimeout(2000);

  // Close dialog
  const closeBtn = dialog.getByRole('button', { name: 'Close' });
  await closeBtn.click();
  await expect(dialog).not.toBeVisible();
  await page.waitForTimeout(1500);

  // Step 4: Frictionless Reversion (Owner makes a Major Edit to original description)
  console.log('[Demo 4] Step 4: Frictionless Reversion (Owner performs major edit to trigger silent demotion)');
  await page.goto(`/guide/editall/${featureId}`);
  await page.waitForTimeout(1500);

  const summaryInput = page.locator('textarea[name="summary"]');
  await summaryInput.scrollIntoViewIfNeeded();
  await summaryInput.focus();
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(500);

  // Fill in a completely brand-new, unrelated description to trigger Major Drift (< 0.85 similarity)
  const majorEditSummary = 'This is a completely brand-new, unrelated description for layout positioning, replacing the old anchor positioning text entirely. It is a major change designed to trigger frictionless reversion.';
  await summaryInput.fill(majorEditSummary);
  await page.waitForTimeout(1000);

  const submitBtn = page.locator('input[type="submit"]');
  await submitBtn.click();
  await page.waitForURL(`**/feature/${featureId}`);
  await page.waitForTimeout(3000); // Allow background Task Queue worker to run and process silent demotion!

  // Step 5: Return to Release Notes page and observe demoted unlocked state
  console.log('[Demo 4] Step 5: Returning to Release Notes to verify silent demotion');
  await page.goto(`/release-notes?milestone=${stableMilestone}`);
  const finalCard = page.getByTestId(`feature-card-${featureId}`);
  await expect(finalCard).toBeVisible();
  await finalCard.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1500);

  // Verify the card's badge has been demoted from "Finalized" back to "Out of Date" (yellow variant="warning")
  const outOfDateBadge = finalCard.locator('sl-tag[variant="warning"]');
  await expect(outOfDateBadge).toHaveText(/Out of Date/);
  await page.waitForTimeout(2000);

  // Click "Review Curation (Drift)"
  const reviewDriftBtn = finalCard.getByRole('button', { name: 'Review Curation (Drift)' });
  await expect(reviewDriftBtn).toBeVisible();
  await reviewDriftBtn.hover();
  await page.waitForTimeout(800);
  await reviewDriftBtn.click();

  // Dialog opens showing Major Drift and is UNLOCKED
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(2000);

  console.log('[Demo 4] Step 6: Verifying workspace is unlocked but one-click merge is disabled for Major Drift');
  // Major Drift warning banner is visible
  const driftWarningBanner = dialog.locator('sl-alert[variant="warning"]');
  await expect(driftWarningBanner).toBeVisible();
  await expect(driftWarningBanner).toContainText('Major Drift: The original summary has changed significantly.');

  // The "Keep Curated Version" button is disabled!
  const keepCuratedBtn = dialog.getByRole('button', { name: 'Keep Curated Version' });
  await expect(keepCuratedBtn).toBeDisabled();

  // Textarea is editable again (lock was demoted!)
  const editableTextarea = dialog.locator('sl-textarea.editable-summary-textarea');
  await expect(editableTextarea).not.toHaveAttribute('disabled', '');
  await page.waitForTimeout(3000); // Hold final screen showing active, editable workspace

  // Close dialog and finish
  const cancelBtn = dialog.getByRole('button', { name: 'Cancel' });
  await cancelBtn.click();
  await expect(dialog).not.toBeVisible();
  await page.waitForTimeout(2000);
});
