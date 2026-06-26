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
  console.log(`[Demo 2] Setting curation details (Milestone: ${milestone}, Explainer: ${explainer}, Spec: ${spec})...`);
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

async function typeSlowly(page, locator, text) {
  console.log(`[Demo 2] Typing slowly: "${text}"`);
  await locator.focus();
  for (const char of text) {
    await page.keyboard.type(char);
    await page.waitForTimeout(45); // 45ms per char for natural visual typing pacing
  }
  await page.waitForTimeout(500);
}

test('Demo 2: Symmetrical Review Dialog Workspace & Markdown Editing', async ({ page, request }) => {
  // Guard to skip this demo script during standard automated E2E test runs
  if (!process.env.RUN_DEMO) {
    test.skip();
  }
  test.setTimeout(120000); // Give a generous 120s runway for live LLM generation and extensive slow-mo UI editing!

  captureConsoleMessages(page);
  await page.route('https://accounts.google.com/**', route => route.abort());

  const response = await request.get('/api/v0/channels');
  const channels = JSON.parse((await response.text()).replace(API_PREFIX, ''));
  const stableMilestone = channels.stable.version;

  console.log('[Demo 2] Step 1: Logging in as Feature Owner');
  await loginAs(page, 'example@chromium.org');
  await page.waitForTimeout(2000);

  console.log('[Demo 2] Step 2: Creating a new real-world feature');
  const targetFeature = demoFeatures.anchorPositioning;
  const uniqueFeatureName = `${targetFeature.name} (Review) - ${Date.now()}`;
  await createNewFeature(page, uniqueFeatureName, targetFeature.summary);
  
  const parts = page.url().split('/');
  const featureId = parseInt(parts[parts.length - 1], 10);
  await page.waitForTimeout(2000);

  console.log('[Demo 2] Step 3: Setting Shipped Milestone, Explainer, and Spec Links');
  await setFeatureCurationDetails(page, featureId, stableMilestone, targetFeature.explainer, targetFeature.spec);

  console.log('[Demo 2] Step 4: Navigating to Release Notes Page & Triggering AI Generation');
  await page.goto(`/release-notes?milestone=${stableMilestone}`);
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

  console.log('[Demo 2] Step 5: Clicking "Review Suggestion"');
  const reviewBtn = card.getByRole('button', { name: /Review.*suggestion/i });
  await reviewBtn.hover();
  await page.waitForTimeout(800);
  await reviewBtn.click();

  console.log('[Demo 2] Step 6: Symmetrical dialog opened');
  const dialog = page.getByRole('dialog', { name: 'Review AI Suggested' });
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(2500); // Pause to let the viewer see the symmetrical layout

  console.log('[Demo 2] Step 7: Demonstrating Workspace Tabs');
  const previewTab = page.getByRole('tab', { name: 'Preview' });
  const diffTab = page.getByRole('tab', { name: 'Visual Diff' });
  const editTab = page.getByRole('tab', { name: 'Review & Edit' });
  
  await previewTab.hover();
  await page.waitForTimeout(500);
  await previewTab.click();
  await page.waitForTimeout(1500); // Look at live preview of generated text

  await editTab.hover();
  await page.waitForTimeout(500);
  await editTab.click();
  await page.waitForTimeout(1000);

  console.log('[Demo 2] Step 8: Editing the summary with Markdown in slow-mo');
  const textarea = page.locator('sl-textarea.editable-summary-textarea').locator('textarea');
  await textarea.click();
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(800);

  // Type a polished summary that relates directly to the real feature!
  const polishedSummary = `This feature **simplifies tooltip and popup positioning** by introducing a native browser-supported anchoring workflow. It tether-positions elements relative to one or more anchor elements, eliminating the need for JavaScript!`;
  await typeSlowly(page, textarea, polishedSummary);
  await page.waitForTimeout(1500);

  console.log('[Demo 2] Step 9: Toggling to Visual Diff tab to show line-by-line diff');
  await diffTab.click();
  await page.waitForTimeout(2500); // Look at visual diff highlights

  console.log('[Demo 2] Step 10: Approving / Pruning documentation links');
  await editTab.click();
  await page.waitForTimeout(1000);

  // Locate the checkbox items using data-testid
  const firstCheckbox = page.getByTestId('link-checkbox-0');
  if (await firstCheckbox.isVisible()) {
    await firstCheckbox.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await firstCheckbox.hover();
    await page.waitForTimeout(500);
    await firstCheckbox.click(); // Toggle approval state
    await page.waitForTimeout(1200);
  }

  console.log('[Demo 2] Step 11: Overriding WebDX Baseline status cards');
  const baselineNewlyRadio = page.getByRole('radio', { name: 'Baseline Newly Available' });
  await baselineNewlyRadio.scrollIntoViewIfNeeded();
  await page.waitForTimeout(800);
  await baselineNewlyRadio.hover();
  await page.waitForTimeout(500);
  await baselineNewlyRadio.click();
  await page.waitForTimeout(1500); // Observe Newly Available date field expanding

  // Fill in Newly Available Date
  const newlyDateInput = page.getByLabel('Newly Available Date');
  await newlyDateInput.focus();
  await page.waitForTimeout(500);
  await newlyDateInput.fill('2026-06-25');
  await page.waitForTimeout(1500);

  console.log('[Demo 2] Step 12: Saving & Applying edits');
  const saveBtn = page.getByRole('button', { name: 'Save & Apply' });
  await saveBtn.hover();
  await page.waitForTimeout(800);
  await saveBtn.click({ force: true });

  // Dialog closes, back to dashboard
  await expect(dialog).not.toBeVisible();
  await page.waitForTimeout(2000);

  console.log('[Demo 2] Step 13: Simulating Curation Drift (Feature Owner edits original description)');
  await page.goto(`/guide/editall/${featureId}`);
  await page.waitForTimeout(1500);
  
  const summaryInput = page.locator('textarea[name="summary"]');
  await summaryInput.scrollIntoViewIfNeeded();
  await summaryInput.focus();
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(500);
  // Minor edit adding a sentence to the original description
  await summaryInput.fill(targetFeature.summary + " Note: This native workflow offers substantial CPU savings on layout passes.");
  await page.waitForTimeout(1000);
  
  const submitBtn = page.locator('input[type="submit"]');
  await submitBtn.click();
  await page.waitForURL(`**/feature/${featureId}`);
  await page.waitForTimeout(2000);

  console.log('[Demo 2] Step 14: Returning to Release Notes page to observe yellow Out of Date badge');
  await page.goto(`/release-notes?milestone=${stableMilestone}`);
  await card.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1500);

  // Verify the yellow Out of Date badge is visible
  const outOfDateBadge = card.locator('sl-tag[variant="warning"]');
  await expect(outOfDateBadge).toHaveText(/Out of Date/);
  await page.waitForTimeout(2000);

  console.log('[Demo 2] Step 15: Clicking "Review Curation (Drift)" to resolve the drift');
  const reviewDriftBtn = card.getByRole('button', { name: 'Review Curation (Drift)' });
  await reviewDriftBtn.hover();
  await page.waitForTimeout(800);
  await reviewDriftBtn.click();

  // Dialog opens showing the Smart Merge Panel!
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(2000);

  console.log('[Demo 2] Step 16: Clicking "Keep Curated Version" to dismiss the drift warning');
  const keepCuratedBtn = page.getByRole('button', { name: 'Keep Curated Version' });
  await expect(keepCuratedBtn).toBeVisible();
  await keepCuratedBtn.hover();
  await page.waitForTimeout(800);

  // Intercept confirm() dialog because Playwright automatically dismisses alerts by default!
  page.once('dialog', async d => {
    console.log(`[Demo 2] Confirm dialog popped up: "${d.message()}". Clicking OK.`);
    await d.accept();
  });
  await keepCuratedBtn.click();

  // Dialog closes, back to dashboard, drift resolved
  await expect(dialog).not.toBeVisible();
  await page.waitForTimeout(1500);

  // Verify the card's badge has returned to "Applied"
  const finalBadge = card.locator('sl-tag[variant="primary"]');
  await expect(finalBadge).toHaveText(/Applied/);
  await page.waitForTimeout(3000); // Hold final screen
});
